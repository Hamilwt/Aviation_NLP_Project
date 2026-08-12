"""Domain Preprocessing Engine: shared text-cleanup for the whole pipeline.

Standardizes unstructured aviation narrative text by lowercasing and
removing non-alphanumeric noise, so all steps (training + RAG) see
exactly the same vocabulary.
"""
import re

_NON_ALNUM = re.compile(r"[^a-z0-9\s]")


def preprocess_text(text) -> str:
    """Clean one aviation narrative: lowercase, strip punctuation/noise."""
    text = str(text).lower()
    return _NON_ALNUM.sub("", text)