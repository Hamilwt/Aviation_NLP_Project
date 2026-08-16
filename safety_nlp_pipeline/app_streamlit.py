"""Safety NLP Pipeline - Streamlit web dashboard.

Run from the pipeline root:

    streamlit run app_streamlit.py

Loads the artifacts produced by ``python main.py`` (dataset, model, vectorizer)
and serves them through a warm, creamy-light themed interface with six tabs:
Overview, Model Performance, RAG Explorer, Data Assistant, Live Alerts
(raised by ``python -m src.monitor``), and System Control (process management).
"""
import json
import queue
import subprocess
import sys
import threading
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import config
from src import analyst, data_fetcher
from src.rag_explainer import build_index, explain_text

st.set_page_config(
    page_title="Safety NLP Pipeline - Dashboard",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------------- theme
st.markdown(
    """
    <style>
    .stApp { background-color: #FFF8F0; }
    h1, h2, h3 { color: #5C4033; }
    .stButton > button {
        background-color: #F5E6D3;
        color: #3E2F1F;
        border: 1px solid #D9C5B2;
    }
    .stButton > button:hover {
        background-color: #ECD9BF;
        color: #3E2F1F;
    }
    div[data-testid="stDataFrame"] { background-color: #FFFDF9; }
    div[data-testid="stMetricValue"] { color: #5C4033; }
    .ev-card {
        background: #FFFDF9; border-left: 4px solid #0f6b9e;
        padding: 8px 12px; margin: 6px 0; border-radius: 0 8px 8px 0;
    }
    .ev-title { color: #5C4033; font-weight: 700; }
    .ev-meta { color: #8b7355; font-size: 0.85em; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================ Process Manager
class ProcessManager:
    """Manages subprocesses for pipeline, monitor, and dashboard with log streaming."""
    
    SERVICES = {
        "pipeline": {
            "cmd": [sys.executable, "main.py"],
            "label": "Pipeline",
            "desc": "Full pipeline: fetch → preprocess → train → evaluate → RAG → report",
        },
        "monitor": {
            "cmd": [sys.executable, "-m", "src.monitor"],
            "label": "Monitor",
            "desc": "Real-time incident ingestion, classification, risk scoring & alerting",
        },
    }
    
    def __init__(self):
        self.processes = {}
        self.log_queues = {}
        self.log_threads = {}
        self.lock = threading.Lock()
    
    def _read_stream(self, stream, q, service_name):
        """Background thread to read subprocess stdout/stderr."""
        try:
            for line in iter(stream.readline, ''):
                if line:
                    q.put((service_name, line.rstrip()))
        except Exception:
            pass
        finally:
            stream.close()
    
    def start(self, service_name: str) -> tuple[bool, str]:
        """Start a service subprocess."""
        with self.lock:
            if service_name in self.processes and self.processes[service_name].poll() is None:
                return False, f"{service_name} already running"
            
            svc = self.SERVICES[service_name]
            cwd = Path(__file__).parent
            
            try:
                proc = subprocess.Popen(
                    svc["cmd"],
                    cwd=cwd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    encoding="utf-8",
                    errors="replace",
                )
            except Exception as e:
                return False, f"Failed to start {service_name}: {e}"
            
            self.processes[service_name] = proc
            self.log_queues[service_name] = queue.Queue()
            
            # Start log reader thread
            t = threading.Thread(
                target=self._read_stream,
                args=(proc.stdout, self.log_queues[service_name], service_name),
                daemon=True,
            )
            t.start()
            self.log_threads[service_name] = t
            
            return True, f"{svc['label']} started (PID: {proc.pid})"
    
    def stop(self, service_name: str) -> tuple[bool, str]:
        """Stop a service subprocess."""
        with self.lock:
            if service_name not in self.processes:
                return False, f"{service_name} not running"
            
            proc = self.processes[service_name]
            if proc.poll() is not None:
                # Already dead
                self._cleanup(service_name)
                return True, f"{service_name} was already stopped"
            
            try:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
            except Exception as e:
                return False, f"Error stopping {service_name}: {e}"
            finally:
                self._cleanup(service_name)
            
            return True, f"{self.SERVICES[service_name]['label']} stopped"
    
    def _cleanup(self, service_name: str):
        """Clean up process resources."""
        self.processes.pop(service_name, None)
        self.log_queues.pop(service_name, None)
        self.log_threads.pop(service_name, None)
    
    def is_running(self, service_name: str) -> bool:
        """Check if a service is currently running."""
        with self.lock:
            proc = self.processes.get(service_name)
            return proc is not None and proc.poll() is None
    
    def get_logs(self, service_name: str, max_lines: int = 200) -> list[str]:
        """Get recent logs for a service."""
        if service_name not in self.log_queues:
            return []
        q = self.log_queues[service_name]
        logs = []
        try:
            while not q.empty() and len(logs) < max_lines:
                logs.append(q.get_nowait())
        except queue.Empty:
            pass
        return logs
    
    def get_all_status(self) -> dict:
        """Get status of all services."""
        return {name: self.is_running(name) for name in self.SERVICES}
    
    def stop_all(self):
        """Stop all running services."""
        for name in list(self.processes.keys()):
            self.stop(name)


# Initialize process manager in session state
if "proc_mgr" not in st.session_state:
    st.session_state.proc_mgr = ProcessManager()
if "log_buffer" not in st.session_state:
    st.session_state.log_buffer = {name: [] for name in ProcessManager.SERVICES}

proc_mgr = st.session_state.proc_mgr

st.title(":shield: Safety NLP Pipeline - Dashboard")
st.caption("Aviation & Power-Grid incident analysis · TF-IDF + SGD · RAG explainability")


# ------------------------------------------------------------------ loading
@st.cache_resource(show_spinner="Loading pipeline artifacts ...")
def load_artifacts():
    """Load dataset, model, vectorizer and a precomputed RAG retrieval index."""
    if not config.DATASET_PATH.exists():
        return None
    if not config.MODEL_PATH.exists() or not config.VECTORIZER_PATH.exists():
        return None
    df = data_fetcher.load_dataset(config.DATASET_PATH)
    model = joblib.load(config.MODEL_PATH)
    vectorizer = joblib.load(config.VECTORIZER_PATH)
    index_vectors = build_index(df, vectorizer)
    return df, model, vectorizer, index_vectors


@st.cache_resource(show_spinner=False)
def load_performance():
    """Load persisted evaluation outputs (report text/csv, plots, metrics)."""
    if not (config.CLASSIFICATION_REPORT_TXT.exists()
            and config.CLASSIFICATION_REPORT_CSV.exists()):
        return None
    return {
        "report_text": config.CLASSIFICATION_REPORT_TXT.read_text(encoding="utf-8"),
        "report_df": pd.read_csv(config.CLASSIFICATION_REPORT_CSV, index_col=0),
        "confusion_png": config.PLOTS_DIR / "confusion_matrix.png",
        "dist_png": config.PLOTS_DIR / "class_distribution.png",
        "metrics": json.loads(config.METRICS_JSON.read_text(encoding="utf-8"))
        if config.METRICS_JSON.exists() else {},
    }


artifacts = load_artifacts()
performance = load_performance()

if artifacts is None:
    st.warning("Pipeline artifacts not found. Run **`python main.py`** first to "
               "generate the dataset, model and vectorizer, then reload this page.")
    st.stop()

df, model, vectorizer, index_vectors = artifacts

# --------------------------------------------------------------------- tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [":bar_chart: Overview", ":chart_with_upwards_trend: Model Performance",
     ":mag: RAG Explorer", ":clipboard: Data Assistant",
     ":rotating_light: Live Alerts", ":gear: System Control"])

# -------------------------------------------------------------- 1 · Overview
with tab1:
    st.subheader("Dataset Snapshot")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Reports", f"{len(df):,}")
    c2.metric("Domains", df[config.DOMAIN_COL].nunique()
              if config.DOMAIN_COL in df.columns else 1)
    c3.metric("Anomaly Classes", df[config.LABEL_COL].nunique())

    if config.DOMAIN_COL in df.columns:
        dom = df[config.DOMAIN_COL].value_counts()
        c4, c5 = st.columns(2)
        c4.metric("Aviation", int(dom.get("Aviation", 0)))
        c5.metric("Power Grid", int(dom.get("Power Grid", 0)))

    st.write("**Class distribution (top 10)**")
    fig, ax = plt.subplots(figsize=(8, 4))
    df[config.LABEL_COL].value_counts().head(10).plot(
        kind="bar", ax=ax, color="#D9C5B2", edgecolor="#A98467")
    ax.set_ylabel("Count")
    ax.set_xlabel("")
    ax.tick_params(axis="x", labelrotation=45)
    st.pyplot(fig)

    st.write("**Sample rows**")
    st.dataframe(df[[config.NARRATIVE_COL, config.LABEL_COL, config.DOMAIN_COL]]
                 .head(10), use_container_width=True)

# --------------------------------------------------- 2 · Model Performance
with tab2:
    st.subheader("Model Performance")
    if performance is None:
        st.warning("No persisted evaluation outputs found - run **`python main.py`** "
                   "to generate the classification report and plots.")
    else:
        met = performance["metrics"]
        m1, m2, m3 = st.columns(3)
        m1.metric("Test Accuracy", f"{met.get('accuracy', 0):.1%}")
        m2.metric("Classes", met.get("n_classes", "-"))
        m3.metric("Test Reports", met.get("test_size", "-"))

        st.write("**Classification report (per class)**")
        report_df = performance["report_df"]
        display = report_df.loc[
            ~report_df.index.isin(["accuracy", "macro avg", "weighted avg"])
        ].copy()
        display.index.name = "class"
        st.dataframe(display, use_container_width=True)

        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.write("**Confusion matrix (normalised)**")
            png = performance["confusion_png"]
            if png.exists():
                st.image(str(png), use_container_width=True)
            else:
                st.info("Confusion-matrix plot not generated yet.")
        with col_img2:
            st.write("**Class distribution**")
            png = performance["dist_png"]
            if png.exists():
                st.image(str(png), use_container_width=True)
            else:
                st.info("Class-distribution plot not generated yet.")

        with st.expander("Full classification report (text)"):
            st.text(performance["report_text"])

# ---------------------------------------------------------- 3 · RAG Explorer
with tab3:
    st.subheader("Explainable RAG - classify a new incident")
    st.caption("Paste an incident narrative and retrieve the top-3 most similar "
               "historical reports as evidence.")
    user_input = st.text_area(
        "Incident narrative",
        height=140,
        placeholder=("I was cleared for the ILS approach but misheard the altitude "
                     "restriction due to heavy static on the radio frequency..."),
    )
    if st.button("Classify & Retrieve Evidence", type="primary"):
        if not user_input.strip():
            st.info("Please paste a narrative first.")
        else:
            with st.spinner("Classifying and searching historical evidence ..."):
                predicted, evidence = explain_text(
                    user_input, model, vectorizer, df,
                    index_vectors=index_vectors, top_k=config.RAG_TOP_K)
            st.success(f"**Predicted risk category:** {predicted}")
            st.write("**Top-%d most similar historical reports:**" % len(evidence))
            for ev in evidence:
                st.markdown(
                    f"""
                    <div class="ev-card">
                      <div class="ev-title">#{ev['rank']} &nbsp;{ev['similarity'] * 100:.1f}% similar</div>
                      <div class="ev-meta">{ev['label']} &middot; {ev['domain']}</div>
                      <div style="background:#EDE4D6;height:6px;border-radius:3px;margin:4px 0">
                        <div style="background:#0f6b9e;height:6px;border-radius:3px;width:{ev['similarity'] * 100:.1f}%"></div>
                      </div>
                      {ev['snippet']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

# ------------------------------------------------------- 4 · Data Assistant
with tab4:
    st.subheader("Data Quality & Safety Insights")
    st.caption("Keyless analysis computed with pandas - no LLM, no API key.")

    c1, c2, c3, c4 = st.columns(4)
    ask = None
    if c1.button("Summary", use_container_width=True):
        ask = "summary"
    if c2.button("Quality / issues", use_container_width=True):
        ask = "quality"
    if c3.button("Safety / critical", use_container_width=True):
        ask = "safety"
    if c4.button("Classes", use_container_width=True):
        ask = "classes"

    free_q = st.text_input(
        "Or ask the assistant",
        placeholder="e.g. analyze <paste a narrative>, quality, safety, classes ...",
    )

    query = ask
    if free_q.strip():
        query = free_q.strip()

    if query:
        st.code("\n".join(analyst.answer(query, df)), language="text")
    else:
        st.info("Use the quick buttons above or type a question to get insights.")

# ------------------------------------------------------ 5 · Live Alerts
with tab5:
    st.subheader("Live Alerts - real-time incident monitoring")
    st.caption("Alerts are raised by `python -m src.monitor` as new reports arrive "
               "from a watched folder, appended dataset rows, or the live NTSB / "
               "UK Power Networks feeds.")

    st.button("Refresh alerts", use_container_width=False)

    def load_alerts():
        if not config.ALERT_LOG_PATH.exists():
            return None
        alerts = pd.read_csv(config.ALERT_LOG_PATH)
        if alerts.empty:
            return alerts
        alerts["timestamp"] = pd.to_datetime(alerts["timestamp"], errors="coerce")
        return alerts.sort_values("timestamp", ascending=False)

    alerts = load_alerts()

    if alerts is None:
        st.info("No alert log found. Start the monitor with **`python -m "
                "src.monitor`**, then drop a CSV/TXT file into `new_incidents/` "
                "to raise alerts.")
    elif alerts.empty:
        st.info("The alert log is empty - no alerts raised yet.")
    else:
        counts = alerts["risk_level"].value_counts()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Critical", int(counts.get("critical", 0)))
        m2.metric("High", int(counts.get("high", 0)))
        m3.metric("Medium", int(counts.get("medium", 0)))
        m4.metric("Total alerts", len(alerts))

        recent = alerts.head(50).copy()
        recent["evidence"] = recent["evidence_json"].apply(
            lambda s: json.loads(s) if isinstance(s, str) and s.strip() else [])
        recent = recent.drop(columns=["evidence_json"])

        def _style_risk(row):
            bg = {"critical": "#ffd6d6", "high": "#ffe9c7",
                  "medium": "#ffffff"}.get(str(row["risk_level"]), "#ffffff")
            return [f"background-color: {bg}"] * len(row)

        st.write(f"**Recent alerts (most recent {len(recent)} shown)**")
        st.dataframe(recent.style.apply(_style_risk, axis=1),
                     use_container_width=True)

        st.write("**RAG evidence for the most recent alerts**")
        for _, row in recent.head(5).iterrows():
            risk = str(row["risk_level"]).upper()
            title = f"{risk} | {row['predicted_label']} | {row['incident_id']}"
            with st.expander(f"{title} &nbsp;&middot;&nbsp; {row['timestamp']}"):
                st.write(row["narrative"])
                for ev in row["evidence"]:
                    st.markdown(
                        f"""
                        <div class="ev-card">
                          <div class="ev-title">#{ev['rank']} &nbsp;{ev['similarity'] * 100:.1f}% similar</div>
                          <div class="ev-meta">{ev['label']} &middot; {ev['domain']}</div>
                          {ev['snippet']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

# ------------------------------------------------------ 6 · System Control
with tab6:
    st.subheader("System Control")
    st.caption("Manage the pipeline and monitor processes. Logs update on demand.")
    
    # Refresh logs button (manual only - no auto-refresh)
    if st.button("Refresh Logs", type="secondary", use_container_width=False):
        st.rerun()
    
    st.divider()
    
    # Service status overview
    status = proc_mgr.get_all_status()
    
    # Control buttons row
    st.write("**Service Controls**")
    
    for name, info in ProcessManager.SERVICES.items():
        running = status[name]
        label = info["label"]
        desc = info["desc"]
        
        scol1, scol2, scol3, scol4 = st.columns([2, 1, 1, 4])
        
        with scol1:
            status_color = "#2ECC71" if running else "#E74C3C"
            status_text = "RUNNING" if running else "STOPPED"
            st.markdown(
                f"""
                <div style="padding:8px;border-radius:6px;margin-bottom:4px;border:1px solid #D9C5B2;background:#FFFDF9;">
                    <div style="font-weight:600;color:#5C4033;">{label}</div>
                    <div style="font-size:0.85em;color:#8B7355;">{desc}</div>
                </div>
                <div style="background:{status_color};padding:4px;border-radius:4px;text-align:center;font-size:0.85em;color:white;">
                    {status_text}
                </div>
                """,
                unsafe_allow_html=True,
            )
        
        with scol2:
            if not running:
                if st.button("Start", key=f"start_{name}", use_container_width=True):
                    ok, msg = proc_mgr.start(name)
                    if ok:
                        st.toast(msg, icon="���")
                    else:
                        st.toast(msg, icon="���")
                    st.rerun()
        
        with scol3:
            if running:
                if st.button("Stop", key=f"stop_{name}", use_container_width=True):
                    ok, msg = proc_mgr.stop(name)
                    if ok:
                        st.toast(msg, icon="���")
                    else:
                        st.toast(msg, icon="���")
                    st.rerun()
    
    # Master controls
    st.divider()
    mcol1, mcol2 = st.columns(2)
    any_running = any(status.values())
    all_running = all(status.values())
    
    with mcol1:
        if st.button("Start ALL", use_container_width=True, type="primary", disabled=all_running):
            for name in ProcessManager.SERVICES:
                if not status[name]:
                    proc_mgr.start(name)
            st.rerun()
    with mcol2:
        if st.button("Stop ALL", use_container_width=True, disabled=not any_running):
            proc_mgr.stop_all()
            st.rerun()
    
    # Logs section
    st.divider()
    st.write("**Process Logs**")
    
    # Log tabs for each service
    log_tabs = st.tabs([f"{info['label']}" for info in ProcessManager.SERVICES.values()])
    
    for i, (name, info) in enumerate(ProcessManager.SERVICES.items()):
        with log_tabs[i]:
            # Collect new logs
            new_logs = proc_mgr.get_logs(name)
            for svc, line in new_logs:
                if svc == name:
                    st.session_state.log_buffer[name].append(line)
            
            # Keep buffer bounded
            if len(st.session_state.log_buffer[name]) > 500:
                st.session_state.log_buffer[name] = st.session_state.log_buffer[name][-500:]
            
            # Display logs
            if st.session_state.log_buffer[name]:
                log_text = "\n".join(st.session_state.log_buffer[name])
                st.code(log_text, language="text")
            else:
                st.info(f"No logs yet for {info['label']}. Start the service to see output.")
