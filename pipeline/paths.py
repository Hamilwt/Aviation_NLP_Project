"""Central artifact/resource paths.

All datasets, models and vectorizers live in the ``data/`` folder so the
TUI can list existing artifacts and display them instead of re-running
expensive steps.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Default Hugging Face ASRS dataset (ungated, no token required)
DEFAULT_HF_DATASET = "elihoole/asrs-aviation-reports"

# Column-name hints used to auto-detect narrative / label columns
NARRATIVE_KEYWORDS = ("narrative", "report", "synopsis")
LABEL_KEYWORDS = ("anomaly", "event", "category", "label")

# Training defaults
NROWS_LIMIT = 2000
TOP_CATEGORIES = 15
MAX_FEATURES = 3000

# Artifact file names
DEFAULT_DATASET = DATA_DIR / "real_asrs_dataset.csv"
DEFAULT_MODEL = DATA_DIR / "asrs_model.pkl"
DEFAULT_VECTORIZER = DATA_DIR / "tfidf_vectorizer.pkl"


def find_datasets():
    """Return all CSV datasets present in the data folder."""
    DATA_DIR.mkdir(exist_ok=True)
    return sorted(DATA_DIR.glob("*.csv"))


def find_model_files():
    """Return all pickled model/vectorizer artifacts in the data folder."""
    DATA_DIR.mkdir(exist_ok=True)
    return sorted(DATA_DIR.glob("*.pkl"))