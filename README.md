# Aviation NLP Pipeline — Terminal UI

A fully terminal-driven demonstration of an aviation-safety NLP pipeline:

1. **Fetch** — download the public NASA ASRS dataset from Hugging Face
   (no token needed) and clean it: multi-label anomaly strings are reduced
   to their primary category and rare categories are bucketed as `Other`.
2. **Preprocess** — domain preprocessing engine: lowercase + noise removal.
3. **Train** — TF-IDF (bigrams) → Logistic Regression, saved as pickles.
4. **RAG explainer** — classify any new incident report and retrieve the
   top-3 most similar historical reports as evidence (in-context prompting).

Everything runs **inside the terminal** — no browser. If a step's artifact
already exists (`data/*.csv`, `data/*.pkl`) the TUI displays it instead of
re-running the expensive operation. Any CSV dropped into `data/` is
immediately selectable in the Dataset tab.

## Run

```bash
pip install -r requirements.txt
python app.py                # full TUI
python app.py --fetch        # headless: download/reuse dataset
python app.py --train        # headless: train model
python app.py --explain "misheard altitude restriction, descended below cleared altitude"
```

## TUI usage

| Key | Action |
|-----|--------|
| `f` | Fetch dataset |
| `t` | Train model |
| `e` | Explain report in the RAG tab |
| `Tab` | Move between widgets |
| `q` / `Ctrl+C` | Quit |

Tabs: `1 · Dataset` (live table preview + class distribution), `2 · Train
Model` (classification report), `3 · RAG Explainer` (type a report, get the
predicted category + evidence spans), `4 · Pipeline Log` (every step's
console output). The top bar shows the pipeline stage statuses
(`FETCH / TRAIN / EXPLAIN` → `[OK]` when artifacts exist).

## Project structure

```
app.py                 TUI entry point (Textual) + headless CLI
pipeline/
  paths.py             data/ layout, artifact discovery, defaults
  fetch_data.py        step 1: download/clean ASRS dataset
  preprocess.py        shared domain preprocessing
  train_model.py       step 2: TF-IDF + LogisticRegression training
  rag_explainer.py     step 3: classify + semantic evidence retrieval
data/                  artifacts (generated, git-ignored)
requirements.txt       textual, pandas, scikit-learn, datasets, joblib
```

## Testing the pipeline headlessly (no UI)

```bash
python -c "from pipeline.fetch_data import fetch_and_clean; print(fetch_and_clean()['status'])"
python -c "from pipeline.train_model import train_classifier; print(train_classifier()['accuracy'])"
python -c "from pipeline.rag_explainer import explain_incident; print(explain_incident('gear down early on finals')['predicted_label'])"
```