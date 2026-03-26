import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import pytz
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ═══════════════════════════════════════════════════
# 1. CLOUD CREDENTIALS SETUP
# ═══════════════════════════════════════════════════
if "gcp_service_account" in st.secrets:
    info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    SERVICE_ACCOUNT_FILE = "/content/drive/MyDrive/Lawsikho/credentials/bigquery_key.json"
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        client = bigquery.Client()
    else:
        st.error("Credentials not found!")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"

# ═══════════════════════════════════════════════════
# 2. PAGE CONFIGURATION
# ═══════════════════════════════════════════════════
st.set_page_config(
    layout="wide",
    page_title="CallerWise · Duration Intelligence",
    page_icon="📡",
    initial_sidebar_state="expanded"
)

# ═══════════════════════════════════════════════════
# 3. DESIGN SYSTEM — CSS
# ═══════════════════════════════════════════════════
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">

<style>
/* ── ROOT TOKENS ── */
:root {
    /* Use Streamlit variables to adapt to Light/Dark mode automatically */
    --bg-base:      var(--pd-background-color, #080c14);
    --bg-surface:   var(--pd-secondary-background-color, #0d1321);
    --text-primary: var(--pd-text-color, #f1f5f9);
    --text-muted:   #8899ac;
    --border:       #1e2d45;
    
    /* Branding Colors stay constant */
    --accent-blue:  #3b82f6;
    --accent-amber: #f59e0b;
    --accent-green: #10b981;
    --accent-red:   #ef4444;
}

/* ── GLOBAL RESET ── */
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
.ai-card {
    background: var(--bg-surface); /* Adapts to theme */
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    color: var(--text-primary) !important;
}
/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

/* ── HEADER ── */
header[data-testid="stHeader"] { 
    background: var(--bg-base) !important; 
    border-bottom: 1px solid var(--border) !important;
}
footer { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none !important; }

/* ── MAIN CONTAINER ── */
[data-testid="stMainViewContainer"] { 
    padding-top: 0 !important; 
    background-color: var(--bg-base) !important;
}
[data-testid="stAppViewBlockContainer"] {
    padding: 1.5rem 2rem !important;
    max-width: 100% !important;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: var(--bg-surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
[data-testid="stSidebar"] .stMarkdown h2 {
    font-family: var(--font-display) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1rem;
}
[data-testid="stSidebar"] .stButton > button {
    width: 100% !important;
    background: var(--accent-blue) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: var(--font-display) !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    padding: 0.65rem 1rem !important;
    transition: all 0.2s ease !important;
    margin-bottom: 0.5rem;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #2563eb !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 20px #3b82f644 !important;
}

/* ── INPUTS ── */
.stTextInput > div > div > input,
.stMultiSelect > div > div,
.stDateInput > div > div > input {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}
.stMultiSelect [data-baseweb="tag"] {
    background: var(--accent-blue) !important;
    color: #fff !important;
}

/* ── TABS ── */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--bg-surface) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [role="tab"] {
    font-family: var(--font-display) !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    padding: 0.85rem 1.5rem !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    background: transparent !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] [role="tab"]:hover { color: var(--text-primary) !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--accent-amber) !important;
    border-bottom: 2px solid var(--accent-amber) !important;
    background: transparent !important;
}
[data-testid="stTabs"] [role="tabpanel"] {
    background: var(--bg-base) !important;
    padding: 1.5rem 0 !important;
}

/* ── METRICS ── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 1rem 1.25rem !important;
    position: relative !important;
    overflow: hidden !important;
    transition: border-color 0.2s !important;
}
[data-testid="stMetric"]:hover { border-color: var(--accent-blue) !important; }
[data-testid="stMetric"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
}
[data-testid="stMetricLabel"] {
    font-family: var(--font-display) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--font-mono) !important;
    font-size: 1.6rem !important;
    font-weight: 500 !important;
    color: var(--text-primary) !important;
    line-height: 1.2 !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] thead tr th {
    background: #0a0e1a !important;
    color: var(--accent-amber) !important;
    font-family: var(--font-display) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    font-weight: 700 !important;
    white-space: normal !important;
    word-wrap: break-word !important;
    text-align: center !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 12px 8px !important;
}
[data-testid="stDataFrame"] tbody tr td {
    font-family: var(--font-body) !important;
    font-size: 0.82rem !important;
    color: var(--text-primary) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 8px !important;
}
[data-testid="stDataFrame"] tbody tr:hover td {
    background: var(--bg-card-alt) !important;
}

/* ── DIVIDER ── */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* ── ALERTS / WARNINGS ── */
[data-testid="stAlert"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-body) !important;
}

/* ── DOWNLOAD BUTTON ── */
.stDownloadButton > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    font-family: var(--font-display) !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.06em !important;
    border-radius: 6px !important;
    transition: all 0.2s !important;
    padding: 0.4rem 1rem !important;
}
.stDownloadButton > button:hover {
    border-color: var(--accent-amber) !important;
    color: var(--accent-amber) !important;
    background: #f59e0b0d !important;
}

/* ── SPINNER ── */
[data-testid="stSpinner"] > div { 
    border-color: var(--accent-blue) var(--bg-card) var(--bg-card) !important; 
}

/* ── CUSTOM COMPONENTS ── */
.cw-page-header {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    padding: 1.5rem 0 1rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}
.cw-page-header .logo-block { display: flex; align-items: center; gap: 1rem; }
.cw-page-header .logo-icon {
    width: auto;
    height: auto;
    background: none;
    border-radius: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
}
.cw-page-header h1 {
    font-family: var(--font-display) !important;
    font-size: 1.7rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
    line-height: 1 !important;
}
.cw-page-header .subtitle {
    font-family: var(--font-body);
    font-size: 0.75rem;
    color: var(--text-muted);
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-top: 3px;
}
.cw-meta-pill {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 0.35rem 0.9rem;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}
.cw-meta-pill .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--accent-green);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}
.cw-section-title {
    font-family: var(--font-display) !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.18em !important;
    text-transform: uppercase !important;
    color: var(--text-muted) !important;
    display: flex !important;
    align-items: center !important;
    gap: 0.6rem !important;
    margin: 1.5rem 0 0.75rem !important;
}
.cw-section-title::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}
.cw-team-badge {
    display: inline-block;
    background: linear-gradient(135deg, #1e3a5f, #0f2340);
    border: 1px solid var(--accent-blue);
    color: var(--accent-cyan);
    font-family: var(--font-display);
    font-size: 0.82rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.5rem 1.2rem;
    border-radius: 6px;
    margin: 1.5rem 0 0.75rem;
}
.ai-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.ai-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-amber), #f97316, var(--accent-amber));
    background-size: 200% 100%;
    animation: shimmer 3s linear infinite;
}
@keyframes shimmer {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
}
.ai-card h4 {
    font-family: var(--font-display) !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: var(--accent-amber) !important;
    margin: 0 0 0.75rem !important;
}
.ai-card p {
    font-family: var(--font-body) !important;
    font-size: 0.88rem !important;
    line-height: 1.65 !important;
    color: var(--text-primary) !important;
    margin: 0 !important;
}
.insight-bullet {
    display: flex;
    gap: 0.75rem;
    padding: 0.6rem 0;
    border-bottom: 1px solid var(--border);
    align-items: flex-start;
    font-family: var(--font-body);
    font-size: 0.85rem;
    color: var(--text-primary);
    line-height: 1.5;
}
.insight-bullet:last-child { border-bottom: none; }
.insight-bullet .tag {
    min-width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.65rem;
    font-weight: 700;
    font-family: var(--font-mono);
    flex-shrink: 0;
    margin-top: 1px;
}
.tag-warn { background: #f59e0b22; color: var(--accent-amber); border: 1px solid var(--accent-amber); }
.tag-good { background: #10b98122; color: var(--accent-green); border: 1px solid var(--accent-green); }
.tag-info { background: #3b82f622; color: var(--accent-blue); border: 1px solid var(--accent-blue); }
.tag-risk { background: #ef444422; color: var(--accent-red); border: 1px solid var(--accent-red); }

/* Score ring placeholder */
.score-ring {
    display: flex; align-items: center; justify-content: center;
    flex-direction: column;
    width: 120px; height: 120px;
    border-radius: 50%;
    border: 4px solid var(--border);
    background: var(--bg-card);
    margin: 0 auto 0.5rem;
}
.score-ring .val {
    font-family: var(--font-mono);
    font-size: 1.6rem;
    font-weight: 500;
    color: var(--accent-cyan);
}
.score-ring .lbl {
    font-family: var(--font-display);
    font-size: 0.6rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
}

/* Sidebar logo */
.sb-logo {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 0 1.25rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.25rem;
}
.sb-logo .icon {
    width: auto;
    height: auto;
    background: none;
    border-radius: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
}
.sb-logo .name {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-primary);
}
.sb-logo .tagline {
    font-size: 0.65rem;
    color: var(--text-muted);
    letter-spacing: 0.04em;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# 4. GLOBAL HELPER FUNCTIONS  (unchanged logic)
# ═══════════════════════════════════════════════════
def style_total(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #0a0e1a; color: #f59e0b'] * len(row)
    if row.name == 0:
        return ['background-color: #2a1f00; color: #fbbf24; font-weight: bold'] * len(row)
    elif row.name == 1:
        return ['background-color: #1a1f2a; color: #94a3b8; font-weight: bold'] * len(row)
    elif row.name == 2:
        return ['background-color: #1f1510; color: #c47b3d; font-weight: bold'] * len(row)
    return [''] * len(row)

def style_static(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #0a0e1a; color: #f59e0b'] * len(row)
    return [''] * len(row)

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    tm = int(round(total_seconds / 60))
    return f"{tm // 60}h {tm % 60}m"

def get_display_gap_seconds(start_time, end_time):
    if pd.isna(start_time) or pd.isna(end_time): return 0
    s, e = start_time.replace(second=0, microsecond=0), end_time.replace(second=0, microsecond=0)
    return (e - s).total_seconds()

# ═══════════════════════════════════════════════════
# 5. DATA FETCHING (unchanged logic)
# ═══════════════════════════════════════════════════
@st.cache_data(ttl=120, show_spinner=False)
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip()
    df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
    teams = sorted(df_meta['Team Name'].dropna().unique())
    verticals = sorted(df_meta['Vertical'].dropna().unique())
    return teams, verticals, df_meta

@st.cache_data(ttl=120, show_spinner=False)
def get_global_last_update():
    query = """
    WITH combined AS (
        SELECT updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT StartTime as updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
    )
    SELECT updated_at_ampm FROM combined WHERE updated_at IS NOT NULL ORDER BY updated_at DESC LIMIT 1
    """
    try:
        res = client.query(query).to_dataframe()
        return str(res['updated_at_ampm'].iloc[0]) if not res.empty else "N/A"
    except:
        return "N/A"

@st.cache_data(ttl=120, show_spinner=False)
def get_available_dates():
    query = """
    SELECT MIN(min_d) as min_date, MAX(max_d) as max_date FROM (
        SELECT MIN(`Call Date`) as min_d, MAX(`Call Date`) as max_d FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT MIN(CallDate) as min_d, MAX(CallDate) as max_d FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
    )
    """
    df_dates = client.query(query).to_dataframe()
    if not df_dates.empty and not pd.isna(df_dates['min_date'].iloc[0]):
        return df_dates['min_date'].iloc[0], df_dates['max_date'].iloc[0]
    return date.today(), date.today()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_call_data(start_date, end_date):
    q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
    df_ace = client.query(q_ace).to_dataframe()
    if not df_ace.empty:
        df_ace['source'] = 'Acefone'
        df_ace['unique_lead_id'] = df_ace['client_number']

    q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
    df_ozo = client.query(q_ozo).to_dataframe()
    if not df_ozo.empty:
        df_ozo['unique_lead_id'] = df_ozo['phone_number']
        df_ozo = df_ozo.rename(columns={
            'CallID': 'call_id', 'AgentName': 'call_owner', 'phone_number': 'client_number',
            'StartTime': 'call_datetime', 'CallDate': 'Call Date', 'duration_sec': 'call_duration',
            'Status': 'status', 'Type': 'direction', 'Disposition': 'reason'
        })
        df_ozo['status'] = df_ozo['status'].str.lower().replace({'unanswered': 'missed'})
        df_ozo['direction'] = df_ozo['direction'].str.lower().replace({'manual': 'outbound'})
        df_ozo['source'] = 'Ozonetel'

    q_man = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.manual_calls` WHERE Call_Date BETWEEN '{start_date}' AND '{end_date}'"
    df_man = client.query(q_man).to_dataframe()
    if not df_man.empty:
        df_man['unique_lead_id'] = df_man['client_number']
        df_man = df_man.rename(columns={'Call_Date': 'Call Date', 'Approved_By': 'reason'})
        df_man['status'] = 'answered'
        df_man['direction'] = 'outbound'
        df_man['source'] = 'Manual'
        df_man['call_datetime'] = pd.NaT

    df = pd.concat([df_ace, df_ozo, df_man], ignore_index=True)
    if not df.empty:
        df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
        df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
        df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
        df['call_starttime_clean'] = df['call_starttime'].dt.tz_localize(None)
        df['call_endtime_clean'] = df['call_endtime'].dt.tz_localize(None)
    return df

# ═══════════════════════════════════════════════════
# 6. CORE METRICS LOGIC (unchanged)
# ═══════════════════════════════════════════════════
def process_metrics_logic(df_filtered):
    agents_list = []
    total_duration_agg = 0
    ist_tz = pytz.timezone("Asia/Kolkata")

    for owner, agent_group in df_filtered.groupby('call_owner'):
        total_ans, total_miss, total_calls = 0, 0, 0
        total_above_3min, total_mid_calls, total_long_calls, agent_valid_dur = 0, 0, 0, 0
        total_break_sec_all_days, total_active_days = 0, 0
        daily_io_list, daily_break_list, all_issues = [], [], []

        for c_date, day_group in agent_group.groupby('Call Date'):
            timed_group = day_group[day_group['call_starttime'].notna()].sort_values('call_starttime')
            total_active_days += 1
            ans = len(day_group[day_group['status'].str.lower() == 'answered'])
            miss = len(day_group[day_group['status'].str.lower() == 'missed'])
            total_ans += ans; total_miss += miss; total_calls += len(day_group)

            total_above_3min += len(day_group[day_group['call_duration'] >= 180])
            total_mid_calls += len(day_group[(day_group['call_duration'] >= 900) & (day_group['call_duration'] < 1200)])
            total_long_calls += len(day_group[day_group['call_duration'] >= 1200])
            day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
            agent_valid_dur += day_dur

            if timed_group.empty: continue

            first_call_start = timed_group['call_starttime'].min()
            last_call_end = timed_group['call_endtime'].max()

            daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {first_call_start.strftime('%I:%M %p')} · Out {last_call_end.strftime('%I:%M %p')}")

            start_office = ist_tz.localize(datetime.combine(c_date, time(10, 0)))
            end_office = ist_tz.localize(datetime.combine(c_date, time(20, 0)))

            if first_call_start > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
            if last_call_end < end_office: all_issues.append("Early Check-Out")

            day_breaks, day_break_sec = [], 0

            if first_call_start > start_office:
                g_start_sec = get_display_gap_seconds(start_office, first_call_start)
                if g_start_sec >= 900:
                    day_breaks.append({'s': start_office, 'e': first_call_start, 'dur': g_start_sec})
                    day_break_sec += g_start_sec

            if len(timed_group) > 1:
                for i in range(len(timed_group) - 1):
                    current_call_end = timed_group['call_endtime'].iloc[i]
                    next_call_start = timed_group['call_starttime'].iloc[i + 1]
                    act_s = max(current_call_end, start_office)
                    act_e = min(next_call_start, end_office)
                    if act_e > act_s:
                        g_mid_sec = get_display_gap_seconds(act_s, act_e)
                        if g_mid_sec >= 900:
                            day_breaks.append({'s': act_s, 'e': act_e, 'dur': g_mid_sec})
                            day_break_sec += g_mid_sec

            if last_call_end < end_office:
                g_end_sec = get_display_gap_seconds(last_call_end, end_office)
                if g_end_sec >= 900:
                    day_breaks.append({'s': last_call_end, 'e': end_office, 'dur': g_end_sec})
                    day_break_sec += g_end_sec

            total_break_sec_all_days += day_break_sec
            if day_breaks:
                b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks : {format_dur_hm(day_break_sec)}"
                for b in day_breaks:
                    b_str += f"\n  {b['s'].strftime('%I:%M %p')}→{b['e'].strftime('%I:%M %p')} ({format_dur_hm(b['dur'])})"
                daily_break_list.append(b_str)

            day_prod_sec = 36000 - day_break_sec
            if len(day_group[day_group['call_duration'] >= 180]) < 40: all_issues.append("Low Calls")
            if day_dur < 11700: all_issues.append("Low Duration")
            if len(day_breaks) > 2: all_issues.append("Excessive Breaks")
            if day_prod_sec < 18000: all_issues.append("Less Productive")

        total_duration_agg += agent_valid_dur
        prod_sec_total = (36000 * total_active_days) - total_break_sec_all_days

        agents_list.append({
            "IN/OUT TIME": "\n".join(daily_io_list),
            "CALLER": owner,
            "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others",
            "TOTAL CALLS": int(total_calls),
            "CALL STATUS": f"{total_ans} Ans / {total_miss} Unans",
            "PICK UP RATIO %": f"{round((total_ans / total_calls * 100)) if total_calls > 0 else 0}%",
            "CALLS > 3 MINS": int(total_above_3min),
            "CALLS 15-20 MINS": int(total_mid_calls),
            "20+ MIN CALLS": int(total_long_calls),
            "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur),
            "PRODUCTIVE HOURS": format_dur_hm(prod_sec_total),
            "BREAKS (>=15 MINS)": "\n---\n".join(daily_break_list) if daily_break_list else "0",
            "REMARKS": ", ".join(sorted(list(set(all_issues)))) if all_issues else "None",
            "raw_prod_sec": prod_sec_total,
            "raw_dur_sec": agent_valid_dur
        })

    return pd.DataFrame(agents_list), total_duration_agg


# ═══════════════════════════════════════════════════
# 7. PLOTLY CHART HELPERS (design-matched)
# ═══════════════════════════════════════════════════
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='IBM Plex Sans', color='#94a3b8', size=11),
    margin=dict(l=20, r=20, t=40, b=20),
    xaxis=dict(gridcolor='#1e2d45', linecolor='#1e2d45', showline=True, zeroline=False),
    yaxis=dict(gridcolor='#1e2d45', linecolor='#1e2d45', showline=False, zeroline=False),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#1e2d45', borderwidth=1),
    colorway=['#3b82f6', '#f59e0b', '#06b6d4', '#10b981', '#8b5cf6', '#ef4444', '#f97316', '#ec4899'],
)

def styled_bar(fig):
    fig.update_layout(**PLOTLY_LAYOUT)
    fig.update_traces(marker_line_width=0)
    return fig

def styled_pie(fig):
    fig.update_layout(**{k: v for k, v in PLOTLY_LAYOUT.items() if k not in ('xaxis', 'yaxis')})
    return fig


# ═══════════════════════════════════════════════════
# 8. AI INSIGHTS FUNCTION
# ═══════════════════════════════════════════════════
def compute_wow_trends(df_raw, report_df, start_date, end_date):
    period_days = (end_date - start_date).days + 1

    prev_start = start_date - timedelta(days=period_days)
    prev_end = start_date - timedelta(days=1)

    df_prev = fetch_call_data(prev_start, prev_end)

    if df_prev.empty:
        return None

    # Process previous period
    df_prev['merge_key'] = df_prev['call_owner'].str.strip().str.lower()
    df_prev = pd.merge(df_prev, df_team_mapping, on='merge_key', how='left')
    df_prev['call_owner'] = df_prev['Caller Name'].fillna(df_prev['call_owner'])

    report_prev, total_dur_prev = process_metrics_logic(df_prev)

    # ── CURRENT METRICS ──
    curr_calls = len(df_raw)
    curr_ans = len(df_raw[df_raw['status'].str.lower() == 'answered'])
    curr_pickup = (curr_ans / curr_calls * 100) if curr_calls > 0 else 0
    curr_dur = total_duration_agg = report_df['raw_dur_sec'].sum()
    curr_prod = report_df['raw_prod_sec'].sum()

    # ── PREVIOUS METRICS ──
    prev_calls = len(df_prev)
    prev_ans = len(df_prev[df_prev['status'].str.lower() == 'answered'])
    prev_pickup = (prev_ans / prev_calls * 100) if prev_calls > 0 else 0
    prev_dur = report_prev['raw_dur_sec'].sum()
    prev_prod = report_prev['raw_prod_sec'].sum()

    def pct_change(curr, prev):
        if prev == 0:
            return 0
        return round(((curr - prev) / prev) * 100, 1)

    return {
        "calls_change": pct_change(curr_calls, prev_calls),
        "pickup_change": pct_change(curr_pickup, prev_pickup),
        "duration_change": pct_change(curr_dur, prev_dur),
        "productivity_change": pct_change(curr_prod, prev_prod),
        "prev_period": f"{prev_start} to {prev_end}"
    }
    
def generate_ai_insights(report_df, df_raw, total_duration_agg, start_date, end_date):
    insights = []

    total_calls = len(df_raw)
    if total_calls == 0:
        return {
            "overall_health": "N/A",
            "health_score": 0,
            "key_insights": insights[:5],
            "top_action": "Load valid data"
        }

    # ── BASIC METRICS ──
    ans = len(df_raw[df_raw['status'].str.lower() == 'answered'])
    miss = len(df_raw[df_raw['status'].str.lower() == 'missed'])
    pickup = round((ans / total_calls) * 100)

    avg_prod = report_df['raw_prod_sec'].mean() / 3600
    avg_dur = report_df['raw_dur_sec'].mean() / 3600
    # ─────────────────────────────────────────────
    # 📅 WEEK-OVER-WEEK TREND ANALYSIS
    # ─────────────────────────────────────────────
    wow = compute_wow_trends(df_raw, report_df, start_date, end_date)
    
    if wow:
        def trend_text(metric, val):
            if val > 5:
                return f"{metric} improved by {val}% WoW"
            elif val < -5:
                return f"{metric} dropped by {abs(val)}% WoW"
            else:
                return f"{metric} is stable ({val}% change)"
    
        insights.append({
            "type": "info",
            "text": trend_text("Total calls", wow["calls_change"])
        })
    
        insights.append({
            "type": "info",
            "text": trend_text("Pickup rate", wow["pickup_change"])
        })
    
        if wow["duration_change"] < -10:
            insights.append({
                "type": "risk",
                "text": f"Call duration dropped significantly by {abs(wow['duration_change'])}% vs last period."
            })
    
        if wow["productivity_change"] > 10:
            insights.append({
                "type": "good",
                "text": f"Productivity increased by {wow['productivity_change']}% — strong upward trend."
            })
    # ── HEALTH SCORE ──
    score = 0

    if pickup >= 75:
        insights.append({"type": "good", "text": f"Strong pickup rate at {pickup}% indicates good responsiveness."})
        score += 25
    elif pickup >= 50:
        insights.append({"type": "warn", "text": f"Pickup rate at {pickup}% needs improvement."})
        score += 15
    else:
        insights.append({"type": "risk", "text": f"Low pickup rate at {pickup}% — high missed opportunity."})
        score += 5

    if avg_prod >= 5:
        insights.append({"type": "good", "text": f"Average productive time is strong at {round(avg_prod,1)} hrs."})
        score += 25
    elif avg_prod >= 3:
        insights.append({"type": "warn", "text": f"Productive hours at {round(avg_prod,1)} hrs can improve."})
        score += 15
    else:
        insights.append({"type": "risk", "text": f"Low productivity at {round(avg_prod,1)} hrs per caller."})
        score += 5

    if avg_dur >= 3:
        insights.append({"type": "good", "text": f"Healthy engagement with avg duration {round(avg_dur,1)} hrs."})
        score += 20
    else:
        insights.append({"type": "warn", "text": f"Low engagement — avg duration only {round(avg_dur,1)} hrs."})
        score += 10

    # ─────────────────────────────────────────────
    # 🧩 TEAM-LEVEL ANALYSIS
    # ─────────────────────────────────────────────
    if 'TEAM' in report_df.columns:
        team_grp = report_df.groupby('TEAM').agg(
            total_calls=('TOTAL CALLS', 'sum'),
            total_duration=('raw_dur_sec', 'sum'),
            avg_prod=('raw_prod_sec', 'mean'),
            callers=('CALLER', 'count')
        ).reset_index()

        team_grp['dur_hrs'] = team_grp['total_duration'] / 3600
        team_grp['avg_prod_hrs'] = team_grp['avg_prod'] / 3600

        # Remove 'Others'
        team_grp = team_grp[team_grp['TEAM'] != 'Others']

        if not team_grp.empty:
            best_team = team_grp.sort_values('dur_hrs', ascending=False).iloc[0]
            worst_team = team_grp.sort_values('dur_hrs', ascending=True).iloc[0]

            insights.append({
                "type": "good",
                "text": f"{best_team['TEAM']} is the top team with {round(best_team['dur_hrs'],1)} hrs total output."
            })

            insights.append({
                "type": "risk",
                "text": f"{worst_team['TEAM']} is lagging with only {round(worst_team['dur_hrs'],1)} hrs."
            })

            # Load imbalance
            max_calls = team_grp['total_calls'].max()
            min_calls = team_grp['total_calls'].min()

            if max_calls > (min_calls * 2):
                insights.append({
                    "type": "warn",
                    "text": "Call distribution is uneven across teams — workload imbalance detected."
                })

            # Productivity gap
            max_prod = team_grp['avg_prod_hrs'].max()
            min_prod = team_grp['avg_prod_hrs'].min()

            if max_prod - min_prod > 2:
                insights.append({
                    "type": "warn",
                    "text": "Significant productivity gap between teams — standardization needed."
                })

    # ─────────────────────────────────────────────
    # 🏆 INDIVIDUAL PERFORMANCE
    # ─────────────────────────────────────────────
    if not report_df.empty:
        top_performer = report_df.iloc[0]
        low_performer = report_df.iloc[-1]

        insights.append({
            "type": "info",
            "text": f"Top performer {top_performer['CALLER']} delivered {round(top_performer['raw_dur_sec']/3600,1)} hrs."
        })

        if low_performer['raw_dur_sec'] < 3600:
            insights.append({
                "type": "risk",
                "text": f"{low_performer['CALLER']} has critically low contribution."
            })

    # ─────────────────────────────────────────────
    # ⚠️ ISSUE PATTERNS
    # ─────────────────────────────────────────────
    all_remarks = []
    for r in report_df['REMARKS']:
        if r and r != "None":
            all_remarks.extend([x.strip() for x in r.split(',')])

    if all_remarks:
        issue_series = pd.Series(all_remarks).value_counts()
        top_issue = issue_series.index[0]

        insights.append({
            "type": "warn",
            "text": f"Most frequent issue across team: {top_issue}."
        })

    # ── HEALTH LABEL ──
    if score >= 70:
        health = "Healthy"
    elif score >= 40:
        health = "Moderate"
    else:
        health = "Critical"

    # ── TOP ACTION ──
    if pickup < 60:
        action = "Improve pickup rate — missed calls are impacting conversions."
    elif avg_prod < 4:
        action = "Increase productive hours and reduce idle time."
    else:
        action = "Replicate top team strategies across underperforming teams."

    return {
        "overall_health": health,
        "health_score": int(score),
        "key_insights": insights[:5],
        "top_action": action
    }

# ═══════════════════════════════════════════════════
# 9. SIDEBAR
# ═══════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sb-logo">
        <div class="icon">📡</div>
        <div>
            <div class="name">CallerWise</div>
            <div class="tagline">Analysis Platform</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("## Report Filters")

    min_d, max_d = get_available_dates()
    selected_dates = st.date_input(
        "Date Range", value=(max_d, max_d),
        min_value=min_d, max_value=max_d, format="DD-MM-YYYY"
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date = end_date = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

    teams, verticals, df_team_mapping = get_metadata()
    selected_team = st.multiselect("Team", options=teams, placeholder="All teams")
    selected_vertical = st.multiselect("Vertical", options=verticals, placeholder="All verticals")
    search_query = st.text_input("🔍 Search Caller")

    st.markdown("---")
    gen_dynamic = st.button("⚡  Generate Dynamic Report")
    gen_static = st.button("📅  Generate Duration Report")

    st.markdown("<br>", unsafe_allow_html=True)
    last_update_str = get_global_last_update()
    st.markdown(f"""
    <div style="font-family: var(--font-mono); font-size: 0.68rem; color: var(--text-muted); 
         padding: 0.6rem 0.75rem; background: var(--bg-card); border-radius: 6px; 
         border: 1px solid var(--border);">
        🕐 Last Sync At<br>
        <span style="color: var(--accent-green);">{last_update_str}</span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# 10. PAGE HEADER
# ═══════════════════════════════════════════════════
display_start = start_date.strftime('%d %b %Y')
display_end = end_date.strftime('%d %b %Y')

st.markdown(f"""
<div class="cw-page-header">
    <div class="logo-block">
        <div class="logo-icon">📡</div>
        <div>
            <h1>Duration Metrics</h1>
            <div class="subtitle">Lawsikho &amp; Skill Arbitrage · Powered By Acefone & Ozonetel </div>
        </div>
    </div>
    <div style="display:flex; gap:0.75rem; align-items:center; flex-wrap:wrap;">
        <div class="cw-meta-pill"><span class="dot"></span>Live</div>
        <div class="cw-meta-pill">📅 {display_start} → {display_end}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# 11. TABS
# ═══════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs([
    "⚡  Dynamic Dashboard",
    "📅  Duration Report",
    "🤖  AI Insights"
])


# ───────────────────────────────────────────────────
# TAB 1: DYNAMIC DASHBOARD
# ───────────────────────────────────────────────────
with tab1:
    if gen_dynamic:
        with st.spinner('Crunching call metrics…'):
            df_raw = fetch_call_data(start_date, end_date)

        if df_raw.empty:
            st.warning("No data found for the selected period.")
        else:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            df = df[df['call_owner'].notna() & (df['call_owner'] != '')]

            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]

            if df.empty:
                st.error("No results match your filters.")
            else:
                report_df, total_duration_agg = process_metrics_logic(df)
                report_df = report_df.sort_values(by="raw_dur_sec", ascending=False)
                
                # --- FIX: Define ans_t before using it in metrics ---
                ans_t = len(df[df['status'].str.lower() == 'answered'])

                # ── KPI STRIP (Reorganized into 2 Rows for 2026 Metrics) ──
                st.markdown('<div class="cw-section-title">Key Performance Indicators</div>', unsafe_allow_html=True)
                
                # Row 1: Volume Metrics (Total, Acefone, Ozonetel, Manual)
                row1_1, row1_2, row1_3, row1_4 = st.columns(4)
                row1_1.metric("Total Calls", f"{len(df):,}")
                row1_2.metric("Acefone", f"{len(df[df['source'] == 'Acefone']):,}")
                row1_3.metric("Ozonetel", f"{len(df[df['source'] == 'Ozonetel']):,}")
                row1_4.metric("Manual", f"{len(df[df['source'] == 'Manual']):,}")
                
                # Row 2: Performance Metrics (Leads, Pickup, Active, Avg Duration)
                row2_1, row2_2, row2_3, row2_4 = st.columns(4)
                row2_1.metric("Unique Leads", f"{df['unique_lead_id'].nunique():,}")
                row2_2.metric("Pick Up %", f"{round(ans_t / len(df) * 100) if len(df) > 0 else 0}%")
                row2_3.metric("Active Callers", len(report_df))
                # UNIQUE DIALLED replaced with AVG PROD HOURS as requested
                row2_4.metric("Avg Prod Hours", format_dur_hm(report_df["raw_prod_sec"].mean()))

                st.divider()

                # ── MAIN TABLE ──
                st.markdown('<div class="cw-section-title">Caller Performance Matrix</div>', unsafe_allow_html=True)
                total_row = pd.DataFrame([{
                    "IN/OUT TIME": "-", "CALLER": "TOTAL", "TEAM": "-",
                    "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                    "CALL STATUS": "-", "PICK UP RATIO %": "-",
                    "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                    "CALLS 15-20 MINS": int(report_df["CALLS 15-20 MINS"].sum()),
                    "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                    "CALL DURATION > 3 MINS": format_dur_hm(total_duration_agg),
                    "PRODUCTIVE HOURS": format_dur_hm(report_df["raw_prod_sec"].sum()),
                    "BREAKS (>=15 MINS)": "-", "REMARKS": "-"
                }])

                display_cols = [
                    "IN/OUT TIME", "CALLER", "TEAM", "TOTAL CALLS", "CALL STATUS",
                    "PICK UP RATIO %", "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS",
                    "CALL DURATION > 3 MINS", "PRODUCTIVE HOURS", "BREAKS (>=15 MINS)", "REMARKS"
                ]
                final_df = pd.concat([report_df, total_row], ignore_index=True)
                st.dataframe(
                    final_df.style.apply(style_total, axis=1).set_properties(**{'white-space': 'pre-wrap'}),
                    column_order=display_cols, use_container_width=True, hide_index=True
                )

                st.divider()

                # ── CDR DOWNLOAD ──
                cdr_csv = df.copy()
                target_cols = [
                    "client_number", "call_datetime", "call_starttime_clean", "call_endtime_clean",
                    "call_duration", "status", "direction", "service", "reason",
                    "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                ]
                existing_cols = [c for c in target_cols if c in cdr_csv.columns]
                st.download_button(
                    label="📥  Download Full CDR",
                    data=cdr_csv[existing_cols].to_csv(index=False).encode('utf-8'),
                    file_name="CDR_LOG.csv", mime='text/csv'
                )

    else:
        st.markdown("""
        <div style="text-align:center; padding: 5rem 2rem; color: var(--text-muted);">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;">⚡</div>
            <div style="font-family: var(--font-display); font-size: 1rem; letter-spacing: 0.1em; 
                 text-transform: uppercase; margin-bottom: 0.5rem;">Ready to Analyse</div>
            <div style="font-size: 0.82rem;">Configure filters in the sidebar, then click <b>Generate Dynamic Report</b></div>
        </div>
        """, unsafe_allow_html=True)


# ───────────────────────────────────────────────────
# TAB 2: DURATION REPORT (unchanged logic, styled output)
# ───────────────────────────────────────────────────
with tab2:
    if gen_static:
        with st.spinner('Building duration layouts…'):
            df_raw = fetch_call_data(start_date, end_date)

        if df_raw.empty:
            st.warning("No data found.")
        else:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df_static_master = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df_static_master['call_owner'] = df_static_master['Caller Name'].fillna(df_static_master['call_owner'])

            if selected_team: df_static_master = df_static_master[df_static_master['Team Name'].isin(selected_team)]
            if selected_vertical: df_static_master = df_static_master[df_static_master['Vertical'].isin(selected_vertical)]
            if search_query: df_static_master = df_static_master[df_static_master['call_owner'].str.contains(search_query, case=False, na=False)]

            if df_static_master.empty:
                st.error("No results match filters.")
            else:
                tl_ad_mask = pd.Series(False, index=df_static_master.index)
                meta_cols = df_team_mapping.columns.tolist()
                for col in meta_cols:
                    if col in df_static_master.columns:
                        clean_col = df_static_master[col].fillna('').astype(str).str.strip().str.upper()
                        tl_ad_mask |= clean_col.isin(['TL', 'ATL', 'AD', 'TEAM LEAD', 'TEAM LEADER'])

                static_display_cols = [
                    "CALLER", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %",
                    "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS"
                ]
                normal_team_data = df_static_master[~tl_ad_mask]
                normal_teams = sorted(normal_team_data['Team Name'].dropna().unique())

                for team in normal_teams:
                    team_df = normal_team_data[normal_team_data['Team Name'] == team]
                    report_df, team_dur_agg_sec = process_metrics_logic(team_df)
                    if team_dur_agg_sec > 0:
                        report_df = report_df.sort_values(by="raw_dur_sec", ascending=False)
                        st.markdown(f'<div class="cw-team-badge">▸ {team.upper()} — {display_start} to {display_end}</div>', unsafe_allow_html=True)
                        total_row = pd.DataFrame([{
                            "CALLER": "TOTAL",
                            "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                            "CALL STATUS": "-", "PICK UP RATIO %": "-",
                            "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                            "CALLS 15-20 MINS": int(report_df["CALLS 15-20 MINS"].sum()),
                            "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                            "CALL DURATION > 3 MINS": format_dur_hm(team_dur_agg_sec)
                        }])
                        final_team_df = pd.concat([report_df[static_display_cols], total_row], ignore_index=True)
                        calc_height = (len(final_team_df) + 1) * 35 + 20
                        st.dataframe(
                            final_team_df.style.apply(style_static, axis=1).set_properties(**{'white-space': 'pre-wrap'}),
                            column_order=static_display_cols, use_container_width=True,
                            hide_index=True, height=calc_height
                        )
                        target_cols = [
                            "client_number", "call_datetime", "call_starttime_clean", "call_endtime_clean",
                            "call_duration", "status", "direction", "service", "reason",
                            "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                        ]
                        existing_cols = [c for c in target_cols if c in team_df.columns]
                        st.download_button(
                            label=f"📥  Download CDR — {team}",
                            data=team_df[existing_cols].to_csv(index=False).encode('utf-8'),
                            file_name=f"CDR_{team}.csv", mime='text/csv',
                            key=f"dl_team_{team}"
                        )
                        st.divider()

                # TL Report
                tl_ad_pool = df_static_master[tl_ad_mask]
                if not tl_ad_pool.empty:
                    report_df_tl, tl_dur_agg_sec = process_metrics_logic(tl_ad_pool)
                    active_tl_report = report_df_tl[report_df_tl['raw_dur_sec'] > 300].sort_values(by="raw_dur_sec", ascending=False)

                    if not active_tl_report.empty:
                        st.markdown(f'<div class="cw-team-badge" style="border-color: var(--accent-amber); color: var(--accent-amber);">▸ Team Leads Duration — {display_start} to {display_end}</div>', unsafe_allow_html=True)
                        total_row_tl = pd.DataFrame([{
                            "CALLER": "TOTAL",
                            "TOTAL CALLS": int(active_tl_report["TOTAL CALLS"].sum()),
                            "CALL STATUS": "-", "PICK UP RATIO %": "-",
                            "CALLS > 3 MINS": int(active_tl_report["CALLS > 3 MINS"].sum()),
                            "CALLS 15-20 MINS": int(active_tl_report["CALLS 15-20 MINS"].sum()),
                            "20+ MIN CALLS": int(active_tl_report["20+ MIN CALLS"].sum()),
                            "CALL DURATION > 3 MINS": format_dur_hm(active_tl_report["raw_dur_sec"].sum())
                        }])
                        final_tl_df = pd.concat([active_tl_report[static_display_cols], total_row_tl], ignore_index=True)
                        calc_height_tl = (len(final_tl_df) + 1) * 35 + 20
                        st.dataframe(
                            final_tl_df.style.apply(style_static, axis=1).set_properties(**{'white-space': 'pre-wrap'}),
                            column_order=static_display_cols, use_container_width=True,
                            hide_index=True, height=calc_height_tl
                        )
                        target_cols = [
                            "client_number", "call_datetime", "call_starttime_clean", "call_endtime_clean",
                            "call_duration", "status", "direction", "service", "reason",
                            "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                        ]
                        valid_tls = active_tl_report['CALLER'].unique()
                        final_tl_cdr = tl_ad_pool[tl_ad_pool['call_owner'].isin(valid_tls)]
                        existing_cols = [c for c in target_cols if c in final_tl_cdr.columns]
                        st.download_button(
                            label="📥  Download TL CDR",
                            data=final_tl_cdr[existing_cols].to_csv(index=False).encode('utf-8'),
                            file_name="CDR_TL_AD.csv", mime='text/csv',
                            key="dl_tl_ad_final_last"
                        )
    else:
        st.markdown("""
        <div style="text-align:center; padding: 5rem 2rem; color: var(--text-muted);">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;">📅</div>
            <div style="font-family: var(--font-display); font-size: 1rem; letter-spacing: 0.1em; 
                 text-transform: uppercase; margin-bottom: 0.5rem;">Duration Report</div>
            <div style="font-size: 0.82rem;">Click <b>Generate Duration Report</b> in the sidebar to view team-wise breakdowns</div>
        </div>
        """, unsafe_allow_html=True)


# ───────────────────────────────────────────────────
# TAB 3: AI INSIGHTS
# ───────────────────────────────────────────────────
with tab3:
    if not (gen_dynamic or gen_static):
        st.markdown("""
        <div style="text-align:center; padding: 5rem 2rem; color: var(--text-muted);">
            <div style="font-size: 3rem; margin-bottom: 1rem; opacity: 0.4;">🤖</div>
            <div style="font-family: var(--font-display); font-size: 1rem; letter-spacing: 0.1em; 
                 text-transform: uppercase; margin-bottom: 0.5rem;">AI Insights Awaiting Data</div>
            <div style="font-size: 0.82rem;">First generate either report using the sidebar, then revisit this tab.</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Fetch and process data for charts
        with st.spinner('Building AI insights…'):
            df_raw_ai = fetch_call_data(start_date, end_date)

        if df_raw_ai.empty:
            st.warning("No data available for insights.")
        else:
            df_raw_ai['merge_key'] = df_raw_ai['call_owner'].str.strip().str.lower()
            df_ai = pd.merge(df_raw_ai, df_team_mapping, on='merge_key', how='left')
            df_ai['call_owner'] = df_ai['Caller Name'].fillna(df_ai['call_owner'])
            df_ai = df_ai[df_ai['call_owner'].notna() & (df_ai['call_owner'] != '')]

            if selected_team: df_ai = df_ai[df_ai['Team Name'].isin(selected_team)]
            if selected_vertical: df_ai = df_ai[df_ai['Vertical'].isin(selected_vertical)]
            if search_query: df_ai = df_ai[df_ai['call_owner'].str.contains(search_query, case=False, na=False)]

            report_df_ai, total_dur_ai = process_metrics_logic(df_ai)
            report_df_ai = report_df_ai.sort_values(by="raw_dur_sec", ascending=False)

            # ── AI INSIGHT CARDS ──
            st.markdown('<div class="cw-section-title">AI-Generated Performance Analysis</div>', unsafe_allow_html=True)

            with st.spinner('Generating Insights…'):
                insights = generate_ai_insights(report_df_ai, df_ai, total_dur_ai, start_date, end_date)

            health = insights.get("overall_health", "N/A")
            score = insights.get("health_score", 0)
            health_color = {"Healthy": "#10b981", "Moderate": "#f59e0b", "Critical": "#ef4444"}.get(health, "#64748b")

            col_score, col_main = st.columns([1, 3])
            col_score, col_main = st.columns([1, 3])
            with col_score:
                st.markdown(f"""
                <div class="ai-card" style="text-align:center; height: 100%;">
                    <h4>Health Score</h4>
                    <div class="score-ring" style="border-color: {health_color};">
                        <div class="val" style="color: {health_color};">{score}</div>
                        <div class="lbl">/ 100</div>
                    </div>
                    <div style="font-family: var(--font-display); font-size: 1rem; font-weight: 700; color: {health_color}; letter-spacing: 0.1em; text-transform: uppercase;">
                        {health}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col_main:
                # 1. Get insights data
                key_insights = insights.get("key_insights", [])
                
                # 2. Build simple Markdown bullets instead of complex HTML
                markdown_bullets = ""
                for ins in key_insights:
                    t = ins.get("type", "info")
                    # Assign an emoji based on type
                    icon = "ℹ️" if t == "info" else "✅" if t == "good" else "⚠️" if t == "warn" else "🚨"
                    
                    # Create a clean markdown line
                    markdown_bullets += f"{icon} **{ins.get('text','')}**\n\n"

                # 3. Display in a clean, theme-aware box
                st.markdown(f"""
                <div class="ai-card">
                    <h4 style="color: var(--accent-amber); margin-bottom: 15px;">Key Insights</h4>
                    <div style="color: var(--text-primary); line-height: 1.6;">
                        {markdown_bullets}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # 4. Simple Recommendation Card
                top_action = insights.get("top_action", "")
                st.info(f"**🎯 Recommended Action:** {top_action}")

            # --- STRAY 'v' REMOVED FROM HERE ---
            st.divider()

            # ── CHARTS ROW 1 ──
            st.markdown('<div class="cw-section-title">Call Volume & Source Distribution</div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)

            with c1:
                # Source pie
                src_counts = df_ai['source'].value_counts().reset_index()
                src_counts.columns = ['Source', 'Calls']
                fig_pie = px.pie(src_counts, values='Calls', names='Source',
                                 title='Calls by Source', hole=0.55,
                                 color_discrete_sequence=['#3b82f6', '#f59e0b', '#06b6d4'])
                styled_pie(fig_pie)
                fig_pie.update_traces(textfont_color='#f1f5f9', textfont_size=11)
                st.plotly_chart(fig_pie, use_container_width=True)

            with c2:
                # Status bar
                status_counts = df_ai['status'].str.lower().value_counts().reset_index()
                status_counts.columns = ['Status', 'Count']
                status_counts['Status'] = status_counts['Status'].str.title()
                fig_status = px.bar(status_counts, x='Status', y='Count',
                                    title='Call Status Breakdown',
                                    color='Status',
                                    color_discrete_map={'Answered': '#10b981', 'Missed': '#ef4444', 'Busy': '#f59e0b'})
                styled_bar(fig_status)
                st.plotly_chart(fig_status, use_container_width=True)

            with c3:
                # Duration buckets
                df_ai['dur_bucket'] = pd.cut(
                    df_ai['call_duration'],
                    bins=[0, 60, 180, 900, 1200, float('inf')],
                    labels=['<1 min', '1-3 min', '3-15 min', '15-20 min', '20+ min']
                )
                bucket_counts = df_ai['dur_bucket'].value_counts().sort_index().reset_index()
                bucket_counts.columns = ['Duration', 'Count']
                fig_bucket = px.bar(bucket_counts, x='Duration', y='Count',
                                    title='Duration Distribution',
                                    color_discrete_sequence=['#3b82f6'])
                styled_bar(fig_bucket)
                st.plotly_chart(fig_bucket, use_container_width=True)

            st.divider()

            # ── CHARTS ROW 2 ──
            st.markdown('<div class="cw-section-title">Caller Performance Analysis</div>', unsafe_allow_html=True)
            c4, c5 = st.columns([3, 2])

            with c4:
                # Top 15 callers by duration
                top15 = report_df_ai.head(15).copy()
                top15['dur_hrs'] = top15['raw_dur_sec'] / 3600
                top15['prod_hrs'] = top15['raw_prod_sec'] / 3600

                fig_top = go.Figure()
                fig_top.add_trace(go.Bar(
                    name='Call Duration (hrs)', x=top15['CALLER'], y=top15['dur_hrs'],
                    marker_color='#3b82f6', marker_line_width=0
                ))
                fig_top.add_trace(go.Bar(
                    name='Productive Hrs', x=top15['CALLER'], y=top15['prod_hrs'],
                    marker_color='#10b981', marker_line_width=0
                ))
                fig_top.update_layout(
                    **PLOTLY_LAYOUT,
                    title='Top 15 Callers — Duration vs Productive Hours',
                    barmode='group', xaxis_tickangle=-35
                )
                st.plotly_chart(fig_top, use_container_width=True)

            with c5:
                # Team comparison
                if 'TEAM' in report_df_ai.columns:
                    team_grp = report_df_ai.groupby('TEAM').agg(
                        Total_Calls=('TOTAL CALLS', 'sum'),
                        Dur_Hrs=('raw_dur_sec', lambda x: x.sum() / 3600),
                        Callers=('CALLER', 'count')
                    ).reset_index()
                    team_grp = team_grp[team_grp['TEAM'] != 'Others']

                    fig_team = px.bar(team_grp, x='TEAM', y='Dur_Hrs',
                                      title='Duration by Team (hrs)',
                                      color='Callers',
                                      color_continuous_scale=[[0, '#1e3a5f'], [1, '#3b82f6']],
                                      text='Callers')
                    fig_team.update_traces(texttemplate='%{text} callers', textposition='outside',
                                          textfont_color='#94a3b8', marker_line_width=0)
                    styled_bar(fig_team)
                    fig_team.update_coloraxes(showscale=False)
                    st.plotly_chart(fig_team, use_container_width=True)

            st.divider()

            # ── CHARTS ROW 3 ──
            st.markdown('<div class="cw-section-title">Quality & Productivity Metrics</div>', unsafe_allow_html=True)
            c6, c7 = st.columns(2)

            with c6:
                # Pick-up ratio scatter
                fig_scatter = px.scatter(
                    report_df_ai,
                    x='TOTAL CALLS', y='CALLS > 3 MINS',
                    size='raw_dur_sec', color='TEAM',
                    hover_name='CALLER',
                    title='Total Calls vs Quality Calls (bubble = duration)',
                    color_discrete_sequence=['#3b82f6', '#f59e0b', '#06b6d4', '#10b981', '#8b5cf6', '#ef4444']
                )
                fig_scatter.update_layout(**PLOTLY_LAYOUT)
                st.plotly_chart(fig_scatter, use_container_width=True)

            with c7:
                # Remarks breakdown
                all_remarks = []
                for r in report_df_ai['REMARKS']:
                    if r and r != "None":
                        all_remarks.extend([x.strip() for x in r.split(',')])
                if all_remarks:
                    rem_series = pd.Series(all_remarks).value_counts().reset_index()
                    rem_series.columns = ['Issue', 'Count']
                    fig_rem = px.bar(rem_series, x='Count', y='Issue', orientation='h',
                                     title='Flagged Issues Breakdown',
                                     color='Count',
                                     color_continuous_scale=[[0, '#1e3a5f'], [0.5, '#f59e0b'], [1, '#ef4444']])
                    fig_rem.update_layout(**PLOTLY_LAYOUT)
                    fig_rem.update_yaxes(autorange='reversed')
                    fig_rem.update_coloraxes(showscale=False)
                    fig_rem.update_traces(marker_line_width=0)
                    st.plotly_chart(fig_rem, use_container_width=True)
                else:
                    st.info("No flagged issues — all callers within thresholds.")

            # ── LONG CALL LEADERBOARD ──
            st.markdown('<div class="cw-section-title">20+ Min Call Champions</div>', unsafe_allow_html=True)
            top_long = report_df_ai.nlargest(10, '20+ MIN CALLS')[['CALLER', 'TEAM', '20+ MIN CALLS', 'CALLS 15-20 MINS', 'CALLS > 3 MINS']].reset_index(drop=True)
            if not top_long.empty:
                fig_long = px.bar(top_long, x='CALLER', y='20+ MIN CALLS',
                                  title='Top 10 Callers by 20+ Min Calls',
                                  color='TEAM',
                                  color_discrete_sequence=['#3b82f6', '#f59e0b', '#06b6d4', '#10b981', '#8b5cf6'])
                fig_long.update_layout(**PLOTLY_LAYOUT, xaxis_tickangle=-30)
                fig_long.update_traces(marker_line_width=0)
                st.plotly_chart(fig_long, use_container_width=True)
