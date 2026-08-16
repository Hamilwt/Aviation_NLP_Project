# Safety NLP Pipeline — Aviation & Power-Grid Incident Analysis

A production-grade NLP pipeline for classifying safety incident reports from **aviation (NASA ASRS)** and **power-grid (NERC)** domains, with **RAG explainability**, **real-time monitoring**, and a **cross-platform React + FastAPI dashboard**.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
cd aviation-safety-app
docker-compose up --build
```
- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Local Development
```bash
# Linux/macOS
cd aviation-safety-app && ./dev.sh

# Windows PowerShell
cd aviation-safety-app && ./dev.ps1
```
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

### Option 3: Desktop App (Tauri)
```bash
cd aviation-safety-app/frontend
npm install
npm run tauri dev        # Development
npm run tauri build      # Production binaries
```

### Option 4: Original Pipeline (Headless)
```bash
cd safety_nlp_pipeline
pip install -r requirements.txt
python main.py           # Full pipeline -> reports/pipeline_report.html
streamlit run app_streamlit.py  # Legacy Streamlit dashboard
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📊 Overview** | Dataset statistics, domain distribution, class charts |
| **📈 Model Performance** | Metrics, confusion matrix, per-class classification reports |
| **🔍 RAG Explorer** | Classify narratives + retrieve similar historical reports as evidence |
| **🤖 Data Assistant** | Keyless pandas analysis (quality, safety, class balance, risk phrases) |
| **🚨 Live Alerts** | Real-time incident monitoring with risk scoring (critical/high/medium) |
| **⚙️ System Control** | Process management, pipeline execution, live logs |

---

## 🏗️ Architecture

```
Aviation_NLP_Project/
├── aviation-safety-app/           # NEW: React + FastAPI Application
│   ├── backend/                   # FastAPI REST API
│   │   ├── main.py               # API endpoints (6 pages + system control)
│   │   ├── ml_service.py         # ML pipeline wrapper
│   │   ├── config.py             # Pydantic settings
│   │   └── schemas.py            # Pydantic models
│   ├── frontend/                 # React + TypeScript + Vite
│   │   ├── src/
│   │   │   ├── pages/            # 6 dashboard pages
│   │   │   ├── components/       # UI components (Card, Button, Input...)
│   │   │   ├── hooks/            # Data-fetching hooks
│   │   │   ├── store/            # Zustand state management
│   │   │   └── api/              # Axios client
│   │   ├── src-tauri/            # Tauri desktop app config
│   │   └── nginx.conf            # Production reverse proxy
│   ├── docker-compose.yml        # Multi-container deployment
│   ├── Dockerfile.backend        # Backend container
│   ├── Dockerfile.frontend       # Frontend container
│   └── dev.sh / dev.ps1          # Cross-platform dev startup
│
├── safety_nlp_pipeline/          # Original Python Pipeline (Preserved)
│   ├── src/                      # Core pipeline modules
│   │   ├── data_fetcher.py       # ASRS + NERC data ingestion
│   │   ├── preprocessor.py       # NLTK preprocessing
│   │   ├── trainer.py            # TF-IDF + SGD + GridSearchCV
│   │   ├── evaluator.py          # Metrics, plots, reports
│   │   ├── rag_explainer.py      # Semantic evidence retrieval
│   │   ├── analyst.py            # Keyless data assistant
│   │   ├── monitor.py            # Real-time monitoring & alerting
│   │   └── report_generator.py   # HTML report generation
│   ├── main.py                   # Headless CLI entry point
│   ├── app_streamlit.py          # Legacy Streamlit dashboard
│   └── config.py                 # All tunable parameters
│
└── PROJECT_OVERVIEW.txt          # Complete project documentation
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

## 📚 Documentation

| File | Description |
|------|-------------|
| `PROJECT_OVERVIEW.txt` | Complete 475-line project documentation |
| `aviation-safety-app/README.md` | React/FastAPI app documentation |
| `safety_nlp_pipeline/README.md` | Original pipeline documentation |
| `aviation-safety-app/backend/.env.example` | Backend configuration template |

---

## 🛠️ Development

### Adding a New Dashboard Page
1. Create component in `aviation-safety-app/frontend/src/pages/`
2. Add route in `aviation-safety-app/frontend/src/App.tsx`
3. Add navigation item in `Sidebar.tsx`

### Extending the API
1. Add schemas in `backend/schemas.py`
2. Add endpoint in `backend/main.py`
3. Update ML service in `backend/ml_service.py`
4. Add hook in `frontend/src/hooks/useApi.ts`

### Running Tests
```bash
# Backend
cd aviation-safety-app/backend && python -m pytest

# Frontend
cd aviation-safety-app/frontend && npm run lint && npm run build
```

---

## 📦 Requirements

### Root (Pipeline)
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

### Backend (FastAPI)
```
fastapi==0.115.0
uvicorn[standard]==0.34.0
pydantic==2.10.6
pydantic-settings==2.9.0
joblib==1.4.2
pandas==2.2.3
scikit-learn==1.6.1
scipy==1.14.1
requests==2.32.3
pypdf==5.1.0
nltk==3.9.1
prometheus-client==0.21.0
structlog==25.1.0
httpx==0.28.1
websockets==13.1
```

### Frontend (React)
```
react: ^18.3.1
react-dom: ^18.3.1
react-router-dom: ^6.26.2
axios: ^1.7.7
recharts: ^2.12.7
lucide-react: ^0.441.0
zustand: ^5.0.0
tailwindcss: ^3.4.13
typescript: ^5.6.2
vite: ^5.4.8
@tauri-apps/cli: ^2.0.0
```

---

## 🎯 Results

- **Dataset**: ~3,700 cleaned reports (2,000 aviation + ~1,700 power-grid)
- **Model**: ~71% accuracy / ~70% weighted F1 over 28 classes
- **RAG**: Every prediction auditable with top-3 historical evidence
- **Cross-domain**: Shared TF-IDF vocabulary surfaces genuine similarities

---

## 📄 License

MIT License — See LICENSE file for details.

---

## 🙏 Acknowledgments

- **NASA ASRS** for aviation incident reports
- **NERC** for power-grid event analysis reports
- **Hugging Face** for datasets-server API
- **UK Power Networks** for live faults open data