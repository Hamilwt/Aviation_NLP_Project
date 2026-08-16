# Safety NLP Pipeline — Aviation & Power-Grid Incident Analysis

A production-grade NLP pipeline for classifying safety incident reports from **aviation (NASA ASRS)** and **power-grid (NERC)** domains, with **RAG explainability**, **real-time monitoring**, and a **modern React + FastAPI web dashboard**.

---

## 🚀 Quick Start

### 1. Run the Core Pipeline (Generate Artifacts)
```bash
cd safety_nlp_pipeline
pip install -r requirements.txt
python main.py           # Full pipeline → generates models, reports, metrics
```

### 2. Launch the Web Dashboard
```bash
cd aviation-safety-app

# Terminal 1 - Backend API
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab')"
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

- **Dashboard**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## ✨ Dashboard Features

| Page | Visualizations | Controls |
|------|---------------|----------|
| **Overview** | Domain pie chart, class bar charts, metric cards | Refresh data |
| **Model Performance** | Per-class precision/recall/F1 bars, support charts, confusion matrix | View training config |
| **RAG Explorer** | Similarity progress bars, evidence cards, sample narratives | Top-K selector, classify button |
| **Data Assistant** | Query history, formatted responses, quick analysis buttons | Natural language queries |
| **Live Alerts** | Risk level pie chart, source bar chart, filterable alert table | Risk/source filters, expandable evidence |
| **System Control** | Pipeline stage progress bars, service status badges, live logs | Start/stop services, run pipeline with options |

---

## 🏗️ Project Structure

```
Aviation_NLP_Project/
├── aviation-safety-app/           # Modern Web Dashboard (React + FastAPI)
│   ├── backend/                   # FastAPI REST API
│   │   ├── main.py               # All API endpoints
│   │   ├── ml_service.py         # ML wrapper with progress tracking
│   │   ├── config.py             # Settings
│   │   └── schemas.py            # Pydantic models
│   ├── frontend/                 # React + TypeScript + Vite
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   ├── charts/       # Recharts: Bar, Pie, Line, Progress
│   │   │   │   ├── layout/       # Sidebar, Header, Layout
│   │   │   │   └── ui/           # Card, Table, Badge, MetricCard
│   │   │   ├── pages/            # 6 dashboard pages
│   │   │   ├── hooks/            # useApi hooks
│   │   │   ├── store/            # Zustand state
│   │   │   └── api/              # Axios client
│   │   └── package.json
│   └── README.md
│
├── safety_nlp_pipeline/          # Core Python Pipeline (Headless)
│   ├── src/                      # Pipeline modules
│   │   ├── data_fetcher.py       # ASRS + NERC ingestion
│   │   ├── preprocessor.py       # NLTK preprocessing
│   │   ├── trainer.py            # TF-IDF + SGD + GridSearchCV
│   │   ├── evaluator.py          # Metrics, plots, reports
│   │   ├── rag_explainer.py      # Semantic evidence retrieval
│   │   ├── analyst.py            # Keyless data assistant
│   │   ├── monitor.py            # Real-time monitoring
│   │   └── report_generator.py   # HTML report generation
│   ├── main.py                   # CLI entry point
│   ├── config.py                 # All parameters
│   └── requirements.txt
│
└── PROJECT_OVERVIEW.txt          # Complete documentation (475 lines)
```

---

## 🔬 Pipeline Details

### Data Sources (Live, Not Pre-baked)
| Domain | Source | Size |
|--------|--------|------|
| **Aviation** | NASA ASRS (Hugging Face datasets-server) | 2,000 reports with expert anomaly labels |
| **Power Grid** | NERC Event Analysis (public PDFs) | 12 reports → ~1,700 narrative chunks |

### ML Pipeline
1. **Fetch** → Live download ASRS + NERC, clean, merge by domain
2. **Preprocess** → NLTK tokenize → stopword removal → lemmatize
3. **Train** → TF-IDF (bigrams, 5000 features) + SGDClassifier (log-loss) with GridSearchCV
4. **Evaluate** → Classification report, confusion matrix, class distribution plots
5. **RAG** → Batch cosine similarity retrieval (top-3 evidence per prediction)
6. **Report** → Self-contained HTML with all results

### Real-Time Monitoring
- **Drop-in folder**: `new_incidents/*.csv` or `*.txt`
- **Master dataset**: Appended rows to `real_safety_dataset.csv`
- **NTSB API**: Daily US aviation accidents (probable cause)
- **UKPN Live Faults**: Minute-level UK power cuts (≥100 customers → high risk)

---

## 🎯 Results

- **Dataset**: ~3,700 cleaned reports (2,000 aviation + ~1,700 power-grid)
- **Model**: ~71% accuracy / ~70% weighted F1 over 28 classes
- **RAG**: Every prediction auditable with top-3 historical evidence
- **Cross-domain**: Shared TF-IDF vocabulary surfaces genuine similarities

---

## 🛠️ Development

### Dashboard Development
```bash
cd aviation-safety-app/frontend
npm run dev          # Hot reload
npm run build        # Production build
npm run lint         # ESLint + TypeScript check
```

### Backend Development
```bash
cd aviation-safety-app/backend
uvicorn main:app --reload
# API docs at http://localhost:8000/docs
```

---

## 📦 Requirements

### Core Pipeline
```
textual>=8.2
pandas>=2.2
scikit-learn>=1.5
datasets>=3.0
joblib>=1.4
nltk>=3.8
python-docx>=1.1
pypdf>=4.0
```

### Backend API
```
fastapi==0.115.0
uvicorn[standard]==0.34.0
pydantic==2.10.6
pydantic-settings==2.9.0
joblib==1.4.2
pandas==2.2.3
scikit-learn==1.6.1
nltk==3.9.1
```

### Frontend
```
react: ^18.3.1
react-router-dom: ^6.26.2
axios: ^1.7.7
recharts: ^2.12.7
lucide-react: ^0.441.0
zustand: ^5.0.0
tailwindcss: ^3.4.13
vite: ^5.4.8
```

---

## 📄 Documentation

| File | Description |
|------|-------------|
| `PROJECT_OVERVIEW.txt` | Complete 475-line project documentation |
| `aviation-safety-app/README.md` | Dashboard documentation |
| `safety_nlp_pipeline/README.md` | Core pipeline documentation |

---

## 📄 License

MIT License