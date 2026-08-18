"""NLP safety-suggestion engine for live alerts.

Generates a concise, actionable safety suggestion for every alert record by
combining the model's predicted category, the risk level and risk phrases
detected in the raw narrative (keyword extraction over the analyst lexicon).
No LLM required - deterministic, fast, and always available.
"""
from typing import Dict, List

# Risk phrases scanned in narrative text (shared lexicon with analyst.py)
RISK_TERMS: Dict[str, List[str]] = {
    "TCAS RA / resolution advisory": ["tcas", "resolution advisory", "ra "],
    "Terrain / CFIT": ["terrain", "cfit", "mva", "msa"],
    "Loss of separation / NMAC": ["nmac", "near midair", "separation"],
    "Wake vortex": ["wake", "vortex"],
    "Bird strike": ["bird", "birds flock"],
    "Fire / smoke": ["fire", "smoke", "fumes", "odor", "explosion"],
    "Fuel issue": ["fuel", "low fuel", "fuel leak"],
    "Fatigue / workload": ["fatigue", "tired", "sleep", "workload", "overloaded"],
    "Weather hazard": ["wind shear", "gust", "icing", "thunderstorm", "microburst"],
    "Unstabilized approach": ["unstabilized", "unstable approach", "overshoot", "long landing"],
    "Medical / incapacitation": ["medical", "illness", "incapacitated", "unresponsive"],
    "Passenger misconduct": ["passenger", "unruly", "disruptive"],
    "Engine failure": ["engine failure", "engine shut", "engine out", "flameout", "loss of power"],
    "Communication failure": ["communication", "radio failure", "static", "frequency"],
    "Emergency / diversion": ["emergency", "divert", "mayday", "declared"],
    "Power outage / blackout": ["power cut", "power outage", "blackout", "outage", "customers"],
    "Grid disturbance": ["disturbance", "oscillation", "cascading", "frequency", "load shed"],
    "Severe weather (grid)": ["storm", "hurricane", "arctic", "snowstorm", "cold weather", "wind"],
    "Underground cable fault": ["cable", "underground", "substation"],
}

# Label keywords that add specific recommendations
LABEL_ACTIONS: Dict[str, List[str]] = {
    "engine": ["Schedule engine borescope inspection", "Review engine FADEC/ECAM logs", "Verify fuel management procedures"],
    "fuel": ["Audit fuel planning and crossfeed procedures", "Re-train fuel-system emergency drills"],
    "bird": ["Review bird-strike reporting and runway wildlife management", "Log strike details for wildlife hazard database"],
    "fire": ["Rehearse fire/smoke checklists and crew coordination", "Inspect fire-suppression and detection systems"],
    "weather": ["Brief weather radar and wind-shear escape maneuvers", "Enforce go/no-go weather minima"],
    "turbulence": ["Reinforce seatbelt discipline and turbulence forecasts"],
    "runway": ["Re-train stabilized-approach and go-around policy", "Audit runway incursion hot spots"],
    "altitude": ["Review altitude-constrained procedures and MSA charts", "Re-train task prioritisation during high workload"],
    "terrain": ["Rehearse terrain-avoidance callouts and GPWS response"],
    "tcas": ["Debrief TCAS RA handling and ATC coordination"],
    "blackout": ["Harden transmission protection schemes", "Drill system-restoration and blackstart procedures"],
    "outage": ["Strengthen redundancy for critical feeders", "Validate load-shedding priorities"],
    "disturbance": ["Review oscillation damping controls and PSS tuning", "Post-event controller training"],
    "storm": ["Pre-storm infrastructure walkdowns", "Update severe-weather outage playbooks"],
    "hurricane": ["Harden poles/lines in storm-prone corridors", "Pre-position repair crews"],
    "arctic": ["Winterise equipment and rehearse cold-weather contingencies"],
    "cable": ["Prioritise cable fault investigation", "Schedule joint integrity surveys"],
    "solar": ["Review inverter ride-through settings", "Update distributed-resource interconnection studies"],
    "load shed": ["Validate UFLS scheme settings", "Rehearse manual load-shed implementation"],
}

RISK_SUGGESTIONS = {
    "critical": (
        "IMMEDIATE ACTION: treat as highest priority. Convene an emergency "
        "safety review, notify all stakeholders, preserve evidence, and "
        "prevent recurrence before operations resume."
    ),
    "high": (
        "PRIORITY ACTION: schedule a detailed investigation within 24 hours. "
        "Review procedures, train affected personnel and implement mitigations "
        "before normal operations continue."
    ),
    "medium": (
        "FOLLOW-UP: log for trending. Add to the safety review backlog and "
        "monitor for repeated occurrences; brief crews/operators in the next "
        "shift change."
    ),
    "low": (
        "MONITOR: low immediate risk. Keep on record, feed into periodic "
        "safety trends and re-evaluate if similar incidents recur."
    ),
}

LEVEL_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _detected_phrases(narrative: str, label: str) -> List[str]:
    low = narrative.lower()
    found = [risk for risk, terms in RISK_TERMS.items() if any(t in low for t in terms)]
    label_low = label.lower()
    for risk, terms in RISK_TERMS.items():
        if risk not in found and any(t in label_low for t in terms):
            found.append(risk)
    return found


def _label_actions(label: str) -> List[str]:
    low = label.lower()
    return [action for key, actions in LABEL_ACTIONS.items() if key in low for action in actions]


def generate_suggestion(narrative: str, predicted_label: str,
                        risk_level: str) -> str:
    """Build a safety suggestion for one alert record."""
    risk_level = str(risk_level or "medium").lower()
    base = RISK_SUGGESTIONS.get(risk_level, RISK_SUGGESTIONS["medium"])

    phrases = _detected_phrases(narrative or "", predicted_label or "")
    actions = _label_actions(predicted_label or "")

    parts = [base]
    if actions:
        unique = list(dict.fromkeys(actions))[:3]
        parts.append("Recommended actions: " + "; ".join(unique) + ".")
    if phrases:
        parts.append("Risk factors detected: " + ", ".join(phrases) + ".")
    return " ".join(parts)


def build_alerts_summary(alerts: List[dict], total: int) -> str:
    """Short NLP digest of the current alert feed for the LLM context."""
    if not alerts:
        return ""
    lines = [f"Live alert feed: {total} total alerts logged."]
    by_level: Dict[str, int] = {}
    for a in alerts:
        by_level[a.get("risk_level", "medium")] = by_level.get(a.get("risk_level", "medium"), 0) + 1
    lines.append("Current breakdown: " + ", ".join(f"{lv}={n}" for lv, n in sorted(by_level.items(), key=lambda kv: LEVEL_ORDER.get(kv[0], 9))))
    return "\n".join(lines)
