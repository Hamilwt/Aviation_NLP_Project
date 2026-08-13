"""Step 2 - Train the classification model (TF-IDF + SGD/Logistic Regression).

Every NLP stage reports REAL progress tied to actual work done:

  * PREPROCESSING  - one NLTK tokenize/lemmatize pass per document, the
                     progress bar advances with every processed narrative.
  * VECTORIZING    - TF-IDF (bigrams) fitted on the processed corpus.
  * TRAINING       - SGD (log-loss ~ logistic regression) trained with
                     partial_fit over shuffled minibatches and epochs; the
                     bar advances after every real minibatch fit.

The model + vectorizer are saved for the RAG explainer.
"""
import sys
from math import ceil

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_class_weight

from pipeline.paths import (DEFAULT_DATASET, DEFAULT_MODEL, DEFAULT_VECTORIZER,
                            LABEL_COL, MAX_FEATURES, NARRATIVE_COL)
from pipeline.preprocess import preprocess_text

EPOCHS = 3
BATCH_SIZE = 256


def train_classifier(dataset=DEFAULT_DATASET, model_path=DEFAULT_MODEL,
                     vectorizer_path=DEFAULT_VECTORIZER, log=print,
                     on_progress=None) -> dict:
    """Train and save the classifier. Returns evaluation results."""
    if on_progress:
        on_progress("LOADING DATASET", 5)
    log(f"[train] Loading dataset: {dataset}")
    df = pd.read_csv(dataset)
    if NARRATIVE_COL not in df.columns or LABEL_COL not in df.columns:
        raise ValueError(f"Dataset missing '{NARRATIVE_COL}'/'{LABEL_COL}' "
                         f"columns: {list(df.columns)}")
    df = df.dropna(subset=[NARRATIVE_COL, LABEL_COL])

    # ---- 1) real per-document NLTK preprocessing --------------------------
    total = len(df)
    processed: list[str] = []
    for i, doc in enumerate(df[NARRATIVE_COL]):
        processed.append(preprocess_text(doc))
        if on_progress and i % 25 == 0:
            on_progress(f"PREPROCESSING {i + 1}/{total} (NLTK)",
                        5 + int(40 * (i + 1) / total))
    log(f"[train] Preprocessed {total} narratives with NLTK "
        f"(tokenize -> stopword removal -> lemmatize).")

    X = processed
    y = df[LABEL_COL]

    # ---- 2) TF-IDF vectorization -------------------------------------------
    if on_progress:
        on_progress("TF-IDF VECTORIZING (BIGRAMS)", 45)
    log("[train] Vectorizing with TF-IDF (bigrams capture domain terms "
        "like 'gear down' / 'load shed' / 'transmission line') ...")
    vectorizer = TfidfVectorizer(
        stop_words="english", max_features=MAX_FEATURES, ngram_range=(1, 2),
    )
    X_vec = vectorizer.fit_transform(X)

    if on_progress:
        on_progress("SPLITTING TRAIN/TEST", 55)
    X_train, X_test, y_train, y_test = train_test_split(
        X_vec, y, test_size=0.2, random_state=42, stratify=y,
    )

    # ---- 3) real minibatch SGD training ------------------------------------
    if on_progress:
        on_progress("TRAINING SGD CLASSIFIER", 60)
    log(f"[train] Fitting SGD (log-loss) over {EPOCHS} epochs, "
        f"{BATCH_SIZE}-doc minibatches, balanced class weights ...")
    model = SGDClassifier(loss="log_loss", max_iter=1, tol=None,
                          shuffle=True, random_state=42)
    classes = np.unique(y_train)
    weights = compute_class_weight("balanced", classes=classes, y=y_train)
    weight_map = dict(zip(classes, weights))
    sample_weight = np.array([weight_map[c] for c in y_train])

    n = X_train.shape[0]
    steps_per_epoch = ceil(n / BATCH_SIZE)
    total_steps = steps_per_epoch * EPOCHS
    done = 0
    rng = np.random.RandomState(42)
    order = rng.permutation(n)
    for epoch in range(1, EPOCHS + 1):
        for start in range(0, n, BATCH_SIZE):
            sel = order[start:start + BATCH_SIZE]
            model.partial_fit(
                X_train[sel], y_train.iloc[sel], classes=classes,
                sample_weight=sample_weight[sel],
            )
            done += 1
            if on_progress:
                on_progress(f"EPOCH {epoch}/{EPOCHS}  BATCH {done}/"
                            f"{total_steps}", 60 + int(35 * done / total_steps))

    # ---- 4) evaluate + save -------------------------------------------------
    if on_progress:
        on_progress("EVALUATING + SAVING ARTIFACTS", 100)
    predictions = model.predict(X_test)
    report = classification_report(y_test, predictions, zero_division=0)
    accuracy = float((predictions == y_test).mean())

    model_path.parent.mkdir(exist_ok=True)
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)

    log(f"[train] Saved model -> {model_path.name} | "
        f"vectorizer -> {vectorizer_path.name}")
    log(f"[train] Accuracy {accuracy:.1%} over {len(model.classes_)} classes.")
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
