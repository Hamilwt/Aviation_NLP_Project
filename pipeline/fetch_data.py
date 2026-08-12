"""Step 1 - Fetch & clean the open NASA ASRS dataset from Hugging Face.

If the dataset already exists on disk, the step skips the download and
simply reports the cached artifact (the TUI then displays its contents).
"""
import sys

import pandas as pd
from datasets import load_dataset

from pipeline.paths import (DEFAULT_DATASET, DEFAULT_HF_DATASET,
                            LABEL_KEYWORDS, NARRATIVE_KEYWORDS, NROWS_LIMIT,
                            TOP_CATEGORIES)


def _detect_column(df: pd.DataFrame, keywords, fallback_name):
    """Auto-detect the narrative / label column from the available columns."""
    lowered = {c: c.lower() for c in df.columns}
    for col, low in lowered.items():
        if any(k in low for k in keywords):
            return col
    raise ValueError(
        f"Could not auto-detect {fallback_name} column; "
        f"available columns: {list(df.columns)}"
    )


def fetch_and_clean(target=DEFAULT_DATASET, hf_dataset=DEFAULT_HF_DATASET,
                    nrows=NROWS_LIMIT, top_categories=TOP_CATEGORIES,
                    log=print, on_progress=None) -> dict:
    """Download (or reuse) the ASRS dataset and save a cleaned CSV.

    Returns a dict describing what happened:
      {"status": "existing"|"downloaded", "rows": int, "path": Path, "df": DataFrame}
    """
    if target.exists():
        df = pd.read_csv(target)
        log(f"[fetch] Dataset already on disk: {target.name} "
            f"({len(df)} rows). Skipping download.")
        if on_progress:
            on_progress("ALREADY ON DISK", 100)
        return {"status": "existing", "rows": len(df), "path": target, "df": df}

    if on_progress:
        on_progress("CONNECTING TO HUGGING FACE", 10)
    log(f"[fetch] Downloading '{hf_dataset}' from Hugging Face ...")
    dataset = load_dataset(hf_dataset)
    df = pd.DataFrame(dataset["train"])
    if on_progress:
        on_progress("DOWNLOADING ASRS REPORTS", 50)

    narrative_col = _detect_column(df, NARRATIVE_KEYWORDS, "narrative")
    label_col = _detect_column(df, LABEL_KEYWORDS, "label")

    df = df[[narrative_col, label_col]].rename(columns={
        narrative_col: "Narrative",
        label_col: "human_factors_groundtruth",
    })

    # Reduce multi-label anomaly strings to the primary category
    # (e.g. "ATC Issue; Conflict Airborne Conflict" -> "ATC Issue All Types")
    df["human_factors_groundtruth"] = (
        df["human_factors_groundtruth"].str.split(";").str[0].str.strip()
    )

    # Keep the most frequent categories; bucket rare ones as 'Other' so the
    # classifier has a tractable label space with enough samples per class.
    top = df["human_factors_groundtruth"].value_counts().nlargest(top_categories).index
    df["human_factors_groundtruth"] = df["human_factors_groundtruth"].where(
        df["human_factors_groundtruth"].isin(top), "Other"
    )

    df = df.dropna().head(nrows)
    target.parent.mkdir(exist_ok=True)
    df.to_csv(target, index=False)
    if on_progress:
        on_progress("SAVING CLEANED CSV", 100)
    log(f"[fetch] Saved {len(df)} cleaned ASRS reports -> {target}")
    return {"status": "downloaded", "rows": len(df), "path": target, "df": df}


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