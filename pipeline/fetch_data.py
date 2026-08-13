"""Step 1 - Collect & download real domain safety data (live, with progress).

Two real public sources are downloaded every run - nothing is pre-baked:

  * Aviation safety
      NASA ASRS incident reports (47k+) streamed from the Hugging Face
      datasets-server API in paginated batches. Narrative text comes from
      ``Report 1_Narrative``, the expert anomaly label from ``Events_Anomaly``.

  * Power infrastructure safety
      Public NERC (North American Electric Reliability Corporation) Event
      Analysis reports - the canonical power-grid incident post-mortems.
      Each PDF is downloaded, its text extracted with pypdf and split into
      incident narratives with NLTK sentence tokenization.

Every stage reports REAL progress driven by actual rows downloaded /
documents processed. Both sources are cleaned (dedupe, drop empty labels,
collapse whitespace) and merged into one ``Domain``-tagged dataset.
"""
import sys
import warnings
from io import BytesIO

import pandas as pd
import requests
from pypdf import PdfReader
from nltk.tokenize import sent_tokenize

from pipeline.paths import (ASRS_DATASET, ASRS_FETCH_BATCH, ASRS_LABEL_COL,
                            ASRS_NARRATIVE_COL, ASRS_ROWS_API, ASRS_SPLIT,
                            AVIATION_DOMAIN, DEFAULT_DATASET, DOMAIN_COL,
                            LABEL_COL, NARRATIVE_COL, NERC_REPORTS,
                            NROWS_LIMIT, POWER_DOMAIN, TOP_CATEGORIES)

_HEADERS = {"User-Agent": "Aviation-NLP-Pipeline/1.0 (academic demo)"}

_TLS_WARNED = False

# Noise lines that appear in the PDF headers/footers and carry no signal.
_PDF_NOISE = (
    "reliability | resilience | security", "nerc |", "report title",
    "report date", "nerc | report", "page ", "e-3", "iii", "glossary of",
    "table of contents", "figure ", "table ", "©", "north american electric",
)


# ------------------------------------------------------------------ http
def _http_get(url: str, timeout: int = 90, log=print) -> requests.Response:
    """GET with graceful SSL fallback (some corporate/Python CA stores fail)."""
    try:
        return requests.get(url, headers=_HEADERS, timeout=timeout)
    except requests.exceptions.SSLError:
        warnings.simplefilter("ignore")
        global _TLS_WARNED
        if not _TLS_WARNED:
            log("[fetch] TLS verification failed for this host - retrying "
                "unverified (public data).")
            _TLS_WARNED = True
        return requests.get(url, headers=_HEADERS, timeout=timeout,
                            verify=False)
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Network failure: {exc}") from exc


# ----------------------------------------------------------------- aviation
def _fetch_aviation(nrows: int, on_progress, log) -> pd.DataFrame:
    """Stream NASA ASRS reports from the datasets-server, row by row."""
    log(f"[fetch] Aviation source: NASA ASRS ({ASRS_DATASET})")
    if on_progress:
        on_progress("CONNECTING TO ASRS (HUGGING FACE)", 2)
    rows: list[dict] = []
    offset = 0
    while len(rows) < nrows:
        if on_progress:
            on_progress("STREAMING ASRS REPORTS", 2 + int(88 * len(rows) / nrows))
        resp = _http_get(
            f"{ASRS_ROWS_API}?dataset={ASRS_DATASET}&config=default"
            f"&split={ASRS_SPLIT}&offset={offset}&length={ASRS_FETCH_BATCH}",
            log=log,
        )
        resp.raise_for_status()
        payload = resp.json()
        batch = payload.get("rows", [])
        if not batch:
            break
        for item in batch:
            rec = item.get("row", {})
            narrative = (rec.get(ASRS_NARRATIVE_COL) or "").strip()
            label = (rec.get(ASRS_LABEL_COL) or "").strip()
            if narrative and label:
                rows.append({NARRATIVE_COL: narrative, LABEL_COL: label})
        offset += len(batch)
    log(f"[fetch] Streamed {len(rows)} ASRS reports (target {nrows}).")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------- power
def _clean_pdf_text(text: str) -> list[str]:
    """Turn raw PDF text into clean, meaningful narrative lines."""
    lines = []
    for raw in text.splitlines():
        line = " ".join(raw.split())
        low = line.lower()
        if not line or len(line) < 40:
            continue
        if any(n in low for n in _PDF_NOISE):
            continue
        if low.isdigit() or line.isupper() and len(line) > 60:
            continue
        lines.append(line)
    return lines


def _chunk_power_narratives(text: str, label: str, log) -> list[dict]:
    """Split a NERC report into NLTK sentence-tokenized narrative chunks."""
    lines = _clean_pdf_text(text)
    body = " ".join(lines)
    if not body:
        return []
    try:
        sentences = sent_tokenize(body)
    except LookupError:
        sentences = body.split(".")
    chunks, current = [], []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        current.append(sentence)
        if len(current) >= 5:  # ~5 sentences per incident narrative
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return [{NARRATIVE_COL: c, LABEL_COL: label} for c in chunks]


