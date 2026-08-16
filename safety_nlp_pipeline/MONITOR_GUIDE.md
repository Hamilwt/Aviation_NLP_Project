# Real-Time Incident Monitoring & Alerting Guide

## Overview

The **monitor** (`src/monitor.py`) turns the batch pipeline into a **proactive decision-support service**. It continuously ingests new incident reports, classifies them on-the-fly with the trained model, scores their risk level (**critical / high / medium**), retrieves RAG evidence from similar past incidents, and raises alerts — all without human intervention.

Alerts are written to `data/alerts.csv` and displayed live in the Streamlit **���� Live Alerts** tab with color-coded rows and per-alert RAG evidence expanders.

---

## Quick Start

### Prerequisites

1. Run the full pipeline at least once so the model exists:
   ```bash
   cd safety_nlp_pipeline
   python main.py
   ```
2. The monitor requires the artifacts: `data/safety_model.pkl`, `data/tfidf_vectorizer.pkl`, `data/real_safety_dataset.csv`.

### Start the Monitor

```bash
# Continuous loop (default: poll every 60s, watches folder + live feeds)
python -m src.monitor

# Single scan (useful for CI / demos)
python -m src.monitor --once --no-api

# Train + start monitoring in one command
python main.py --monitor --poll 30
```

### Feed It Incidents

```bash
# Option 1: Drop a CSV into the watched folder
echo 'id,narrative
DEMO-001,Engine fire at FL350, declared emergency, dumping fuel.
DEMO-002,Unplanned power cut affecting 250 customers in PINNER.' \
  > new_incidents/DEMO-2026.csv

# Option 2: Append rows to the master dataset (auto-detected on next scan)
```

### View Alerts

```bash
streamlit run app_streamlit.py
# → click the "���� Live Alerts" tab
```

---

## Architecture

```
��─────────────────────────────────────────────────────────────────��
│                    INCIDENT MONITOR LOOP                         │
├─────────────────────────────────────────────────────────────────��
│  WATCH FOLDER     MASTER DATASET     NTSB API      UKPN API      │
│  (CSV/TXT)        (appended rows)    (daily)       (every min)   │
│       │                │               │               │          │
│       └────────��───────��───────��───────��───────��───────��          │
│                ��               ��               ��                  │
│         ��─────────────────────────────────────────────��           │
│         │           classify + risk score              │           │
│         │  process_new_incident(narrative, id, source) │           │
│         └────────────────────��────────────────────────��           │
│                              ��                                    │
│                    ��─────────────────────��                        │
│                    │  assess_risk(text,  │                        │
│                    │       predicted)    │                        │
│                    │  → critical/high/   │                        │
│                    │     medium          │                        │
│                    └──────────��──────────��                        │
│                               ��                                    │
│                    ��─────────────────────��                        │
│                    │  RAG evidence       │                        │
│                    │  (explain_text)     │                        │
│                    └──────────��──────────��                        │
│                               ��                                    │
│              critical/high? → log_alert() → data/alerts.csv       │
│                               │                                    │
│                               ��                                    │
│                    Streamlit "Live Alerts" tab                    │
��─────────────────────────────────────────────────────────────────��
```

---

## Data Sources

| Source                     | Type                                              | Cadence                                     | Notes                                                                                                                                                                                                                                                                          |
| -------------------------- | ------------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Drop-in folder**   | CSV/TXT files in`new_incidents/`                | Every`MONITOR_POLL_SECONDS` (60s)         | Forgiving parser: handles unquoted commas.                                                                                                                                                                                                                                     |
| **Master dataset**   | Rows appended to`data/real_safety_dataset.csv`  | Every loop                                  | First scan establishes baseline — history is NOT re-alerted.                                                                                                                                                                                                                  |
| **NTSB API**         | US aviation accidents (probable-cause narratives) | Every`NTSB_POLL_SECONDS` (3600s / hourly) | `https://api.ai-analytics.org/api/v1/ntsb/aviation/recent` — CC0 public domain. Skips records without `probable_cause`.                                                                                                                                                   |
| **UKPN Live Faults** | UK power cuts (unplanned only)                    | Every`UKPN_POLL_SECONDS` (60s)            | `ukpn-live-faults` dataset on `ukpowernetworks.opendatasoft.com`. **NOTE**: `live-power-cuts` returns 404 — the real dataset is `ukpn-live-faults`. Power cuts affecting ≥ `ALERT_HIGH_MIN_CUSTOMERS` (100) escalate to `high` regardless of keyword hits. |

---

## Drop-In Folder Format

### CSV (recommended)

```csv
id,narrative
INC-001,Lost communication with ATC due to static, declared emergency.
INC-002,Unplanned power cut affecting 500 customers in PINNER area.
```

