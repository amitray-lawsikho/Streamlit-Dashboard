from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
# Import the exact functions from your app.py
from app import fetch_call_data, process_metrics_logic, get_metadata

app = FastAPI()

# Allow your Vercel app to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/metrics")
def get_dashboard_data(start_date: str = "2026-03-01", end_date: str = "2026-03-24"):
    # 1. Fetch raw data using your existing Streamlit function
    df_raw = fetch_call_data(start_date, end_date)
    
    # 2. Get the team mappings from your Google Sheet URL
    _, _, df_team_mapping = get_metadata()
    
    # 3. Apply your existing merge/filter logic
    df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
    df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
    
    # 4. Run your heavy "process_metrics_logic" function
    report_df, total_duration_agg = process_metrics_logic(df)
    
    # 5. Return the exact data your UI needs
    return {
        "summary": {
            "total_calls": len(df),
            "total_duration": total_duration_agg,
            "avg_prod_hrs": report_df["raw_prod_sec"].mean()
        },
        "table_data": report_df.to_dict(orient="records")
    }
