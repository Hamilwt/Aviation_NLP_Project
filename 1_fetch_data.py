import pandas as pd
from datasets import load_dataset

def fetch_and_clean_data():
    print("Fetching open NASA ASRS dataset from Hugging Face...")
    
    # Using an ungated, public ASRS dataset (requires no login/token)
    try:
        dataset = load_dataset("elihoole/asrs-aviation-reports")
        df = pd.DataFrame(dataset["train"])
        
        # Dynamically find the narrative text and the anomaly/event category
        narrative_col = [col for col in df.columns if 'Narrative' in col][0]
        label_col = [col for col in df.columns if 'Anomaly' in col or 'Event' in col][0]
        
        # Rename columns to match the methodology in your project report
        df = df[[narrative_col, label_col]].rename(columns={
            narrative_col: 'Narrative', 
            label_col: 'human_factors_groundtruth'
        })
        
        # Drop blanks and limit to 2000 rows to ensure fast training tonight
        df = df.dropna()
        df = df.head(2000)
        
        # Save locally
        df.to_csv("real_asrs_dataset.csv", index=False)
        
        print(f"✅ Successfully downloaded and cleaned {len(df)} real ASRS reports!")
        print("Data saved locally as 'real_asrs_dataset.csv'")
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        print("Please check your internet connection and try again.")

if __name__ == "__main__":
    fetch_and_clean_data()