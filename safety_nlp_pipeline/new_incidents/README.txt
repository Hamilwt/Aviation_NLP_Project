DROP-IN FOLDER FOR NEW INCIDENT REPORTS
=======================================

The real-time monitor (src/monitor.py) watches this folder. Drop any file
with a .csv or .txt extension here and it will be picked up on the next scan,
classified, risk-scored and logged to data/alerts.csv.

You can then view alerts in either of the supported dashboards:
  - React + FastAPI dashboard (recommended):
      cd ../../aviation-safety-app
      python start.py          # or start_app.bat / .sh / .ps1 from the repo root
      open http://localhost:5173  -> "Live Alerts" page
  - Legacy Streamlit dashboard:
      streamlit run app_streamlit.py
      open http://localhost:8501  -> "Live Alerts" tab


CSV format (recommended)
------------------------
Columns:
    id          - optional, any unique string (used for de-duplication)
    narrative   - the incident text (required)

Example:
    id,narrative
    DEMO-001,At FL350 the aircraft lost communication with ATC due to static; we declared an emergency and returned to base.
    DEMO-002,Unplanned power cut affecting 200 customers in the PINNER area; main message said problems with the electricity supply.

TXT format
----------
Any .txt file is treated as one narrative (file name becomes the id).

How to use
----------
1. Make sure you have run `python main.py` once so the model exists.
2. Start the monitor (separate terminal):
       python -m src.monitor
3. Drop a CSV/TXT file into this folder.
4. Open one of the dashboards above and check the "Live Alerts" tab/page.

You can also watch for rows appended to data/real_safety_dataset.csv, or poll
the live NTSB (aviation) and UK Power Networks (power-cut) feeds - all three
sources run automatically inside the monitor loop.
