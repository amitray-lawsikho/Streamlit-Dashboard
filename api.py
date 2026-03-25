from fastapi import FastAPI
import pandas as pd
# Import your existing BigQuery logic from app.py here

app = FastAPI()

@app.get("/api/metrics")
def get_metrics():
    # Call your existing BigQuery function
    df = get_bigquery_data() 
    # Return it as JSON so the Vercel UI can read it
    return df.to_dict(orient="records")
