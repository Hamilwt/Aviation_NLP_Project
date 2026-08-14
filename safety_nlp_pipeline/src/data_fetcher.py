"""Step 1 - Collect & download real domain safety data (live, with fallbacks).

Two real public sources are downloaded - nothing is pre-baked:

  * Aviation safety
      NASA ASRS incident reports (47k+) streamed from the Hugging Face
      datasets-server API in paginated batches. Narrative text comes from
      ``Report 1_Narrative``, the expert anomaly label from ``Events_Anomaly``.

  * Power infrastructure safety
      Public NERC (North American Electric Reliability Corporation) Event
      Analysis reports - canonical power-grid incident post-mortems. Each PDF
      is downloaded (optionally cached), text extracted with pypdf and split
      into narrative chunks with NLTK sentence tokenization.

Fault tolerance / idempotency:
  * If ``data/real_safety_dataset.csv`` already exists and ``force_refresh``
    is False, the fetch is skipped entirely and the cached dataset is loaded.
  * Each domain is fetched independently. If one source fails it falls back to
    the cached rows for that domain, or is gracefully skipped with a warning.
  * Legacy column names (Narrative / human_factors_groundtruth / Domain) are
    normalised to the canonical lowercase schema on load.
"""
import logging
import warnings
from io import BytesIO

import pandas as pd
import requests
from pypdf import PdfReader
from nltk.tokenize import sent_tokenize

from config import (ASRS_DATASET, ASRS_FETCH_BATCH, ASRS_LABEL_COL,
                    ASRS_NARRATIVE_COL, ASRS_ROWS_API, ASRS_SPLIT,
                    COLUMN_ALIASES, DATASET_PATH, DOMAIN_AVIATION,
                    DOMAIN_COL, DOMAIN_POWER, LABEL_COL, MIN_NARRATIVE_LEN,
                    NARRATIVE_COL, NERC_PDFS, NROWS_AVIATION, PDF_CACHE,
                    RAW_DIR, TOP_CATEGORIES)

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Safety-NLP-Pipeline/2.0 (academic demo)"}
_TLS_WARNED = False

# Noise lines found in the PDF headers/footers that carry no signal.
_PDF_NOISE = (
    "reliability | resilience | security", "nerc |", "report title",
    "report date", "nerc | report", "page ", "e-3", "iii", "glossary of",
    "table of contents", "figure ", "table ", "\u00a9", "north american electric",
)


# ------------------------------------------------------------------ http
def _http_get(url: str, timeout: int = 120) -> requests.Response:
    """GET with graceful SSL fallback (some corporate/Python CA stores fail)."""
    global _TLS_WARNED
    try:
        return requests.get(url, headers=_HEADERS, timeout=timeout)
    except requests.exceptions.SSLError:
        warnings.simplefilter("ignore")
        if not _TLS_WARNED:
            logger.warning("TLS verification failed for %s - retrying "
                           "unverified (public data).", url.split("/")[2])
            _TLS_WARNED = True
        return requests.get(url, headers=_HEADERS, timeout=timeout,
                            verify=False)
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Network failure: {exc}") from exc


# ----------------------------------------------------------------- aviation
def _fetch_aviation(nrows: int) -> pd.DataFrame:
    """Stream NASA ASRS reports from the datasets-server, row by row."""
    logger.info("Aviation source: NASA ASRS (%s)", ASRS_DATASET)
    rows: list[dict] = []
    offset = 0
    while len(rows) < nrows:
        resp = _http_get(
            f"{ASRS_ROWS_API}?dataset={ASRS_DATASET}&config=default"
            f"&split={ASRS_SPLIT}&offset={offset}&length={ASRS_FETCH_BATCH}",
        )
        resp.raise_for_status()
        batch = resp.json().get("rows", [])
        if not batch:
            break
        for item in batch:
            rec = item.get("row", {})
            narrative = (rec.get(ASRS_NARRATIVE_COL) or "").strip()
            label = (rec.get(ASRS_LABEL_COL) or "").strip()
            if narrative and label:
                rows.append({NARRATIVE_COL: narrative, LABEL_COL: label})
        offset += len(batch)
        if len(rows) >= nrows or offset % 1000 == 0:
            logger.info("  streamed %d/%d ASRS reports", len(rows), nrows)
    rows = rows[:nrows]  # batch boundaries can overshoot the target
    logger.info("Streamed %d ASRS reports (target %d).", len(rows), nrows)
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
        if low.isdigit() or (line.isupper() and len(line) > 60):
            continue
        lines.append(line)
    return lines


def _chunk_power_narratives(text: str, label: str) -> list[dict]:
    """Split a NERC report into NLTK sentence-tokenized narrative chunks."""
    body = " ".join(_clean_pdf_text(text))
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


