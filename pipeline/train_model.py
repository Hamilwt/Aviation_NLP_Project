"""Step 2 - Train the classification model (TF-IDF + Logistic Regression).

Trains on the cleaned dataset, evaluates on a held-out split and saves
the model + vectorizer artifacts for the RAG explainer.
"""
import sys

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

from pipeline.paths import (DEFAULT_DATASET, DEFAULT_MODEL, DEFAULT_VECTORIZER,
                            MAX_FEATURES)
from pipeline.preprocess import preprocess_text


def train_classifier(dataset=DEFAULT_DATASET, model_path=DEFAULT_MODEL,
                     vectorizer_path=DEFAULT_VECTORIZER, log=print,
                     on_progress=None) -> dict:
    """Train and save the classifier. Returns evaluation results."""
    if on_progress:
        on_progress("LOADING DATASET", 10)
    log(f"[train] Loading dataset: {dataset}")
    df = pd.read_csv(dataset)

    if on_progress:
        on_progress("DOMAIN PREPROCESSING", 25)
    log("[train] Applying domain preprocessing (lowercase + noise removal) ...")
    df["Processed_Narrative"] = df["Narrative"].apply(preprocess_text)

    X = df["Processed_Narrative"]
    y = df["human_factors_groundtruth"]

    if on_progress:
        on_progress("TF-IDF VECTORIZING (BIGRAMS)", 45)
    log("[train] Vectorizing with TF-IDF (bigrams capture terms like 'gear down') ...")
    vectorizer = TfidfVectorizer(
        stop_words="english", max_features=MAX_FEATURES, ngram_range=(1, 2),
    )
    X_vectorized = vectorizer.fit_transform(X)

    if on_progress:
        on_progress("SPLITTING TRAIN/TEST", 60)
    X_train, X_test, y_train, y_test = train_test_split(
        X_vectorized, y, test_size=0.2, random_state=42,
    )

    if on_progress:
        on_progress("TRAINING LOGISTIC REGRESSION", 80)
    log("[train] Fitting Logistic Regression (balanced class weights) ...")
    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(X_train, y_train)

    if on_progress:
        on_progress("EVALUATING + SAVING ARTIFACTS", 100)
    predictions = model.predict(X_test)
    report = classification_report(y_test, predictions, zero_division=0)
    accuracy = float((predictions == y_test).mean())

    model_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    log(f"[train] Saved model -> {model_path.name} | vectorizer -> {vectorizer_path.name}")
    return {
        "classes": int(len(model.classes_)),
        "accuracy": accuracy,
        "report": report,
        "model_path": model_path,
        "vectorizer_path": vectorizer_path,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    result = train_classifier()
    print(result["report"])