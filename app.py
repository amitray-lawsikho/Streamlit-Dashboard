import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import pytz
import numpy as np

# --- 1. Cloud Credentials Setup ---
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

# --- 2. Page Configuration ---
st.set_page_config(
    layout="wide",
    page_title="CALLING METRICS",
    initial_sidebar_state="expanded",
    page_icon="🔔"
)

# --- PROFESSIONAL WARM THEME (Yellow · Orange · Red) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --accent-primary:   #F97316;
    --accent-secondary: #EF4444;
    --accent-success:   #EAB308;
    --accent-warn:      #FBBF24;
    --accent-danger:    #DC2626;
    --gold:             #F59E0B;
    --silver:           #9CA3AF;
    --bronze:           #CD7F32;
    --radius-sm:        8px;
    --radius-md:        12px;
    --radius-lg:        16px;
    --shadow-sm:        0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
    --shadow-md:        0 4px 16px rgba(0,0,0,.10);
    --shadow-lg:        0 8px 32px rgba(0,0,0,.14);
    --transition:       all 0.22s cubic-bezier(.4,0,.2,1);
}

[data-testid="stAppViewContainer"]:not([class*="dark"]) {
    --bg-base:      #FFF8F3;
    --bg-surface:   #FFFFFF;
    --bg-elevated:  #FFFFFF;
    --bg-muted:     #FEF3E8;
    --border:       rgba(249,115,22,.12);
    --text-primary: #111827;
    --text-muted:   #6B7280;
    --metric-bg:    #FFFFFF;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-base:      #0F0A05;
        --bg-surface:   #1A1006;
        --bg-elevated:  #231508;
        --bg-muted:     #1E1207;
        --border:       rgba(249,115,22,.10);
        --text-primary: #FEF3E8;
        --text-muted:   #D1A67A;
        --metric-bg:    #231508;
    }
}

