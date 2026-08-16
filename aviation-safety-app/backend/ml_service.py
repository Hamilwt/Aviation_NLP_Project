"""Core ML service wrapping the safety NLP pipeline functionality."""
import json
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from config import settings
from schemas import EvidenceItem

logger = logging.getLogger(__name__)

# Column names
NARRATIVE_COL = "narrative"
LABEL_COL = "label"
DOMAIN_COL = "domain"
PROCESSED_COL = "processed_text"

# Risk keywords (from analyst.py)
CRITICAL_KEYWORDS = [
    "cfit", "nmac", "loss of aircraft control", "wake vortex",
    "unstabilized approach", "smoke / fire", "engine", "fuel",
    "near midair", "midair", "terrain",
    "blackout", "outage", "disturbance", "system emergency",
]
HIGH_KEYWORDS = [
    "altitude excursion", "altitude overshoot", "altitude undershoot",
    "runway", "incursion", "excursion", "bird / animal", "object",
    "weather / turbulence", "speed", "track / heading", "vfr in imc",
    "wind shear", "fod", "hard landing",
    "storm", "arctic", "snowstorm", "cold weather", "hurricane",
    "solar pv", "oscillation", "load shed",
]

NARRATIVE_RISK_TERMS = {
    "TCAS RA / resolution advisory": ["tcas", "resolution advisory", "ra "],
    "Terrain / CFIT": ["terrain", "cfit", "mva", "msa"],
    "Loss of separation / NMAC": ["nmac", "near midair", "separation"],
    "Wake vortex": ["wake", "vortex"],
    "Bird strike": ["bird", "birds flock"],
    "Fire / smoke": ["fire", "smoke", "fumes", "odor"],
    "Fuel issue": ["fuel"],
    "Fatigue / workload": ["fatigue", "tired", "sleep", "workload", "overloaded"],
    "Weather hazard": ["wind shear", "gust", "icing", "thunderstorm", "microburst"],
    "Unstabilized approach": ["unstabilized", "unstable approach", "overshoot", "long landing"],
    "Medical / incapacitation": ["medical", "illness", "incapacitated", "unresponsive"],
    "Passenger misconduct": ["passenger", "unruly", "disruptive"],
}


