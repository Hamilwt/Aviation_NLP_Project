"""Step 3 - RAG explainer: classify a new incident and retrieve evidence.

The TF-IDF vectors double as the retrieval index: the new report is
embedded with the trained vectorizer, its risk category is predicted,
and the top-N most semantically similar historical reports are returned
as in-context evidence for the classification.

Embedding the historical corpus is done in real batches - the progress
bar advances after every actual cosine-similarity computation.
"""
import sys
from math import ceil

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.paths import (DEFAULT_DATASET, DEFAULT_MODEL, DEFAULT_VECTORIZER,
                            LABEL_COL, NARRATIVE_COL)
from pipeline.preprocess import preprocess_text

BATCH = 200


def explain_incident(new_report_text, dataset=DEFAULT_DATASET,
                     model_path=DEFAULT_MODEL, vectorizer_path=DEFAULT_VECTORIZER,
                     top_k=3, log=print, on_progress=None) -> dict:
    """Explain a raw incident report. Returns a structured result dict."""
    if on_progress:
        on_progress("LOADING ARTIFACTS", 10)
    df = pd.read_csv(dataset)
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    processed_text = preprocess_text(new_report_text)
    new_vector = vectorizer.transform([processed_text])
    predicted_risk = model.predict(new_vector)[0]

    # ---- real batch embedding + similarity -------------------------------
    n = len(df)
    log(f"[rag] Embedding {n} historical reports in batches of {BATCH} ...")
    similarities = np.zeros(n)
    for start in range(0, n, BATCH):
        end = min(start + BATCH, n)
        if on_progress:
            on_progress(f"EMBEDDING + MATCHING {end}/{n}", 
                        10 + int(85 * end / n))
        batch = df.iloc[start:end]
        vectors = vectorizer.transform(
            batch[NARRATIVE_COL].apply(preprocess_text))
        similarities[start:end] = cosine_similarity(
            new_vector, vectors).flatten()

    if on_progress:
        on_progress("RANKING EVIDENCE", 100)
    top_indices = similarities.argsort()[-top_k:][::-1]
    matches = []
    for rank, idx in enumerate(top_indices, 1):
        row = df.iloc[idx]
        matches.append({
            "rank": rank,
            "similarity": float(similarities[idx]),
            "label": str(row[LABEL_COL]),
            "domain": str(row["Domain"]) if "Domain" in df.columns else "",
            "narrative": str(row[NARRATIVE_COL]),
        })

    log(f"[rag] Predicted '{predicted_risk}' with {len(matches)} evidence spans.")
    return {
        "text": new_report_text,
        "predicted_label": predicted_risk,
        "matches": matches,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    SAMPLE = ("I was cleared for the ILS approach but misheard the altitude "
              "restriction due to heavy static on the radio frequency. I descended "
              "to 3000 feet instead of 5000. ATC immediately called and issued a "
              "climb instruction to avoid terrain.")
    result = explain_incident(SAMPLE)
    print("PREDICTED:", result["predicted_label"])
    for m in result["matches"]:
        print(f"  #{m['rank']} {m['similarity']:.2%} {m['label']}")
