# Safety NLP Pipeline — Terminal UI (menu-driven)

A fully terminal-driven demonstration of a **real** NLP pipeline over real
safety-incident data, built as an interactive TUI (Textual). Every step runs
**visually inside the terminal** with live progress bars driven by actual
work — no browser, no fake animation.

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

## What the progress bar is really showing

Every `%` maps to a completed operation — nothing is staged:

- **Fetch** — advances as ASRS report rows are actually streamed from the
  datasets-server and as each NERC PDF is downloaded and parsed.
- **Train (option 3)** — advances per *document* during NLTK
  preprocessing (`PREPROCESSING 412/2035 (NLTK)`), then per *minibatch*
  while the SGD/logistic classifier is fitted (`EPOCH 2/3 BATCH 9/21`).
- **RAG (option 4)** — advances per real cosine-similarity batch
  (`EMBEDDING + MATCHING 1200/2035`).

## What the fetch step really downloads

The dataset is collected **live from public sources every run** (it is not
pre-baked into the repo):

| Domain | Source | What is downloaded |
|--------|--------|--------------------|
| Aviation | NASA ASRS (via Hugging Face datasets-server) | 2,000 real incident reports, expert anomaly labels from `Events_Anomaly` |
| Power grid | NERC Event Analysis reports (public PDFs) | 12 real grid-incident post-mortems (Northeast 2003 blackout, Hurricane Sandy, San Fernando disturbance, ...) parsed with pypdf and split into narratives with NLTK sentence tokenization |

Both are merged into `data/real_safety_dataset.csv` with a `Domain` column
(`Aviation` / `Power Grid`). If a source is unreachable the run falls back
to the cached copy instead of dying.

## What each option does

1. **Fetch dataset** — live-downloads the two real sources above with real
   streaming progress, then shows the cleaned, domain-tagged result.
2. **View datasets** — lists every CSV in `data/` and opens the selected
   one: raw narrative preview table (with domain) + anomaly-category
   distribution. Any dataset file you add later appears here automatically.
3. **Train model** — full NLP training chain with visible real progress:
   domain preprocessing (NLTK tokenize → stopword removal → lemmatize) →
   TF-IDF vectorization (bigrams) → stratified train/test split → SGD
   (log-loss) fitted over shuffled minibatches/epochs with balanced class
   weights → evaluation, then the complete classification report.
4. **RAG explainer** — paste a new incident report; the system predicts its
   risk category (aviation or power-grid) and retrieves the top-3 most
   similar historical reports as evidence, with similarity bars
   (`█…` + %) and the domain of each match.
5. **NLP data assistant** — keyless analyst working on the loaded dataset.
   Quick buttons: Summary, Quality/issues, Safety/critical, Classes; or
   type free-form questions:
   - `quality` / `issues` — what is right and wrong in the data (missing
     values, duplicate narratives, very short reports, class imbalance,
     'Other' bucket coverage)
   - `safety` / `critical` — safety-criticality breakdown, domain split
     (Aviation vs Power Grid) and the most frequent critical categories
   - `classes` — class distribution
   - `analyze <text>` — scans a narrative for high-risk phrases
6. **Pipeline log** — full console output of every step, live.
7. **Exit** — close the TUI.

## Why scikit-learn?

The training step (option 3) uses scikit-learn's `TfidfVectorizer`,
`SGDClassifier` (log-loss — mathematically the same objective as logistic
regression, but it trains incrementally so the progress bar reflects real
minibatch fits), `train_test_split` and `classification_report`; the RAG
step (option 4) uses its `cosine_similarity` for semantic evidence
retrieval. That is why `scikit-learn` is in `requirements.txt`.

## Project structure

```
app.py               TUI entry point (Textual) + headless CLI
pipeline/
  paths.py           data/ layout, live data-source URLs, defaults
  fetch_data.py      step 1: live-download ASRS + NERC, clean, merge by domain
  preprocess.py      shared NLTK domain preprocessing
  train_model.py     step 2: TF-IDF + SGD/Logistic minibatch training
  rag_explainer.py   step 3: classify + batch semantic evidence retrieval
  analyst.py         NLP data assistant (quality & safety analysis)
data/                artifacts (generated; git-ignored)
requirements.txt     textual · pandas · scikit-learn · datasets · joblib · nltk · pypdf · python-docx
```

## Data & artifacts

- Datasets: `data/*.csv` — the Dataset tab (option 2) lists every one.
- Models: `data/*.pkl` (model + vectorizer) — produced by option 3.
- Both folders are git-ignored; `data/real_safety_dataset.csv` is the
  default combined dataset (2000 aviation + ~1700 power-grid narratives).
