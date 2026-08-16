# Safety NLP Pipeline - React + FastAPI Application

A cross-platform safety incident analysis application for aviation and power-grid domains, featuring TF-IDF + SGD classification with RAG explainability.

## Architecture

```
aviation-safety-app/
├── backend/                 # FastAPI backend
│   ├── main.py             # FastAPI application with REST API
│   ├── config.py           # Configuration management
│   ├── schemas.py          # Pydantic models
│   ├── ml_service.py       # ML pipeline wrapper
│   └── requirements.txt    # Python dependencies
├── frontend/               # React + TypeScript frontend
│   ├── src/
│   │   ├── components/     # Reusable UI components
│   │   ├── pages/          # Page components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── store/          # Zustand state management
│   │   ├── api/            # API client
│   │   ├── types/          # TypeScript types
│   │   └── utils/          # Utility functions
│   ├── src-tauri/          # Tauri desktop app config
│   └── package.json
├── Dockerfile.backend      # Backend Docker image
├── Dockerfile.frontend     # Frontend Docker image
└── docker-compose.yml      # Multi-container orchestration
```

## Features

- **Overview**: Dataset statistics and domain distribution
- **Model Performance**: Classification metrics, confusion matrix, per-class reports
- **RAG Explorer**: Classify narratives with evidence retrieval
- **Data Assistant**: Keyless pandas-based data analysis
- **Live Alerts**: Real-time incident monitoring dashboard
- **System Control**: Process management for pipeline and monitor

## Quick Start

### Option 1: Docker (Recommended)

```bash
cd aviation-safety-app
docker-compose up --build
```

Access the app at http://localhost:80

### Option 2: Local Development

#### Backend
```bash
cd aviation-safety-app/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('punkt_tab')"

# Run the API server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend
```bash
cd aviation-safety-app/frontend
npm install
npm run dev
```

Access the app at http://localhost:5173

### Option 3: Desktop App (Tauri)

```bash
cd aviation-safety-app/frontend
npm install
npm run tauri dev
```

Build for distribution:
```bash
npm run tauri build
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/overview` | Dataset statistics |
| GET | `/api/model-performance` | Model metrics & reports |
| POST | `/api/classify` | Classify narrative with RAG evidence |
| POST | `/api/analyze` | Data assistant queries |
| GET | `/api/alerts` | Live alerts |
| GET | `/api/system/status` | Service status & logs |
| POST | `/api/system/control/{service}` | Start/stop services |
| POST | `/api/pipeline/run` | Execute full pipeline |

## Configuration

Environment variables (backend/.env):

```env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","tauri://localhost"]
LOG_LEVEL=INFO
```

## Cross-Platform Support

| Platform | Status |
|----------|--------|
| Web (Chrome/Firefox/Safari/Edge) | ✅ Full support |
| Windows (Tauri) | ✅ Native desktop |
| macOS (Tauri) | ✅ Native desktop |
| Linux (Tauri) | ✅ Native desktop |
| Mobile (Capacitor) | 🚧 Planned |

## Data Pipeline

The backend wraps the original Python pipeline (`safety_nlp_pipeline/`):

1. **Fetch**: NASA ASRS aviation reports + NERC power-grid PDFs
2. **Preprocess**: NLTK tokenization, lemmatization, stopword removal
3. **Train**: TF-IDF (bigrams) + SGDClassifier with GridSearchCV
4. **Evaluate**: Classification reports, confusion matrix, plots
5. **RAG**: Cosine similarity evidence retrieval
6. **Monitor**: Real-time incident ingestion & alerting

## Development

### Adding a New Page

1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add navigation item in `frontend/src/components/layout/Sidebar.tsx`

### Extending the API

1. Add schemas in `backend/schemas.py`
2. Add endpoint in `backend/main.py`
3. Update ML service in `backend/ml_service.py` if needed
4. Add hook in `frontend/src/hooks/useApi.ts`
5. Create/update page component

## Troubleshooting

### Model Not Loaded
- Run pipeline first: `POST /api/pipeline/run` or `python main.py` in `safety_nlp_pipeline/`
- Check data exists at `safety_nlp_pipeline/data/real_safety_dataset.csv`

### CORS Errors
- Ensure frontend URL is in `CORS_ORIGINS` in backend config
- For Tauri: add `tauri://localhost` to origins

### WebSocket Issues
- Check proxy config in `frontend/nginx.conf` (Docker) or `vite.config.ts` (dev)

## License

MIT License - See LICENSE file for details.