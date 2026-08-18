"""Real-time incident monitoring & alerting service.

Turns the batch pipeline into a proactive decision-support system. It
continuously ingests new incident reports, classifies them on-the-fly with the
trained model, scores their risk level, retrieves RAG evidence from similar
past incidents and raises alerts (logged to ``data/alerts.csv`` and shown in
the React dashboard's Live Alerts page).

Four ingestion sources (all optional, all fault-tolerant):

  1. Drop-in folder   - any ``new_incidents/*.csv`` / ``*.txt`` file.
  2. Master dataset   - rows appended to ``data/real_safety_dataset.csv``.
  3. NTSB API         - public-domain US aviation accident feed (daily).
  4. UKPN Live Faults - near-real-time UK power-cut feed (unplanned only).

Run it standalone:

    python -m src.monitor                # continuous loop
    python -m src.monitor --once --no-api   # single scan (CI / demos)

or start it after a training run:

    python main.py --monitor --poll 30
"""
import argparse
import csv
import hashlib
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd

import config
from src import analyst, data_fetcher
from src.rag_explainer import build_index, explain_text

logger = logging.getLogger(__name__)

RISK_LEVELS = {"medium": 0, "high": 1, "critical": 2}

# De-duplication state is persisted here so a monitor restart never re-alerts
# on incidents that were already processed.
STATE_PATH = config.DATA_DIR / "monitor_state.json"

# Alert trigger phrases scanned in raw narrative text (beyond the model label).
# A match on these upgrades the alert level regardless of the prediction.
CRITICAL_TRIGGERS = [
    "loss of communication", "lost communication", "lost contact",
    "radio failure", "atc communication", "communication failure",
    "power outage", "power cut", "blackout", "grid collapse",
    "system emergency", "uncontrolled", "crash", "cfit", "terrain",
    "fire", "smoke", "explosion", "evacuation", "emergency", "mayday",
    "engine failure", "dual engine",
]
HIGH_TRIGGERS = [
    "altitude", "runway", "weather", "storm", "hurricane", "arctic", "icing",
    "turbulence", "wind shear", "engine", "hydraulic", "fuel",
    "bird strike", "decompression", "loss of power", "outage",
]


# ------------------------------------------------------------ risk scoring
def assess_risk(text: str, predicted_label: str) -> str:
    """Return 'critical' | 'high' | 'medium' from text triggers + label.

    Raw-text triggers take precedence (an explicit emergency keyword wins over
    what the classifier says), then the label's intrinsic criticality, then the
    narrative's high-risk vocabulary.
    """
    low = text.lower()
    if any(p in low for p in CRITICAL_TRIGGERS):
        return "critical"
    label_level = analyst._risk_level(predicted_label)
    if label_level in ("critical", "high"):
        return label_level
    if any(p in low for p in HIGH_TRIGGERS):
        return "high"
    return "medium"


# ---------------------------------------------------------- artifact loading
_ARTIFACTS = None


def _get_artifacts():
    """Lazily load (dataset, model, vectorizer, RAG index) and cache them."""
    global _ARTIFACTS
    if _ARTIFACTS is None:
        for path in (config.DATASET_PATH, config.MODEL_PATH,
                     config.VECTORIZER_PATH):
            if not path.exists():
                raise FileNotFoundError(
                    f"Monitor artifact missing: {path}\n"
                    "Run `python main.py` first to train the model, "
                    "then start the monitor.")
        logger.info("Loading monitor artifacts (dataset + model + RAG index) ...")
        df = data_fetcher.load_dataset(config.DATASET_PATH)
        model = joblib.load(config.MODEL_PATH)
        vectorizer = joblib.load(config.VECTORIZER_PATH)
        index_vectors = build_index(df, vectorizer)
        _ARTIFACTS = (df, model, vectorizer, index_vectors)
        logger.info("Monitor artifacts ready (%d-document evidence corpus).",
                    len(df))
    return _ARTIFACTS


