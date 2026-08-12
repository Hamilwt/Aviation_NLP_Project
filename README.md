# Aviation NLP Pipeline — Terminal UI (menu-driven)

A fully terminal-driven demonstration of an aviation-safety NLP pipeline,
built as an interactive TUI (Textual). Every step runs **visually inside
the terminal** with live progress bars — no browser.

```
  1 · Fetch / Refresh dataset        4 · RAG explainer
  2 · View datasets                 5 · NLP data assistant
  3 · Train model                   6 · Pipeline log
                                     7 · Exit
```

Press a number to select an option (or `m` to re-open the menu at any
time). Option 7 quits.

## Install & run

```bash
pip install -r requirements.txt
python app.py
```

Headless CLI (scripting / CI): `python app.py --fetch`, `--train`,
`--explain <incident text>`.

## What each option does

1. **Fetch dataset** — downloads the public NASA ASRS dataset from Hugging
   Face (no token). If the dataset already exists in `data/`, it is **not
   re-downloaded**: the terminal shows the cached result instantly. Live
   progress: `[███░░░░] DOWNLOADING ASRS REPORTS ...`.
2. **View datasets** — lists every CSV in `data/` and opens the selected
   one: raw narrative preview table + anomaly-category distribution. Any
   dataset file you add later appears here automatically.
3. **Train model** — runs the full NLP training chain with visible stages:
   domain preprocessing → TF-IDF vectorization → train/test split →
   Logistic Regression fitting → evaluation, then displays the complete
   classification report (accuracy, per-category precision/recall).
4. **RAG explainer** — paste a new incident report; the system predicts its
   risk category and retrieves the top-3 most similar historical reports
   as evidence, with similarity bars (`█…` + %).
5. **NLP data assistant** — keyless analyst working on the loaded dataset.
   Quick buttons: Summary, Quality/issues, Safety/critical, Classes; or
   type free-form questions:
   - `quality` / `issues` — what is right and wrong in the data (missing
     values, duplicate narratives, very short reports, class imbalance,
     'Other' bucket coverage)
   - `safety` / `critical` — safety-criticality breakdown and the most
     frequent critical categories (CFIT, NMAC, loss of control, ...)
   - `classes` — class distribution
   - `analyze <text>` — scans a narrative for high-risk phrases (TCAS RA,
     terrain, wake vortex, fatigue, fire/smoke, ...)
6. **Pipeline log** — full console output of every step, live.
7. **Exit** — close the TUI.

## Why scikit-learn?

The training step (option 3) uses scikit-learn's `TfidfVectorizer`,
`LogisticRegression`, `train_test_split` and `classification_report`; the
RAG step (option 4) uses its `cosine_similarity` for the semantic
evidence retrieval. That is why `scikit-learn` is in `requirements.txt`.

## Project structure

```
app.py               TUI entry point (Textual) + headless CLI
pipeline/
  paths.py           data/ layout, artifact discovery, defaults
  fetch_data.py      step 1: download/clean ASRS dataset
  preprocess.py      shared domain preprocessing
  train_model.py     step 2: TF-IDF + LogisticRegression training
  rag_explainer.py   step 3: classify + semantic evidence retrieval
  analyst.py         NLP data assistant (quality & safety analysis)
data/                artifacts (generated; git-ignored)
requirements.txt     textual · pandas · scikit-learn · datasets · joblib
```

## Data & artifacts

- Datasets: `data/*.csv` — the Dataset tab (option 2) lists every one.
- Models: `data/*.pkl` (model + vectorizer) — produced by option 3.
- Both folders are git-ignored; `data/real_asrs_dataset.csv` is the default
  ASRS dataset (2000 cleaned reports, 16 anomaly categories).