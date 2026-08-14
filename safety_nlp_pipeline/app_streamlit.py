"""Safety NLP Pipeline - Streamlit web dashboard.

Run from the pipeline root:

    streamlit run app_streamlit.py

Loads the artifacts produced by ``python main.py`` (dataset, model, vectorizer)
and serves them through a warm, creamy-light themed interface with four tabs:
Overview, Model Performance, RAG Explorer and Data Assistant.
"""
import json
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

st.title(":shield: Safety NLP Pipeline - Dashboard")
st.caption("Aviation & Power-Grid incident analysis &middot; TF-IDF + SGD &middot; RAG explainability")


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
tab1, tab2, tab3, tab4 = st.tabs(
    [":bar_chart: Overview", ":chart_with_upwards_trend: Model Performance",
     ":mag: RAG Explorer", ":clipboard: Data Assistant"])

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
