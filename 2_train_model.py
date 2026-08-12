import sys
import pandas as pd
import re

sys.stdout.reconfigure(encoding='utf-8')
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import joblib

def preprocess_text(text):
    """
    Domain Preprocessing Engine:
    Cleans unstructured aviation text by standardizing casing and 
    removing non-alphanumeric noise to isolate the core vocabulary.
    """
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def train_classifier():
    print("Loading real ASRS dataset...")
    df = pd.read_csv("real_asrs_dataset.csv")
    
    print("Applying Domain Preprocessing...")
    df['Processed_Narrative'] = df['Narrative'].apply(preprocess_text)
    
    X = df['Processed_Narrative']
    y = df['human_factors_groundtruth']
    
    print("Vectorizing text (converting aviation language to numerical semantic vectors)...")
    # We use TF-IDF with bigrams (ngram_range=(1,2)) to capture 2-word aviation terms (e.g., "gear down")
    vectorizer = TfidfVectorizer(stop_words='english', max_features=3000, ngram_range=(1, 2))
    X_vectorized = vectorizer.fit_transform(X)
    
    # Split data (80% training, 20% testing)
    X_train, X_test, y_train, y_test = train_test_split(X_vectorized, y, test_size=0.2, random_state=42)
    
    print("Training the Classification Model...")
    # 'balanced' weights help handle rare anomaly categories
    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(X_train, y_train)
    
    print("\n--- Model Evaluation ---")
    predictions = model.predict(X_test)
    print(classification_report(y_test, predictions, zero_division=0))
    
    # Save the semantic vectorizer and trained model for our RAG system
    joblib.dump(model, "asrs_model.pkl")
    joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
    print("\n✅ Domain Vectorizer and Model saved successfully as .pkl files!")

if __name__ == "__main__":
    train_classifier()