# Safety NLP Pipeline - Web Dashboard

A modern, cross-platform React + FastAPI dashboard for the Aviation & Power-Grid Safety NLP Pipeline. Full web-based control of all NLP processes with rich visualizations, **local Ollama LLM integration**, and **auto-generated safety suggestions**.

## ✨ Features

| Page | Description |
|------|-------------|
| **Overview** | Dataset statistics, domain distribution, class charts with interactive visualizations |
| **Model Performance** | Metrics, confusion matrix, per-class reports with bar charts and progress bars |
| **RAG Explorer** | Classify narratives + retrieve similar historical reports as evidence |
| **Data Assistant** | **Local Ollama LLM** (domain-constrained) + rule-based analyst fallback; model selector |
| **Live Alerts** | Real-time incident monitoring with risk scoring, **critical/high/medium/low categories**, **auto-generated safety suggestions**, evidence |
| **System Control** | Process management, pipeline execution with real-time progress tracking, **sanitized paths** |

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- **Ollama** (optional, for LLM-powered Data Assistant): `ollama serve && ollama pull llama3`
- Run the original pipeline first to generate artifacts:
  ```bash
  cd ../safety_nlp_pipeline
  pip install -r requirements.txt
  python main.py
  ```

### Development Mode
```bash
# Terminal 1 - Backend
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

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Production Build
```bash
cd frontend
npm run build
# Serve dist/ with nginx or any static server
```

## 🏗️ Architecture

```
aviation-safety-app/
├── backend/                   # FastAPI REST API
│   ├── main.py               # API endpoints (all 6 pages + system control)
│   ├── ml_service.py         # ML pipeline wrapper with progress tracking
│   ├── config.py             # Pydantic settings (incl. Ollama)
│   ├── schemas.py            # Pydantic models (request/response)
│   ├── ollama_service.py     # Ollama client with domain-constrained chat
│   ├── suggestions.py        # Auto-generated safety suggestions for alerts
│   └── requirements.txt      # Python dependencies
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── charts/       # Recharts components (Bar, Pie, Line, Progress)
│   │   │   ├── layout/       # Sidebar, Header, Layout, **StatusBar**
│   │   │   └── ui/           # Card, Button, Input, Table, Badge, MetricCard
│   │   ├── pages/            # 6 dashboard pages
│   │   ├── hooks/            # Custom React hooks (useApi, useOllamaStatus)
│   │   ├── store/            # Zustand state management
│   │   ├── api/              # Axios client
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Helpers
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── tsconfig.json
└── README.md
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check (includes Ollama status) |
| GET | `/api/overview` | Dataset statistics |
| GET | `/api/model-performance` | Model metrics & reports |
| POST | `/api/classify` | Classify narrative with RAG evidence |
| POST | `/api/analyze` | Data Assistant (Ollama LLM + fallback) |
| GET | `/api/ollama/status` | Ollama connection + live models |
| GET | `/api/alerts` | Live alerts with risk categories + suggestions |
| GET | `/api/system/status` | Service status & logs |
| POST | `/api/system/control/{service}/{action}` | Start/stop/restart services |
| POST | `/api/pipeline/run` | Execute full pipeline with progress |
| GET | `/api/pipeline/progress` | Get pipeline stage progress |
| POST | `/api/pipeline/fetch` | Fetch data only |
| POST | `/api/pipeline/train` | Train model only |
| POST | `/api/monitor/control` | Monitor control |
| POST | `/api/ml/load-artifacts` | Manually load ML artifacts |

## 🎨 Visualization Components

### ChartComponents.tsx
- **BarChartComponent** - Horizontal/vertical bar charts with labels
- **PieChartComponent** - Donut charts with percentages
- **LineChartComponent** - Multi-line charts
- **ProgressBar** - Animated progress bars with color coding
- **MetricCardChart** - KPI cards with trends

### DataDisplay.tsx
- **Card** - Consistent card layout
- **Table** - Sortable, striped tables with custom renderers
- **Badge** - Status badges (success, warning, error, info, critical, high, medium, low)
- **StatGrid** - Responsive metric grid (1-5 columns)
- **Section** - Page sections with headers (flex-wrap for alignment)

### New UI Components
- **StatusBar** - Bottom-fixed bar: Ollama connection, live model count, active model
- **Improved Layout** - Fixed double-scroll issue, proper `h-screen overflow-hidden` root

## 🎯 Key Features

### Real-time Pipeline Progress
- Stage-by-stage tracking (fetch → preprocess → train → evaluate → rag → report)
- Progress bars with status icons
- Live log streaming via WebSocket

### Interactive Charts
- Hover tooltips with formatted values
- Color-coded risk levels (critical=red, high=orange, medium=yellow, low=green)
- Responsive design for all screen sizes

### Full Web Control
- Start/stop pipeline and monitor services
- Configure pipeline parameters (force refresh, skip fetch, skip RAG, samples)
- View real-time logs with filtering
- Run individual pipeline stages

### Live Alerts Dashboard (Enhanced)
- Risk level filtering (critical/high/medium/low)
- Source filtering
- **Category tabs with counts** (All/Critical/High/Medium/Low)
- **Auto-generated safety suggestions** per alert (NLP keyword extraction)
- Expandable alert details with RAG evidence
- Timeline and source distribution charts

### Data Assistant with Local LLM (New)
- **Ollama integration** — zero API key, fully private inference
- **Domain-constrained system prompt** — answers ONLY aviation/power-grid safety questions
- Out-of-domain questions politely refused
- **Model selector** — pick any live Ollama model
- **Rule-based fallback** — works without Ollama (pandas analyst)
- Source badge: "Ollama LLM" vs "Rule-based analyst"

### Status Bar (New)
- Fixed bottom bar
- Ollama connectivity: green "Connected" / red "Disconnected"
- Live model count + active model name
- Backend health indicator
- App version

## 🛠️ Development

### Adding a New Page
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.tsx`
3. Add navigation item in `Sidebar.tsx`

### Extending the API
1. Add schemas in `backend/schemas.py`
2. Add endpoint in `backend/main.py`
3. Update ML service in `backend/ml_service.py` if needed
4. Add hook in `frontend/src/hooks/useApi.ts`
5. Create/update page component

## 📦 Dependencies

### Backend
```
fastapi==0.115.0
uvicorn[standard]==0.34.0
pydantic==2.10.6
pydantic-settings==2.9.0
joblib==1.4.2
pandas==2.2.3
scikit-learn==1.6.1
nltk==3.9.1
httpx==0.28.1
websockets==13.1
```

### Frontend
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
```

## 🔧 Configuration

Environment variables (`backend/.env`):
```env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
LOG_LEVEL=INFO

# Ollama (local LLM)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TIMEOUT=120
OLLAMA_STATUS_TTL=10
```

## 📄 License

MIT License