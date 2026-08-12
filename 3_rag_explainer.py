import sys
import pandas as pd
import joblib
import re

sys.stdout.reconfigure(encoding='utf-8')
from sklearn.metrics.pairwise import cosine_similarity

def preprocess_text(text):
    """Same domain preprocessing used during training."""
    text = str(text).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

def explain_incident(new_report_text):
    print("\n[SYSTEM] Ingesting Raw ASRS Incident Report...\n")
    print(f"RAW TEXT: '{new_report_text}'\n")
    
    # 1. Load Dataset, Vectorizer, and Model
    df = pd.read_csv("real_asrs_dataset.csv")
    model = joblib.load("asrs_model.pkl")
    vectorizer = joblib.load("tfidf_vectorizer.pkl")
    
    # 2. Preprocess and Vectorize the New Report
    processed_text = preprocess_text(new_report_text)
    new_vector = vectorizer.transform([processed_text])
    
    # 3. Predict the Risk Category (Explainable Classification)
    predicted_risk = model.predict(new_vector)[0]
    
    print("-" * 60)
    print(f"⚠️ PREDICTED RISK CATEGORY: {predicted_risk.upper()}")
    print("-" * 60)
    
    # 4. RAG Retrieval (Semantic Search for Historical Evidence)
    print("\n🔍 RAG IN-CONTEXT PROMPTING (Retrieving Historical Evidence):")
    print("The system retrieved the following historical records to justify its classification:\n")
    
    # Vectorize the entire historical database to find similarities
    # (In a massive production system, this would be a dedicated Vector DB like Pinecone)
    historical_vectors = vectorizer.transform(df['Narrative'].apply(preprocess_text))
    similarities = cosine_similarity(new_vector, historical_vectors).flatten()
    
    # Get the indices of the top 3 most similar past incidents
    top_3_indices = similarities.argsort()[-3:][::-1]
    
    for rank, idx in enumerate(top_3_indices, 1):
        match_score = round(similarities[idx] * 100, 2)
        past_label = df.iloc[idx]['human_factors_groundtruth']
        # Truncate the narrative so it fits nicely on the screen
        past_incident = str(df.iloc[idx]['Narrative'])[:250] + "..." 
        
        print(f"--- Top Match #{rank} (Semantic Similarity: {match_score}%) ---")
        print(f"Verified Historical Risk: {past_label}")
        print(f"Highlighted Evidence Span: {past_incident}\n")
        
    print("✅ Pipeline Execution Complete.")

if __name__ == "__main__":
    # Simulating a new, unstructured text input from a pilot
    sample_pilot_narrative = "I was cleared for the ILS approach but misheard the altitude restriction due to heavy static on the radio frequency. I descended to 3000 feet instead of 5000. ATC immediately called and issued a climb instruction to avoid terrain. Checklist was complete."
    
    explain_incident(sample_pilot_narrative)