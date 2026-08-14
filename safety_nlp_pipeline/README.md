# Safety NLP Pipeline (Headless)

A **production-grade, headless NLP pipeline** that runs end-to-end with **zero
user intervention** and produces a **comprehensive HTML report** with all
outcomes: model metrics, confusion matrix, RAG evidence examples and data
quality insights.

It classifies real safety-incident reports from two domains:

| Domain      | Source                                       | Size                                    |
|-------------|----------------------------------------------|-----------------------------------------|
| Aviation    | NASA ASRS (Hugging Face datasets-server)     | 2,000 reports with expert anomaly labels |
| Power grid  | NERC Event Analysis reports (public PDFs)    | 12 reports -> ~1,700 narrative chunks   |

## Run everything with one command

```bash
pip install -r requirements.txt
python main.py            # fetch -> preprocess -> train -> evaluate -> RAG -> HTML report
```

Then open `reports/pipeline_report.html` in any browser.

## Web dashboard (Streamlit)

A warm, creamy-light themed interactive dashboard for stakeholders. It loads
the artifacts produced by `main.py` and adds live RAG predictions.

```bash
streamlit run app_streamlit.py      # opens http://localhost:8501
```

| Tab                  | Content                                                        |
|----------------------|----------------------------------------------------------------|
| Overview             | dataset size, domain split, class-distribution chart, sample rows |
| Model Performance    | metrics, per-class classification table, confusion-matrix & distribution plots |
| RAG Explorer         | paste an incident -> predicted class + top-3 evidence with similarity bars |
| Data Assistant       | keyless quality / safety / class insights and risk-phrase scanning |

Run `python main.py` at least once before starting the dashboard so the
artifacts exist. The theme can also be tuned in `.streamlit/config.toml`.

## What the pipeline does

```
[1/6] FETCH      Live-download ASRS + NERC, clean, merge by domain -> data/real_safety_dataset.csv
[2/6] PREPROCESS NLTK tokenize -> stopword removal -> lemmatize (per document)
[3/6] TRAIN      TF-IDF (bigrams, max_features=5000) + SGD (log-loss) with GridSearchCV
[4/6] EVALUATE   classification report + confusion-matrix heatmap + class distribution plot
[5/6] RAG        batch explainability: top-3 most similar historical reports per prediction
[6/6] REPORT     self-contained HTML report with all results
```

All console output is mirrored to `pipeline.log`.

## CLI flags

| Flag              | Effect                                                        |
|-------------------|---------------------------------------------------------------|
| `--force-refresh` | Re-download data even if a cached CSV exists                  |
| `--no-fetch`      | Skip fetching (requires the cached CSV)                       |
| `--no-rag`        | Skip the RAG explainability step                              |
| `--samples N`     | Number of test reports to explain with RAG (default 100)      |

## Fault tolerance & idempotency

- If `data/real_safety_dataset.csv` already exists the fetch is **skipped**
  (idempotent). Delete the CSV or pass `--force-refresh` to re-download.
- If **one domain's source fails**, the pipeline falls back to the cached rows
  for that domain, or gracefully skips it with a warning.
- If **both sources fail**, the cached dataset is reused (if present).
- Downloaded NERC PDFs are cached in `data/raw/` so re-fetches are fast.
- Legacy datasets with the old column names (`Narrative`,
  `human_factors_groundtruth`, `Domain`) are auto-normalised on load.

## Configuration

Every tunable parameter lives in `config.py`:

- Data: `NROWS_AVIATION`, `TOP_CATEGORIES`, `NERC_PDFS`
- Modeling: `MAX_FEATURES`, `NGRAM_RANGE`, `TEST_SIZE`, `CV_FOLDS`,
  `GRID_ALPHAS`, `GRID_CLASS_WEIGHTS`
- RAG: `RAG_TOP_K`, `RAG_N_SAMPLES`, `RAG_BATCH`
- Report: `RAG_EXAMPLES_IN_REPORT`, `PLOT_CLASS_TOP_N`

## Project structure

```
safety_nlp_pipeline/
├── README.md
├── requirements.txt
├── config.py                 all parameters (paths, model settings, ...)
├── main.py                   single entry point - runs the full pipeline
├── app_streamlit.py          Streamlit web dashboard (creamy light theme)
├── src/
│   ├── data_fetcher.py       downloads ASRS (HF) + NERC (PDFs) -> CSV
│   ├── preprocessor.py       NLTK tokenization, stopwords, lemmatization
│   ├── trainer.py            TF-IDF + SGD classifier (log-loss) with GridSearchCV
│   ├── evaluator.py          classification report, confusion matrix, plots
│   ├── rag_explainer.py      batch + single-query semantic retrieval (cosine)
│   ├── analyst.py            keyless data quality & safety analysis
│   └── report_generator.py   self-contained HTML report (Jinja2)
├── data/                     auto-created; CSV, models, plots
│   ├── raw/                  cached PDFs
│   ├── real_safety_dataset.csv
│   ├── safety_model.pkl
│   ├── tfidf_vectorizer.pkl
│   ├── training_config.json
│   └── plots/                confusion matrix, class distribution, ...
└── reports/                  generated HTML report
    └── pipeline_report.html
```

## Expected outcomes

- **~70% weighted F1** overall (aviation anomaly labels are noisy and
  imbalanced); **power-grid classes are near-perfect** because NERC event
  names are descriptive.
- The **RAG evidence** makes every prediction auditable: each report in the
  report shows the top-3 historical incidents that most influenced the
  classification, with similarity scores.
- The **confusion matrix** highlights which classes are commonly confused
  (e.g. ATC vs Ground in aviation).

## Notes on research gaps

- **Gap 4 (black-box provenance):** the RAG module explains every prediction
  by example - an audit trail rendered directly in the HTML report.
- **Gap 2 (edge deployment):** the TF-IDF + SGD model is tiny compared to LLMs
  and deploys to constrained devices easily.
- **Gap 3 (cross-domain taxonomy):** aviation and power-grid narratives share
  one TF-IDF vocabulary, so the model distinguishes domains while the RAG
  evidence surfaces genuine cross-domain similarities when they exist.
- **Gap 1 (physical constraints):** the modular design allows swapping the
  classifier head for a solver-based constraint verifier.

## First run

The first run auto-downloads the NLTK corpora (stopwords, punkt, wordnet) and
fetches the live datasets. This may take 2-5 minutes depending on bandwidth.