# ------------------------------------------------------ incident processing
def process_new_incident(narrative: str, incident_id: str = None,
                         source: str = None, risk_floor: str = None) -> dict:
    """Classify a new report, score its risk and retrieve RAG evidence.

    Args:
        narrative: raw incident text.
        incident_id: stable identifier used for de-duplication.
        source: human-readable origin (e.g. "new_incidents/FOO.csv").
        risk_floor: optional minimum risk level ("high") when a source signals
            extra severity that keyword scanning cannot see (e.g. customer
            impact counts).

    Returns a dict ready for ``log_alert`` / dashboard display.
    """
    df, model, vectorizer, index_vectors = _get_artifacts()
    predicted, evidence = explain_text(
        narrative, model, vectorizer, df,
        index_vectors=index_vectors, top_k=config.RAG_TOP_K)

    risk = assess_risk(narrative, predicted)
    if risk_floor and RISK_LEVELS[risk] < RISK_LEVELS[risk_floor]:
        risk = risk_floor

    snippet = str(narrative).strip()
    if len(snippet) > config.MONITOR_ALERT_SNIPPET:
        snippet = snippet[:config.MONITOR_ALERT_SNIPPET] + "..."

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "incident_id": incident_id or "manual",
        "source": source or "manual",
        "narrative": snippet,
        "predicted_label": predicted,
        "risk_level": risk,
        "is_alert": risk in ("critical", "high"),
        "evidence": evidence,
    }


def log_alert(result: dict) -> None:
    """Append one alert row (evidence as JSON) to ``data/alerts.csv``."""
    path = Path(config.ALERT_LOG_PATH)
    row = {
        "timestamp": result["timestamp"],
        "incident_id": result["incident_id"],
        "source": result["source"],
        "risk_level": result["risk_level"],
        "predicted_label": result["predicted_label"],
        "narrative": result["narrative"],
        "evidence_json": json.dumps(result["evidence"], ensure_ascii=False),
    }
    pd.DataFrame([row]).to_csv(path, mode="a", header=not path.exists(),
                               index=False)


def _process_and_alert(narrative: str, incident_id: str, state: dict,
                       source: str = None, risk_floor: str = None) -> int:
    """Classify + log an incident unless its key was already handled."""
    key = incident_id or hashlib.sha1(
        narrative.encode("utf-8")).hexdigest()[:16]
    if key in state["seen"]:
        return 0
    state["seen"].add(key)
    try:
        result = process_new_incident(narrative, incident_id=incident_id,
                                      source=source, risk_floor=risk_floor)
    except Exception as exc:  # one bad incident must not stop the monitor
        logger.warning("Could not process incident %s: %s: %s",
                       incident_id, type(exc).__name__, exc)
        return 0
    if result["is_alert"]:
        log_alert(result)
        logger.warning("ALERT [%s] %s -> %s", result["risk_level"].upper(),
                       incident_id, result["predicted_label"])
    else:
        logger.info("No alert for %s (%s - %s).", incident_id,
                    result["predicted_label"], result["risk_level"])
    return 1


# ------------------------------------------------------- source: drop folder
def _iter_incidents(path: Path):
    """Yield (narrative, incident_id) pairs from a CSV or TXT file.

    CSV parsing is forgiving: it uses the stdlib csv module and joins trailing
    fields back into the narrative, so hand-written files with unquoted commas
    (e.g. ``DEMO-001,Engine fire at FL350, declared emergency.``) still parse
    correctly instead of being silently misaligned.
    """
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8", errors="replace", newline="") as fh:
            reader = csv.reader(fh)
            header = [h.strip().lower() for h in next(reader, [])]
            if not header:
                return
            narr_idx = next((i for i, h in enumerate(header)
                             if h in ("narrative", "text", "report")), 0)
            id_idx = next((i for i, h in enumerate(header) if h == "id"), None)
            for i, row in enumerate(reader, 1):
                if not any(v.strip() for v in row):
                    continue
                incident_id = f"{path.stem}-row{i}"
                if id_idx is not None and len(row) > id_idx:
                    incident_id = row[id_idx].strip() or incident_id
                # narrative runs from its column to the end of the row, which
                # reassembles unquoted commas inside the text.
                parts = [p.strip() for p in row[narr_idx:] if p.strip()]
                narrative = " ".join(parts)
                if not narrative or narrative.lower() in ("nan", "none"):
                    continue
                yield narrative, incident_id
    else:  # .txt - one whole report per file
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if text:
            yield text, path.name