def _fetch_power() -> pd.DataFrame:
    """Download + parse public NERC Event Analysis PDFs (real incidents)."""
    logger.info("Power source: NERC Event Analysis reports (%d PDFs)",
                len(NERC_PDFS))
    all_rows: list[dict] = []
    for i, (label, url) in enumerate(NERC_PDFS, 1):
        try:
            short = label.split(" - ")[-1]
            logger.info("  [%d/%d] %s ...", i, len(NERC_PDFS), short)
            pdf_bytes = _download_pdf(url, label)
            reader = PdfReader(BytesIO(pdf_bytes))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            rows = _chunk_power_narratives(text, label)
            all_rows.extend(rows)
            logger.info("         extracted %d narratives from %d pages",
                        len(rows), len(reader.pages))
        except Exception as exc:  # one bad report must not kill the fetch
            logger.warning("         [warn] %s failed: %s: %s",
                           short, type(exc).__name__, exc)
    logger.info("Built %d power-grid narratives from %d NERC reports.",
                len(all_rows), len(NERC_PDFS))
    return pd.DataFrame(all_rows)


def _download_pdf(url: str, label: str) -> bytes:
    """Download a PDF, optionally caching it under data/raw for reuse."""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in label)
    cache_path = RAW_DIR / f"{safe}.pdf"
    if PDF_CACHE and cache_path.exists():
        logger.info("         using cached PDF: %s", cache_path.name)
        return cache_path.read_bytes()
    resp = _http_get(url, timeout=120)
    resp.raise_for_status()
    content = resp.content
    if PDF_CACHE:
        cache_path.write_bytes(content)
    return content


# ------------------------------------------------------------------- main
def _load_cached(path=DATASET_PATH) -> pd.DataFrame | None:
    """Load a previously saved dataset, normalising column names."""
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df.rename(columns=COLUMN_ALIASES)
    keep = [c for c in (NARRATIVE_COL, LABEL_COL, DOMAIN_COL) if c in df.columns]
    return df[keep].copy()


def _merge_and_save(aviation: pd.DataFrame | None,
                    power: pd.DataFrame | None) -> pd.DataFrame:
    """Merge the two domains, clean, and persist to CSV."""
    frames = []
    if aviation is not None and len(aviation):
        aviation = aviation.copy()
        aviation[DOMAIN_COL] = DOMAIN_AVIATION
        # Multi-label strings -> primary category, rare ones bucketed as Other.
        aviation[LABEL_COL] = (
            aviation[LABEL_COL].astype(str)
            .str.split(";").str[0].str.strip()
        )
        top = (aviation[LABEL_COL].value_counts()
               .nlargest(TOP_CATEGORIES).index)
        aviation[LABEL_COL] = aviation[LABEL_COL].where(
            aviation[LABEL_COL].isin(top), "Other")
        frames.append(aviation)
    if power is not None and len(power):
        power = power.copy()
        power[DOMAIN_COL] = DOMAIN_POWER
        frames.append(power)

    if not frames:
        raise RuntimeError("No data available from any source.")

    df = pd.concat(frames, ignore_index=True)
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])
    df = df[df[NARRATIVE_COL].astype(str).str.len() > MIN_NARRATIVE_LEN]
    df = df.drop_duplicates(subset=[NARRATIVE_COL])
    df = df.reset_index(drop=True)

    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    av = int((df[DOMAIN_COL] == DOMAIN_AVIATION).sum())
    pw = int((df[DOMAIN_COL] == DOMAIN_POWER).sum())
    logger.info("Saved %d cleaned reports -> %s (%d aviation, %d power-grid)",
                len(df), DATASET_PATH.name, av, pw)
    return df


def load_dataset(path=DATASET_PATH) -> pd.DataFrame:
    """Public loader: read + normalise a dataset CSV (raises if missing)."""
    df = _load_cached(path)
    if df is None:
        raise FileNotFoundError(f"Dataset not found: {path}")
    return df


def fetch_all(force_refresh: bool = False, nrows: int = NROWS_AVIATION) -> pd.DataFrame:
    """Download aviation + power-grid safety data, or load the cached CSV.

    Returns the domain-tagged DataFrame (and persists it to CSV on fetch).
    """
    cached = _load_cached()
    if cached is not None and not force_refresh:
        logger.info("Cached dataset found (%d rows) - skipping fetch "
                    "(delete the CSV or use --force-refresh to re-download).",
                    len(cached))
        return cached

    if cached is not None:
        logger.info("Re-fetching data (--force-refresh); cached copy kept as "
                    "fallback for individual domains.")

    aviation = power = None
    try:
        aviation = _fetch_aviation(nrows)
    except Exception as exc:
        logger.warning("Aviation fetch FAILED (%s: %s).", type(exc).__name__, exc)
        if cached is not None:
            aviation = cached[cached[DOMAIN_COL] == DOMAIN_AVIATION]
            logger.warning("Falling back to cached aviation rows (%d).", len(aviation))

    try:
        power = _fetch_power()
    except Exception as exc:
        logger.warning("Power-grid fetch FAILED (%s: %s).", type(exc).__name__, exc)
        if cached is not None:
            power = cached[cached[DOMAIN_COL] == DOMAIN_POWER]
            logger.warning("Falling back to cached power-grid rows (%d).", len(power))

    if aviation is None and power is None:
        if cached is not None:
            logger.warning("Both sources unavailable - reusing cached dataset.")
            return cached
        raise RuntimeError("Both data sources unavailable and no cached dataset "
                           "exists. Check network connectivity.")

    return _merge_and_save(aviation, power)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)-8s | %(message)s")
    result = fetch_all(force_refresh=True, nrows=200)
    print(result[["domain", "label"]].head())
