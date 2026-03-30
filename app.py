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

.brand-name {
    font-size: .85rem;
    font-weight: 700;
    letter-spacing: -.3px;
    color: #111827;
}
[data-theme="dark"] .brand-name { color: #FEF3E8 !important; }

.brand-tagline {
    font-size: .58rem;
    letter-spacing: .8px;
    font-family: monospace;
    margin-bottom: .9rem;
    color: #6B7280;
}
[data-theme="dark"] .brand-tagline { color: #D1A67A !important; }

.brand-tagline {
    font-size: .58rem;
    letter-spacing: .8px;
    font-family: monospace;
    margin-bottom: .9rem;
    color: #6B7280;
}
@media (prefers-color-scheme: dark) {
    .brand-tagline { color: #D1A67A; }
}
[data-theme="dark"] .brand-tagline { color: #D1A67A !important; }
[data-theme="light"] .brand-tagline { color: #6B7280 !important; }
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

def _unique_approvals(series):
    seen = {}
    for v in series.dropna().astype(str):
        v = v.strip()
        k = v.lower()
        if k and k not in seen:
            seen[k] = v
    return ", ".join(seen.values()) if seen else "—"

def style_team_manual_total(row):
    if row.get('TEAM') == 'TOTAL':
        return ['font-weight:bold;background-color:#374151;color:#FFFFFF;'] * len(row)
    return [''] * len(row)
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

def generate_calling_helper_pdf_bytes() -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.platypus import Flowable
    from reportlab.lib.enums import TA_CENTER
    import io

    buffer = io.BytesIO()
    ORANGE_DARK=colors.HexColor("#7c2d12"); ORANGE_MID=colors.HexColor("#431407")
    ORANGE_PALE=colors.HexColor("#FEF3E8"); ORANGE_ROW=colors.HexColor("#FFF8F3")
    GREY_DARK=colors.HexColor("#374151"); GREY_MID=colors.HexColor("#6B7280")
    WHITE=colors.white; BLACK=colors.HexColor("#111827"); W,H=A4

    def s(name,**kw):
        d=dict(fontName='Helvetica',fontSize=9,textColor=BLACK,spaceAfter=3,leading=14)
        d.update(kw); return ParagraphStyle(name,**d)

    S={'body':s('body'),
       'label':s('label',fontName='Helvetica-Bold',fontSize=8,textColor=ORANGE_DARK,spaceAfter=1),
       'formula':s('formula',fontName='Helvetica-Oblique',fontSize=8.5,textColor=colors.HexColor("#7c2d12"),backColor=ORANGE_PALE,leftIndent=8,rightIndent=8),
       'footer':s('footer',fontSize=7.5,textColor=GREY_MID,alignment=TA_CENTER)}

    class CoverBlock(Flowable):
        def __init__(self,w): Flowable.__init__(self); self.w=w; self.height=90
        def draw(self):
            c=self.canv
            c.setFillColor(ORANGE_DARK); c.rect(0,52,self.w,38,fill=1,stroke=0)
            c.setFillColor(ORANGE_MID);  c.rect(0,22,self.w,30,fill=1,stroke=0)
            c.setFillColor(colors.HexColor("#1c0700")); c.rect(0,0,self.w,22,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold",22)
            c.drawCentredString(self.w/2,66,"CALLING METRICS DASHBOARD")
            c.setFillColor(colors.HexColor("#FBBF24")); c.setFont("Helvetica-Bold",11)
            c.drawCentredString(self.w/2,34,"Logic & Metric Reference Guide")
            c.setFillColor(colors.HexColor("#FDE68A")); c.setFont("Helvetica",8.5)
            c.drawCentredString(self.w/2,8,"LawSikho & Skill Arbitrage  \u00b7  Sales & Operations Team  \u00b7  Internal Use Only")

    class SectionBanner(Flowable):
        def __init__(self,icon,title,color=None,w=None):
            Flowable.__init__(self); self.icon=icon; self.title=title
            self.color=color or ORANGE_DARK; self.w=w or (W-30*mm); self.height=22
        def draw(self):
            c=self.canv; c.setFillColor(self.color)
            c.roundRect(0,0,self.w,self.height,4,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold",11)
            c.drawString(10,6,f"{self.icon}  {self.title}")

    def btable(rows,cw=None):
        cw=cw or [44*mm,116*mm]
        data=[[Paragraph(f"<b>{r[0]}</b>",S['label']),Paragraph(r[1],S['body'])] for r in rows]
        t=Table(data,colWidths=cw,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,-1),ORANGE_PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#FDE68A")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,ORANGE_ROW]),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        return t

    def ltable(rows):
        data=[[Paragraph(f"<b>{r[0]}</b>",S['label']),Paragraph(r[1],S['formula'])] for r in rows]
        t=Table(data,colWidths=[52*mm,108*mm],hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#FDE68A")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,ORANGE_ROW]),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        return t

    SP=Spacer; BAN=SectionBanner; cw=W-30*mm
    HR=lambda: HRFlowable(width="100%",thickness=0.6,color=colors.HexColor("#FBBF24"),spaceAfter=6,spaceBefore=4)

    story=[
        SP(1,18*mm),CoverBlock(cw),SP(1,10*mm),
        Paragraph("This document explains every metric, table, tab, and column in the Calling Metrics Dashboard. Use it as a quick reference to understand how each number is calculated and what each section means.",S['body']),
        SP(1,6*mm),
        BAN("📋","SECTION 1 — DASHBOARD TABS OVERVIEW"),SP(1,3*mm),
        Paragraph("The dashboard has three tabs. Each serves a different purpose.",S['body']),SP(1,2*mm),
        btable([
            ("🚀 Dynamic Dashboard","The main report tab. Shows agent-level performance for the selected date range — Top 3 highlights, Summary KPIs, and the full Agent Performance Table. Click 'Generate Dynamic Report' in the sidebar to load it."),
            ("📅 Duration Report","A team-by-team breakdown showing call duration metrics only. Each team gets its own table sorted by call duration. TLs and ATLs are grouped separately at the bottom. Useful for sharing per-team performance without exposing cross-team data. Click 'Generate Duration Report' in the sidebar."),
            ("🧠 Insights & Leaderboard","Auto-populated from whichever report was generated last. Shows 5-6 auto-generated team insights and a Team Leaderboard table. No separate button needed — switch to this tab after generating any report."),
        ]),SP(1,6*mm),
        BAN("🏆","SECTION 2 — TOP 3 PERFORMANCE HIGHLIGHTS"),SP(1,3*mm),
        Paragraph("Three highlight cards at the top of the Dynamic Dashboard. Each picks the single best agent in one dimension.",S['body']),SP(1,2*mm),
        btable([
            ("🥇 Top Performer","Agent with the highest total Call Duration for calls above 3 minutes (raw_dur_sec). Agents are sorted by qualifying call duration descending — the top row wins this card."),
            ("✆ Highest Calls","Agent with the highest Total Calls count across all statuses (answered + missed). Sorted separately — a different agent may win this card."),
            ("🗣️ Deep Engagement","Agent with the most calls lasting 20 minutes or more (duration >= 1200 seconds). Signals high-quality prospect conversations."),
        ]),SP(1,6*mm),
        BAN("📊","SECTION 3 — SUMMARY METRICS (KPI CARDS)"),SP(1,3*mm),
        Paragraph("Eight KPI cards shown below the Top 3 highlights. Aggregate numbers across ALL agents and sources for the selected date range.",S['body']),SP(1,2*mm),
        ltable([
            ("Total Calls","Count of all call rows across Acefone + Ozonetel + Manual after filters applied."),
            ("Acefone Calls","Count of rows where source = 'Acefone'."),
            ("Ozonetel Calls","Count of rows where source = 'Ozonetel'."),
            ("Manual Calls","Count of rows where source = 'Manual'. Calls logged manually by agents and approved — not system-generated CDR."),
            ("Unique Leads","Count of distinct phone numbers across all sources. One lead dialled multiple times still counts as 1 unique lead."),
            ("Pick-Up Ratio","Answered Calls / Total Calls x 100, rounded to nearest whole percent. Answered = rows where status = 'answered'."),
            ("Active Callers","Count of distinct agents in the report after all filters. Only agents with at least one call in the date range are counted."),
            ("Avg Prod Hrs","Average Productive Hours across all active agents. Productive Hours = (10 hrs x active days) - total break time >= 15 mins. Shown as Xh Ym."),
        ]),SP(1,6*mm),
        BAN("📋","SECTION 4 — AGENT PERFORMANCE TABLE"),SP(1,3*mm),
        Paragraph("Main data table in the Dynamic Dashboard. One row per active agent, sorted by Call Duration > 3 Mins descending. Top 3 rows get medal emojis. A bold TOTAL row is appended at the bottom.",S['body']),SP(1,2*mm),
        btable([
            ("Rank","Medal emoji for top 3 agents by call duration: Gold, Silver, Bronze."),
            ("IN/OUT TIME","First call start (In) and last call end (Out) per day. Format: DD/MM: In HH:MM AM/PM . Out HH:MM AM/PM. Derived from call_starttime and call_endtime after IST conversion."),
            ("CALLER","Agent name from the team sheet, normalised via lowercase merge key. Falls back to raw system name if not matched."),
            ("TEAM","Team name from the team sheet. Shows 'Others' if the agent is unmatched."),
            ("TOTAL CALLS","All calls for this agent in the date range — all statuses combined."),
            ("CALL STATUS","'X Ans / Y Unans' — count of answered and missed/unanswered calls for this agent."),
            ("PICK UP RATIO %","Answered / Total Calls x 100 for this agent, rounded to nearest whole percent."),
            ("CALLS > 3 MINS","Count of calls where duration >= 180 seconds. Qualifying threshold for duration metrics."),
            ("CALLS 15-20 MINS","Count of calls where duration >= 900 seconds AND < 1200 seconds. Mid-range engagement."),
            ("20+ MIN CALLS","Count of calls where duration >= 1200 seconds. Deep engagement indicator."),
            ("CALL DURATION > 3 MINS","Sum of duration for calls >= 3 minutes, shown as Xh Ym."),
            ("PRODUCTIVE HOURS","(10 hrs x active days) - total break time >= 15 mins. Shown as Xh Ym."),
            ("BREAKS (>=15 MINS)","Gaps between calls of 15+ minutes shown per day with time ranges. Gaps < 15 mins are ignored."),
            ("REMARKS","Auto-flagged issues: Late Check-In (first call after 10:15 AM), Early Check-Out (last call before 8 PM), Low Calls (<40 qualifying/day), Low Duration (<3h 15m/day), Excessive Breaks (>2 breaks >= 15 mins/day), Less Productive (<5 hrs productive/day)."),
        ],cw=[46*mm,114*mm]),SP(1,6*mm),
        BAN("📅","SECTION 5 — DURATION REPORT TAB"),SP(1,3*mm),
        Paragraph("Generates a simplified shareable table per team showing duration columns only — no break details or remarks.",S['body']),SP(1,2*mm),
        btable([
            ("Team separation","Each team gets its own section and table. Teams with zero qualifying duration are skipped entirely."),
            ("TL / ATL separation","Agents flagged as TL, ATL, AD, Team Lead, or Team Leader in the team sheet are shown in a single 'TL Duration Report' section at the bottom. Only TLs with > 5 mins qualifying duration are included."),
            ("Columns shown","CALLER, TOTAL CALLS, CALL STATUS, PICK UP RATIO %, CALLS > 3 MINS, CALLS 15-20 MINS, 20+ MIN CALLS, CALL DURATION > 3 MINS. Same definitions as Section 4."),
            ("Sorting","Within each team table, agents are sorted by Call Duration > 3 Mins descending."),
            ("TOTAL row","Each team table has a TOTAL row summing calls and duration."),
            ("CDR per team","Each team section has its own Download CDR button exporting only that team's raw records."),
        ]),SP(1,6*mm),
        BAN("🏅","SECTION 6 — TEAM LEADERBOARD (INSIGHTS TAB)"),SP(1,3*mm),
        Paragraph("Appears in the Insights tab. Aggregates all agents by team, ranked by total call duration descending. Only shown when no Team or Name filter is active.",S['body']),SP(1,2*mm),
        ltable([
            ("Team","Team name from the team sheet."),
            ("Agents","Count of distinct agents from this team in the report."),
            ("Total Calls","Sum of all calls across all agents in this team."),
            ("Total Dur (h)","Sum of qualifying call duration (>3 min) in hours, 1 decimal place."),
            ("Avg Dur/Agent (h)","Total Duration divided by agent count for this team, in hours."),
            ("Avg Prod Hrs (h)","Average productive hours per agent in this team, in hours."),
            ("20+ Min Calls","Sum of 20+ minute calls across all agents in this team."),
            ("Medal","Gold, Silver, Bronze for the top 3 teams by Total Duration."),
        ]),SP(1,6*mm),
        BAN("📥","SECTION 7 — CDR DOWNLOAD COLUMNS"),SP(1,3*mm),
        Paragraph("The Download CDR button exports a CSV of raw call detail records. Each row is one call.",S['body']),SP(1,2*mm),
        btable([
            ("client_number","Lead phone number. Unique lead identifier."),
            ("call_datetime","Original timestamp from the source system (UTC). For Ozonetel: call start. For Acefone: call end."),
            ("call_starttime_clean","Call start time in IST, timezone stripped. Used for break and productive hours calculations."),
            ("call_endtime_clean","Call end time in IST, timezone stripped. For Acefone: call_datetime. For Ozonetel: start + duration."),
            ("call_duration","Call duration in seconds. Zero-duration answered calls from Ozonetel are excluded before ingestion."),
            ("status","Call outcome: 'answered' or 'missed'. Ozonetel 'unanswered' mapped to 'missed'."),
            ("direction","Call direction: 'outbound' or 'inbound'. Ozonetel 'manual' mapped to 'outbound'."),
            ("service","Service or campaign name (Acefone only)."),
            ("reason","Disposition or reason code. For Manual calls this is the Approver name."),
            ("call_owner","Agent name after team sheet normalisation. Raw system name replaced by canonical Caller Name."),
            ("Call Date","Date of the call only. Used for day-level grouping."),
            ("updated_at_ampm","Timestamp when the record was last written to BigQuery, in AM/PM format."),
            ("Team Name","Team name from the team sheet, merged on lowercase agent name."),
            ("Vertical","Business vertical from the team sheet (e.g. Lawsikho, Skill Arbitrage)."),
            ("Analyst","Analyst name from the team sheet, if populated."),
            ("source","Data source: 'Acefone', 'Ozonetel', or 'Manual'."),
        ],cw=[46*mm,114*mm]),SP(1,6*mm),
        BAN("⚠️","SECTION 8 — HIGHEST MANUAL CALLS TABLE (DYNAMIC DASHBOARD)"),SP(1,3*mm),
        Paragraph("Appears below the CDR download button in the Dynamic Dashboard when manual calls exist in the selected date range. Shows agent-level manual call activity sorted by count descending. No medal ranking — manual calls are a flag, not an achievement.",S['body']),SP(1,2*mm),
        btable([
            ("CALLER",                "Agent name from the team sheet, same as the main performance table."),
            ("VERTICAL",              "Business vertical from the team sheet (e.g. Lawsikho, Skill Arbitrage)."),
            ("TEAM",                  "Team name from the team sheet."),
            ("MANUAL CALLS COUNT",    "Total number of manual call entries for this agent in the selected date range. Sorted descending — highest manual caller appears at top."),
            ("MANUAL CALLS DURATION", "Total duration of manual calls for this agent in Xh Ym format. Sourced from the call_duration column of the manual_calls BigQuery table."),
            ("APPROVED BY",           "Unique approver names from the Approved_By field, deduplicated case-insensitively (e.g. 'John', 'john', 'JOHN' collapse to one entry). Multiple unique approvers are separated by ', '."),
            ("TOTAL row",             "Bottom row summing Manual Calls Count and Duration across all agents shown."),
        ]),SP(1,6*mm),

        BAN("⚠️","SECTION 9 — TEAM MANUAL CALLS TABLE (INSIGHTS TAB)"),SP(1,3*mm),
        Paragraph("Appears at the bottom of the Insights & Leaderboard tab after generating any report. Shows the same manual call data aggregated by team instead of by agent. Sorted by Manual Calls Count descending.",S['body']),SP(1,2*mm),
        btable([
            ("VERTICAL",              "Business vertical from the team sheet."),
            ("TEAM",                  "Team name. The TOTAL row at the bottom sums across all teams."),
            ("MANUAL CALLS COUNT",    "Total manual calls across all agents in this team."),
            ("MANUAL CALLS DURATION", "Total manual call duration across all agents in this team, in Xh Ym format."),
            ("APPROVALS BY",          "All unique approver names across all agents in this team, deduplicated case-insensitively and joined by ', '."),
            ("Why no medals?",        "Manual calls indicate reliance on manual logging rather than system-dialled calls. High manual call counts may signal data quality gaps or agents bypassing the dialler. This table exists for monitoring, not ranking."),
        ]),SP(1,6*mm),

        BAN("📖","KEY TERMS GLOSSARY",color=GREY_DARK),SP(1,3*mm),
        btable([
            ("Qualifying Call","Any call with duration >= 180 seconds (3 minutes). Used for all duration metrics and performance flags."),
            ("Office Hours","10:00 AM to 8:00 PM IST (10 hours = 36,000 seconds). Reference window for breaks and productive hours."),
            ("Break","A gap between consecutive calls >= 900 seconds (15 minutes). Shorter gaps are ignored."),
            ("Productive Hours","(10 hrs x active days) - total break seconds. Expressed as Xh Ym."),
            ("Late Check-In","First call of the day starts after 10:15 AM IST."),
            ("Early Check-Out","Last call of the day ends before 8:00 PM IST."),
            ("Low Calls","Fewer than 40 qualifying calls (>3 min) in a single day."),
            ("Low Duration","Total qualifying duration < 3h 15m (11,700 seconds) in a single day."),
            ("Excessive Breaks","More than 2 breaks >= 15 minutes in a single day."),
            ("Less Productive","Productive seconds < 5 hours (18,000 seconds) in a single day."),
            ("Merge Key","Lowercase-stripped agent name used to join call data with the team sheet."),
            ("IST","Indian Standard Time (UTC+5:30). All timestamps are converted to IST for display and calculations."),
        ],cw=[46*mm,114*mm]),
        SP(1,8*mm),HR(),
        Paragraph("Designed by Amit Ray  \u00b7  amitray@lawsikho.com  \u00b7  For Internal Use of Sales and Operations Team Only. All Rights Reserved.",S['footer']),
    ]

    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=14*mm,title="Calling Metrics — Logic Reference Guide",author="Amit Ray")
    doc.build(story)
    return buffer.getvalue()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.markdown("""
<div style='padding:.6rem 0 .4rem; text-align:center;'>
    <div style='display:flex; align-items:center; justify-content:center; gap:0; margin-bottom:.3rem;'>
        <span class='brand-name'>LawSikho</span>
        <div style='width:1px; height:18px; margin:0 .6rem;
                    background:linear-gradient(180deg,transparent,rgba(249,115,22,.9),transparent);
                    box-shadow:0 0 6px rgba(249,115,22,.5);'></div>
        <span class='brand-name'>Skill Arbitrage</span>
    </div>
    <div class='brand-tagline'>India Learning 📖 India Earning</div>
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

st.sidebar.markdown("""
<hr style='border:none; border-top:1px solid #F97316; opacity:.4; margin:.6rem 0;'>
<div style='font-size:.72rem; color:var(--text-muted,#6B7280); font-weight:500; letter-spacing:0.3px;'>
    <span style='font-size:.65rem; opacity:.75; display:block; margin-bottom:.5rem;'>For Internal Use of Sales and Operations Team Only.<br>All Rights Reserved.</span>
    DESIGNED BY: <b>AMIT RAY</b><br>
    <a href="mailto:amitray@lawsikho.com" style="color:#F97316; text-decoration:none;">amitray@lawsikho.com</a>
</div>
""", unsafe_allow_html=True)

st.sidebar.download_button(
    label="📖 Metrics Guide (PDF)",
    data=generate_calling_helper_pdf_bytes(),
    file_name="Calling_Metrics_Logic_Guide.pdf",
    mime="application/pdf",
    key="dl_calling_helper_pdf"
)


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

                    # ── Manual Calls Table ──
                    manual_df_view = df[df['source'] == 'Manual'].copy()
                    if not manual_df_view.empty:
                        st.divider()
                        section_header("⚠️ HIGHEST MANUAL CALLS")

                        man_agg = (
                            manual_df_view.groupby('call_owner', sort=False)
                            .agg(
                                Vertical  = ('Vertical',      'first'),
                                Team      = ('Team Name',     'first'),
                                Count     = ('source',        'count'),
                                DurSec    = ('call_duration', 'sum'),
                                Approvals = ('reason',        _unique_approvals),
                            )
                            .reset_index()
                            .sort_values('Count', ascending=False)
                            .reset_index(drop=True)
                        )

                        man_display = pd.DataFrame({
                            'CALLER'               : man_agg['call_owner'],
                            'VERTICAL'             : man_agg['Vertical'].fillna('—'),
                            'TEAM'                 : man_agg['Team'].fillna('—'),
                            'MANUAL CALLS COUNT'   : man_agg['Count'],
                            'MANUAL CALLS DURATION': man_agg['DurSec'].apply(format_dur_hm),
                            'APPROVED BY'          : man_agg['Approvals'],
                        })

                        total_man_row = pd.DataFrame([{
                            'CALLER'               : 'TOTAL',
                            'VERTICAL'             : '—',
                            'TEAM'                 : '—',
                            'MANUAL CALLS COUNT'   : int(man_agg['Count'].sum()),
                            'MANUAL CALLS DURATION': format_dur_hm(man_agg['DurSec'].sum()),
                            'APPROVED BY'          : '—',
                        }])

                        man_final = pd.concat([man_display, total_man_row], ignore_index=True)
                        st.dataframe(
                            man_final.style.apply(style_total, axis=1),
                            use_container_width=True, hide_index=True
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

    # ── Team Manual Calls ──
        manual_team_df = df_ins[df_ins['source'] == 'Manual'].copy()
        if not manual_team_df.empty:
            st.divider()
            section_header("⚠️ TEAM MANUAL CALLS")

            team_man_agg = (
                manual_team_df.groupby('Team Name', sort=False)
                .agg(
                    Vertical  = ('Vertical',      'first'),
                    Count     = ('source',        'count'),
                    DurSec    = ('call_duration', 'sum'),
                    Approvals = ('reason',        _unique_approvals),
                )
                .reset_index()
                .sort_values('Count', ascending=False)
                .reset_index(drop=True)
            )

            team_man_display = pd.DataFrame({
                'VERTICAL'             : team_man_agg['Vertical'].fillna('—'),
                'TEAM'                 : team_man_agg['Team Name'],
                'MANUAL CALLS COUNT'   : team_man_agg['Count'],
                'MANUAL CALLS DURATION': team_man_agg['DurSec'].apply(format_dur_hm),
                'APPROVALS BY'         : team_man_agg['Approvals'],
            })

            total_team_man = pd.DataFrame([{
                'VERTICAL'             : '—',
                'TEAM'                 : 'TOTAL',
                'MANUAL CALLS COUNT'   : int(team_man_agg['Count'].sum()),
                'MANUAL CALLS DURATION': format_dur_hm(team_man_agg['DurSec'].sum()),
                'APPROVALS BY'         : '—',
            }])

            team_man_final = pd.concat([team_man_display, total_team_man], ignore_index=True)
            st.dataframe(
                team_man_final.style.apply(style_team_manual_total, axis=1),
                use_container_width=True, hide_index=True
            )

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