def _scan_watch_dir(watch_dir: Path, state: dict) -> int:
    """Process every new/changed file in the drop-in folder."""
    count = 0
    for path in sorted(watch_dir.iterdir()):
        name_lower = path.name.lower()
        if path.suffix.lower() not in (".csv", ".txt"):
            continue
        if name_lower.startswith(("readme", ".")):
            continue  # documentation / hidden files are not incidents
        try:
            stat = path.stat()
        except OSError:
            continue
        stamp = (path.name, stat.st_size, int(stat.st_mtime))
        if state["seen_files"].get(path.name) == stamp:
            continue
        state["seen_files"][path.name] = stamp
        try:
            for narrative, incident_id in _iter_incidents(path):
                count += _process_and_alert(
                    narrative, incident_id, state, source=f"watch/{path.name}")
        except Exception as exc:
            logger.warning("Could not parse %s: %s: %s",
                           path.name, type(exc).__name__, exc)
    return count


# --------------------------------------------------- source: master dataset
def _scan_master_dataset(state: dict) -> int:
    """Process rows appended to the master dataset (baseline on first scan)."""
    if not config.DATASET_PATH.exists():
        return 0
    try:
        df = data_fetcher.load_dataset(config.DATASET_PATH)
    except Exception as exc:
        logger.warning("Could not read master dataset: %s: %s",
                       type(exc).__name__, exc)
        return 0
    current = len(df)
    if state["master_rows"] is None:
        state["master_rows"] = current  # baseline - only NEW rows alert
        return 0
    count = 0
    for i in range(state["master_rows"], current):
        narrative = str(df.iloc[i][config.NARRATIVE_COL])
        if not narrative.strip():
            continue
        count += _process_and_alert(narrative, f"ds-row-{i}", state,
                                    source="dataset", risk_floor=None)
    state["master_rows"] = current
    return count


# ------------------------------------------------------- source: NTSB API
def _ntsb_narrative(rec: dict) -> str | None:
    """Build an aviation narrative from a NTSB record (None if no cause)."""
    cause = (rec.get("probable_cause") or "").strip()
    if not cause:
        return None
    acft = " ".join(x for x in (rec.get("acft_make"), rec.get("acft_model"))
                    if x)
    loc = ", ".join(x for x in (rec.get("ev_city"), rec.get("ev_state"),
                                rec.get("ev_country")) if x)
    parts = []
    if rec.get("ev_date"):
        parts.append(f"On {rec['ev_date']}")
    if acft:
        parts.append(f"a {acft}")
    if loc:
        parts.append(f"at {loc}")
    if rec.get("ev_highest_injury"):
        parts.append(f"({rec['ev_highest_injury']} injury outcome)")
    prefix = " ".join(parts)
    return f"{prefix}: {cause}" if prefix else cause


def _poll_ntsb(state: dict) -> int:
    """Poll the NTSB recent-accidents feed for new probable-cause reports."""
    url = config.NTSB_API_URL
    try:
        resp = data_fetcher._http_get(url, timeout=30)
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except Exception as exc:
        logger.warning("NTSB poll failed: %s: %s", type(exc).__name__, exc)
        return 0
    count = 0
    for rec in items:
        narrative = _ntsb_narrative(rec)
        ev_id = str(rec.get("ev_id") or "")
        if not narrative or not ev_id:
            continue
        count += _process_and_alert(narrative, f"ntsb-{ev_id}", state,
                                    source="NTSB API")
    if count:
        logger.info("NTSB poll: %d new aviation report(s).", count)
    return count


# ---------------------------------------------------- source: UKPN API
def _ukpn_narrative(fields: dict) -> str:
    """Build a power-cut narrative from a UKPN live-fault record."""
    parts = []
    message = (fields.get("mainmessage") or "").strip()
    category = (fields.get("incidentcategorycustomerfriendlydescription")
                or "").strip()
    parts.append(message or category or "Unplanned power cut")
    zone = (fields.get("operatingzone") or "").strip()
    if zone:
        parts.append(f"Affecting the {zone} operating zone")
    postcodes = (fields.get("postcodesaffected") or "").strip()
    if postcodes:
        parts.append(f"postcodes {postcodes}")
    customers = fields.get("nocustomeraffected") or 0
    if int(customers) > 0:
        parts.append(f"{int(customers)} customers affected")
    return ". ".join(p.strip().rstrip(".") for p in parts if p) + "."


