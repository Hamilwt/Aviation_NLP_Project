"""Central artifact/resource paths.

All datasets, models and vectorizers live in the ``data/`` folder so the
TUI can list existing artifacts and display them instead of re-running
expensive steps.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# ------------------------------------------------------------------ sources
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
NERC_REPORTS = [
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

# Column-name hints used to auto-detect narrative / label columns
NARRATIVE_KEYWORDS = ("narrative", "report", "synopsis")
LABEL_KEYWORDS = ("anomaly", "event", "category", "label")

# Training defaults
NROWS_LIMIT = 2000
TOP_CATEGORIES = 15
MAX_FEATURES = 3000

# Artifact file names
DEFAULT_DATASET = DATA_DIR / "real_safety_dataset.csv"
DEFAULT_MODEL = DATA_DIR / "safety_model.pkl"
DEFAULT_VECTORIZER = DATA_DIR / "tfidf_vectorizer.pkl"

DOMAIN_COL = "Domain"
AVIATION_DOMAIN = "Aviation"
POWER_DOMAIN = "Power Grid"
NARRATIVE_COL = "Narrative"
LABEL_COL = "human_factors_groundtruth"


def find_datasets():
    """Return all CSV datasets present in the data folder."""
    DATA_DIR.mkdir(exist_ok=True)
    return sorted(DATA_DIR.glob("*.csv"))


def find_model_files():
    """Return all pickled model/vectorizer artifacts in the data folder."""
    DATA_DIR.mkdir(exist_ok=True)
    return sorted(DATA_DIR.glob("*.pkl"))
