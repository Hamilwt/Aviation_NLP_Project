# Safety NLP Pipeline (Headless Python Core)

The **production-grade headless NLP pipeline** that powers the cross-platform dashboard. Runs end-to-end with **zero user intervention** and produces a **comprehensive HTML report** with all outcomes: model metrics, confusion matrix, RAG evidence examples, and data quality insights.

> **New**: This pipeline is now wrapped by a **FastAPI backend** and **React frontend** in `../aviation-safety-app/` for a modern cross-platform dashboard experience.

---

## 🚀 Run Everything with One Command

```bash
pip install -r requirements.txt
python main.py            # fetch → preprocess → train → evaluate → RAG → HTML report
```

Then open `reports/pipeline_report.html` in any browser.

---

## 🌐 Web Dashboards

### Modern React + FastAPI Dashboard (Recommended)
```bash
cd ../aviation-safety-app
# See ../aviation-safety-app/README.md for full setup.
# Easiest path: use the one-click launcher from the project root:
cd ..
python start.py                      # Linux/Mac/Windows (Python 3.11+)
#   or
./start_app.sh                       # Linux/Mac
./start_app.ps1                      # Windows PowerShell
start_app.bat                        # Windows cmd
```
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Legacy Streamlit Dashboard (Deprecated)
> Still functional and supported for offline use, but the React + FastAPI dashboard above is the recommended interface.
```bash
streamlit run app_streamlit.py      # opens http://localhost:8501
```

| Tab | Content |
|-----|---------|
| Overview | dataset size, domain split, class-distribution chart, sample rows |
| Model Performance | metrics, per-class classification table, confusion-matrix & distribution plots |
| RAG Explorer | paste an incident → predicted class + top-3 evidence with similarity bars |
| Data Assistant | keyless quality / safety / class insights and risk-phrase scanning |
| Live Alerts | alerts raised by the monitor: color-coded table + RAG evidence expanders |
| System Control | manage pipeline/monitor processes, view logs, run pipeline |

---

## ⚡ Real-Time Monitoring & Alerting

The batch pipeline only reacts when run. `src/monitor.py` makes it **proactive**:

```bash
python main.py            # train once so the model exists
python -m src.monitor     # start the monitor (continuous loop)
```

### Ingestion Sources
| Source | How incidents arrive |
|--------|---------------------|
| Drop-in folder | drop a `new_incidents/*.csv` or `*.txt` report (forgiving parser) |
| Master dataset | rows appended to `data/real_safety_dataset.csv` (baseline on first scan) |
| NTSB API (CC0) | public US aviation accidents with probable-cause narratives, refreshed daily |
| UKPN Live Faults | near-real-time UK power cuts; unplanned only, ≥100 customers escalates to high |

### Risk Scoring
- **Critical**: fire, smoke, loss of communication, power outage, crash, emergency, terrain, engine failure...
- **High**: altitude, runway, weather, wind shear, engine, fuel, outage, storm, arctic...
- **Medium**: everything else

Alerts land in `data/alerts.csv` and appear in the dashboard's **Live Alerts** tab. De-duplication state persists to `data/monitor_state.json`.

```bash
python -m src.monitor --once --no-api   # single scan (CI / demos)
python main.py --monitor --poll 30      # train, then start monitoring
```

---

## 🏗️ Pipeline Architecture

```
data/real_safety_dataset.csv   (NASA ASRS + NERC, ~3,700 domain-tagged reports)
      |
[1/6] FETCH      Live-download ASRS + NERC, clean, merge by domain -> CSV
      |
[2/6] PREPROCESS NLTK tokenize → stopword removal → lemmatize (per document)
      |
[3/6] TRAIN      TF-IDF (bigrams, max_features=5000) + SGD (log-loss) with GridSearchCV
      |
[4/6] EVALUATE   classification report + confusion-matrix heatmap + class distribution plot
      |
[5/6] RAG        batch explainability: top-3 most similar historical reports per prediction
      |
[6/6] REPORT     self-contained HTML report with all results
      |
[Web] FASTAPI    REST API wrapping all pipeline functionality
      |
[Web] REACT      Cross-platform dashboard (Web)
      |
[Mon] MONITOR    Real-time incident monitoring & alerting
```

---

## 📋 CLI Flags

| Flag | Effect |
|------|--------|
| `--force-refresh` | Re-download data even if a cached CSV exists |
| `--no-fetch` | Skip fetching (requires the cached CSV) |
| `--no-rag` | Skip the RAG explainability step |
| `--samples N` | Number of test reports to explain with RAG (default 100) |
| `--monitor` | Start the real-time incident monitor after the pipeline |
| `--poll N` | Monitor poll interval in seconds (default 60) |

---

## 🛡️ Fault Tolerance & Idempotency

