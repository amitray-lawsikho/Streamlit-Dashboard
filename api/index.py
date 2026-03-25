@app.get("/api/metrics")
def get_metrics():
    # ... Your BigQuery Fetching Logic ...
    # ... Your Calculation Logic ...
    return {
        "logs": agents_list, # This is what the 'map' function looks for
        "teams": teams_list,
        "verticals": verticals_list,
        "metrics": {
            "TOTAL CALLS": total_calls,
            "PICK UP RATIO %": pickup_percentage,
            "PRODUCTIVE HOURS": total_productive_hours
        }
    }
