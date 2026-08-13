"""Aviation NLP Pipeline — Terminal UI (menu-driven).

Run:  python app.py

Numbered menu (always available, re-open with 'm'):

  1 · Fetch / Refresh dataset     4 · RAG explainer       7 · Exit
  2 · View datasets               5 · NLP data assistant
  3 · Train model                 6 · Pipeline log

Every operation renders *visually* in the terminal: a stage label plus a
live progress bar (`[███░░░░] STREAMING ASRS REPORTS ...`) driven by REAL
work — actual rows downloaded, documents NLTK-preprocessed, minibatches
fitted, embeddings matched. No fake staged animation.

The fetch step LIVE-DOWNLOADS real domain safety data every run:
  * NASA ASRS aviation incident reports (Hugging Face datasets-server)
  * NERC power-grid event analysis reports (public PDFs)
cleaned and merged into one Domain-tagged dataset.

The NLP data assistant (option 5) inspects the loaded dataset without any
LLM: it reports data-quality issues, class balance, the domain split and
the safety-criticality of anomaly categories, and it scans any pasted
report narrative for high-risk phrases.

CLI:  python app.py --fetch | --train | --explain <text>
"""
import sys
from pathlib import Path

import pandas as pd
from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import (Button, DataTable, Footer, Header, Input,
                             ProgressBar, RichLog, Select, Static,
                             TabbedContent, TabPane, TextArea)
from textual.worker import WorkerState

from pipeline import analyst, fetch_data, train_model
from pipeline.paths import (DEFAULT_DATASET, DEFAULT_MODEL, find_datasets)
from pipeline.rag_explainer import explain_incident

SAMPLE_REPORT = ("I was cleared for the ILS approach but misheard the altitude "
                 "restriction due to heavy static on the radio frequency. I "
                 "descended to 3000 feet instead of 5000. ATC immediately called "
                 "and issued a climb instruction to avoid terrain. Checklist was "
                 "complete.")

MENU_TEXT = """
[bold cyan]   SAFETY NLP PIPELINE  —  ASRS Aviation  ·  NERC Power Grid  ·  TF-IDF  ·  RAG[/]

   [bold]1[/] · Fetch / Refresh dataset         [bold]4[/] · RAG explainer
   [bold]2[/] · View datasets                  [bold]5[/] · NLP data assistant
   [bold]3[/] · Train model                    [bold]6[/] · Pipeline log
                                              [bold]7[/] · Exit

[dim]   Press a number, or 'Esc' to go straight to the console.[/]
"""

CSS = """
Screen { layout: vertical; }
#pipeline_bar { height: 1; padding: 0 1; color: $text-muted; }
#pipeline_bar .done { color: $success; text-style: bold; }
#pipeline_bar .skip { color: $text-muted; }
#pipeline_bar .busy { color: $warning; text-style: bold; }
#progress_row { height: 1; padding: 0 1; }
#stage_label { width: 36; color: $accent; text-style: bold; }
#progress { width: 1fr; }
TabbedContent { height: 1fr; }

#dataset_hint { padding: 1 2; color: $text-muted; }
#preview_table { height: 1fr; }
#distribution_table { height: 1fr; }

#train_hint { padding: 1 2; }
#report_text { height: 1fr; padding: 1 2; border: round $accent; }
#report_text .accent { color: $accent; text-style: bold; }
#report_text .good { color: $success; text-style: bold; }

#rag_input { height: 6; border: round $accent; padding: 1; }
#rag_result { height: 1fr; padding: 1 2; border: round $accent; }
#rag_result .category { color: $success; text-style: bold; }
#rag_result .warn { color: $warning; }
#rag_result .muted { color: $text-muted; }

#assistant_chips { height: auto; }
#assistant_log { height: 1fr; }
#assistant_input { height: 3; border: round $accent; }

#log_view { height: 1fr; }
Button { margin: 1 2; }
Horizontal { height: auto; }

#menu_screen { align: center middle; }
#menu_box { width: 78; height: auto; border: round $accent; padding: 1 2; }
#menu_box #menu_hint { width: 100%; text-align: center; padding-top: 1; }
"""