- **id**: optional unique string (used for de-duplication).
- **narrative**: required incident text.
- Parser joins any unquoted commas back into the narrative.

### TXT (one file = one report)

```
new_incidents/INC-003.txt
```

Content is the full narrative; filename becomes the `incident_id`.

---

## Risk Assessment (`assess_risk`)

Returns **critical / high / medium** based on:

1. **Raw-text triggers** (override model label):

   - **Critical**: `fire`, `smoke`, `explosion`, `crash`, `cfit`, `terrain`, `loss of communication`, `lost contact`, `radio failure`, `atc communication`, `power outage`, `power cut`, `blackout`, `grid collapse`, `system emergency`, `evacuation`, `emergency`, `mayday`, `engine failure`, `dual engine`.
   - **High**: `altitude`, `runway`, `weather`, `storm`, `hurricane`, `arctic`, `icing`, `turbulence`, `wind shear`, `engine`, `hydraulic`, `fuel`, `bird strike`, `decompression`, `loss of power`, `outage`.
2. **Model label intrinsic criticality** (from `analyst._risk_level`): label keywords mapped to critical/high/medium.
3. **High-risk narrative vocabulary** (if no label match): same high list above.

Result priority: triggers → label → vocab → medium.

---

## Alert Lifecycle

1. **Ingest**: new report arrives from any source.
2. **Classify**: `explain_text` → predicted label + top-3 RAG evidence.
3. **Score risk**: `assess_risk` → critical / high / medium.
4. **Filter**: only **critical** and **high** become alerts; medium is logged as "No alert".
5. **Persist**: `log_alert` appends one row to `data/alerts.csv`:| Column              | Description                                                         |
   | ------------------- | ------------------------------------------------------------------- |
   | `timestamp`       | ISO datetime                                                        |
   | `incident_id`     | stable ID (from source)                                             |
   | `source`          | `watch/FILE.csv`, `dataset`, `NTSB API`, `UKPN Live Faults` |
   | `risk_level`      | `critical` / `high` / `medium`                                |
   | `predicted_label` | model prediction                                                    |
   | `narrative`       | snippet (first`MONITOR_ALERT_SNIPPET` chars)                      |
   | `evidence_json`   | JSON array of RAG evidence dicts                                    |
6. **Display**: Streamlit Live Alerts tab reads `alerts.csv`, parses `evidence_json`, shows color-coded table + expanders with evidence.

---

## De-duplication (Survives Restarts)

State is persisted to `data/monitor_state.json` after every scan:

- **Seen incident keys** (incident_id or hash of narrative).
- **Seen files** (name + size + mtime) — unchanged files skipped.
- **Master dataset baseline** (row count) — only NEW rows after first scan.
- **Last poll timestamps** per live feed.

A monitor **restart never re-alerts** on already-processed incidents.

---

## Streamlit "Live Alerts" Tab

- **Metrics row**: Critical / High / Medium counts + Total.
- **Table** (most recent 50): color-coded rows (red = critical, yellow = high).
- **Evidence expanders** (top 5): RAG evidence with similarity bars, same style as RAG Explorer tab.
- **Refresh button**: re-reads `alerts.csv` on click.

---

## CLI Reference

### `python -m src.monitor`

```text
usage: monitor.py [-h] [--watch-dir WATCH_DIR] [--delay DELAY]
                  [--once] [--no-api]

Real-time incident monitoring & alerting service.

options:
  --watch-dir PATH   folder to watch (default: new_incidents/)
  --delay SECONDS    poll interval in seconds (default: 60)
  --once             scan a single pass and exit
  --no-api           disable the NTSB / UKPN live feeds
```

### `python main.py --monitor --poll N`

Runs the full pipeline, then starts the monitor loop with poll interval `N` seconds (default 60).

---

## Verification / Testing

### 1. Unit smoke (no network, no artifacts)

```bash
python -c "
from src import monitor
assert monitor.assess_risk('Engine fire at FL350', 'x') == 'critical'
assert monitor.assess_rink('Paperwork completed', 'x') == 'medium'
print('assess_risk OK')
"
```

### 2. End-to-end scan with seeded file (no live feeds)

```bash
# clean slate
rm -f data/alerts.csv data/monitor_state.json
echo 'id,narrative
DEMO-001,Engine fire at FL350, declared emergency.
DEMO-002,Unplanned power cut affecting 250 customers.
DEMO-003,Routine preflight checks.' > new_incidents/DEMO.csv

python -m src.monitor --once --no-api
# → alerts.csv has 2 rows (critical + critical)
# → second run with --once produces 0 new
```

### 3. Live API poll test (requires network)

