REPORT_CONFIGS = [
    {
        "group_name":      "Testing 1",
        "chat_id":         "-5002121002",   # ← your real chat_id from Step 3
        "filter_team":     ["Elite"],           # ← exact team name as in your sheet
        "filter_vertical": [],
        "report_types":    ["pending", "drops"],
    },
  
    {
        "group_name":      "Testing 2",
        "chat_id":         "-1001234567890",   # ← your real chat_id from Step 3
        "filter_team":     ["Team ID"],           # ← exact team name as in your sheet
        "filter_vertical": [],
        "report_types":    ["pending", "drops"],
    },
    # add one block per group
]
```

---

## STEP 7 — Create the GitHub Actions workflow

1. In your repository, create this folder structure:
```
.github/
  workflows/
    telegram_reports.yml