def _poll_ukpn(state: dict) -> int:
    """Poll the UKPN live-faults feed for new UNPLANNED power cuts."""
    url = config.UKPN_API_URL + "?limit=50"
    try:
        resp = data_fetcher._http_get(url, timeout=30)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as exc:
        logger.warning("UKPN poll failed: %s: %s", type(exc).__name__, exc)
        return 0
    count = 0
    for item in results:
        rec = item.get("record", item)
        fields = rec.get("fields", rec)
        if str(fields.get("powercuttype") or "").lower() != "unplanned":
            continue  # scheduled / already-restored work is not an incident
        ref = str(fields.get("incidentreference") or "")
        narrative = _ukpn_narrative(fields)
        if not narrative or not ref:
            continue
        customers = int(fields.get("nocustomeraffected") or 0)
        risk_floor = ("high" if customers >= config.ALERT_HIGH_MIN_CUSTOMERS
                      else None)
        count += _process_and_alert(narrative, f"ukpn-{ref}", state,
                                    source="UKPN Live Faults",
                                    risk_floor=risk_floor)
    if count:
        logger.info("UKPN poll: %d new power-cut report(s).", count)
    return count


# ------------------------------------------------------------ state storage
def _load_state() -> dict:
    """Restore de-duplication state from disk (empty dict if none yet)."""
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            return {
                "seen_files": {k: tuple(v)
                               for k, v in data.get("seen_files", {}).items()},
                "seen": set(data.get("seen", [])),
                "master_rows": data.get("master_rows"),
                "last_poll": data.get("last_poll", {"ntsb": 0.0, "ukpn": 0.0}),
            }
        except Exception as exc:
            logger.warning("Could not load monitor state: %s", exc)
    return {"seen_files": {}, "seen": set(), "master_rows": None,
            "last_poll": {"ntsb": 0.0, "ukpn": 0.0}}


def _save_state(state: dict) -> None:
    """Persist de-duplication state so restarts do not re-alert."""
    try:
        STATE_PATH.write_text(json.dumps({
            "seen_files": {k: list(v) for k, v in state["seen_files"].items()},
            "seen": sorted(state["seen"]),
            "master_rows": state["master_rows"],
            "last_poll": state["last_poll"],
        }, indent=2), encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not save monitor state: %s", exc)


# ------------------------------------------------------------------ main loop
def scan_and_alert(watch_dir: Path = None, poll_seconds: int = None,
                   once: bool = False, enable_api: bool = True) -> int:
    """Continuously ingest new incidents and raise alerts.

    Args:
        watch_dir: folder scanned for dropped CSV/TXT files.
        poll_seconds: delay between scans.
        once: scan a single pass and return the number of new incidents.
        enable_api: poll the NTSB / UKPN live feeds.
    """
    watch_dir = Path(watch_dir) if watch_dir else config.WATCH_DIR
    if poll_seconds is None:
        poll_seconds = config.MONITOR_POLL_SECONDS
    watch_dir.mkdir(parents=True, exist_ok=True)

    state = _load_state()

    logger.info("Incident monitor started - watching %s (poll %ds).",
                watch_dir, poll_seconds)
    logger.info("  drop CSV/TXT reports into %s or append rows to %s.",
                watch_dir.name, config.DATASET_PATH.name)
    if enable_api:
        logger.info("  live feeds: NTSB aviation every %ds, UKPN faults every %ds.",
                    config.NTSB_POLL_SECONDS, config.UKPN_POLL_SECONDS)

    while True:
        total = _scan_watch_dir(watch_dir, state)
        total += _scan_master_dataset(state)

        if enable_api:
            now = time.time()
            if now - state["last_poll"]["ntsb"] >= config.NTSB_POLL_SECONDS:
                _poll_ntsb(state)
                state["last_poll"]["ntsb"] = now
            if now - state["last_poll"]["ukpn"] >= config.UKPN_POLL_SECONDS:
                _poll_ukpn(state)
                state["last_poll"]["ukpn"] = now

        _save_state(state)
        if total:
            logger.info("Scan completed: processed %d new incident(s).", total)
        if once:
            return total
        time.sleep(poll_seconds)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Real-time incident monitoring & alerting service.")
    parser.add_argument("--watch-dir", default=None,
                        help="folder to watch (default: new_incidents/)")
    parser.add_argument("--delay", type=int, default=None,
                        help="poll interval in seconds")
    parser.add_argument("--once", action="store_true",
                        help="scan a single pass and exit")
    parser.add_argument("--no-api", action="store_true",
                        help="disable the NTSB / UKPN live feeds")
    args = parser.parse_args()
    try:
        scan_and_alert(watch_dir=args.watch_dir, poll_seconds=args.delay,
                       once=args.once, enable_api=not args.no_api)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
    return 0


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)-8s | %(message)s")
    sys.exit(main())