class MLService:
    """Service class encapsulating all ML pipeline functionality."""
    
    def __init__(self):
        self._model = None
        self._vectorizer = None
        self._df = None
        self._index_vectors = None
        self._training_config = None
        self._metrics = None
        self._classification_report_df = None
    
    def load_artifacts(self) -> bool:
        """Load all model artifacts. Returns True if successful."""
        try:
            if not settings.DATASET_PATH.exists():
                logger.warning("Dataset not found at %s", settings.DATASET_PATH)
                return False
            if not settings.MODEL_PATH.exists() or not settings.VECTORIZER_PATH.exists():
                logger.warning("Model or vectorizer not found")
                return False
            
            logger.info("Loading dataset...")
            self._df = pd.read_csv(settings.DATASET_PATH)
            
            logger.info("Loading model and vectorizer...")
            self._model = joblib.load(settings.MODEL_PATH)
            self._vectorizer = joblib.load(settings.VECTORIZER_PATH)
            
            logger.info("Building RAG index...")
            self._index_vectors = self._build_index()
            
            # Load training config
            if settings.TRAIN_CONFIG_PATH.exists():
                with open(settings.TRAIN_CONFIG_PATH) as f:
                    self._training_config = json.load(f)
            
            # Load metrics
            if settings.METRICS_JSON.exists():
                with open(settings.METRICS_JSON) as f:
                    self._metrics = json.load(f)
            
            # Load classification report
            if settings.CLASSIFICATION_REPORT_CSV.exists():
                self._classification_report_df = pd.read_csv(
                    settings.CLASSIFICATION_REPORT_CSV, index_col=0
                )
            
            logger.info("All artifacts loaded successfully (%d reports)", len(self._df))
            return True
            
        except Exception as e:
            logger.error("Failed to load artifacts: %s", e)
            return False
    
    def _build_index(self) -> csr_matrix:
        """Build the RAG retrieval index."""
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        import re
        
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words("english"))
        
        def preprocess_text(text: str) -> str:
            if not isinstance(text, str):
                return ""
            text = text.lower()
            text = re.sub(r"[^a-z\s]", " ", text)
            tokens = word_tokenize(text)
            tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
            return " ".join(tokens)
        
        corpus = self._df[NARRATIVE_COL].apply(preprocess_text)
        return self._vectorizer.transform(corpus)
    
    def is_ready(self) -> bool:
        return all([
            self._model is not None,
            self._vectorizer is not None,
            self._df is not None,
            self._index_vectors is not None,
        ])
    
    def preprocess_text(self, text: str) -> str:
        """Preprocess text using NLTK."""
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        import re
        
        lemmatizer = WordNetLemmatizer()
        stop_words = set(stopwords.words("english"))
        
        if not isinstance(text, str):
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z\s]", " ", text)
        tokens = word_tokenize(text)
        tokens = [lemmatizer.lemmatize(t) for t in tokens if t not in stop_words and len(t) > 2]
        return " ".join(tokens)
    
    def classify_with_evidence(
        self, 
        narrative: str, 
        top_k: int = 3
    ) -> Tuple[str, List[EvidenceItem], float]:
        """Classify a narrative and retrieve evidence."""
        if not self.is_ready():
            raise RuntimeError("ML artifacts not loaded")
        
        start_time = time.perf_counter()
        
        # Preprocess and vectorize
        processed = self.preprocess_text(narrative)
        query_vec = self._vectorizer.transform([processed])
        
        # Predict
        predicted = str(self._model.predict(query_vec)[0])
        
        # Retrieve evidence
        n = self._index_vectors.shape[0]
        sims = np.zeros(n)
        
        for start in range(0, n, settings.RAG_BATCH):
            end = min(start + settings.RAG_BATCH, n)
            sims[start:end] = cosine_similarity(
                query_vec, self._index_vectors[start:end]
            ).flatten()
        
        top = sims.argsort()[-top_k:][::-1]
        
        evidence = []
        for rank, idx in enumerate(top, 1):
            row = self._df.iloc[int(idx)]
            narrative_text = str(row[NARRATIVE_COL])
            evidence.append(EvidenceItem(
                rank=rank,
                similarity=float(sims[idx]),
                label=str(row[LABEL_COL]),
                domain=str(row[DOMAIN_COL]) if DOMAIN_COL in self._df.columns else "",
                snippet=narrative_text[:settings.RAG_EVIDENCE_SNIPPET] + 
                       ("..." if len(narrative_text) > settings.RAG_EVIDENCE_SNIPPET else "")
            ))
        
        processing_time = (time.perf_counter() - start_time) * 1000
        return predicted, evidence, processing_time
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """Get dataset statistics."""
        if self._df is None:
            return {}
        
        dom_counts = {}
        if DOMAIN_COL in self._df.columns:
            dom_counts = self._df[DOMAIN_COL].value_counts().to_dict()
        
        class_dist = self._df[LABEL_COL].value_counts().head(20).to_dict()
        
        return {
            "total_reports": int(len(self._df)),
            "domains": dom_counts,
            "anomaly_classes": int(self._df[LABEL_COL].nunique()),
            "class_distribution": class_dist,
        }
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics."""
        if self._metrics is None or self._classification_report_df is None:
            return {}
        
        # Convert classification report to list of dicts
        report_rows = []
        for idx, row in self._classification_report_df.iterrows():
            if idx not in ["accuracy", "macro avg", "weighted avg"]:
                report_rows.append({
                    "class_name": str(idx),
                    "precision": float(row.get("precision", 0)),
                    "recall": float(row.get("recall", 0)),
                    "f1_score": float(row.get("f1-score", 0)),
                    "support": int(row.get("support", 0)),
                })
        
        return {
            "metrics": {
                "accuracy": self._metrics.get("accuracy", 0),
                "n_classes": self._metrics.get("n_classes", 0),
                "test_size": self._metrics.get("test_size", 0),
                "best_cv_f1": self._training_config.get("best_cv_f1_weighted") if self._training_config else None,
                "training_config": self._training_config,
            },
            "classification_report": report_rows,
            "confusion_matrix_url": "/api/plots/confusion_matrix.png" if (settings.PLOTS_DIR / "confusion_matrix.png").exists() else None,
            "class_distribution_url": "/api/plots/class_distribution.png" if (settings.PLOTS_DIR / "class_distribution.png").exists() else None,
        }
    
    def analyze_data(self, query: str) -> List[str]:
        """Run data analysis queries (keyless analyst)."""
        if self._df is None:
            return ["Dataset not loaded"]
        
        q = query.lower().strip()
        if not q:
            return ["Type a question about the data, e.g. 'safety', 'quality', 'classes', or 'analyze <narrative>'."]
        
        def _risk_level(label: str) -> str:
            low = label.lower()
            if any(k in low for k in CRITICAL_KEYWORDS):
                return "critical"
            if any(k in low for k in HIGH_KEYWORDS):
                return "high"
            return "medium"
        
        def quality_report() -> List[str]:
            total = len(self._df)
            narrative = self._df[NARRATIVE_COL].astype(str)
            dist = self._df[LABEL_COL].value_counts()
            
            missing = int(self._df[LABEL_COL].isna().sum())
            dups = int(narrative.duplicated().sum())
            short = int((narrative.str.len() < 20).sum())
            ratio = dist.iloc[0] / max(1, dist.iloc[-1])
            other = int(dist.get("Other", 0)) if "Other" in dist.index else 0
            
            return [
                "DATA QUALITY AUDIT",
                f"  [OK]   Rows: {total}  |  Columns: {list(self._df.columns)}",
                f"  [OK]   Missing labels: {missing}",
                f"  [WARN] Duplicate narratives (possible re-reports): {dups}",
                f"  [WARN] Very short narratives (<20 chars, low signal): {short}",
                f"  [INFO] Narrative length  min={narrative.str.len().min()}  avg={narrative.str.len().mean():.0f}  max={narrative.str.len().max()}",
                f"  [WARN] Imbalanced classes: '{dist.index[0]}' has {dist.iloc[0]} rows vs '{dist.index[-1]}' with {dist.iloc[-1]} ({ratio:.0f}x) - model is biased.",
                f"  [INFO] 'Other' bucket covers {other / total:.1%} of reports (rare categories merged under one label).",
            ]
        
        def safety_report() -> List[str]:
            levels = self._df[LABEL_COL].apply(_risk_level)
            total = len(self._df)
            counts = {lv: int((levels == lv).sum()) for lv in ("critical", "high", "medium")}
            
            lines = ["SAFETY-CRITICALITY BREAKDOWN (by anomaly category)"]
            if DOMAIN_COL in self._df.columns:
                dom = self._df[DOMAIN_COL].value_counts()
                lines.append("  " + "  ".join(f"{k.upper()}: {v}" for k, v in dom.items()))
            lines.append("")
            for lv in ("critical", "high", "medium"):
                lines.append(f"  {lv.upper():<8} {counts[lv]:>5} reports  {counts[lv] / total:5.1%}")
            top_critical = self._df[levels == "critical"][LABEL_COL].value_counts().head(5)
            lines.append("")
            lines.append("TOP SAFETY-CRITICAL CATEGORIES:")
            for label, n in top_critical.items():
                lines.append(f"  * {label}  ({n} reports)")
            return lines
        
        def class_distribution(top: int = 16) -> List[str]:
            dist = self._df[LABEL_COL].value_counts()
            lines = [f"ANOMALY CATEGORY DISTRIBUTION (top {top})"]
            for label, n in dist.head(top).items():
                lines.append(f"  {n:>4}  {label}  ({n / len(self._df):5.1%})")
            return lines
        
        def analyze_narrative(text: str) -> List[str]:
            low = text.lower()
            found = [risk for risk, terms in NARRATIVE_RISK_TERMS.items() if any(t in low for t in terms)]
            if not found:
                return ["No known high-risk phrases detected in this narrative.", ""]
            return ["RISK PHRASES DETECTED IN NARRATIVE:"] + [f"  * {r}" for r in found]
        
        if any(k in q for k in ("quality", "issue", "wrong", "problem", "bad", "clean")):
            return quality_report()
        if any(k in q for k in ("safety", "critical", "risk", "danger", "severe")):
            return safety_report()
        if any(k in q for k in ("class", "categor", "label", "balance", "distribut")):
            return class_distribution()
        if q.startswith("analyze"):
            text = query[len("analyze"):].strip() or "no text given"
            return analyze_narrative(text)
        
        return [
            "I can inspect the dataset for you. Try:",
            "  'summary' or 'classes'  - what is in the data",
            "  'quality' / 'issues'    - what is right and wrong with the data",
            "  'safety' / 'critical'   - safety-criticality breakdown",
            "  'analyze <text>'        - scan a report narrative for risk phrases",
        ]
    
    def get_alerts(self, limit: int = 50) -> Dict[str, Any]:
        """Get alerts from the alert log."""
        if not settings.ALERT_LOG_PATH.exists():
            return {"counts": {}, "alerts": [], "total": 0}
        
        try:
            alerts_df = pd.read_csv(settings.ALERT_LOG_PATH)
            if alerts_df.empty:
                return {"counts": {}, "alerts": [], "total": 0}
            
            alerts_df["timestamp"] = pd.to_datetime(alerts_df["timestamp"], errors="coerce")
            alerts_df = alerts_df.sort_values("timestamp", ascending=False)
            
            counts = alerts_df["risk_level"].value_counts().to_dict()
            
            recent = alerts_df.head(limit).copy()
            recent["evidence"] = recent["evidence_json"].apply(
                lambda s: json.loads(s) if isinstance(s, str) and s.strip() else []
            )
            recent = recent.drop(columns=["evidence_json"])
            
            alerts = []
            for _, row in recent.iterrows():
                alerts.append({
                    "timestamp": str(row["timestamp"]),
                    "incident_id": str(row["incident_id"]),
                    "source": str(row["source"]),
                    "risk_level": str(row["risk_level"]),
                    "predicted_label": str(row["predicted_label"]),
                    "narrative": str(row["narrative"]),
                    "evidence": [
                        EvidenceItem(
                            rank=ev.get("rank", 0),
                            similarity=ev.get("similarity", 0),
                            label=ev.get("label", ""),
                            domain=ev.get("domain", ""),
                            snippet=ev.get("snippet", "")
                        ) for ev in row["evidence"]
                    ]
                })
            
            return {"counts": counts, "alerts": alerts, "total": len(alerts_df)}
            
        except Exception as e:
            logger.error("Failed to load alerts: %s", e)
            return {"counts": {}, "alerts": [], "total": 0}


# Global service instance
ml_service = MLService()