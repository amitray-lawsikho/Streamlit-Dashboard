from fastapi import FastAPI
from google.cloud import bigquery
import pandas as pd
import os
import json
import pytz
from datetime import datetime, time, timedelta

app = FastAPI()

def get_client():
    # Pulls credentials from Vercel Environment Variables
    info = json.loads(os.environ.get("GCP_SERVICE_ACCOUNT"))
    return bigquery.Client.from_service_account_info(info)

@app.get("/api/metrics")
def get_metrics(start_date: str = None, end_date: str = None):
    client = get_client()
    ist = pytz.timezone("Asia/Kolkata")
    
    # Default to today if no dates provided
    if not start_date:
        start_date = datetime.now(ist).strftime('%Y-%m-%d')
        end_date = start_date

    # 1. Fetch Data (Reuse your exact SQL logic)
    query = f"""
        SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` 
        WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'
    """
    df = client.query(query).to_dataframe()
    
    # 2. Process Logic (Your exact Break Calculation)
    # [Insert your process_metrics_logic function here]
    # For this example, we return the agents_list you already built
    
    agents_list, total_dur = [], 0 # This would be the result of your logic
    
    # Standardize the output for the Frontend
    return {
        "logs": agents_list,
        "teams": sorted(list(set([a['TEAM'] for a in agents_list]))),
        "metrics": {
            "TOTAL CALLS": sum([a['TOTAL CALLS'] for a in agents_list]),
            "PICK UP RATIO %": "60%", # Example
            "CALL DURATION > 3 MINS": "45h 20m",
            "PRODUCTIVE HOURS": "120h"
        }
    }
