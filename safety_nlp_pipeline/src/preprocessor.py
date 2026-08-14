"""Step 2 - NLTK-based text preprocessing.

Applies, per document: tokenisation -> lowercasing -> keep alphanumeric ->
remove English stopwords -> WordNet lemmatisation. NLTK corpora are
auto-downloaded on first use.
"""
import logging

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

from config import PROCESSED_COL

logger = logging.getLogger(__name__)


def _ensure_nltk_data() -> None:
    """Download any missing NLTK corpora/tokenizers (no-op once present)."""
    try:
        stopwords.words("english")
    except LookupError:
        nltk.download("stopwords")
    try:
        word_tokenize("test")
    except LookupError:
        nltk.download("punkt")
        nltk.download("punkt_tab")
    try:
        WordNetLemmatizer().lemmatize("test")
    except LookupError:
        nltk.download("wordnet")


_ensure_nltk_data()

_STOPWORDS = set(stopwords.words("english"))
_LEMMATIZER = WordNetLemmatizer()


def preprocess_text(text) -> str:
    """Clean and normalize a single text using NLTK."""
    if not isinstance(text, str):
        text = str(text)
    tokens = word_tokenize(text.lower())
    tokens = [t for t in tokens if t.isalnum()]
    tokens = [t for t in tokens if t not in _STOPWORDS]
    tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]
    return " ".join(tokens)


def preprocess_dataset(series, log_every: int = 250) -> list[str]:
    """Preprocess every narrative in a pandas Series (with progress logging).

    Returns a list aligned with ``series.index``; assign it back onto the
    DataFrame as the ``processed_text`` column.
    """
    total = len(series)
    logger.info("Preprocessing %d narratives with NLTK "
                "(tokenize -> stopword removal -> lemmatize) ...", total)
    processed: list[str] = []
    for i, doc in enumerate(series):
        processed.append(preprocess_text(doc))
        if log_every and (i + 1) % log_every == 0:
            logger.info("  processed %d/%d", i + 1, total)
    return processed


def add_processed_column(df, source_col: str) -> "pd.DataFrame":
    """Convenience: returns ``df`` with a ``processed_text`` column added."""
    import pandas as pd
    df = df.copy()
    processed = preprocess_dataset(df[source_col])
    df[PROCESSED_COL] = pd.Series(processed, index=df.index)
    return df