```bash
python -c "
from src import monitor
state = monitor._load_state()
print('NTSB:', monitor._poll_ntsb(state))
print('UKPN:', monitor._poll_ukpn(state))
monitor._save_state(state)
"
# Should print counts > 0 and raise alerts to alerts.csv
```

### 4. Streamlit AppTest (automated)

```bash
python -c "
from streamlit.testing.v1 import AppTest
at = AppTest.from_file('app_streamlit.py', default_timeout=300)
at.run()
assert len(at.exception) == 0
assert len(at.tabs) == 5  # includes Live Alerts
print('DASHBOARD OK')
"
```

---

## Configuration (config.py)

| Key                          | Default                          | Description                 |
| ---------------------------- | -------------------------------- | --------------------------- |
| `WATCH_DIR`                | `BASE_DIR / "new_incidents"`   | Drop-in folder              |
| `ALERT_LOG_PATH`           | `DATA_DIR / "alerts.csv"`      | Alert log                   |
| `MONITOR_POLL_SECONDS`     | `60`                           | Main loop delay             |
| `MONITOR_ALERT_SNIPPET`    | `200`                          | Narrative chars stored      |
| `NTSB_API_URL`             | `.../ntsb/aviation/recent`     | NTSB endpoint               |
| `NTSB_POLL_SECONDS`        | `3600`                         | NTSB cadence (hourly)       |
| `UKPN_API_URL`             | `.../ukpn-live-faults/records` | UKPN endpoint               |
| `UKPN_POLL_SECONDS`        | `60`                           | UKPN cadence (every minute) |
| `ALERT_HIGH_MIN_CUSTOMERS` | `100`                          | UKPN high-risk threshold    |

Tune these for your environment (e.g., lower `UKPN_POLL_SECONDS` for faster reaction, raise `ALERT_HIGH_MIN_CUSTOMERS` to reduce noise).

---

## Troubleshooting

| Symptom                                         | Cause                                             | Fix                                                                                           |
| ----------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `FileNotFoundError: Monitor artifact missing` | Model not trained                                 | Run`python main.py` first.                                                                  |
| `TLS verification failed`                     | Corporate CA / cert store                         | Monitor uses`data_fetcher._http_get` which falls back to `verify=False` (logged warning). |
| No alerts from NTSB                             | `probable_cause` is null for recent records     | Normal — only records with cause text are processed.                                         |
| No alerts from UKPN                             | All recent records are`Planned` or `Restored` | Normal — only`Unplanned` cuts are incidents.                                               |
| Duplicate alerts after restart                  | State file missing / corrupted                    | Check`data/monitor_state.json` exists and is valid JSON.                                    |
| `ModuleNotFoundError: config`                 | Running from wrong directory                      | Run from`safety_nlp_pipeline/` root.                                                        |
| `use_container_width` deprecation warnings    | Streamlit ≥1.37                                  | Harmless; dashboard works.                                                                    |
| pypdf`CryptographyDeprecationWarning`         | ARC4 deprecation                                  | Harmless; PDF extraction works.                                                               |

---

## Future Extensions

- **Kafka / RabbitMQ subscriber** instead of polling (true push).
- **Email / Slack / PagerDuty** notifications (`smtplib`, `twilio`, `requests` webhook).
- **Recommendation engine**: given RAG evidence, auto-suggest SOPs / checklists.
- **Incremental learning**: retrain model periodically with new labeled incidents.
- **Multi-region monitoring**: add ENTSO-E API, ORNL GSL, US DOE OE-417.

---

## Important Correction

> **The UK Power Networks dataset often referenced as `live-power-cuts` does NOT exist (404).**
> The real near-real-time feed is **`ukpn-live-faults`** — this is what the monitor polls every minute.

---

## File Locations Summary

```
safety_nlp_pipeline/
├── config.py                    # all monitor parameters
├── main.py                      # --monitor / --poll flags
├── src/monitor.py               # monitoring service (entry point)
├── app_streamlit.py             # Live Alerts tab (tab 5)
├── new_incidents/               # drop CSV/TXT here
│   └── README.txt               # format documentation
├── data/
│   ├── alerts.csv               # every raised alert (dashboard)
│   ├── monitor_state.json       # de-dup state (survives restarts)
│   ├── real_safety_dataset.csv
│   ├── safety_model.pkl
│   └── tfidf_vectorizer.pkl
```

---

## One-Command Demo

```bash
cd safety_nlp_pipeline
python main.py                 # trains model (or reuses cache)
python -m src.monitor --once   # single scan of folder + dataset
streamlit run app_streamlit.py # open http://localhost:8501 → Live Alerts tab
```

Drop a file into `new_incidents/` and click **Refresh alerts** to see it appear.