def _fetch_power(on_progress, log) -> pd.DataFrame:
    """Download + parse public NERC Event Analysis PDFs (real incidents)."""
    log(f"[fetch] Power source: NERC Event Analysis reports "
        f"({len(NERC_REPORTS)} PDFs)")
    all_rows: list[dict] = []
    total = len(NERC_REPORTS)
    for i, (label, url) in enumerate(NERC_REPORTS, 1):
        if on_progress:
            on_progress(f"NERC PDF {i}/{total}", 90 + int(10 * i / total))
        try:
            log(f"[fetch]   [{i}/{total}] {label.split(' - ')[-1]} ...")
            resp = _http_get(url, timeout=120, log=log)
            resp.raise_for_status()
            reader = PdfReader(BytesIO(resp.content))
            text = "\n".join(page.extract_text() or ""
                             for page in reader.pages)
            rows = _chunk_power_narratives(text, label, log)
            all_rows.extend(rows)
            log(f"[fetch]   extracted {len(rows)} narratives "
                f"from {len(reader.pages)} pages")
        except Exception as exc:  # one bad report must not kill the fetch
            log(f"[fetch]   [warn] {label} failed: {type(exc).__name__}: {exc}")
    log(f"[fetch] Built {len(all_rows)} power-grid narratives from "
        f"{len(NERC_REPORTS)} NERC reports.")
    return pd.DataFrame(all_rows)


# ------------------------------------------------------------------- main
def fetch_and_clean(target=DEFAULT_DATASET, nrows=NROWS_LIMIT,
                    top_categories=TOP_CATEGORIES, log=print,
                    on_progress=None) -> dict:
    """Download live aviation + power-grid safety data and save a cleaned CSV.

    Returns:
      {"status": "downloaded"|"fallback_existing", "rows": int,
       "aviation": int, "power": int, "path": Path, "df": DataFrame}
    """
    try:
        if on_progress:
            on_progress("COLLECTING REAL SAFETY DATASETS", 0)
        aviation = _fetch_aviation(nrows, on_progress, log)
        aviation[DOMAIN_COL] = AVIATION_DOMAIN

        # Multi-label strings -> primary category, rare ones bucketed as Other.
        aviation[LABEL_COL] = (
            aviation[LABEL_COL].str.split(";").str[0].str.strip()
        )
        top = (aviation[LABEL_COL].value_counts()
               .nlargest(top_categories).index)
        aviation[LABEL_COL] = aviation[LABEL_COL].where(
            aviation[LABEL_COL].isin(top), "Other")

        power = _fetch_power(on_progress, log)
        power[DOMAIN_COL] = POWER_DOMAIN

        df = pd.concat([aviation, power], ignore_index=True)
        df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])
        df = df[df[NARRATIVE_COL].str.len() > 20]
        df = df.drop_duplicates(subset=[NARRATIVE_COL])
        df = df.reset_index(drop=True)

        target.parent.mkdir(exist_ok=True)
        df.to_csv(target, index=False)
        if on_progress:
            on_progress("SAVED CLEANED DATASET", 100)
        log(f"[fetch] Saved {len(df)} cleaned reports -> {target.name} "
            f"({aviation.shape[0]} aviation, {power.shape[0]} power-grid)")
        return {
            "status": "downloaded",
            "rows": int(len(df)),
            "aviation": int(aviation.shape[0]),
            "power": int(power.shape[0]),
            "path": target,
            "df": df,
        }
    except Exception as exc:
        if target.exists():
            df = pd.read_csv(target)
            log(f"[fetch] Download failed ({type(exc).__name__}: {exc}); "
                f"reusing cached {target.name} ({len(df)} rows).")
            if on_progress:
                on_progress("USING CACHED DATASET", 100)
            return {"status": "fallback_existing", "rows": int(len(df)),
                    "aviation": int(df[df[DOMAIN_COL] == AVIATION_DOMAIN].shape[0])
                    if DOMAIN_COL in df.columns else int(len(df)),
                    "power": int(df[df[DOMAIN_COL] == POWER_DOMAIN].shape[0])
                    if DOMAIN_COL in df.columns else 0,
                    "path": target, "df": df}
        raise


def describe_dataset(path=DEFAULT_DATASET) -> dict:
    """Read a dataset and summarize it for terminal display."""
    df = pd.read_csv(path)
    distribution = (df.iloc[:, -1].value_counts() if df.shape[1] > 1
                    else pd.Series(dtype=int))
    return {
        "path": path, "rows": len(df), "columns": list(df.columns),
        "distribution": distribution,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    result = fetch_and_clean()
    print(result)
