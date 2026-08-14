"""Step 4 - Evaluate the trained model and produce diagnostic plots.

Generates a per-class classification report, a confusion-matrix heatmap and a
top-N class-distribution bar chart, saving the plots as PNGs under
``data/plots/`` for embedding in the HTML report.
"""
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless backend - no GUI required
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

from config import DOMAIN_COL, LABEL_COL, PLOT_CLASS_TOP_N, PLOTS_DIR

logger = logging.getLogger(__name__)


def _save_figure(fig, name: str) -> Path:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOTS_DIR / name
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)
    logger.info("Saved plot -> %s", path)
    return path


def plot_confusion_matrix(conf: np.ndarray, labels: list[str]) -> Path:
    """Heatmap of the (normalised) confusion matrix."""
    n = len(labels)
    fig, ax = plt.subplots(
        figsize=(max(9, n * 0.55), max(7, n * 0.5)))
    norm = conf.astype(float) / conf.sum(axis=1, keepdims=True).clip(min=1)
    annot = n <= 25
    sns.heatmap(norm, annot=annot, fmt=".2f" if annot else None,
                cmap="Blues", cbar=True, ax=ax,
                xticklabels=labels, yticklabels=labels,
                annot_kws={"size": 6} if annot else None, linewidths=0.2)
    ax.set_title(f"Confusion Matrix (normalised, {n} classes)")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    plt.setp(ax.get_xticklabels(), rotation=90, fontsize=7)
    plt.setp(ax.get_yticklabels(), fontsize=7)
    fig.tight_layout()
    return _save_figure(fig, "confusion_matrix.png")


def plot_class_distribution(df: pd.DataFrame, top_n: int = PLOT_CLASS_TOP_N) -> Path:
    """Horizontal bar chart of the top-N most frequent classes."""
    counts = df[LABEL_COL].value_counts().head(top_n).sort_values()
    fig, ax = plt.subplots(figsize=(10, max(5, 0.45 * len(counts))))
    bars = ax.barh(counts.index, counts.values, color="#2f6fb3")
    if DOMAIN_COL in df.columns:
        domain_colors = {
            "Aviation": "#2f6fb3",
            "Power Grid": "#d97706",
        }
        for bar, label in zip(bars, counts.index):
            subset = df[df[LABEL_COL] == label]
            doms = subset[DOMAIN_COL].value_counts()
            top_dom = doms.idxmax() if len(doms) else "other"
            bar.set_color(domain_colors.get(top_dom, "#8b8b8b"))
    ax.set_title(f"Top {len(counts)} Most Frequent Classes")
    ax.set_xlabel("Number of reports")
    for i, v in enumerate(counts.values):
        ax.text(v + max(counts.values) * 0.01, i, str(v), va="center", fontsize=8)
    fig.tight_layout()
    return _save_figure(fig, "class_distribution.png")


def evaluate_and_plot(model, vectorizer, X_test, y_test, df: pd.DataFrame | None = None) -> dict:
    """Vectorize the test set, predict, and produce all evaluation outputs.

    Returns:
        dict with keys: accuracy, report_text, report_df (per-class table),
        confusion_matrix, y_pred, y_true, and saved plot paths.
    """
    logger.info("Vectorizing test set (%d docs) and predicting ...", len(X_test))
    X_vec = vectorizer.transform(X_test)
    y_pred = model.predict(X_vec)
    y_true = y_test

    accuracy = float((y_pred == y_true).mean())
    report_text = classification_report(y_true, y_pred, zero_division=0)
    report_df = pd.DataFrame(
        classification_report(y_true, y_pred, output_dict=True,
                              zero_division=0)).T
    conf = confusion_matrix(y_true, y_pred)

    labels = sorted(y_true.unique().tolist())
    conf_plot = plot_confusion_matrix(conf, labels)
    logger.info("Accuracy: %.1f%%", accuracy * 100)
    logger.info("\n%s", report_text)

    result = {
        "accuracy": accuracy,
        "report_text": report_text,
        "report_df": report_df,
        "confusion_matrix": conf,
        "y_pred": y_pred,
        "y_true": y_true,
        "plots": {"confusion_matrix": conf_plot},
    }
    if df is not None:
        result["plots"]["class_distribution"] = plot_class_distribution(df)
    return result
