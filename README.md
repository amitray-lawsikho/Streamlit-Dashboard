# 📊 LawSikho & Skill Arbitrage — Internal Analytics Hub

> **Real-time intelligence across Calling, Revenue & Leads — built for the Sales & Operations team.**

[![Calling Metrics](https://img.shields.io/badge/🔔%20Calling%20Metrics-Live-orange?style=for-the-badge)](https://dashboard-lawsikho-call.streamlit.app/)
[![Revenue Metrics](https://img.shields.io/badge/💰%20Revenue%20Metrics-Live-green?style=for-the-badge)](https://dashboard-lawsikho-revenue.streamlit.app/)
[![Home Hub](https://img.shields.io/badge/🏠%20Analytics%20Hub-Live-blue?style=for-the-badge)](https://lawsikho-skillarbitrage.streamlit.app/)

---

## 🗂️ Table of Contents

1. [What Is This Project?](#-what-is-this-project)
2. [Live Dashboards](#-live-dashboards)
3. [Architecture at a Glance](#-architecture-at-a-glance)
4. [Data Sources](#-data-sources)
5. [Dashboard 1 — Analytics Home Hub](#-dashboard-1--analytics-home-hub)
6. [Dashboard 2 — Calling Metrics](#-dashboard-2--calling-metrics)
   - [How Data Is Fetched](#how-data-is-fetched)
   - [Core Metric Logic](#core-metric-logic)
   - [Tab 1: Dynamic Dashboard](#tab-1-dynamic-dashboard)
   - [Tab 2: Duration Report](#tab-2-duration-report)
   - [Tab 3: Insights & Leaderboard](#tab-3-insights--leaderboard)
   - [How Breaks Are Calculated](#how-breaks-are-calculated)
   - [Remarks / Flags Logic](#remarks--flags-logic)
   - [CDR Download](#cdr-download)
7. [Dashboard 3 — Revenue Metrics](#-dashboard-3--revenue-metrics)
   - [Caller Classification System](#caller-classification-system)
   - [Revenue Summary Metrics](#revenue-summary-metrics)
   - [Enrollment Summary Metrics](#enrollment-summary-metrics)
   - [Target & Achievement Logic](#target--achievement-logic)
   - [Till Day Target — Prorated Progress](#till-day-target--prorated-progress)
   - [Performance Tables](#performance-tables)
   - [Insights Tab & Team Leaderboards](#insights-tab--team-leaderboards)
8. [Key Terms Glossary](#-key-terms-glossary)
9. [Tech Stack](#-tech-stack)
10. [Project Structure](#-project-structure)
11. [Setup & Deployment](#-setup--deployment)
12. [Design Decisions](#-design-decisions)
13. [Credits](#-credits)

---

## 💡 What Is This Project?

This is a **suite of internal business intelligence dashboards** built for the Sales and Operations teams at [LawSikho](https://lawsikho.com) and Skill Arbitrage. It replaces manual reporting by pulling **live data from Google BigQuery** and presenting it through clean, interactive Streamlit web apps.

### The Problem It Solves

Before these dashboards, managers had to:
- Export raw call logs manually from Acefone and Ozonetel
- Maintain separate spreadsheets for revenue entries
- Calculate agent productivity, break times, and target achievement by hand
- Write and share multiple reports per day across WhatsApp or email

### What It Does Now

- ✅ Pulls **live call data** (Acefone + Ozonetel + Manual) from BigQuery
- ✅ Pulls **live revenue data** from the revenue BigQuery table
- ✅ Calculates agent-level performance: calls, durations, break patterns, productive hours
- ✅ Tracks revenue by enrollment type, caller classification, and target achievement
- ✅ Auto-generates insights, flags underperformers, and builds leaderboards
- ✅ Lets managers download raw CDR logs and summary CSVs with one click
- ✅ Generates a downloadable PDF reference guide explaining every metric

---

## 🌐 Live Dashboards

| Dashboard | URL | Status |
|---|---|---|
| 🏠 Analytics Home Hub | https://lawsikho-skillarbitrage.streamlit.app/ | 🟢 Live |
| 🔔 Calling Metrics | https://dashboard-lawsikho-call.streamlit.app/ | 🟢 Live |
| 💰 Revenue Metrics | https://dashboard-lawsikho-revenue.streamlit.app/ | 🟢 Live |
| 📊 Lead Metrics | _Coming Soon_ | 🚧 WIP |

---

## 🏗️ Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                             │
│                                                                 │
│  📞 Acefone API  →  BigQuery: acefone_calls                     │
│  📱 Ozonetel API →  BigQuery: ozonetel_calls                    │
│  ✏️  Manual Logs  →  BigQuery: manual_calls                     │
│  💰 Revenue CRM  →  BigQuery: revenue_sheet                     │
│  👥 Team Roster  →  Google Sheets (published CSV)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                     BigQuery Queries
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT APPS (Python)                      │
│                                                                 │
│  home.py          →  Analytics Hub (landing page)               │
│  calling.py       →  Calling Metrics Dashboard                  │
│  revenue.py       →  Revenue Metrics Dashboard                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                     Deployed on
                            │
                            ▼
               Streamlit Community Cloud
```

**BigQuery Project:** `studious-apex-488820-c3`  
**Dataset:** `crm_dashboard`

---

## 📦 Data Sources

### 1. `acefone_calls` — Acefone CDR
Raw call detail records from the Acefone telephony system. Each row = one call. Key columns used: `Call Date`, `call_owner`, `call_datetime` (call end time), `call_duration`, `status`, `direction`, `client_number`.

### 2. `ozonetel_calls` — Ozonetel CDR
Raw CDR from the Ozonetel dialler. Columns are differently named and are **renamed on-the-fly** during data fetch:

| Ozonetel Column | Renamed To |
|---|---|
| `AgentName` | `call_owner` |
| `StartTime` | `call_datetime` |
| `CallDate` | `Call Date` |
| `duration_sec` | `call_duration` |
| `Status` | `status` |
| `Type` | `direction` |
| `Disposition` | `reason` |

> ⚠️ **Important:** For Ozonetel, `call_datetime` is the **call start**, not the end. The code correctly handles this by computing `call_endtime = call_starttime + duration`.

### 3. `manual_calls` — Manually Logged Calls
Calls entered manually by agents and approved by a manager. These are tracked separately and flagged in the dashboard because they don't come from the dialler system. Key field: `Approved_By` (approver name).

### 4. `revenue_sheet` — Revenue Records
Each row = one fee payment. Key columns: `Date`, `Caller_name`, `Fee_paid`, `Course_Price`, `Enrollment` (type of transaction), `Source` (channel).

### 5. Google Sheets Team Roster (CSV)
A published Google Sheet with one row per agent per month. Contains: Caller Name, Team Name, Vertical, Designation (Academic Counselor / TL / ATL), Monthly Target, Analyst. Used to map raw agent names to canonical names and team metadata.

---

## 🏠 Dashboard 1 — Analytics Home Hub

**File:** `home.py` | **URL:** https://lawsikho-skillarbitrage.streamlit.app/

This is the **landing page** — a single-screen portal that links to all the dashboards. It is not interactive; it simply displays live status information and links.

### What It Shows

- **Logo banner** — LawSikho | Skill Arbitrage branding
- **Live stat cards** — Last updated timestamp and total record count for both Calling and Revenue data, fetched directly from BigQuery on page load
- **Dashboard cards** — Clickable cards for Calling Metrics, Revenue Metrics, and Lead Metrics (coming soon)

### How Navigation Works

Since Streamlit apps run inside iframes on some deployments, the JavaScript `goTo()` function attempts `window.top.location.href` first (to break out of the iframe), then `window.parent.location.href`, and finally `window.open()` as a fallback. This ensures navigation works correctly in all environments.

---

## 🔔 Dashboard 2 — Calling Metrics

**File:** `calling.py` | **URL:** https://dashboard-lawsikho-call.streamlit.app/

This is the primary operational dashboard for the calling team. It tracks every agent's call activity — how many calls they made, how long they spoke, when they started and stopped, how many breaks they took, and how productive they were.

---

### How Data Is Fetched

```
User clicks "Generate Report"
         │
         ▼
fetch_call_data(start_date, end_date)
         │
         ├─── BigQuery: acefone_calls  → df_ace
         ├─── BigQuery: ozonetel_calls → df_ozo (columns renamed)
         └─── BigQuery: manual_calls   → df_man
         │
         ▼
pd.concat([df_ace, df_ozo, df_man])  →  Combined df
         │
         ▼
Timezone conversion: UTC → IST (Asia/Kolkata)
         │
         ▼
call_starttime and call_endtime computed for each source:
  Acefone:  call_endtime = call_datetime (IST)
            call_starttime = call_endtime − duration
  Ozonetel: call_starttime = call_datetime (IST)
            call_endtime = call_starttime + duration
  Manual:   No timestamps (call_datetime = NaT)
         │
         ▼
Merge with team roster CSV on lowercase agent name
         │
         ▼
Apply filters (Team / Vertical / Name search)
         │
         ▼
process_metrics_logic(df_filtered)  →  Agent-level report_df
```

> ⚙️ All data is **cached for 120 seconds** using `@st.cache_data(ttl=120)` to avoid repeated BigQuery queries on every interaction.

---

### Core Metric Logic

All agent metrics are computed inside `process_metrics_logic()`. This function loops through each agent, then through each day that agent made calls.

#### What counts as a "qualifying call"?
Any call with **duration ≥ 180 seconds (3 minutes)**. Shorter calls do not count toward duration metrics.

#### What is "office hours"?
**10:00 AM to 8:00 PM IST** = 10 hours = 36,000 seconds. This is the reference window for all break and productive hours calculations.

#### How is call_starttime computed?

```python
# For Acefone — the stored timestamp IS the call end time:
call_endtime   = call_datetime (IST)
call_starttime = call_endtime − duration_seconds

# For Ozonetel — the stored timestamp IS the call start time:
call_starttime = call_datetime (IST)
call_endtime   = call_starttime + duration_seconds
```

---

### Tab 1: Dynamic Dashboard

Click **🚀 Generate Dynamic Report** in the sidebar to load this tab.

#### 🏆 Top 3 Performance Highlights

Three highlight cards at the top showing the single best agent in each dimension:

| Card | Logic |
|---|---|
| 🥇 Top Performer | Agent with highest total qualifying call duration (`raw_dur_sec`) |
| ✆ Highest Calls | Agent with highest total call count (all statuses) |
| 🗣️ Deep Engagement | Agent with most calls lasting 20+ minutes (≥ 1200 seconds) |

#### 📊 Summary KPI Cards

Eight aggregate metrics across all agents and sources:

| Metric | Formula |
|---|---|
| Total Calls | Count of all call rows after filters |
| Acefone Calls | Rows where `source = 'Acefone'` |
| Ozonetel Calls | Rows where `source = 'Ozonetel'` |
| Manual Calls | Rows where `source = 'Manual'` |
| Unique Leads | `df['unique_lead_id'].nunique()` — distinct phone numbers |
| Pick-Up Ratio | `Answered Calls / Total Calls × 100` |
| Active Callers | Count of distinct agents in the filtered dataset |
| Avg Prod Hrs | `mean(raw_prod_sec)` across all agents, shown as Xh Ym |

#### 📋 Agent Performance Table

One row per agent, sorted by Call Duration > 3 Mins (descending). Top 3 get medal emojis. A bold **TOTAL** row is appended at the bottom.

| Column | Definition |
|---|---|
| IN/OUT TIME | First call start (In) and last call end (Out) per day in IST |
| CALLER | Agent's canonical name from the team roster |
| TEAM | Team name from roster; "Others" if unmatched |
| TOTAL CALLS | All calls for this agent (answered + missed) |
| CALL STATUS | "X Ans / Y Unans" |
| PICK UP RATIO % | Answered / Total × 100 for this agent |
| CALLS > 3 MINS | Count of calls with duration ≥ 180 seconds |
| CALLS 15-20 MINS | Count of calls with 900 ≤ duration < 1200 seconds |
| 20+ MIN CALLS | Count of calls with duration ≥ 1200 seconds |
| CALL DURATION > 3 MINS | Sum of durations for qualifying calls (Xh Ym) |
| PRODUCTIVE HOURS | (10 hrs × active days) − total break time |
| BREAKS (≥ 15 MINS) | Per-day gap log with timestamps |
| REMARKS | Auto-flagged issues (see below) |

---

### Tab 2: Duration Report

Click **📅 Generate Duration Report** in the sidebar to load this tab.

This tab generates a **simplified, shareable** table per team — only duration-related columns, no breaks or remarks. Useful for sharing team-level performance without exposing sensitive individual data.

**Key behaviors:**
- Each team gets its own section and table
- Teams with zero qualifying duration are **skipped entirely**
- Agents flagged as **TL / ATL / AD / Team Lead / Team Leader** in the roster are separated into a single "TL Duration Report" section at the bottom
- TLs with ≤ 5 minutes of qualifying duration are excluded from the TL section
- Each team section includes a dedicated **Download CDR** button for that team's raw records only

---

### Tab 3: Insights & Leaderboard

This tab **auto-populates** after generating either report. No separate button needed.

#### Auto-Generated Insights (up to 6 cards)

| Insight | Trigger |
|---|---|
| 🏆 Top Team by Avg Duration | Team with highest average qualifying duration per agent |
| ⚠️ Focus Required — Manual Calls | Team with the most manual calls (potential data quality issue) |
| 🔔 Pick-Up Ratio Spread | Best vs worst team by answer rate, with gap in percentage points |
| 💬 Highest Deep-Engagement Rate | Team with highest % of 20+ min calls |
| ⏸️ Break Discipline Alert | Team with most agents flagged for excessive breaks |
| ⏱️ Lowest Productive Hours | Team with lowest average productive hours |

#### 🏅 Team Leaderboard

Only shown when no Team or Name filter is active. Aggregates all agents by team:

| Column | Formula |
|---|---|
| Total Dur (h) | Sum of qualifying duration in hours |
| Avg Dur/Agent (h) | Total Duration ÷ Agent count |
| Avg Prod Hrs (h) | Average productive hours per agent |
| 20+ Min Calls | Sum of 20+ minute calls |

---

### How Breaks Are Calculated

This is the most complex part of the dashboard. Here is how it works, step by step:

```
For each agent, for each day:

1. Sort all calls by start time.

2. Identify the office window: 10:00 AM → 8:00 PM IST

3. Check for a gap BEFORE the first call:
   Gap = first_call_start − 10:00 AM
   If gap ≥ 15 minutes → it's a break (also flags "Late Check-In")

4. Check gaps BETWEEN consecutive calls:
   For each pair of adjacent calls:
     act_start = max(current_call_end, 10:00 AM)
     act_end   = min(next_call_start, 8:00 PM)
     If act_end > act_start AND gap ≥ 15 minutes → it's a break

5. Check for a gap AFTER the last call:
   Gap = 8:00 PM − last_call_end
   If gap ≥ 15 minutes → it's a break (also flags "Early Check-Out")

6. Sum all break seconds for the day.

7. Productive Hours for the day = 36,000 seconds − total_break_seconds
```

> **Why 15 minutes?** Gaps under 15 minutes are considered normal transition time between calls and are not counted as breaks.

---

### Remarks / Flags Logic

Flags are computed **per day** and then de-duplicated across the date range:

| Flag | Trigger |
|---|---|
| Late Check-In | First call of the day starts after 10:15 AM IST |
| Early Check-Out | Last call of the day ends before 8:00 PM IST |
| Low Calls | Fewer than 40 qualifying calls (> 3 min) in a single day |
| Low Duration | Total qualifying duration < 3h 15m (11,700 seconds) in a day |
| Excessive Breaks | More than 2 breaks ≥ 15 minutes in a single day |
| Less Productive | Productive seconds < 5 hours (18,000 seconds) in a day |

---

### CDR Download

The **Download CDR** button exports a CSV of raw call records. Each row is one call. Columns included:

`client_number`, `call_datetime`, `call_starttime_clean`, `call_endtime_clean`, `call_duration`, `status`, `direction`, `service`, `reason`, `call_owner`, `Call Date`, `updated_at_ampm`, `Team Name`, `Vertical`, `Analyst`, `source`

---

## 💰 Dashboard 3 — Revenue Metrics

**File:** `revenue.py` | **URL:** https://dashboard-lawsikho-revenue.streamlit.app/

This dashboard tracks enrollment revenue, collection payments, and target achievement. It classifies every agent into one of three buckets based on their revenue type, then builds separate performance tables and leaderboards for each bucket.

---

### Caller Classification System

Not all people listed in the revenue data are actual agents. The system first **excludes pseudo-callers**, then classifies the rest.

#### Step 1: Exclude Non-Agents

```python
EXCLUDE_CALLERS = {'direct', 'bootcamp - direct'}
```

These are system placeholders for organic admissions and bootcamp admissions — not real sales agents. They are excluded from all agent performance tables.

#### Step 2: Classify Remaining Agents

```
For each real agent:

  calling_rev    = Enrollment Revenue + Balance Payment Revenue
  collection_rev = Bootcamp Collections + Community Collections

  IF team == 'Changemakers'     → always → Collection Agent
  ELIF has calling AND collection rev → Calling + Collection Agent
  ELIF has collection only      → Collection Agent
  ELSE                          → Calling Agent (default)
```

**Why separate tables?**
- A **Calling Agent** closes new admissions — their KPI is Calling Revenue vs Target
- A **Collection Agent** recovers pending fees — their KPI is Collection Revenue vs Target
- A **Calling + Collection Agent** does both — their KPI is Total Revenue vs Target

---

### Revenue Summary Metrics

These are the 7 KPI cards shown at the top of the Revenue Dashboard. They give a bird's-eye view of all money that came in during the selected period.

| Metric | What It Includes |
|---|---|
| **Total Revenue** | Everything below added together |
| **Calling Revenue** | Fee Paid where `Enrollment = New Enrollment` OR `Balance Payment`, caller ∉ {direct, bootcamp-direct} |
| **Bootcamp-Direct Revenue** | Fee Paid where `Enrollment = New Enrollment` AND `Caller = bootcamp-direct` |
| **Bootcamp-Collection Revenue** | Fee Paid where `Enrollment = Bootcamp Collections - Balance Payments` |
| **Community Revenue** | Community Collections + Other Revenue with community Source + New Enrollment by 'direct' with community Source |
| **Direct/Other Revenue** | Fee Paid where Caller = 'direct', Source has no 'community', Enrollment ∈ {Other Revenue, New Enrollment, Balance Payment} |
| **DNA / Not Updated Yet** | Fee Paid where `Enrollment` column is blank — not yet categorised |

> 💡 **DNA** = "Details Not Available" — rows that exist in the database but haven't been tagged with an enrollment type yet. These are tracked so nothing goes unaccounted.

---

### Enrollment Summary Metrics

These 5 cards count **only new admissions** — rows where `Enrollment = 'New Enrollment'`. Balance payments and collections are not counted here.

| Metric | Filter |
|---|---|
| Total Enrollments | All New Enrollment rows |
| Caller Enrollments | Caller ∉ {direct, bootcamp-direct} |
| Direct Enrollments | Caller = 'direct' AND Source has no 'community' |
| Bootcamp-Direct Enrollments | Caller = 'bootcamp-direct' |
| Community-Direct Enrollments | Caller = 'direct' AND Source contains 'community' |

---

### Target & Achievement Logic

Targets are pulled from the **Google Sheets team roster**, which has one row per agent per month. If the date range spans multiple months, the targets for all relevant months are summed.

```python
# For each agent:
total_target = sum of monthly targets across all months in selected range

# Achievement % depends on agent type:
Calling Agent:             Calling Revenue / Total Target × 100
Collection Agent:          Collection Revenue / Total Target × 100
Calling+Collection Agent:  Total Revenue / Total Target × 100
```

---

### Till Day Target — Prorated Progress

The "Till Day Target" tells you **how much an agent should have achieved by today**, not what their full monthly target is. This is a fairer measure of progress mid-month.

```python
working_days    = count of Mon–Fri days in the selected date range
months_count    = number of calendar months in the range
till_day_ratio  = min(working_days / (20 × months_count), 1.0)

# 20 working days is used as the standard month length

till_day_target = Total Target × till_day_ratio
```

**Example:** It's the 15th of March (10 working days elapsed so far). An agent has a ₹1,00,000 target. Their Till Day Target = ₹1,00,000 × (10 / 20) = ₹50,000. If they've already done ₹55,000 — they're ahead of pace.

---

### Performance Tables

Three separate tables are rendered — one per agent classification. All follow the same structure:

1. **Sorted** by primary revenue metric (descending)
2. **Top 3 agents** get medal emojis (🥇 🥈 🥉)
3. A bold **TOTAL** row is appended at the bottom
4. A **Download CSV** button appears below each table

#### Calling Revenue Performance Table (Table 1)

For agents with Calling Revenue > 0 and no collection revenue.

| Column | Definition |
|---|---|
| DESIGNATION | Role from roster: Academic Counselor, TL, ATL, etc. |
| TOTAL TARGET (₹) | Sum of monthly targets for selected range |
| TILL DAY TARGET (₹) | Prorated target (see above) |
| ENROLLMENTS | Count of New Enrollment rows |
| ENROLLMENT REV | Sum of Fee Paid for New Enrollment rows |
| BALANCE REV | Sum of Fee Paid for Balance Payment rows |
| CALLING REVENUE | Enrollment Rev + Balance Rev |
| ACHIEVEMENT % | Calling Revenue / Total Target × 100 |

#### Collection Caller Revenue Performance Table (Table 2)

For agents with Collection Revenue > 0 and no calling revenue. Changemakers team always appears here.

| Column | Definition |
|---|---|
| COMMUNITY COLLECTION | Fee Paid where `Enrollment = Community Collections - Balance Payments` |
| BOOTCAMP COLLECTION | Fee Paid where `Enrollment = Bootcamp Collections - Balance Payments` |
| COLLECTION REVENUE | Community + Bootcamp Collection |
| ACHIEVEMENT % | Collection Revenue / Total Target × 100 |

#### Calling + Collection Revenue Performance Table (Table 3)

For agents with BOTH calling and collection revenue (not Changemakers).

| Column | Definition |
|---|---|
| TOTAL REVENUE | Calling Revenue + Collection Revenue |
| ACHIEVEMENT % | Total Revenue / Total Target × 100 |

---

### Insights Tab & Team Leaderboards

The **🧠 Insights & Leaderboard** tab loads when "Generate Revenue Report" is clicked.

#### Auto-Generated Insights (up to 6)

| Insight | Logic |
|---|---|
| 🏆 Top Calling Revenue | Caller with highest `raw_calling_rev` |
| 🏦 Top Collection Revenue | Caller with highest `raw_collection_rev` |
| 🎓 Most Enrollments | Caller with highest enrollment count |
| 🎯 Best Target Achievement | Caller with highest achievement % (among those with a target) |
| ⚠️ Focus Required | Caller with lowest achievement % (< 60%) |
| 🚨 Zero Revenue / Below 50% | Callers with target but no revenue, or callers below 50% of target |

#### Three Team Leaderboard Tables

Each mirrors the three agent classification tables, but **aggregated by team**:

- **Caller Revenue Team Table** — sorted by total Calling Revenue, includes total target, till-day target, enrollments, and achievement %
- **Collection Team Table** — sorted by total Collection Revenue
- **Calling + Collection Team Table** — sorted by total Revenue

---

## 📖 Key Terms Glossary

| Term | Meaning |
|---|---|
| **Qualifying Call** | Any call ≥ 3 minutes (180 seconds). Used for all duration metrics. |
| **Office Hours** | 10:00 AM – 8:00 PM IST (10 hours = 36,000 seconds) |
| **Break** | A gap between consecutive calls ≥ 15 minutes (900 seconds) |
| **Productive Hours** | (10 hrs × active days) − total break time |
| **Merge Key** | Lowercase, stripped agent name — used to join call data with the team roster |
| **IST** | Indian Standard Time (UTC + 5:30) — all timestamps are converted to IST |
| **CDR** | Call Detail Record — one row per call in the raw export |
| **New Enrollment** | A fresh admission. Counted toward enrollment metrics and Calling Revenue |
| **Balance Payment** | Remaining fee from a prior enrollment. Not a new enrollment |
| **DNA** | Details Not Available — revenue rows without an enrollment type in BigQuery |
| **Changemakers** | A special team always routed to the Collection table regardless of revenue type |
| **direct** | Pseudo-caller for organic admissions. Excluded from agent performance tables |
| **bootcamp-direct** | Pseudo-caller for bootcamp direct admissions. Tracked separately |
| **Till Day Target** | Prorated daily target: Total Target × (Working Days elapsed / (20 × Months)) |
| **Late Check-In** | First call after 10:15 AM IST |
| **Early Check-Out** | Last call before 8:00 PM IST |
| **Low Calls** | Fewer than 40 qualifying calls (> 3 min) in a single day |
| **Low Duration** | Qualifying duration < 3h 15m (11,700 seconds) in a day |
| **Excessive Breaks** | More than 2 breaks ≥ 15 minutes in a single day |
| **Less Productive** | Productive seconds < 5 hours (18,000 seconds) in a day |

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Frontend | [Streamlit](https://streamlit.io/) — Python web app framework |
| Database | [Google BigQuery](https://cloud.google.com/bigquery) — cloud data warehouse |
| Team Roster | Google Sheets (published as CSV) |
| Authentication | Google Service Account JSON (via Streamlit Secrets) |
| Data Processing | [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/) |
| PDF Generation | [ReportLab](https://www.reportlab.com/) |
| Timezone Handling | [pytz](https://pypi.org/project/pytz/) |
| Deployment | [Streamlit Community Cloud](https://streamlit.io/cloud) |
| Caching | `@st.cache_data(ttl=120)` — 2-minute cache on all BigQuery queries |

---

## 📁 Project Structure

```
├── home.py                  # Analytics Hub landing page
├── calling.py               # Calling Metrics Dashboard
├── revenue.py               # Revenue Metrics Dashboard
├── requirements.txt         # Python dependencies
├── .streamlit/
│   └── secrets.toml         # GCP credentials (NOT committed to Git)
└── README.md                # This file
```

### `requirements.txt`

```
streamlit
google-cloud-bigquery
google-auth
pandas
numpy
pytz
reportlab
db-dtypes
```

---

## ⚙️ Setup & Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Google Cloud Credentials

Create a Service Account in Google Cloud with BigQuery Data Viewer permissions. Download the JSON key file.

For **local development**, create `.streamlit/secrets.toml`:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

> ⚠️ **Never commit `secrets.toml` to Git.** Add it to `.gitignore`.

For **Streamlit Cloud deployment**, paste the same key-value pairs into the app's Secrets panel in the Streamlit Cloud dashboard.

### 4. Run Locally

```bash
# Run any of the three apps
streamlit run home.py
streamlit run calling.py
streamlit run revenue.py
```

### 5. Deploy to Streamlit Cloud

1. Push the repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Connect your GitHub repo
4. Set the main file path (e.g., `calling.py`)
5. Add your GCP secrets in the Secrets panel
6. Click Deploy

---

## 🎨 Design Decisions

### Why two separate color themes?

The **Calling Metrics** dashboard uses a **warm amber/orange gradient** header (`#1c0700 → #7c2d12`) to signal urgency and operational focus.

The **Revenue Metrics** dashboard uses a **deep forest green gradient** header (`#064e3b → #065f46`) to signal financial stability and growth.

This makes it immediately obvious at a glance which dashboard you're on — especially useful when both are open in different tabs.

### Why HTML over image downloads for reports?

Earlier versions had separate buttons for downloading reports as screenshots or JPGs. This was replaced with a single **HTML download** that generates a self-contained file with all three tabs. HTML is:
- **Shareable** — opens in any browser with no software needed
- **Readable** — text is selectable and searchable, unlike images
- **Lightweight** — no third-party image rendering library required

### Why cache at 120 seconds?

BigQuery charges per byte scanned. Caching for 2 minutes means that if multiple managers load the dashboard simultaneously, only one query is sent to BigQuery instead of one per user per click. This keeps costs low while keeping data fresh enough for operational use.

### Why prorated Till Day Target?

A raw "Achievement %" against a full monthly target on the 5th of the month is meaningless — nobody expects 100% achievement in the first 5 days. The prorated Till Day Target adjusts the benchmark to the current date, making the number immediately actionable.

---

## 👤 Credits

**Designed and Developed by:** Amit Ray  
**Email:** amitray@lawsikho.com  
**Organisation:** LawSikho & Skill Arbitrage  

> *For internal use of the Sales and Operations team only. All rights reserved.*

---

<div align="center">

**LawSikho** &nbsp;|&nbsp; **Skill Arbitrage**  
*India Learning 📖 India Earning*

</div>