- If `data/real_safety_dataset.csv` exists → fetch **skipped** (idempotent)
- One domain fails → falls back to cached rows for that domain
- Both fail → cached dataset reused (if present)
- NERC PDFs cached in `data/raw/` → fast re-fetches
- Legacy column names (`Narrative`, `human_factors_groundtruth`, `Domain`) auto-normalised

---

## ⚙️ Configuration (`config.py`)

All tunable parameters in one place:

```python
# Data
NROWS_AVIATION = 2000
TOP_CATEGORIES = 15
NERC_PDFS = [...]  # 12 public NERC PDF URLs

# Modeling
MAX_FEATURES = 5000
NGRAM_RANGE = (1, 2)
TEST_SIZE = 0.2
CV_FOLDS = 3
GRID_ALPHAS = [1e-5, 1e-4, 1e-3]
GRID_CLASS_WEIGHTS = [None, "balanced"]

# RAG
RAG_TOP_K = 3
RAG_N_SAMPLES = 100
RAG_BATCH = 200

# Monitor
MONITOR_POLL_SECONDS = 60
NTSB_POLL_SECONDS = 3600
UKPN_POLL_SECONDS = 60
ALERT_HIGH_MIN_CUSTOMERS = 100
```

---

## 📁 Project Structure

```
safety_nlp_pipeline/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config.py                    # All parameters (paths, model settings, ...)
├── main.py                      # Single entry point - runs the full pipeline
├── app_streamlit.py             # Legacy Streamlit web dashboard (deprecated)
├── .streamlit/
│   └── config.toml              # Dashboard theme configuration
├── src/
│   ├── __init__.py
│   ├── data_fetcher.py          # Downloads ASRS (HF) + NERC (PDFs) -> CSV
│   ├── preprocessor.py          # NLTK tokenization, stopwords, lemmatization
│   ├── trainer.py               # TF-IDF + SGD classifier (log-loss) with GridSearchCV
│   ├── evaluator.py             # Classification report, confusion matrix, plots
│   ├── rag_explainer.py         # Batch + single-query semantic retrieval (cosine)
│   ├── analyst.py               # Keyless data quality & safety analysis
│   ├── monitor.py               # Real-time incident monitoring & alerting
│   └── report_generator.py      # Self-contained HTML report (Jinja2)
├── new_incidents/               # Drop-in folder for new CSV/TXT reports
│   └── README.txt               # Format documentation
├── data/                        # Auto-created; CSV, models, plots, metrics
│   ├── raw/                     # Cached NERC PDFs
│   ├── real_safety_dataset.csv  # Combined dataset (~3,700 reports)
│   ├── safety_model.pkl         # Trained SGDClassifier
│   ├── tfidf_vectorizer.pkl     # Fitted TF-IDF vectorizer
│   ├── training_config.json     # Best hyperparameters
│   ├── classification_report.txt / .csv
│   ├── metrics.json             # Accuracy, F1, etc.
│   ├── alerts.csv               # Every raised alert
│   ├── monitor_state.json       # Monitor de-dup state (survives restarts)
│   └── plots/                   # confusion_matrix.png, class_distribution.png
└── reports/                     # Generated HTML report
    └── pipeline_report.html     # Self-contained, opens in any browser
```

---

## 📊 Expected Outcomes

- **~70% weighted F1** overall (aviation anomaly labels are noisy and imbalanced)
- **Power-grid classes near-perfect** (NERC event names are descriptive)
- **RAG evidence** makes every prediction auditable
- **Confusion matrix** highlights commonly confused classes (e.g., ATC vs Ground)

---

## 🔬 Research Gaps Addressed

| Gap | Solution |
|-----|----------|
| **Black-box provenance** | RAG module explains every prediction by example |
| **Edge deployment** | Lightweight TF-IDF + SGD deploys to constrained devices |
| **Cross-domain taxonomy** | Shared vocabulary distinguishes domains, surfaces similarities |
| **Physical constraints** | Modular design allows swapping classifier head |

---

## 📦 Dependencies

```
pandas>=2.2
scikit-learn>=1.5
datasets>=3.0
joblib>=1.4
nltk>=3.8
pypdf>=4.0
requests>=2.31
matplotlib>=3.8
seaborn>=0.13
jinja2>=3.1
streamlit>=1.37
textual>=8.2
python-docx>=1.1
```

---

## 🏃 First Run

```bash
pip install -r requirements.txt
python main.py
```

First run auto-downloads NLTK corpora (stopwords, punkt, wordnet) and fetches live datasets (2-5 minutes). Subsequent runs reuse cache. Monitor requires trained model — run `python main.py` first.

---

## 🔗 Related

- **Modern Dashboard**: `../aviation-safety-app/` — React + FastAPI
- **One-click Launcher**: `../start.py`, `../start_app.sh`, `../start_app.ps1`, `../start_app.bat`
- **Full Documentation**: `../PROJECT_OVERVIEW.txt` (~475 lines)
- **Legacy TUI**: `../app.py` — Textual terminal interface (preserved)