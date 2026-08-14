"""Central configuration for the Safety NLP Pipeline.

Every tunable parameter lives here so the pipeline can be re-run or scaled
without touching module code. Directory creation is done at import time so
downstream modules can rely on the folders existing.
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Register the pipeline root on sys.path so sibling modules (config,
# preprocessor, src.*) resolve regardless of the process working directory
# (e.g. when launched via `streamlit run`).
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# ------------------------------------------------------------------- dirs
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"          # optional cached PDFs / raw downloads
PLOTS_DIR = DATA_DIR / "plots"      # confusion matrix, class distribution, ...
REPORTS_DIR = BASE_DIR / "reports"  # generated HTML report
LOG_FILE = BASE_DIR / "pipeline.log"

for _d in (DATA_DIR, RAW_DIR, PLOTS_DIR, REPORTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------ data sources
# Aviation safety: NASA ASRS reports served by the Hugging Face datasets-server
# (lightweight, paginated JSON rows - no full-dataset download required).
ASRS_DATASET = "elihoole/asrs-aviation-reports"
ASRS_SPLIT = "train"
ASRS_NARRATIVE_COL = "Report 1_Narrative"
ASRS_LABEL_COL = "Events_Anomaly"
ASRS_ROWS_API = "https://datasets-server.huggingface.co/rows"
ASRS_FETCH_BATCH = 100

# Power infrastructure safety: public NERC Event Analysis reports (PDFs).
# Each entry is (event label, direct PDF url).
NERC_PDFS = [
    ("Power Grid - Northeast Blackout 2003",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "august_2003_blackout_final_report.pdf"),
    ("Power Grid - Hurricane Sandy",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "hurricane_sandy_ear_20140312_final.pdf"),
    ("Power Grid - Hurricane Harvey",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "nerc_hurricane_harvey_ear_20180309.pdf"),
    ("Power Grid - Hurricane Irma",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "september-2017-hurricane-irma-event-analysis-report.pdf"),
    ("Power Grid - San Fernando Disturbance",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "san_fernando_disturbance_report.pdf"),
    ("Power Grid - January 11 Oscillation Event",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "january_11_oscillation_event_report.pdf"),
    ("Power Grid - South Central Cold Weather",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "south_central_cold_weather_event_ferc-nerc-report_20190718.pdf"),
    ("Power Grid - Solar PV Disturbance 2018",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "april_may_2018_solar_pv_disturbance_report.pdf"),
    ("Power Grid - Northeast Snowstorm 2011",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "ne_outage_report-05-31-12.pdf"),
    ("Power Grid - Arizona Southern California Outage",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "azoutage_report_01may12.pdf"),
    ("Power Grid - IBR Disturbances Western Interconnection",
     "https://www.nerc.com/globalassets/our-work/reports/event-reports/"
     "ibr_disturbances_wi_20251105.pdf"),
    ("Power Grid - January 2025 Arctic Events",
     "https://www.nerc.com/globalassets/programs/event-analysis/"
     "25_arctic_storms_performance_review_0416.pdf"),
]

# ------------------------------------------------------ canonical schema
# The pipeline normalises every dataset (new fetches AND legacy caches) to
# these lowercase column names.
NARRATIVE_COL = "narrative"
LABEL_COL = "label"
DOMAIN_COL = "domain"
PROCESSED_COL = "processed_text"

DOMAIN_AVIATION = "Aviation"
DOMAIN_POWER = "Power Grid"

# Column aliases accepted when loading a cached/legacy CSV.
COLUMN_ALIASES = {
    "Report 1_Narrative": NARRATIVE_COL,
    "Events_Anomaly": LABEL_COL,
    "Narrative": NARRATIVE_COL,
    "human_factors_groundtruth": LABEL_COL,
    "Domain": DOMAIN_COL,
    "narrative": NARRATIVE_COL,
    "label": LABEL_COL,
    "domain": DOMAIN_COL,
}

# ------------------------------------------------------------- collection
NROWS_AVIATION = 2000        # ASRS narratives to stream
TOP_CATEGORIES = 15          # rare anomaly labels are bucketed as "Other"
MIN_NARRATIVE_LEN = 20       # rows shorter than this are dropped
PDF_CACHE = True             # cache downloaded NERC PDFs in data/raw

# -------------------------------------------------------------- modeling
MAX_FEATURES = 5000
NGRAM_RANGE = (1, 2)
TEST_SIZE = 0.2
RANDOM_STATE = 42
CV_FOLDS = 3
SGD_MAX_ITER = 1000

# GridSearchCV hyperparameter space (SGDClassifier, loss="log_loss").
GRID_ALPHAS = [1e-5, 1e-4, 1e-3]
GRID_CLASS_WEIGHTS = [None, "balanced"]

# ------------------------------------------------------------------- rag
RAG_TOP_K = 3                # evidence spans per prediction
RAG_BATCH = 200              # cosine-similarity batch size
RAG_N_SAMPLES = 100          # test reports explained in the report
RAG_EVIDENCE_SNIPPET = 170   # characters shown per evidence narrative

# ------------------------------------------------------------- artifacts
DATASET_PATH = DATA_DIR / "real_safety_dataset.csv"
MODEL_PATH = DATA_DIR / "safety_model.pkl"
VECTORIZER_PATH = DATA_DIR / "tfidf_vectorizer.pkl"
TRAIN_CONFIG_PATH = DATA_DIR / "training_config.json"

# Persisted evaluation outputs (consumed by the Streamlit dashboard)
CLASSIFICATION_REPORT_TXT = DATA_DIR / "classification_report.txt"
CLASSIFICATION_REPORT_CSV = DATA_DIR / "classification_report.csv"
METRICS_JSON = DATA_DIR / "metrics.json"

# ---------------------------------------------------------------- report
REPORT_PATH = REPORTS_DIR / "pipeline_report.html"
RAG_EXAMPLES_IN_REPORT = 10  # RAG rows rendered in the HTML report
PLOT_CLASS_TOP_N = 10        # classes shown in the distribution bar chart
