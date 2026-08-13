"""NLTK-based preprocessing: tokenization, stopword removal, lemmatization."""
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Ensure NLTK data is downloaded
def _ensure_nltk_data():
    try:
        stopwords.words('english')
    except LookupError:
        nltk.download('stopwords')
    try:
        word_tokenize("test")
    except LookupError:
        nltk.download('punkt')
        nltk.download('punkt_tab')
    try:
        WordNetLemmatizer().lemmatize("test")
    except LookupError:
        nltk.download('wordnet')

_ensure_nltk_data()

_STOPWORDS = set(stopwords.words('english'))
_LEMMATIZER = WordNetLemmatizer()

def preprocess_text(text) -> str:
    """
    Clean and normalize text using NLTK:
    - Tokenize
    - Lowercase
    - Remove stopwords
    - Lemmatize
    - Remove non-alphanumeric tokens (optional, keep alphanumeric only)
    """
    if not isinstance(text, str):
        text = str(text)
    tokens = word_tokenize(text.lower())
    # Keep only alphanumeric tokens (optional, but helps with noise)
    tokens = [t for t in tokens if t.isalnum()]
    tokens = [t for t in tokens if t not in _STOPWORDS]
    tokens = [_LEMMATIZER.lemmatize(t) for t in tokens]
    return " ".join(tokens)