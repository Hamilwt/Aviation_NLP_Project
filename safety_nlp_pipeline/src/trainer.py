"""Step 3 - Train & cross-validate the classifier.

Model: TF-IDF (bigrams) -> SGDClassifier with loss="log_loss" (logistic
regression objective, trained incrementally). Hyperparameters (regularization
strength ``alpha`` and ``class_weight``) are selected with GridSearchCV so the
test set is never used for tuning.

The best model + vectorizer are persisted with joblib; the chosen parameters
are written to ``training_config.json`` for auditability in the report.
"""
import json
import logging

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline

from config import (CV_FOLDS, GRID_ALPHAS, GRID_CLASS_WEIGHTS, LABEL_COL,
                    MAX_FEATURES, MODEL_PATH, NGRAM_RANGE, PROCESSED_COL,
                    RANDOM_STATE, SGD_MAX_ITER, TEST_SIZE,
                    TRAIN_CONFIG_PATH, VECTORIZER_PATH)

logger = logging.getLogger(__name__)


def _build_pipeline() -> Pipeline:
    """TF-IDF + SGD(log-loss) pipeline with the fixed vocabulary settings."""
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            stop_words="english", max_features=MAX_FEATURES,
            ngram_range=NGRAM_RANGE)),
        ("sgd", SGDClassifier(
            loss="log_loss", max_iter=SGD_MAX_ITER, random_state=RANDOM_STATE)),
    ])


def train_and_save(df: pd.DataFrame):
    """Train + GridSearchCV the classifier and persist artifacts.

    Returns:
        (model, vectorizer, X_train, y_train, X_test, y_test)
    """
    if PROCESSED_COL not in df.columns:
        raise ValueError(f"Dataset missing '{PROCESSED_COL}' column - run the "
                         "preprocessing step first.")
    X = df[PROCESSED_COL]
    y = df[LABEL_COL]
    X = X[y.notna()]
    y = y.dropna()

    logger.info("Splitting %d rows (stratified, test_size=%.2f).",
                len(df), TEST_SIZE)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y)

    pipeline = _build_pipeline()
    param_grid = {
        "sgd__alpha": GRID_ALPHAS,
        "sgd__class_weight": GRID_CLASS_WEIGHTS,
    }
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True,
                         random_state=RANDOM_STATE)
    logger.info("GridSearchCV over %d combinations x %d folds "
                "(alpha=%s, class_weight=%s).",
                len(param_grid["sgd__alpha"]) * len(param_grid["sgd__class_weight"]),
                CV_FOLDS, GRID_ALPHAS, GRID_CLASS_WEIGHTS)
    grid = GridSearchCV(pipeline, param_grid, cv=cv, scoring="f1_weighted",
                        n_jobs=-1, verbose=0)
    grid.fit(X_train, y_train)

    best = grid.best_estimator_
    model = best.named_steps["sgd"]
    vectorizer = best.named_steps["tfidf"]
    logger.info("Best params: %s | best CV F1 (weighted): %.3f",
                grid.best_params_, grid.best_score_)

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    train_config = {
        "best_params": {str(k): str(v) for k, v in grid.best_params_.items()},
        "best_cv_f1_weighted": float(grid.best_score_),
        "n_classes": int(len(grid.classes_)),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
        "max_features": int(MAX_FEATURES),
        "ngram_range": list(NGRAM_RANGE),
        "test_size": float(TEST_SIZE),
        "cv_folds": int(CV_FOLDS),
        "random_state": int(RANDOM_STATE),
    }
    TRAIN_CONFIG_PATH.write_text(json.dumps(train_config, indent=2),
                                 encoding="utf-8")
    logger.info("Saved model -> %s | vectorizer -> %s | config -> %s",
                MODEL_PATH.name, VECTORIZER_PATH.name, TRAIN_CONFIG_PATH.name)
    return model, vectorizer, X_train, y_train, X_test, y_test


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s | %(levelname)-8s | %(message)s")
    from config import DATASET_PATH
    data = pd.read_csv(DATASET_PATH)
    from src.preprocessor import add_processed_column
    data = add_processed_column(data, "narrative")
    model, vec, Xtr, ytr, Xte, yte = train_and_save(data)
    print("trained OK")
