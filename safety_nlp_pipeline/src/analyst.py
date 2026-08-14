"""NLP Data Analyst - a keyless assistant that inspects the loaded dataset.

Answers questions about the data: what is right/wrong with it, class balance,
and which anomaly categories are safety-critical. Everything is computed from
the actual dataset with pandas - no LLM, no API key.

Query words:
  quality | issues   -> data-quality audit
  safety  | critical -> safety-criticality breakdown
  classes | balance  -> class distribution
  analyze <text>     -> scan a report narrative for high-risk phrases
"""
import re

import pandas as pd

from config import DOMAIN_COL, LABEL_COL, NARRATIVE_COL

# Safety-criticality mapping for anomaly categories (substring match).
CRITICAL_KEYWORDS = [
    "cfit", "nmac", "loss of aircraft control", "wake vortex",
    "unstabilized approach", "smoke / fire", "engine", "fuel",
    "near midair", "midair", "terrain",
    # power-grid system-level collapses / interruptions
    "blackout", "outage", "disturbance", "system emergency",
]
HIGH_KEYWORDS = [
    "altitude excursion", "altitude overshoot", "altitude undershoot",
    "runway", "incursion", "excursion", "bird / animal", "object",
    "weather / turbulence", "speed", "track / heading", "vfr in imc",
    "wind shear", "fod", "hard landing",
    # power-grid weather/event driven events
    "storm", "arctic", "snowstorm", "cold weather", "hurricane",
    "solar pv", "oscillation", "load shed",
]
# Risk phrases scanned inside raw narrative text.
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
    "Unstabilized approach": ["unstabilized", "unstable approach", "overshoot",
                              "long landing"],
    "Medical / incapacitation": ["medical", "illness", "incapacitated",
                                 "unresponsive"],
    "Passenger misconduct": ["passenger", "unruly", "disruptive"],
}
LEVEL_KEYWORDS = {"critical": CRITICAL_KEYWORDS, "high": HIGH_KEYWORDS}


def _risk_level(label: str) -> str:
    low = label.lower()
    if any(k in low for k in CRITICAL_KEYWORDS):
        return "critical"
    if any(k in low for k in HIGH_KEYWORDS):
        return "high"
    return "medium"


def _risk_counts(df: pd.DataFrame) -> dict[str, int]:
    levels = df[LABEL_COL].apply(_risk_level)
    return {lv: int((levels == lv).sum()) for lv in ("critical", "high", "medium")}


def quality_report(df: pd.DataFrame) -> list[str]:
    """Data-quality audit: what is right and what is wrong with the data."""
    total = len(df)
    narrative = df[NARRATIVE_COL].astype(str)
    dist = df[LABEL_COL].value_counts()

    missing = int(df[LABEL_COL].isna().sum())
    dups = int(narrative.duplicated().sum())
    short = int((narrative.str.len() < 20).sum())
    ratio = dist.iloc[0] / max(1, dist.iloc[-1])
    other = int(dist.get("Other", 0)) if "Other" in dist.index else 0
    vocab = set()
    for text in narrative.head(200):
        vocab.update(re.split(r"\s+", text.lower()))

    lines = [
        "DATA QUALITY AUDIT",
        f"  [OK]   Rows: {total}  |  Columns: {list(df.columns)}",
        f"  [OK]   Missing labels: {missing}",
        f"  [WARN] Duplicate narratives (possible re-reports): {dups}",
        f"  [WARN] Very short narratives (<20 chars, low signal): {short}",
        f"  [INFO] Narrative length  min={narrative.str.len().min()}  "
        f"avg={narrative.str.len().mean():.0f}  "
        f"max={narrative.str.len().max()}",
        f"  [WARN] Imbalanced classes: '{dist.index[0]}' has {dist.iloc[0]} "
        f"rows vs '{dist.index[-1]}' with {dist.iloc[-1]} ({ratio:.0f}x) - "
        f"model is biased.",
        f"  [INFO] 'Other' bucket covers {other / total:.1%} of reports "
        f"(rare categories merged under one label).",
        f"  [INFO] Unique words across first 200 narratives: {len(vocab)}",
    ]
    return lines


def safety_report(df: pd.DataFrame) -> list[str]:
    """Share of each risk level + the most critical frequent categories."""
    levels = df[LABEL_COL].apply(_risk_level)
    total = len(df)
    counts = _risk_counts(df)

    lines = ["SAFETY-CRITICALITY BREAKDOWN (by anomaly category)"]
    if DOMAIN_COL in df.columns:
        dom = df[DOMAIN_COL].value_counts()
        lines.append("  " + "  ".join(f"{k.upper()}: {v}" for k, v in dom.items()))
    lines.append("")
    for lv in ("critical", "high", "medium"):
        lines.append(f"  {lv.upper():<8} {counts[lv]:>5} reports  "
                     f"{counts[lv] / total:5.1%}")
    top_critical = df[levels == "critical"][LABEL_COL].value_counts().head(5)
    lines.append("")
    lines.append("TOP SAFETY-CRITICAL CATEGORIES:")
    for label, n in top_critical.items():
        lines.append(f"  * {label}  ({n} reports)")
    return lines


def class_distribution(df: pd.DataFrame, top: int = 16) -> list[str]:
    dist = df[LABEL_COL].value_counts()
    lines = ["ANOMALY CATEGORY DISTRIBUTION (top %d)" % top]
    for label, n in dist.head(top).items():
        lines.append(f"  {n:>4}  {label}  ({n / len(df):5.1%})")
    return lines


def analyze_narrative(text: str) -> list[str]:
    """Scan a raw narrative for safety-risk phrases."""
    low = text.lower()
    return [risk for risk, terms in NARRATIVE_RISK_TERMS.items()
            if any(t in low for t in terms)]


def answer(query: str, df: pd.DataFrame) -> list[str]:
    """Route a free-form question to the right analysis. Returns lines."""
    q = query.lower().strip()
    if not q:
        return ["Type a question about the data, e.g. 'safety', 'quality', "
                "'classes', or 'analyze <narrative>'."]
    if any(k in q for k in ("quality", "issue", "wrong", "problem", "bad", "clean")):
        return quality_report(df)
    if any(k in q for k in ("safety", "critical", "risk", "danger", "severe")):
        return safety_report(df)
    if any(k in q for k in ("class", "categor", "label", "balance", "distribut")):
        return class_distribution(df)
    if q.startswith("analyze"):
        text = query[len("analyze"):].strip() or "no text given"
        found = analyze_narrative(text)
        if not found:
            return ["No known high-risk phrases detected in this narrative.", ""]
        return ["RISK PHRASES DETECTED IN NARRATIVE:"] + [f"  * {r}" for r in found]
    return [
        "I can inspect the dataset for you. Try:",
        "  'summary' or 'classes'  - what is in the data",
        "  'quality' / 'issues'    - what is right and wrong with the data",
        "  'safety' / 'critical'   - safety-criticality breakdown",
        "  'analyze <text>'        - scan a report narrative for risk phrases",
    ]


def summary(df: pd.DataFrame) -> list[str]:
    return ([
        f"DATASET: {len(df)} reports, {df.shape[1]} columns.",
        f"Classes: {df[LABEL_COL].nunique()} anomaly categories.",
    ] + quality_report(df))
