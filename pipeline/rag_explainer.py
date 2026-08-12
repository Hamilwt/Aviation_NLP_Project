"""Step 3 - RAG explainer: classify a new incident and retrieve evidence.

The TF-IDF vectors double as the retrieval index: the new report is
embedded with the trained vectorizer, its risk category is predicted,
and the top-N most semantically similar historical reports are returned
as in-context evidence for the classification.
"""
import sys

import joblib
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from pipeline.paths import DEFAULT_DATASET, DEFAULT_MODEL, DEFAULT_VECTORIZER
from pipeline.preprocess import preprocess_text


def explain_incident(new_report_text, dataset=DEFAULT_DATASET,
                     model_path=DEFAULT_MODEL, vectorizer_path=DEFAULT_VECTORIZER,
                     top_k=3, log=print) -> dict:
    """Explain a raw incident report. Returns a structured result dict."""
    df = pd.read_csv(dataset)
    model = joblib.load(model_path)
    vectorizer = joblib.load(vectorizer_path)

    processed_text = preprocess_text(new_report_text)
    new_vector = vectorizer.transform([processed_text])

    predicted_risk = model.predict(new_vector)[0]

    log("[rag] Embedding historical reports and matching by cosine similarity ...")
    historical_vectors = vectorizer.transform(df["Narrative"].apply(preprocess_text))
    similarities = cosine_similarity(new_vector, historical_vectors).flatten()
    top_indices = similarities.argsort()[-top_k:][::-1]

    matches = []
    for rank, idx in enumerate(top_indices, 1):
        matches.append({
            "rank": rank,
            "similarity": float(similarities[idx]),
            "label": df.iloc[idx]["human_factors_groundtruth"],
            "narrative": str(df.iloc[idx]["Narrative"]),
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