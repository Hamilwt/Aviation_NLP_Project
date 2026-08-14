"""Step 5 - Batch RAG explainability.

For a sample of the test set, each report is:
  1. Preprocessed and TF-IDF vectorized with the trained vectorizer,
  2. Classified by the trained model,
  3. Scored against ALL training narratives with batch cosine similarity,
  4. Assigned the top-K most similar historical reports as evidence.

This makes every prediction explainable by example - an audit trail that can
be rendered in the HTML report.
"""
import logging

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from config import (DOMAIN_COL, LABEL_COL, NARRATIVE_COL, PROCESSED_COL,
                    RAG_BATCH, RAG_EVIDENCE_SNIPPET, RAG_N_SAMPLES,
                    RAG_TOP_K, RANDOM_STATE)

logger = logging.getLogger(__name__)


def _evidence_row(df: pd.DataFrame, train_index, tr_pos: int,
                  similarity: float, rank: int) -> dict:
    """Build a human-readable evidence entry from a training-row position."""
    row = df.loc[train_index[tr_pos]]
    narrative = str(row[NARRATIVE_COL])
    return {
        "rank": rank,
        "similarity": float(similarity),
        "label": str(row[LABEL_COL]),
        "domain": str(row[DOMAIN_COL]) if DOMAIN_COL in df.columns else "",
        "snippet": narrative[:RAG_EVIDENCE_SNIPPET]
        + ("..." if len(narrative) > RAG_EVIDENCE_SNIPPET else ""),
    }


def batch_rag(model, vectorizer, df: pd.DataFrame, X_train, X_test, y_test,
              n_samples: int = RAG_N_SAMPLES, top_k: int = RAG_TOP_K,
              batch: int = RAG_BATCH) -> pd.DataFrame:
    """Run RAG explainability over ``n_samples`` test reports.

    Args:
        model / vectorizer: trained artifacts.
        df: full dataset (used to look up narrative/label/domain of training
            evidence rows; indices must line up with ``X_train``/``X_test``).
        X_train / X_test: preprocessed text Series (training / test).
        y_test: ground-truth labels for the test set.

    Returns:
        DataFrame with one row per explained test report containing input,
        true/predicted labels, correctness and the top-K evidence list.
    """
    n_samples = min(n_samples, len(X_test))
    rng = np.random.RandomState(RANDOM_STATE)
    positions = np.sort(rng.choice(len(X_test), size=n_samples, replace=False))
    logger.info("Explaining %d test reports (top-%d evidence each) ...",
                n_samples, top_k)

    # Precompute the retrieval index once (all training narratives).
    logger.info("Embedding %d training narratives ...", len(X_train))
    train_vecs = vectorizer.transform(X_train)
    train_index = X_train.index

    rows = []
    # Vectorize the sampled test documents in batches.
    sampled_texts = [X_test.iloc[p] for p in positions]
    test_vecs = vectorizer.transform(sampled_texts)

    for local, (pos, query_vec) in enumerate(zip(positions, test_vecs)):
        query_vec = query_vec.reshape(1, -1)
        predicted = model.predict(query_vec)[0]
        sims = cosine_similarity(query_vec, train_vecs).flatten()
        top = sims.argsort()[-top_k:][::-1]

        evidence = [
            _evidence_row(df, train_index, tr, sims[tr], rank)
            for rank, tr in enumerate(top, 1)
        ]
        true_label = str(y_test.iloc[pos])
        text = str(X_test.iloc[pos])
        rows.append({
            "test_position": int(pos),
            "input": text,
            "input_snippet": text[:120] + ("..." if len(text) > 120 else ""),
            "true_label": true_label,
            "predicted_label": str(predicted),
            "correct": bool(str(predicted) == true_label),
            "evidence": evidence,
        })
        if (local + 1) % 25 == 0 or (local + 1) == n_samples:
            logger.info("  explained %d/%d", local + 1, n_samples)

    return pd.DataFrame(rows)


if __name__ == "__main__":
    import sys
    import joblib
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)-8s | %(message)s")
    from config import DATASET_PATH, MODEL_PATH, VECTORIZER_PATH
    data = pd.read_csv(DATASET_PATH)
    m = joblib.load(MODEL_PATH)
    v = joblib.load(VECTORIZER_PATH)
    from preprocessor import add_processed_column
    from trainer import train_and_save
    data = add_processed_column(data, "narrative")
    _, _, Xtr, ytr, Xte, yte = train_and_save(data)
    out = batch_rag(m, v, data, Xtr, Xte, yte, n_samples=10)
    print(out[["input_snippet", "true_label", "predicted_label", "correct"]])
