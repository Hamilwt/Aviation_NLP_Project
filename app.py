"""Aviation NLP Pipeline — Terminal UI.

Demonstrates the full NLP workflow visually inside the terminal:

  Fetch ASRS dataset  ->  view it  ->  train model  ->  RAG explainer

If an artifact already exists (dataset / model / vectorizer) the TUI shows
its contents instead of re-running the expensive step. Every CSV placed in
the ``data/`` folder is immediately selectable in the Dataset tab.

Run:  python app.py
CLI:  python app.py --fetch | --train | --explain <text>
"""
import sys
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import (Button, DataTable, Footer, Header, RichLog,
                             Select, Static, TabbedContent, TabPane, TextArea)
from textual import work
from textual.worker import Worker, WorkerState

from pipeline import fetch_data, train_model
from pipeline.paths import (DATA_DIR, DEFAULT_DATASET, DEFAULT_MODEL,
                            DEFAULT_VECTORIZER, find_datasets)
from pipeline.rag_explainer import explain_incident

SAMPLE_REPORT = ("I was cleared for the ILS approach but misheard the altitude "
                 "restriction due to heavy static on the radio frequency. I "
                 "descended to 3000 feet instead of 5000. ATC immediately called "
                 "and issued a climb instruction to avoid terrain. Checklist was "
                 "complete.")

CSS = """
Screen { layout: vertical; }
#pipeline_bar { height: 1; padding: 0 1; color: $text-muted; }
#pipeline_bar .done { color: $success; text-style: bold; }
#pipeline_bar .skip { color: $text-muted; }
#pipeline_bar .busy { color: $warning; text-style: bold; }
TabbedContent { height: 1fr; }

#dataset_hint { padding: 1 2; color: $text-muted; }
#preview_table { height: 1fr; }
#distribution_table { height: 1fr; }

#train_hint { padding: 1 2; }
#report_text { height: 1fr; padding: 1 2; border: round $accent; }
#report_text .accent { color: $accent; text-style: bold; }
#report_text .good { color: $success; text-style: bold; }
#report_text .warn { color: $warning; }

#rag_input { height: 6; border: round $accent; padding: 1; }
#rag_result { height: 1fr; padding: 1 2; border: round $accent; }
#rag_result .category { color: $success; text-style: bold; }
#rag_result .warn { color: $warning; }
#rag_result .muted { color: $text-muted; }

#log_view { height: 1fr; }
Button { margin: 1 2; }
Horizontal { height: auto; }
"""