# --------------------------------------------------------------------------
# Menu screen (option-based navigation)
# --------------------------------------------------------------------------
class MenuScreen(Screen):
    BINDINGS = [
        Binding("1", "menu(1)", "1 · Fetch", show=False),
        Binding("2", "menu(2)", "2 · View data", show=False),
        Binding("3", "menu(3)", "3 · Train", show=False),
        Binding("4", "menu(4)", "4 · RAG", show=False),
        Binding("5", "menu(5)", "5 · Assistant", show=False),
        Binding("6", "menu(6)", "6 · Log", show=False),
        Binding("7", "menu(7)", "7 · Exit", show=False),
        Binding("escape", "close", "Console", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Horizontal(id="menu_box"):
            yield Static(MENU_TEXT, id="menu_text")

    def action_menu(self, number: str) -> None:
        self.app.dispatch_menu_option(int(number))

    def action_close(self) -> None:
        self.app.pop_screen()


# --------------------------------------------------------------------------
# Main application
# --------------------------------------------------------------------------
class PipelineTUI(App):
    """Terminal app: numbered options, visual progress, data assistant."""

    TITLE = "Safety NLP Pipeline"
    SUB_TITLE = ("ASRS Aviation · NERC Power Grid · TF-IDF · SGD/Logistic "
                 "Regression · RAG explainer")
    CSS = CSS
    SCREENS = {"menu": MenuScreen}

    BINDINGS = [
        Binding("m", "menu", "Menu", show=True),
        Binding("1", "goto(1)", show=False),
        Binding("2", "goto(2)", show=False),
        Binding("3", "goto(3)", show=False),
        Binding("4", "goto(4)", show=False),
        Binding("5", "goto(5)", show=False),
        Binding("6", "goto(6)", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.active_csv = DEFAULT_DATASET
        self.df: pd.DataFrame | None = None

    # ---------------------------------------------------------------- UI
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="pipeline_bar")
        with Horizontal(id="progress_row"):
            yield Static("", id="stage_label")
            yield ProgressBar(id="progress", total=100, show_eta=False)
        with TabbedContent():
            with TabPane("1 · Dataset", id="tab_dataset"):
                yield Static(
                    "Live-downloads REAL safety data every run: NASA ASRS "
                    "aviation incident reports + NERC power-grid event "
                    "analysis reports, cleaned and merged by domain.",
                    id="dataset_hint",
                )
                with Horizontal():
                    yield Select(
                        [(p.name, str(p)) for p in find_datasets()]
                        or [("(no datasets yet)", "")],
                        id="dataset_select", prompt="Dataset file",
                    )
                    yield Button("Fetch / Refresh", id="btn_fetch",
                                 variant="primary")
                    yield Button("View contents", id="btn_view",
                                 variant="default")
                with Horizontal():
                    yield DataTable(id="preview_table")
                    yield DataTable(id="distribution_table")
            with TabPane("2 · Train Model", id="tab_train"):
                yield Static(
                    "Domain preprocessing -> TF-IDF vectorization -> Logistic "
                    "Regression. Trains on the selected dataset and saves model + "
                    "vectorizer pickles.",
                    id="train_hint",
                )
                yield Button("Train model", id="btn_train", variant="primary")
                yield Static("", id="report_text")
            with TabPane("3 · RAG Explainer", id="tab_rag"):
                yield TextArea(SAMPLE_REPORT, id="rag_input")
                yield Button("Explain incident", id="btn_explain",
                             variant="primary")
                yield Static("", id="rag_result")
            with TabPane("4 · Pipeline Log", id="tab_log"):
                yield RichLog(id="log_view", markup=True, wrap=False)
            with TabPane("5 · NLP Data Assistant", id="tab_assistant"):
                yield Static(
                    "Keyless analyst working on the loaded dataset. Ask about "
                    "quality, safety, classes — or paste a narrative.",
                    id="dataset_hint",
                )
                with Horizontal(id="assistant_chips"):
                    yield Button("Summary", id="chip_summary")
                    yield Button("Quality / issues", id="chip_quality")
                    yield Button("Safety / critical", id="chip_safety")
                    yield Button("Classes", id="chip_classes")
                yield RichLog(id="assistant_log", markup=True, wrap=False)
                yield Input(placeholder="Ask the data assistant ...",
                            id="assistant_input")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#log_view", RichLog).write("[cyan]Pipeline console ready.[/]")
        self._load_dataframe()
        self.show_pipeline_status()
        self.refresh_preview()
        self.push_screen("menu")

    # ------------------------------------------------------- data helpers
    def _load_dataframe(self) -> None:
        if Path(self.active_csv).exists():
            try:
                self.df = pd.read_csv(self.active_csv)
            except Exception as exc:
                self.df = None
                self._log(f"[red]Could not read dataset: {exc}[/]")
        else:
            self.df = None

    def loaded_df(self) -> pd.DataFrame | None:
        if self.df is None:
            self._log("[yellow]No dataset loaded — fetch one first (option 1).[/]")
        return self.df

    def show_pipeline_status(self) -> None:
        csv_ok = Path(self.active_csv).exists()
        model_ok = Path(DEFAULT_MODEL).exists()
        parts = []
        for name, ok in [("1 FETCH", csv_ok), ("2 TRAIN", model_ok),
                         ("3 EXPLAIN", model_ok)]:
            cls = "done" if ok else "skip"
            parts.append(f"[{cls}]{'[OK]' if ok else '[--]'} {name}[/]")
        self.query_one("#pipeline_bar", Static).update(
            "  " + "   ".join(parts) + "      Press [cyan]m[/] for the menu")

    # -------------------------------------------------------------- menu
    def dispatch_menu_option(self, number: int) -> None:
        actions = {1: "fetch", 2: "datasets", 3: "train", 4: "rag",
                   5: "assistant", 6: "log"}
        action = actions.get(number)
        if action is None:  # 7 = exit
            self.exit()
            return
        self.goto_target(action)
        try:
            self.pop_screen()
        except Exception:
            pass

    def action_menu(self) -> None:
        if not any(isinstance(s, MenuScreen) for s in self.screen_stack):
            self.push_screen("menu")

    def goto_target(self, destination: str) -> None:
        actions = {
            "fetch": lambda: (self.tab("tab_dataset"), self.perform_fetch()),
            "datasets": lambda: (self.tab("tab_dataset"),
                                 self.refresh_preview()),
            "train": lambda: (self.tab("tab_train"), self.perform_train()),
            "rag": lambda: (self.tab("tab_rag"), self.perform_explain()),
            "assistant": lambda: self.tab("tab_assistant"),
            "log": lambda: self.tab("tab_log"),
        }
        actions[destination]()

    def action_goto(self, destination: int) -> None:
        names = {1: "fetch", 2: "datasets", 3: "train", 4: "rag",
                 5: "assistant", 6: "log"}
        self.goto_target(names.get(int(destination), "datasets"))

    def tab(self, name: str):
        tabs = self.query_one(TabbedContent)
        try:
            tabs.active = name
        except Exception:
            pass
        return self

    # ------------------------------------------------------- progress bar
    def _set_progress(self, label: str, pct: int) -> None:
        self.query_one("#stage_label", Static).update(label)
        self.query_one("#progress", ProgressBar).update(progress=pct, total=100)

    def _log(self, text: str) -> None:
        self.call_from_thread(
            lambda: self.query_one("#log_view", RichLog).write(text))

    # ------------------------------------------------------------- workers
    def perform_fetch(self) -> None:
        self.run_worker(lambda: fetch_data.fetch_and_clean(
            target=Path(self.active_csv),
            log=lambda m: self._log(m),
            on_progress=lambda l, p: self.call_from_thread(self._set_progress, l, p),
        ), name="fetch", thread=True, exclusive=True)

    def perform_train(self) -> None:
        if self.loaded_df() is None:
            return
        self.run_worker(lambda: train_model.train_classifier(
            dataset=Path(self.active_csv),
            log=lambda m: self._log(m),
            on_progress=lambda l, p: self.call_from_thread(self._set_progress, l, p),
        ), name="train", thread=True, exclusive=True)

    def perform_explain(self) -> None:
        if self.loaded_df() is None or not Path(DEFAULT_MODEL).exists():
            self._log("[yellow]Model not trained yet — run option 3 first.[/]")
            return
        text = self.query_one("#rag_input", TextArea).text
        self.run_worker(lambda: explain_incident(
            text, dataset=Path(self.active_csv),
            log=lambda m: self._log(m),
            on_progress=lambda l, p: self.call_from_thread(self._set_progress, l, p),
        ), name="explain", thread=True, exclusive=True)

    def on_worker_state_changed(self, event) -> None:
        worker_name = getattr(event.worker, "name", "unknown")
        if event.state == WorkerState.RUNNING:
            bar = self.query_one("#pipeline_bar", Static)
            bar.update(f"  [busy]{'●' if hasattr(event.worker, 'name') else ''} "
                       f"RUNNING: {worker_name.upper()} ...[/]")
        elif event.state == WorkerState.SUCCESS:
            result = event.worker.result
            if worker_name == "fetch":
                self._load_dataframe()
                self.show_pipeline_status()
                self.refresh_preview()
            elif worker_name == "train":
                self.show_train_report(result)
                self.show_pipeline_status()
            elif worker_name == "explain":
                self.show_explain_result(result)
            self._set_progress("DONE", 100)
            self.show_pipeline_status()
        elif event.state == WorkerState.ERROR:
            self._log(f"[red]Error: {event.worker.error}[/]")
            self.show_pipeline_status()

    # ------------------------------------------------------------ results
    def show_train_report(self, result: dict) -> None:
        report = (
            f"[b]Model trained[/] — accuracy [accent]{result['accuracy']:.1%}[/]"
            f" over [accent]{result['classes']}[/] anomaly categories\n\n"
            + result["report"]
        )
        self.query_one("#report_text", Static).update(report)

    def show_explain_result(self, result: dict) -> None:
        lines = [
            f"[b]PREDICTED RISK CATEGORY:[/] {result['predicted_label']}",
            "",
            "RAG evidence — most similar historical reports:",
        ]
        for m in result["matches"]:
            pct = m["similarity"] * 100
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            domain = f" [muted]({m['domain']})[/]" if m.get("domain") else ""
            lines.append(f"#{m['rank']}  {bar} {pct:5.1f}%  "
                         f"[warn]{m['label']}[/]{domain}")
            narrative = m["narrative"][:170]
            lines.append(
                f"    [muted]{narrative}{'…' if len(m['narrative']) > 170 else ''}[/]"
            )
        self.query_one("#rag_result", Static).update("\n".join(lines))

    # ------------------------------------------------------------ dataset
    def refresh_preview(self) -> None:
        table = self.query_one("#preview_table", DataTable)
        dist = self.query_one("#distribution_table", DataTable)
        table.clear(columns=True)
        dist.clear(columns=True)
        if not Path(self.active_csv).exists():
            table.add_columns("No dataset found")
            table.add_row("Run 'Fetch / Refresh' (option 1) to download the "
                          "ASRS dataset.")
            return
        df = pd.read_csv(self.active_csv)
        has_domain = "Domain" in df.columns
        table.add_columns("Narrative (truncated)", "Domain", "Anomaly / Event")
        for _, row in df.head(30).iterrows():
            narrative = str(row["Narrative"])
            table.add_row(
                narrative[:100] + ("…" if len(narrative) > 100 else ""),
                str(row["Domain"]) if has_domain else "",
                str(row["human_factors_groundtruth"]),
            )
        dist.add_columns("Anomaly category", "Count", "Share")
        total = len(df)
        for label, count in df["human_factors_groundtruth"].value_counts().items():
            dist.add_row(str(label), str(count), f"{count / total:5.1%}")

    # ---------------------------------------------------------- assistant
    def assistant_ask(self, query: str) -> None:
        log = self.query_one("#assistant_log", RichLog)
        df = self.loaded_df()
        if not query.strip():
            return
        log.write(f"[cyan]You:[/] {query.strip()}")
        if df is None:
            log.write("[red]Assistant:[/] No dataset loaded — fetch one first.")
            return
        for line in analyst.answer(query, df):
            log.write(line if line else " ")
        log.write("")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "assistant_input":
            self.assistant_ask(event.value)
            self.query_one("#assistant_input", Input).value = ""

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_fetch":
            self.perform_fetch()
        elif bid == "btn_train":
            self.perform_train()
        elif bid == "btn_explain":
            self.perform_explain()
        elif bid == "btn_view":
            self.refresh_preview()
        elif bid == "chip_summary":
            self.assistant_ask("summary")
        elif bid == "chip_quality":
            self.assistant_ask("quality")
        elif bid == "chip_safety":
            self.assistant_ask("safety")
        elif bid == "chip_classes":
            self.assistant_ask("classes")

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "dataset_select" and event.value:
            self.active_csv = Path(str(event.value))
            self._load_dataframe()
            self.show_pipeline_status()
            self.refresh_preview()


# --------------------------------------------------------------------- CLI
def run_cli() -> int:
    """Headless mode: python app.py --fetch / --train / --explain <text>"""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    ran = False
    if "--fetch" in args:
        res = fetch_data.fetch_and_clean()
        print(f"status={res['status']} rows={res['rows']}")
        ran = True
    if "--train" in args:
        res = train_model.train_classifier()
        print(res["report"])
        ran = True
    if "--explain" in args:
        i = args.index("--explain")
        text = " ".join(args[i + 1:]) or SAMPLE_REPORT
        res = explain_incident(text)
        print(f"PREDICTED: {res['predicted_label']}")
        for m in res["matches"]:
            print(f"  #{m['rank']} {m['similarity']:.1%} {m['label']}")
        ran = True
    if not ran:
        print(__doc__)
        return 1
    return 0


def run() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        pass
    if any(a in sys.argv for a in ("--fetch", "--train", "--explain")):
        sys.exit(run_cli())
    PipelineTUI().run()


if __name__ == "__main__":
    run()