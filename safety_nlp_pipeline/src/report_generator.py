"""Step 6 - Generate the self-contained HTML report.

Builds ``reports/pipeline_report.html`` with Jinja2: project summary, dataset
statistics, data-quality insights, model performance (classification table +
confusion matrix + class distribution plots as embedded base64 PNGs) and a
selection of RAG explainability examples with similarity-scored evidence.
"""
import base64
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from jinja2 import Template

from config import (DOMAIN_COL, LABEL_COL, NARRATIVE_COL, RAG_EXAMPLES_IN_REPORT,
                    REPORT_PATH, TRAIN_CONFIG_PATH)

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------ template
_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Safety NLP Pipeline Report</title>
<style>
  :root {
    --accent:#0f6b9e; --accent-dark:#0a4d73; --bg:#f6f8fa;
    --card:#ffffff; --border:#dde3ea; --muted:#6b7280;
    --good:#16a34a; --bad:#dc2626; --warn:#d97706;
  }
  * { box-sizing: border-box; }
  body { font-family: "Segoe UI", Arial, sans-serif; margin:0; background:var(--bg); color:#1f2937; }
  header { background:linear-gradient(120deg, var(--accent-dark), var(--accent));
           color:#fff; padding:28px 40px; }
  header h1 { margin:0 0 6px; font-size:26px; }
  header p { margin:2px 0; opacity:.9; font-size:14px; }
  main { max-width:1100px; margin:24px auto; padding:0 20px; }
  h2 { color:var(--accent-dark); border-bottom:2px solid var(--border);
       padding-bottom:6px; margin-top:44px; }
  .cards { display:flex; flex-wrap:wrap; gap:14px; margin-top:18px; }
  .card { flex:1 1 200px; background:var(--card); border:1px solid var(--border);
          border-radius:10px; padding:16px 18px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
  .card .k { font-size:12px; text-transform:uppercase; color:var(--muted); letter-spacing:.04em; }
  .card .v { font-size:22px; font-weight:700; margin-top:4px; }
  table { border-collapse:collapse; width:100%; background:var(--card);
          border:1px solid var(--border); border-radius:8px; overflow:hidden;
          font-size:13px; }
  th, td { border:1px solid var(--border); padding:7px 10px; text-align:left; }
  th { background:#eef2f6; font-weight:600; }
  tr:nth-child(even) td { background:#fafbfc; }
  img.chart { max-width:100%; height:auto; border:1px solid var(--border);
              border-radius:8px; margin:10px 0; }
  pre.report { background:#0d1117; color:#d2e3f0; padding:14px; border-radius:8px;
               overflow-x:auto; font-size:12px; line-height:1.45; }
  .badge { display:inline-block; padding:2px 9px; border-radius:12px; font-size:11px;
           font-weight:600; color:#fff; }
  .badge.good { background:var(--good); } .badge.bad { background:var(--bad); }
  .ev { border-left:3px solid var(--accent); background:#f0f6fb; padding:6px 10px;
        margin:6px 0; border-radius:0 6px 6px 0; }
  .ev .sim { font-weight:700; color:var(--accent-dark); }
  .ev .label { font-weight:600; }
  .ev .domain { color:var(--muted); font-size:11px; }
  .ev p { margin:4px 0 0; font-size:12px; color:#374151; }
  .sim-bar { height:6px; background:#dde3ea; border-radius:3px; overflow:hidden; }
  .sim-bar > div { height:100%; background:var(--accent); }
  .warn { color:var(--warn); font-weight:600; }
  footer { text-align:center; color:var(--muted); font-size:12px;
           padding:30px 0 40px; }
  .badge-row { display:inline-block; }
</style>
</head>
<body>
<header>
  <h1>Safety NLP Pipeline Report</h1>
  <p>Aviation &amp; Power-Grid incident classification &middot; TF-IDF + SGD (log-loss) &middot;
     GridSearchCV &middot; RAG explainability</p>
  <p>Generated {{ generated_at }} &middot; pipeline run on {{ num_reports }} reports</p>
</header>
<main>

  <h2>1 &middot; Project Summary</h2>
  <div class="cards">
    <div class="card"><div class="k">Total records</div><div class="v">{{ num_reports }}</div></div>
    <div class="card"><div class="k">Classes</div><div class="v">{{ n_classes }}</div></div>
    <div class="card"><div class="k">Test accuracy</div><div class="v">{{ "%.1f"|format(accuracy*100) }}%</div></div>
    <div class="card"><div class="k">Best CV F1 (weighted)</div><div class="v">{{ "%.3f"|format(cv_f1) }}</div></div>
  </div>
  <div class="cards">
    {% for dom, cnt in domain_counts.items() %}
    <div class="card"><div class="k">{{ dom }} reports</div><div class="v">{{ cnt }}</div></div>
    {% endfor %}
    <div class="card"><div class="k">Training rows</div><div class="v">{{ train_rows }}</div></div>
    <div class="card"><div class="k">Test rows</div><div class="v">{{ test_rows }}</div></div>
  </div>
  {% if best_params %}
  <h3>Best hyperparameters (GridSearchCV)</h3>
  <table>
    <tr><th>Parameter</th><th>Value</th></tr>
    {% for k, v in best_params.items() %}
    <tr><td>{{ k }}</td><td>{{ v }}</td></tr>
    {% endfor %}
  </table>
  {% endif %}

  <h2>2 &middot; Data Quality Insights</h2>
  <table>
    <tr><th>Metric</th><th>Value</th><th>Status</th></tr>
    {% for row in quality_rows %}
    <tr>
      <td>{{ row.metric }}</td><td>{{ row.value }}</td>
      <td><span class="badge {{ row.badge }}">{{ row.status }}</span></td>
    </tr>
    {% endfor %}
  </table>
  <p>Class distribution (top {{ top_classes|length }}):</p>
  <table>
    <tr><th>Class</th><th>Count</th><th>Share</th></tr>
    {% for row in top_classes %}
    <tr><td>{{ row.class }}</td><td>{{ row.count }}</td><td>{{ "%.1f"|format(row.share*100) }}%</td></tr>
    {% endfor %}
  </table>

  <h2>3 &middot; Model Performance</h2>
  <h3>Classification report</h3>
  <table>
    <tr><th>Class</th><th>Precision</th><th>Recall</th><th>F1</th><th>Support</th></tr>
    {% for row in class_report_rows %}
    <tr><td>{{ row.class }}</td><td>{{ row.precision }}</td><td>{{ row.recall }}</td>
        <td>{{ row.f1 }}</td><td>{{ row.support }}</td></tr>
    {% endfor %}
  </table>
  <h3>Confusion matrix (normalised)</h3>
  <img class="chart" src="data:image/png;base64,{{ confusion_img }}" alt="Confusion matrix">

  <h3>Class distribution (top {{ dist_top_n }})</h3>
  <img class="chart" src="data:image/png;base64,{{ distribution_img }}" alt="Class distribution">

  <h2>4 &middot; RAG Explainability Examples</h2>
  <p>The model retrieves the top-{{ top_k }} most similar historical reports as
     evidence for each prediction - an auditable explanation by example.</p>
  <table>
    <tr><th>#</th><th>Input (truncated)</th><th>True &rarr; Predicted</th><th>Top-{{ top_k }} Evidence</th></tr>
    {% for ex in rag_examples %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ ex.input_snippet }}</td>
      <td>{{ ex.true_label }} &rarr; <b>{{ ex.predicted_label }}</b><br>
          <span class="badge {{ 'good' if ex.correct else 'bad' }}">{{ 'CORRECT' if ex.correct else 'MISMATCH' }}</span></td>
      <td>
        {% for ev in ex.evidence %}
        <div class="ev">
          <span class="sim">#{{ ev.rank }} {{ "%.1f"|format(ev.similarity*100) }}%</span>
          <span class="label">{{ ev.label }}</span>
          <span class="domain">&middot; {{ ev.domain }}</span>
          <div class="sim-bar"><div style="width:{{ (ev.similarity*100)|round(1) }}%"></div></div>
          <p>{{ ev.snippet }}</p>
        </div>
        {% endfor %}
      </td>
    </tr>
    {% endfor %}
  </table>

  <h2>5 &middot; Full Classification Report (text)</h2>
  <pre class="report">{{ report_text }}</pre>

</main>
<footer>Safety NLP Pipeline &middot; generated automatically by <code>python main.py</code></footer>
</body>
</html>
"""


# ----------------------------------------------------------------- helpers
def _b64(path: Path) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode()


def _data_quality(df: pd.DataFrame) -> list[dict]:
    """Compute the data-quality audit rows shown in the report."""
    n = len(df)
    narrative = df[NARRATIVE_COL].astype(str)
    dist = df[LABEL_COL].value_counts()

    missing = int(df[LABEL_COL].isna().sum())
    dups = int(narrative.duplicated().sum())
    short = int((narrative.str.len() < 20).sum())
    imbalance = dist.iloc[0] / max(1, dist.iloc[-1])
    other = int(dist.get("Other", 0)) if "Other" in dist.index else 0
    other_share = other / n if n else 0.0

    rows = [
        {"metric": "Total rows", "value": n, "badge": "good", "status": "OK"},
        {"metric": "Columns", "value": ", ".join(df.columns),
         "badge": "good", "status": "OK"},
        {"metric": "Missing labels", "value": missing,
         "badge": "good" if missing == 0 else "warn", "status": "OK" if missing == 0 else "WARN"},
        {"metric": "Duplicate narratives", "value": dups,
         "badge": "good" if dups == 0 else "warn", "status": "OK" if dups == 0 else "WARN"},
        {"metric": "Very short narratives (<20 chars)", "value": short,
         "badge": "good" if short == 0 else "warn", "status": "OK" if short == 0 else "WARN"},
        {"metric": "Class imbalance (majority/minority ratio)",
         "value": f"{imbalance:.1f}x",
         "badge": "warn" if imbalance > 10 else "good",
         "status": "WARN" if imbalance > 10 else "OK"},
        {"metric": "'Other' bucket coverage", "value": f"{other_share:.1%}",
         "badge": "warn" if other_share > 0.5 else "good",
         "status": "WARN" if other_share > 0.5 else "OK"},
        {"metric": "Distinct classes", "value": int(dist.nunique()),
         "badge": "good", "status": "OK"},
    ]
    return rows


# ------------------------------------------------------------------- main
def generate_report(df: pd.DataFrame, eval_results: dict, rag_examples: pd.DataFrame,
                    train_config: dict | None = None) -> Path:
    """Render and save the self-contained HTML report."""
    train_config = train_config or {}
    if Path(TRAIN_CONFIG_PATH).exists():
        try:
            train_config = json.loads(Path(TRAIN_CONFIG_PATH).read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Could not read training_config.json: %s", exc)

    report_df = eval_results["report_df"]
    # Drop non-class rows (accuracy / macro / weighted averages) from the table,
    # keep them visible only in the text report.
    class_rows = []
    for label, vals in report_df.iterrows():
        if label in ("accuracy", "macro avg", "weighted avg"):
            continue
        class_rows.append({
            "class": label,
            "precision": f"{vals['precision']:.3f}",
            "recall": f"{vals['recall']:.3f}",
            "f1": f"{vals['f1-score']:.3f}",
            "support": int(vals["support"]),
        })

    dist = df[LABEL_COL].value_counts()
    top_classes = [
        {"class": c, "count": int(v), "share": float(v / len(df))}
        for c, v in dist.head(15).items()
    ]
    domain_counts = (df[DOMAIN_COL].value_counts().to_dict()
                     if DOMAIN_COL in df.columns else {})

    rag_list = rag_examples.head(RAG_EXAMPLES_IN_REPORT).to_dict("records") \
        if rag_examples is not None and len(rag_examples) else []
    for ex in rag_list:
        if isinstance(ex.get("evidence"), list):
            ex["evidence"] = sorted(ex["evidence"], key=lambda e: -e["similarity"])

    context = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "num_reports": len(df),
        "n_classes": int(df[LABEL_COL].nunique()),
        "accuracy": float(eval_results["accuracy"]),
        "cv_f1": float(train_config.get("best_cv_f1_weighted", 0.0)),
        "domain_counts": domain_counts,
        "train_rows": int(train_config.get("n_train", 0)),
        "test_rows": int(train_config.get("n_test", 0)),
        "best_params": train_config.get("best_params", {}),
        "quality_rows": _data_quality(df),
        "top_classes": top_classes,
        "dist_top_n": int(len(top_classes)),
        "class_report_rows": class_rows,
        "confusion_img": _b64(eval_results["plots"]["confusion_matrix"]),
        "distribution_img": _b64(eval_results["plots"].get("class_distribution")
                                 or eval_results["plots"]["confusion_matrix"]),
        "report_text": eval_results["report_text"],
        "rag_examples": rag_list,
        "top_k": int(len(rag_list[0]["evidence"])) if rag_list else 3,
    }

    html = Template(_REPORT_TEMPLATE).render(**context)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(html, encoding="utf-8")
    logger.info("HTML report written -> %s", REPORT_PATH)
    return REPORT_PATH