class PipelineTUI(App):
    """Terminal UI that visually walks the Aviation NLP pipeline."""

    TITLE = "Aviation NLP Pipeline"
    SUB_TITLE = "ASRS dataset  ·  TF-IDF  ·  Logistic Regression  ·  RAG explainer"
    CSS = CSS

    BINDINGS = [
        Binding("f", "fetch", "Fetch dataset", show=True),
        Binding("t", "train", "Train model", show=True),
        Binding("e", "explain", "Explain report", show=True),
        Binding("d", "datasets_tab", "Dataset", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.active_csv = DEFAULT_DATASET
        self.current_report_text = SAMPLE_REPORT

    # ------------------------------------------------------------------ UI
    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="pipeline_bar")
        with TabbedContent():
            with TabPane("1 · Dataset", id="tab_dataset"):
                yield Static(
                    "Fetch the NASA ASRS dataset. If it already exists on disk it "
                    "is displayed below — nothing is re-downloaded.",
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
        yield Footer()

    def on_mount(self) -> None:
        log = self.query_one("#log_view", RichLog)
        log.write("[cyan]Pipeline console ready.[/]")
        self.datasets_tab()
        self.refresh_bar()

    # ----------------------------------------------------- pipeline status
    def refresh_bar(self) -> None:
        """Render the visual pipeline stage strip (fetch -> train -> rag)."""
        csv_exists = DEFAULT_DATASET.exists()
        model_ready = DEFAULT_MODEL.exists() and DEFAULT_VECTORIZER.exists()
        parts = []
        for name, ready, done in [
            ("1 FETCH", csv_exists, False),
            ("2 TRAIN", model_ready, False),
            ("3 EXPLAIN", model_ready, False),
        ]:
            cls = "done" if ready else "skip"
            parts.append(f"[{cls}]{'[OK]' if ready else '[--]'} {name}[/]")
        self.query_one("#pipeline_bar", Static).update("  " + "   ".join(parts))

    def refresh_preview(self) -> None:
        """Display the selected dataset's contents + label distribution."""
        table = self.query_one("#preview_table", DataTable)
        dist = self.query_one("#distribution_table", DataTable)
        table.clear(columns=True)
        dist.clear(columns=True)
        if not self.active_csv or not Path(self.active_csv).exists():
            table.add_columns("No dataset found")
            table.add_row("Run 'Fetch / Refresh' to download the ASRS dataset.")
            return
        import pandas as pd

        df = pd.read_csv(self.active_csv)
        table.add_columns("Narrative (truncated)", "Anomaly / Event")
        for _, row in df.head(30).iterrows():
            narrative = str(row["Narrative"])
            table.add_row(narrative[:100] + ("…" if len(narrative) > 100 else ""),
                          str(row["human_factors_groundtruth"]))
        dist.add_columns("Anomaly category", "Count", "Share")
        total = len(df)
        for label, count in df["human_factors_groundtruth"].value_counts().items():
            dist.add_row(str(label), str(count), f"{count / total:5.1%}")

    # -------------------------------------------------------------- workers
    def _log(self, text: str, markup: bool = True) -> None:
        self.call_from_thread(self.query_one, "#log_view", RichLog
                              ).write(text)

    @work(thread=True, name="fetch", exclusive=True)
    def run_fetch(self) -> dict:
        return fetch_data.fetch_and_clean(
            target=Path(self.active_csv),
            log=lambda m: self._log(m),
        )

    @work(thread=True, name="train", exclusive=True)
    def run_train(self) -> dict:
        return train_model.train_classifier(
            dataset=Path(self.active_csv),
            log=lambda m: self._log(m),
        )

    @work(thread=True, name="explain", exclusive=True)
    def run_explain(self, text: str) -> dict:
        return explain_incident(
            text,
            dataset=Path(self.active_csv),
            log=lambda m: self._log(m),
        )

    def _busy(self, on: bool, worker_name: str) -> None:
        bar = self.query_one("#pipeline_bar", Static)
        if on:
            bar.update(f"  [busy]WORKING: {worker_name} ...[/]")
        else:
            self.refresh_bar()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        if event.state == WorkerState.RUNNING:
            self._busy(True, event.worker.name)
        elif event.state in (WorkerState.SUCCESS, WorkerState.ERROR):
            self._busy(False, event.worker.name)
            if event.worker.name == "fetch" and event.state == WorkerState.SUCCESS:
                self.refresh_preview()
            elif event.worker.name == "train" and event.state == WorkerState.SUCCESS:
                self.show_train_report(event.worker.result)
                self.refresh_bar()
            elif event.worker.name == "explain" and event.state == WorkerState.SUCCESS:
                self.show_explain_result(event.worker.result)
            elif event.state == WorkerState.ERROR:
                self._log(f"[red]Error: {event.worker.error}[/]")

    # ------------------------------------------------------------- results
    def show_train_report(self, result: dict) -> None:
        report = (
            f"[good]Model trained[/] — accuracy [accent]{result['accuracy']:.1%}[/]"
            f" over [accent]{result['classes']}[/] anomaly categories\n\n"
            + result["report"]
        )
        self.query_one("#report_text", Static).update(report)

    def show_explain_result(self, result: dict) -> None:
        lines = [
            f"[category]PREDICTED RISK CATEGORY: {result['predicted_label']}[/]",
            "",
            "[warn]RAG evidence — most similar historical reports:[/]",
        ]
        for m in result["matches"]:
            pct = m["similarity"] * 100
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            lines.append(
                f"#{m['rank']}  {bar} {pct:5.1f}%  [warn]{m['label']}[/]"
            )
            narrative = m["narrative"][:170]
            lines.append(f"    [muted]{narrative}{'…' if len(m['narrative']) > 170 else ''}[/]")
            lines.append("")
        self.query_one("#rag_result", Static).update("\n".join(lines))

    # --------------------------------------------------------------- events
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_fetch":
            self.run_fetch()
        elif event.button.id == "btn_train":
            self.run_train()
        elif event.button.id == "btn_explain":
            text = self.query_one("#rag_input", TextArea).text
            self.run_explain(text)
        elif event.button.id == "btn_view":
            self.refresh_preview()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "dataset_select" and event.value:
            selected = str(event.value)
            if selected:
                self.active_csv = Path(selected)
                self.refresh_bar()

    # ------------------------------------------------------------- actions
    def action_fetch(self) -> None:
        self.get_tab("tab_dataset")
        self.run_fetch()

    def action_train(self) -> None:
        self.get_tab("tab_train")
        self.run_train()

    def action_explain(self) -> None:
        self.get_tab("tab_rag")
        text = self.query_one("#rag_input", TextArea).text
        self.run_explain(text)

    def action_datasets_tab(self) -> None:
        self.datasets_tab()

    def datasets_tab(self) -> None:
        tabs = self.query_one(TabbedContent)
        try:
            tabs.active = "tab_dataset"
        except Exception:
            pass
        self.refresh_preview()

    def get_tab(self, name: str):
        tabs = self.query_one(TabbedContent)
        try:
            tabs.active = name
        except Exception:
            pass
        return self


# --------------------------------------------------------------------- CLI
def run_cli() -> int:
    """Headless mode: python app.py --fetch / --train / --explain <text>"""
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if "--fetch" in args:
        res = fetch_data.fetch_and_clean()
        print(f"status={res['status']} rows={res['rows']}")
    if "--train" in args:
        res = train_model.train_classifier()
        print(res["report"])
    if "--explain" in args:
        i = args.index("--explain")
        text = " ".join(args[i + 1:]) or SAMPLE_REPORT
        res = explain_incident(text)
        print(f"PREDICTED: {res['predicted_label']}")
        for m in res["matches"]:
            print(f"  #{m['rank']} {m['similarity']:.1%} {m['label']}")
    if not any(a in args for a in ("--fetch", "--train", "--explain")):
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