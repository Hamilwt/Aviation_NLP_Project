"""NLP Data Analyst — a keyless assistant that inspects the ASRS dataset.

Answers questions about the data: what is right/wrong with it, class
balance, and which anomaly categories are safety-critical. Everything is
computed from the actual dataset with pandas — no LLM, no API key.

Use it from the TUI assistant tab with commands like:
  summary | safety | critical | quality | issues | classes | balance
  analyze <paste a report narrative>
"""
import re

import pandas as pd

# Safety-criticality mapping for anomaly categories (substring match).
CRITICAL_KEYWORDS = [
    "cfit", "nmac", "loss of aircraft control", "wake vortex",
    "unstabilized approach", "smoke / fire", "engine", "fuel",
    "near midair", "midair", "terrain",
]
HIGH_KEYWORDS = [
    "altitude excursion", "altitude overshoot", "altitude undershoot",
    "runway", "incursion", "excursion", "bird / animal", "object",
    "weather / turbulence", "speed", "track / heading", "vfr in imc",
    "wind shear", "fod", "hard landing",
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
    "Unstabilized approach": ["unstabilized", "unstable approach", "overshoot", "long landing"],
    "Medical / incapacitation": ["medical", "illness", "incapacitated", "unresponsive"],
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


def safety_report(df: pd.DataFrame) -> list:
    """Share of each risk level + the most critical frequent categories."""
    levels = df["human_factors_groundtruth"].apply(_risk_level)
    total = len(df)
    counts = {lv: int((levels == lv).sum()) for lv in ("critical", "high", "medium")}
    lines = ["SAFETY-CRITICALITY BREAKDOWN (by anomaly category)"]
    for lv, pct in [("critical", 5), ("high", 3), ("medium", 1)]:
        lines.append(f"  {lv.upper():<8} {counts[lv]:>5} reports  {counts[lv] / total:5.1%}")
    top_critical = (
        df[levels == "critical"]["human_factors_groundtruth"]
        .value_counts().head(5)
    )
    lines.append("")
    lines.append("TOP SAFETY-CRITICAL CATEGORIES:")
    for label, n in top_critical.items():
        lines.append(f"  * {label}  ({n} reports)")
    return lines


def quality_report(df: pd.DataFrame) -> list:
    """Data-quality audit: what is right and what is wrong with the data."""
    lines = ["DATA QUALITY AUDIT"]
    total = len(df)
    narrative = df["Narrative"].astype(str)

    missing = int(df["human_factors_groundtruth"].isna().sum())
    lines.append(f"  [OK]   Rows: {total}  |  Columns: {list(df.columns)}")
    lines.append(f"  [OK]   Missing labels: {missing}")
    dup = int(narrative.duplicated().sum())
    lines.append(f"  [WARN] Duplicate narratives (possible re-reports): {dup}")
    lengths = narrative.str.len()
    short = int((lengths < 20).sum())
    lines.append(f"  [WARN] Very short narratives (<20 chars, low signal): {short}")
    lines.append(f"  [INFO] Narrative length  min={lengths.min()}  avg={lengths.mean():.0f}  max={lengths.max()}")

    dist = df["human_factors_groundtruth"].value_counts()
    majority, minority = dist.iloc[0], dist.iloc[-1]
    ratio = majority / max(1, minority)
    lines.append(
        f"  [WARN] Imbalanced classes: '{dist.index[0]}' has {majority} rows "
        f"vs '{dist.index[-1]}' with {minority} ({ratio:.0f}x) — model is biased."
    )
    other_share = dist.get("Other", 0) / total
    lines.append(
        f"  [INFO] 'Other' bucket covers {other_share:.1%} of reports "
        f"(rare categories merged under one label)."
    )
    vocab = set()
    for text in narrative.head(200):
        vocab.update(re.split(r"\s+", text.lower()))
    lines.append(f"  [INFO] Unique words across first 200 narratives: {len(vocab)}")
    return lines


def analyze_narrative(text: str) -> list:
    """Scan a raw narrative for safety-risk phrases."""
    low = text.lower()
    found = []
    for risk, terms in NARRATIVE_RISK_TERMS.items():
        if any(t in low for t in terms):
            found.append(risk)
    return found


def answer(query: str, df: pd.DataFrame) -> list:
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
        dist = df["human_factors_groundtruth"].value_counts()
        lines = ["ANOMALY CATEGORY DISTRIBUTION (top 16)"]
        for label, n in dist.head(16).items():
            lines.append(f"  {n:>4}  {label}  ({n / len(df):5.1%})")
        return lines
    if q.startswith("analyze"):
        text = query[len("analyze"):].strip() or "no text given"
        found = analyze_narrative(text)
        if not found:
            return ["No known high-risk phrases detected in this narrative.", ""]
        lines = ["RISK PHRASES DETECTED IN NARRATIVE:"]
        for r in found:
            lines.append(f"  * {r}")
        return lines
    return [
        "I can inspect the dataset for you. Try:",
        "  'summary' or 'classes'  — what is in the data",
        "  'quality' / 'issues'    — what is right and wrong with the data",
        "  'safety' / 'critical'   — safety-criticality breakdown",
        "  'analyze <text>'        — scan a report narrative for risk phrases",
    ]


def summary(df: pd.DataFrame) -> list:
    return [
        f"DATASET: {len(df)} ASRS reports, {df.shape[1]} columns.",
        f"Classes: {df['human_factors_groundtruth'].nunique()} anomaly categories."
    ] + quality_report(df)