[data-theme="dark"] {
    --bg-base:      #0F0A05 !important;
    --bg-surface:   #1A1006 !important;
    --bg-elevated:  #231508 !important;
    --bg-muted:     #1E1207 !important;
    --border:       rgba(249,115,22,.10) !important;
    --text-primary: #FEF3E8 !important;
    --text-muted:   #D1A67A !important;
    --metric-bg:    #231508 !important;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

footer { visibility: hidden; }
[data-testid="stStatusWidget"], .stStatusWidget { display: none !important; }
[data-testid="stMainViewContainer"] { padding-top: 1.5rem; }
[data-testid="stSidebar"] { border-right: 1px solid var(--border, rgba(249,115,22,.12)); }

.cw-header {
    background: linear-gradient(135deg, #1c0700 0%, #7c2d12 50%, #431407 100%);
    border-radius: var(--radius-lg);
    padding: 1.5rem 2rem 1.2rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}
.cw-header::before, .cw-header::after { display: none; }
.cw-title { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; letter-spacing: .5px; margin: 0 0 .25rem; }
.cw-subtitle { font-size: .82rem; color: rgba(255,255,255,.6); font-weight: 400; margin: 0; font-family: 'DM Mono', monospace; }
.cw-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: var(--bg-muted, #FEF3E8);
    border: 1px solid var(--border, rgba(249,115,22,.12));
    border-radius: 20px; padding: 3px 10px; font-size: .73rem;
    color: var(--text-primary, #111827); font-family: 'DM Mono', monospace;
}
.cw-pulse {
    width: 6px; height: 6px; background: #EAB308; border-radius: 50%;
    display: inline-block; animation: pulse-ring 1.8s ease-in-out infinite;
}
@keyframes pulse-ring {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .5; transform: scale(1.4); }
}

.metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; margin: .5rem 0 1rem; }
.metric-card {
    background: var(--metric-bg, #fff);
    border: 1px solid var(--border, rgba(249,115,22,.12));
    border-radius: var(--radius-md); padding: .9rem 1rem;
    transition: var(--transition); box-shadow: var(--shadow-sm);
    position: relative; overflow: hidden; text-align: center;
}
.metric-card::before {
    content: ""; position: absolute; top: 0; left: 0;
    width: 100%; height: 3px;
    background: linear-gradient(90deg, #F97316, #EF4444);
    opacity: 0; transition: opacity .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.metric-card:hover::before { opacity: 1; }
.metric-label { font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--text-muted, #6B7280); margin: 0 0 .3rem; }
.metric-value { font-size: 1.45rem; font-weight: 700; color: var(--text-primary, #111827); line-height: 1; font-family: 'DM Mono', monospace; }
.metric-delta { font-size: .7rem; color: #EAB308; margin-top: .2rem; font-weight: 500; }

.section-header { display: flex; align-items: center; gap: .6rem; margin: 1.5rem 0 .8rem; }
.section-header-line { flex: 1; height: 1px; background: linear-gradient(90deg, #F97316, transparent); opacity: .35; }
.section-title { font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #F97316; white-space: nowrap; text-align: center; }

.static-team-header {
    text-align: center; margin: 2rem 0 .6rem; font-size: 1rem; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; color: #F97316;
    display: flex; align-items: center; justify-content: center; gap: .75rem;
}
.static-team-header::before, .static-team-header::after {
    content: ""; flex: 1; max-width: 120px; height: 1px;
    background: linear-gradient(90deg, transparent, #F97316); opacity: .4;
}
.static-team-header::after { background: linear-gradient(90deg, #F97316, transparent); }

.insight-card {
    background: var(--metric-bg, #fff);
    border: 1px solid var(--border, rgba(249,115,22,.12));
    border-radius: var(--radius-md); padding: 1rem 1.1rem;
    margin-bottom: .6rem; box-shadow: var(--shadow-sm); transition: var(--transition);
}
.insight-card:hover { box-shadow: var(--shadow-md); }
.insight-card.good  { border-left: 3px solid #EAB308; }
.insight-card.warn  { border-left: 3px solid #FBBF24; }
.insight-card.bad   { border-left: 3px solid #EF4444; }
.insight-card.info  { border-left: 3px solid #F97316; }
.insight-icon { font-size: 1.1rem; }
.insight-title { font-size: .82rem; font-weight: 700; color: var(--text-primary, #111827); margin: .2rem 0; text-align: center; }
.insight-body { font-size: .76rem; color: var(--text-muted, #6B7280); line-height: 1.5; text-align: center; }

[data-testid="stTabs"] [role="tablist"] { gap: .3rem; border-bottom: 1px solid var(--border, rgba(249,115,22,.12)); padding-bottom: 0; }
[data-testid="stTabs"] button[role="tab"] {
    font-family: 'DM Sans', sans-serif !important; font-size: .82rem !important;
    font-weight: 600 !important; letter-spacing: .3px;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    padding: .55rem 1.1rem !important; transition: var(--transition);
}

div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, #431407, #7c1d1d) !important;
    color: #fff !important; font-family: 'DM Sans', sans-serif !important;
    font-size: .72rem !important; font-weight: 700 !important; letter-spacing: .6px;
    text-transform: uppercase; white-space: normal !important; word-wrap: break-word !important;
    text-align: center !important; vertical-align: middle !important;
    min-width: 100px !important; padding: 10px !important;
}

[data-testid="stSidebar"] .stButton>button {
    width: 100%; font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: .82rem !important;
    border-radius: var(--radius-sm); transition: var(--transition);
}
[data-testid="stSidebar"] .stButton>button:first-child {
    background: linear-gradient(135deg, #EA580C, #DC2626) !important;
    color: #fff !important; border: none !important;
}
[data-testid="stSidebar"] .stButton>button:last-child {
    background: linear-gradient(135deg, #B45309, #EA580C) !important;
    color: #fff !important; border: none !important;
}

.stDownloadButton>button {
    background: linear-gradient(135deg, #431407, #7c1d1d) !important;
    color: #fff !important; border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: .78rem !important; font-weight: 600 !important;
    transition: var(--transition) !important;
}
.stDownloadButton>button:hover { opacity: .88; transform: translateY(-1px); }

hr { border-color: var(--border, rgba(249,115,22,.12)) !important; margin: 1.2rem 0 !important; }
.js-plotly-plot { border-radius: var(--radius-md); overflow: hidden; }

.kpi-pill { display: inline-flex; align-items: center; gap: 4px; padding: 2px 9px; border-radius: 20px; font-size: .7rem; font-weight: 600; font-family: 'DM Mono', monospace; }
.kpi-pill.green  { background: rgba(234,179,8,.15);   color: #CA8A04; }
.kpi-pill.amber  { background: rgba(251,191,36,.15);  color: #D97706; }
.kpi-pill.red    { background: rgba(239,68,68,.15);   color: #DC2626; }
.kpi-pill.blue   { background: rgba(249,115,22,.15);  color: #EA580C; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# GLOBAL HELPER FUNCTIONS
# ─────────────────────────────────────────────

def style_total(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
    return [''] * len(row)

def style_static(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
    return [''] * len(row)

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    tm = int(round(total_seconds / 60))
    return f"{tm // 60}h {tm % 60}m"

def get_display_gap_seconds(start_time, end_time):
    if pd.isna(start_time) or pd.isna(end_time): return 0
    s = start_time.replace(second=0, microsecond=0)
    e = end_time.replace(second=0, microsecond=0)
    return (e - s).total_seconds()

def section_header(label):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header-line"></div>
        <span class="section-title">{label}</span>
        <div class="section-header-line" style="background:linear-gradient(90deg,transparent,#F97316)"></div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────

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
        SELECT MIN(`Call Date`) as min_d, MAX(`Call Date`) as max_d
        FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT MIN(CallDate) as min_d, MAX(CallDate) as max_d
        FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
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

        ozo_mask = df['source'] == 'Ozonetel'
        df.loc[ozo_mask, 'call_starttime'] = df.loc[ozo_mask, 'call_endtime']
        df.loc[ozo_mask, 'call_endtime']   = (
            df.loc[ozo_mask, 'call_starttime']
            + pd.to_timedelta(df.loc[ozo_mask, 'call_duration'], unit='s')
        )

        df['call_starttime_clean'] = df['call_starttime'].dt.tz_localize(None)
        df['call_endtime_clean']   = df['call_endtime'].dt.tz_localize(None)
    return df


# ─────────────────────────────────────────────
# CORE METRICS PROCESSING
# ─────────────────────────────────────────────

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
            ans  = len(day_group[day_group['status'].str.lower() == 'answered'])
            miss = len(day_group[day_group['status'].str.lower() == 'missed'])
            total_ans  += ans
            total_miss += miss
            total_calls += len(day_group)

            total_above_3min  += len(day_group[day_group['call_duration'] >= 180])
            total_mid_calls   += len(day_group[(day_group['call_duration'] >= 900) & (day_group['call_duration'] < 1200)])
            total_long_calls  += len(day_group[day_group['call_duration'] >= 1200])
            day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
            agent_valid_dur += day_dur

            if timed_group.empty: continue

            first_call_start = timed_group['call_starttime'].min()
            last_call_end    = timed_group['call_endtime'].max()
            daily_io_list.append(
                f"{c_date.strftime('%d/%m')}: In {first_call_start.strftime('%I:%M %p')} · Out {last_call_end.strftime('%I:%M %p')}"
            )

            start_office = ist_tz.localize(datetime.combine(c_date, time(10, 0)))
            end_office   = ist_tz.localize(datetime.combine(c_date, time(20, 0)))

            if first_call_start > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
            if last_call_end   < end_office: all_issues.append("Early Check-Out")

            day_breaks, day_break_sec = [], 0

            if first_call_start > start_office:
                g = get_display_gap_seconds(start_office, first_call_start)
                if g >= 900:
                    day_breaks.append({'s': start_office, 'e': first_call_start, 'dur': g})
                    day_break_sec += g

            if len(timed_group) > 1:
                for i in range(len(timed_group) - 1):
                    cur_end   = timed_group['call_endtime'].iloc[i]
                    nxt_start = timed_group['call_starttime'].iloc[i + 1]
                    act_s = max(cur_end,   start_office)
                    act_e = min(nxt_start, end_office)
                    if act_e > act_s:
                        g = get_display_gap_seconds(act_s, act_e)
                        if g >= 900:
                            day_breaks.append({'s': act_s, 'e': act_e, 'dur': g})
                            day_break_sec += g

            if last_call_end < end_office:
                g = get_display_gap_seconds(last_call_end, end_office)
                if g >= 900:
                    day_breaks.append({'s': last_call_end, 'e': end_office, 'dur': g})
                    day_break_sec += g

            total_break_sec_all_days += day_break_sec
            if day_breaks:
                b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks : {format_dur_hm(day_break_sec)}"
                for b in day_breaks:
                    b_str += f"\n  {b['s'].strftime('%I:%M %p')}→{b['e'].strftime('%I:%M %p')} ({format_dur_hm(b['dur'])})"
                daily_break_list.append(b_str)

            day_prod_sec = 36000 - day_break_sec
            if len(day_group[day_group['call_duration'] >= 180]) < 40: all_issues.append("Low Calls")
            if day_dur < 11700:    all_issues.append("Low Duration")
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
            "REMARKS": ", ".join(sorted(set(all_issues))) if all_issues else "None",
            "raw_prod_sec": prod_sec_total,
            "raw_dur_sec": agent_valid_dur,
        })

    return pd.DataFrame(agents_list), total_duration_agg


# ─────────────────────────────────────────────
# INSIGHTS COMPUTATION
# ─────────────────────────────────────────────

def compute_team_insights(df_merged, report_df):
    insights = []
    if df_merged.empty or report_df.empty:
        return insights

    team_dur = report_df.groupby("TEAM")["raw_dur_sec"].mean().sort_values(ascending=False)
    if len(team_dur) >= 1:
        top_team = team_dur.index[0]
        top_val  = format_dur_hm(team_dur.iloc[0])
        insights.append({
            "type": "good", "icon": "🏆",
            "title": f"Top Team by Avg Call Duration: {top_team}",
            "body": f"Averaging {top_val} of qualifying call duration per agent — highest across all teams."
        })

    exclude_teams = ['Others', 'CD - Community Manager', 'CD - Community', 'Criminal - Community Manager',
                     'Criminal - Community', 'ID - Community Manager', 'ID - Community',
                     'Clerkship community', 'Women ai - Community']

    manual_df = df_merged[(df_merged['source'] == 'Manual') & (~df_merged['Team Name'].isin(exclude_teams))]
    if not manual_df.empty:
        man_counts = manual_df.groupby('Team Name').agg(
            total_manual=('source', 'count'),
            unique_agents=('call_owner', 'nunique')
        ).sort_values('total_manual', ascending=False)
        if not man_counts.empty:
            top_man_team = man_counts.index[0]
            insights.append({
                "type": "bad", "icon": "⚠️",
                "title": f"Focus Required: {top_man_team} (Highest manual calls)",
                "body": f"Total {int(man_counts.iloc[0]['total_manual'])} Manual Calls are getting dialled by {int(man_counts.iloc[0]['unique_agents'])} agents."
            })

    df_merged['_ans'] = df_merged['status'].str.lower() == 'answered'
    pur = df_merged.groupby('Team Name')['_ans'].mean().mul(100).round(1)
    best_pur  = pur.idxmax()
    worst_pur = pur.idxmin()
    if best_pur != worst_pur:
        insights.append({
            "type": "info", "icon": "🔔",
            "title": f"Pick-Up Ratio Spread: {best_pur} vs {worst_pur}",
            "body": (f"{best_pur} leads at {pur[best_pur]}% answer rate. "
                     f"{worst_pur} trails at {pur[worst_pur]}%. "
                     f"Gap of {round(pur[best_pur]-pur[worst_pur],1)} pp — review missed-call handling in {worst_pur}.")
        })

    long_rate = report_df.groupby("TEAM").apply(
        lambda g: g["20+ MIN CALLS"].sum() / g["TOTAL CALLS"].sum() * 100
        if g["TOTAL CALLS"].sum() > 0 else 0
    ).round(2)
    if not long_rate.empty:
        best_long = long_rate.idxmax()
        insights.append({
            "type": "good", "icon": "💬",
            "title": f"Highest Deep-Engagement Rate: {best_long}",
            "body": (f"{long_rate[best_long]}% of calls in {best_long} exceed 20 minutes — "
                     f"a strong signal of qualified prospect conversations. Replicate best practices across other teams.")
        })

    break_df = report_df[~report_df["TEAM"].isin(exclude_teams)]
    remarks_series = break_df["REMARKS"].str.contains("Excessive Breaks", na=False)
    if remarks_series.sum() > 0:
        b_teams = break_df.loc[remarks_series, "TEAM"].value_counts().idxmax()
        b_count = remarks_series.sum()
        insights.append({
            "type": "warn", "icon": "⏸️",
            "title": f"Break Discipline Alert — {b_teams}",
            "body": f"{b_count} agent(s) flagged for excessive breaks (>2 breaks ≥15 min/day). Heaviest cluster in {b_teams}."
        })

    prod_df = report_df[~report_df["TEAM"].isin(exclude_teams)]
    if not prod_df.empty:
        team_avg_prod = prod_df.groupby("TEAM")["raw_prod_sec"].mean().sort_values()
        if not team_avg_prod.empty:
            worst_prod_team = team_avg_prod.index[0]
            agent_count = len(prod_df[prod_df["TEAM"] == worst_prod_team])
            insights.append({
                "type": "bad", "icon": "⏱️",
                "title": f"Focus Required: Lowest Productive Hours: {worst_prod_team}",
                "body": f"{agent_count} agents on {worst_prod_team} team have the least average productive hours as compared to other teams."
            })

    return insights


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.markdown("""
<div style='padding:.6rem 0 .4rem; text-align:center;'>
    <div style='display:flex; align-items:center; justify-content:center; gap:0; margin-bottom:.3rem;'>
        <span style='font-size:.85rem; font-weight:700; color:#FFFFFF; letter-spacing:-.3px;'>LawSikho</span>
        <div style='width:1px; height:18px; margin:0 .6rem;
                    background:linear-gradient(180deg,transparent,rgba(249,115,22,.9),transparent);
                    box-shadow:0 0 6px rgba(249,115,22,.5);'></div>
        <span style='font-size:.85rem; font-weight:700; color:#FFFFFF; letter-spacing:-.3px;'>Skill Arbitrage</span>
    </div>
    <div style='font-size:.58rem; color:rgba(255,255,255,.3); letter-spacing:.8px;
                font-family:monospace; margin-bottom:.9rem;'>India Learning 📖 India Earning</div>
    <div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                color:var(--text-muted,#6B7280);margin-bottom:.5rem;'>Report Controls</div>
</div>
""", unsafe_allow_html=True)

min_d, max_d = get_available_dates()
selected_dates = st.sidebar.date_input(
    "📅 Date Range", value=(max_d, max_d),
    min_value=min_d, max_value=max_d, format="DD-MM-YYYY"
)
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

teams, verticals, df_team_mapping = get_metadata()
selected_vertical = st.sidebar.multiselect("👑 Filter by Vertical", options=verticals)
selected_team     = st.sidebar.multiselect("👥 Filter by Team",       options=teams)
search_query      = st.sidebar.text_input("👤 Search By Name")

st.sidebar.markdown("<div style='margin:.5rem 0'></div>", unsafe_allow_html=True)
gen_dynamic = st.sidebar.button("🚀 Generate Dynamic Report")
st.sidebar.markdown("<div style='margin:.3rem 0'></div>", unsafe_allow_html=True)
gen_static  = st.sidebar.button("📅 Generate Duration Report")

st.sidebar.divider()
st.sidebar.markdown("""
<div style='font-size:.72rem; color:var(--text-muted,#6B7280); font-weight:500; letter-spacing:0.3px;'>
    <span style='font-size:.65rem; opacity:.75;'>For Internal Use of Sales and Operations Team Only.<br>All Rights Reserved.</span><br><br>
    DESIGNED BY: <b>AMIT RAY</b><br>
    <a href="mailto:amitray@lawsikho.com" style="color:#F97316; text-decoration:none;">amitray@lawsikho.com</a>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────

last_update_str = get_global_last_update()
display_start   = start_date.strftime('%d-%m-%Y')
display_end     = end_date.strftime('%d-%m-%Y')

st.markdown(f"""
<div class="cw-header">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:.75rem;">
        <div>
            <div class="cw-title">🔔 CALLING METRICS</div>
            <div class="cw-subtitle">DURATION PERIOD&nbsp;·&nbsp; {display_start} to {display_end}</div>
        </div>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-top:.25rem;">
            <span class="cw-badge"><span class="cw-pulse"></span>OZONETEL &amp; ACEFONE</span>
            <span class="cw-badge">🕐 UPDATED AT: {last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs([
    "🚀 Dynamic Dashboard",
    "📅 Duration Report",
    "🧠 Insights & Leaderboard"
])


# ══════════════════════════════════════════════
# TAB 1 — DYNAMIC DASHBOARD
# ══════════════════════════════════════════════

with tab1:
    if gen_dynamic:
        with st.spinner("Calculating metrics…"):
            df_raw = fetch_call_data(start_date, end_date)
            if df_raw.empty:
                st.warning("No data found for the selected period.")
            else:
                df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
                df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
                df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
                df = df[df['call_owner'].notna() & (df['call_owner'] != '')]

                if selected_team:     df = df[df['Team Name'].isin(selected_team)]
                if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
                if search_query:      df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]

                if df.empty:
                    st.error("No results match the selected filters.")
                else:
                    report_df, total_duration_agg = process_metrics_logic(df)
                    report_df = report_df.sort_values(by="raw_dur_sec", ascending=False)
                    report_df['Rank'] = ""
                    if len(report_df) > 0: report_df.iloc[0, report_df.columns.get_loc('Rank')] = "🥇"
                    if len(report_df) > 1: report_df.iloc[1, report_df.columns.get_loc('Rank')] = "🥈"
                    if len(report_df) > 2: report_df.iloc[2, report_df.columns.get_loc('Rank')] = "🥉"

                    # ── Store for Insights tab ──
                    st.session_state['insights_df']     = df.copy()
                    st.session_state['insights_report'] = report_df.copy()
                    st.session_state['insights_source'] = "Dynamic Report"

                    section_header("🏆 TOP 3 PERFORMANCE HIGHLIGHTS")
                    top_cols = st.columns(3)

                    top_dur = report_df.iloc[0]
                    with top_cols[0]:
                        st.markdown(f"""
                        <div class="metric-card" style="border-top: 3px solid var(--gold);">
                            <div class="metric-label">🥇 TOP PERFORMER</div>
                            <div class="metric-value" style="font-size:1.1rem;">{top_dur['CALLER']}</div>
                            <div class="metric-delta">{top_dur['CALL DURATION > 3 MINS']} Duration</div>
                        </div>""", unsafe_allow_html=True)

                    top_calls = report_df.sort_values('TOTAL CALLS', ascending=False).iloc[0]
                    with top_cols[1]:
                        st.markdown(f"""
                        <div class="metric-card" style="border-top: 3px solid #F97316;">
                            <div class="metric-label">✆ HIGHEST CALLS</div>
                            <div class="metric-value" style="font-size:1.1rem;">{top_calls['CALLER']}</div>
                            <div class="metric-delta">{top_calls['TOTAL CALLS']} Total Calls</div>
                        </div>""", unsafe_allow_html=True)

                    top_long = report_df.sort_values('20+ MIN CALLS', ascending=False).iloc[0]
                    with top_cols[2]:
                        st.markdown(f"""
                        <div class="metric-card" style="border-top: 3px solid var(--bronze);">
                            <div class="metric-label">🗣️ DEEP ENGAGEMENT</div>
                            <div class="metric-value" style="font-size:1.1rem;">{top_long['CALLER']}</div>
                            <div class="metric-delta">{top_long['20+ MIN CALLS']} Long Calls</div>
                        </div>""", unsafe_allow_html=True)

                    section_header("SUMMARY METRICS")
                    ans_t = len(df[df['status'].str.lower() == 'answered'])
                    pur_val = f"{round(ans_t / len(df) * 100)}%" if len(df) > 0 else "0%"
                    kpis = [
                        ("Total Calls",    len(df),                                         "📲"),
                        ("Acefone Calls",  len(df[df['source'] == 'Acefone']),              "🔵"),
                        ("Ozonetel Calls", len(df[df['source'] == 'Ozonetel']),             "🟠"),
                        ("Manual Calls",   len(df[df['source'] == 'Manual']),               "✏️"),
                        ("Unique Leads",   df['unique_lead_id'].nunique(),                  "👤"),
                        ("Pick-Up Ratio",  pur_val,                                         "✅"),
                        ("Active Callers", len(report_df),                                  "🎙️"),
                        ("Avg Prod Hrs",   format_dur_hm(report_df["raw_prod_sec"].mean()), "⏱"),
                    ]

                    cols = st.columns(len(kpis))
                    for col, (label, val, icon) in zip(cols, kpis):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{icon} {label}</div>
                                <div class="metric-value">{val}</div>
                            </div>""", unsafe_allow_html=True)

                    st.divider()
                    section_header("AGENT PERFORMANCE TABLE")

                    total_row = pd.DataFrame([{
                        "Rank": "",
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
                        "Rank", "IN/OUT TIME", "CALLER", "TEAM", "TOTAL CALLS", "CALL STATUS",
                        "PICK UP RATIO %", "CALLS > 3 MINS", "CALLS 15-20 MINS",
                        "20+ MIN CALLS", "CALL DURATION > 3 MINS",
                        "PRODUCTIVE HOURS", "BREAKS (>=15 MINS)", "REMARKS"
                    ]

                    final_df = pd.concat([report_df, total_row], ignore_index=True)
                    st.dataframe(
                        final_df.style.apply(style_total, axis=1)
                                      .set_properties(**{'white-space': 'pre-wrap'}),
                        column_order=display_cols,
                        use_container_width=True, hide_index=True
                    )

                    st.divider()
                    target_cols = [
                        "client_number", "call_datetime", "call_starttime_clean",
                        "call_endtime_clean", "call_duration", "status", "direction",
                        "service", "reason", "call_owner", "Call Date",
                        "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                    ]
                    existing_cols = [c for c in target_cols if c in df.columns]
                    st.download_button(
                        label="📥 Download CDR",
                        data=df[existing_cols].to_csv(index=False).encode('utf-8'),
                        file_name="CDR_LOG.csv", mime='text/csv'
                    )
    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>🚀</div>
            <div style='font-size:.9rem;font-weight:600;'>Select a date range and click <b>Generate Dynamic Report</b></div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — DURATION REPORT
# ══════════════════════════════════════════════

with tab2:
    if gen_static:
        with st.spinner("Building static layouts…"):
            df_raw = fetch_call_data(start_date, end_date)
            if df_raw.empty:
                st.warning("No data found.")
            else:
                df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
                df_static_master = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
                df_static_master['call_owner'] = df_static_master['Caller Name'].fillna(df_static_master['call_owner'])

                if selected_team:     df_static_master = df_static_master[df_static_master['Team Name'].isin(selected_team)]
                if selected_vertical: df_static_master = df_static_master[df_static_master['Vertical'].isin(selected_vertical)]
                if search_query:      df_static_master = df_static_master[df_static_master['call_owner'].str.contains(search_query, case=False, na=False)]

                if df_static_master.empty:
                    st.error("No results match filters.")
                else:
                    tl_ad_mask = pd.Series(False, index=df_static_master.index)
                    for col in df_team_mapping.columns:
                        if col in df_static_master.columns:
                            clean_col = df_static_master[col].fillna('').astype(str).str.strip().str.upper()
                            tl_ad_mask |= clean_col.isin(['TL', 'ATL', 'AD', 'TEAM LEAD', 'TEAM LEADER'])

                    static_display_cols = [
                        "CALLER", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %",
                        "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS",
                        "CALL DURATION > 3 MINS"
                    ]

                    normal_team_data = df_static_master[~tl_ad_mask]
                    normal_teams     = sorted(normal_team_data['Team Name'].dropna().unique())

                    for team in normal_teams:
                        team_df = normal_team_data[normal_team_data['Team Name'] == team]
                        report_df, team_dur_agg_sec = process_metrics_logic(team_df)
                        if team_dur_agg_sec > 0:
                            report_df = report_df.sort_values(by="raw_dur_sec", ascending=False)
                            st.markdown(f"""
                            <div class="static-team-header">
                                DURATION REPORT — {team.upper()} &nbsp;({display_start} to {display_end})
                            </div>""", unsafe_allow_html=True)

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
                            calc_h = (len(final_team_df) + 1) * 35 + 20
                            st.dataframe(
                                final_team_df.style.apply(style_static, axis=1)
                                                   .set_properties(**{'white-space': 'pre-wrap'}),
                                column_order=static_display_cols,
                                use_container_width=True, hide_index=True, height=calc_h
                            )

                            target_cols = [
                                "client_number", "call_datetime", "call_starttime_clean",
                                "call_endtime_clean", "call_duration", "status", "direction",
                                "service", "reason", "call_owner", "Call Date",
                                "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                            ]
                            existing_cols = [c for c in target_cols if c in team_df.columns]
                            st.download_button(
                                label=f"📥 Download CDR — {team}",
                                data=team_df[existing_cols].to_csv(index=False).encode('utf-8'),
                                file_name=f"CDR_{team}.csv", mime='text/csv',
                                key=f"dl_team_{team}"
                            )
                            st.divider()

                    tl_ad_pool = df_static_master[tl_ad_mask]
                    if not tl_ad_pool.empty:
                        report_df_tl, tl_dur_agg_sec = process_metrics_logic(tl_ad_pool)
                        active_tl = report_df_tl[report_df_tl['raw_dur_sec'] > 300].sort_values(by="raw_dur_sec", ascending=False)
                        if not active_tl.empty:
                            st.markdown(f"""
                            <div class="static-team-header">
                                TL'S DURATION REPORT &nbsp;({display_start} to {display_end})
                            </div>""", unsafe_allow_html=True)
                            total_row_tl = pd.DataFrame([{
                                "CALLER": "TOTAL",
                                "TOTAL CALLS": int(active_tl["TOTAL CALLS"].sum()),
                                "CALL STATUS": "-", "PICK UP RATIO %": "-",
                                "CALLS > 3 MINS": int(active_tl["CALLS > 3 MINS"].sum()),
                                "CALLS 15-20 MINS": int(active_tl["CALLS 15-20 MINS"].sum()),
                                "20+ MIN CALLS": int(active_tl["20+ MIN CALLS"].sum()),
                                "CALL DURATION > 3 MINS": format_dur_hm(active_tl["raw_dur_sec"].sum())
                            }])
                            final_tl_df = pd.concat([active_tl[static_display_cols], total_row_tl], ignore_index=True)
                            calc_h_tl = (len(final_tl_df) + 1) * 35 + 20
                            st.dataframe(
                                final_tl_df.style.apply(style_static, axis=1)
                                                 .set_properties(**{'white-space': 'pre-wrap'}),
                                column_order=static_display_cols,
                                use_container_width=True, hide_index=True, height=calc_h_tl
                            )
                            valid_tls    = active_tl['CALLER'].unique()
                            final_tl_cdr = tl_ad_pool[tl_ad_pool['call_owner'].isin(valid_tls)]
                            target_cols  = [
                                "client_number", "call_datetime", "call_starttime_clean",
                                "call_endtime_clean", "call_duration", "status", "direction",
                                "service", "reason", "call_owner", "Call Date",
                                "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"
                            ]
                            existing_cols = [c for c in target_cols if c in final_tl_cdr.columns]
                            st.download_button(
                                label="📥 Download TL CDR",
                                data=final_tl_cdr[existing_cols].to_csv(index=False).encode('utf-8'),
                                file_name="CDR_TL_AD.csv", mime='text/csv',
                                key="dl_tl_ad_final_last"
                            )

                    # ── Store full dataset for Insights tab ──
                    report_all, _ = process_metrics_logic(
                        df_static_master[df_static_master['call_owner'].notna() & (df_static_master['call_owner'] != '')]
                    )
                    st.session_state['insights_df']     = df_static_master.copy()
                    st.session_state['insights_report'] = report_all.copy()
                    st.session_state['insights_source'] = "Duration Report"

    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>📅</div>
            <div style='font-size:.9rem;font-weight:600;'>Click <b>Generate Duration Report</b> in the sidebar</div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 3 — INSIGHTS (auto-populated from session state)
# ══════════════════════════════════════════════

with tab3:
    if 'insights_df' in st.session_state and 'insights_report' in st.session_state:
        df_ins       = st.session_state['insights_df']
        report_df_all = st.session_state['insights_report']
        source_label  = st.session_state.get('insights_source', 'Report')

        st.markdown(f"""
        <div style='text-align:center;margin-bottom:1rem;'>
            <span style='font-size:.75rem;font-weight:600;color:#F97316;
                         background:rgba(249,115,22,.1);border:1px solid rgba(249,115,22,.2);
                         border-radius:20px;padding:4px 14px;font-family:DM Mono,monospace;'>
                ⚡ AUTO-GENERATED FROM {source_label.upper()}
            </span>
        </div>""", unsafe_allow_html=True)

        section_header("🧠 GENERATED TEAM INSIGHTS")
        insights = compute_team_insights(df_ins, report_df_all)

        if insights:
            cols_ins = st.columns(2)
            for i, ins in enumerate(insights):
                with cols_ins[i % 2]:
                    st.markdown(f"""
                    <div class="insight-card {ins['type']}">
                        <div style='display:flex;align-items:center;justify-content:center;gap:.4rem;'>
                            <span class="insight-icon">{ins['icon']}</span>
                            <span class="insight-title">{ins['title']}</span>
                        </div>
                        <div class="insight-body">{ins['body']}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("Not enough data to generate comparative insights.")

        st.divider()

        if not selected_team and not search_query:
            section_header("🏅 TEAM LEADERBOARD")
            lb = (
                report_df_all.groupby("TEAM")
                .agg(
                    agents=("CALLER", "count"),
                    total_calls=("TOTAL CALLS", "sum"),
                    total_dur_h=("raw_dur_sec", lambda x: round(x.sum() / 3600, 1)),
                    avg_dur_h=("raw_dur_sec", lambda x: round(x.mean() / 3600, 1)),
                    avg_prod_h=("raw_prod_sec", lambda x: round(x.mean() / 3600, 1)),
                    long_calls=("20+ MIN CALLS", "sum"),
                )
                .reset_index().sort_values("total_dur_h", ascending=False)
                .rename(columns={
                    "TEAM": "Team", "agents": "Agents", "total_calls": "Total Calls",
                    "total_dur_h": "Total Dur (h)", "avg_dur_h": "Avg Dur/Agent (h)",
                    "avg_prod_h": "Avg Prod Hrs (h)", "long_calls": "20+ Min Calls"
                })
            )
            medals = (["🥇", "🥈", "🥉"] + [""] * max(0, len(lb) - 3))[:len(lb)]
            lb.insert(0, "🏅", medals)
            lb = lb.reset_index(drop=True)
            st.dataframe(lb, use_container_width=True, hide_index=True)

    else:
        # Nothing generated yet
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>🧠</div>
            <div style='font-size:.9rem;font-weight:600;'>
                Generate a <b>Dynamic Report</b> or <b>Duration Report</b> first —<br>
                Insights will appear here automatically.
            </div>
        </div>""", unsafe_allow_html=True)
