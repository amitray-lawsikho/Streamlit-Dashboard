import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import pytz
import plotly.express as px

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
st.set_page_config(layout="wide", page_title="CALLERWISE DURATION METRICS", initial_sidebar_state="expanded")

# --- CLEAN UI CSS ---
st.markdown("""
<style>
header[data-testid="stHeader"] { visibility: visible !important; }
footer {visibility: hidden;}
[data-testid="stMainViewContainer"] { padding-top: 2rem; }
[data-testid="stStatusWidget"], .stStatusWidget { display: none !important; visibility: hidden !important; }

div[data-testid="stDataFrame"] thead tr th {
    background-color: #000000 !important;
    color: #ffffff !important;
    text-align: center !important;
    padding: 10px !important;
}

.static-team-header {
    text-align: center;
    margin-top: 40px;
    margin-bottom: 10px;
    font-size: 1.2rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# --- GLOBAL HELPER FUNCTIONS ---
def style_total(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #f0f2f6; color: #000000'] * len(row)
    return [''] * len(row)

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    tm = int(round(total_seconds / 60))
    return f"{tm // 60}h {tm % 60}m"

# --- 3. Data Fetching Functions ---
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
    except: return "N/A"

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
            agent_valid_dur += day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
            
            if timed_group.empty: continue

            first_start = timed_group['call_starttime'].min()
            last_end = timed_group['call_endtime'].max()
            daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {first_start.strftime('%I:%M %p')} · Out {last_end.strftime('%I:%M %p')}")
            
            start_off = ist_tz.localize(datetime.combine(c_date, time(10, 0)))
            end_off = ist_tz.localize(datetime.combine(c_date, time(20, 0)))
            
            day_breaks, day_break_sec = [], 0

            if first_start > start_off:
                gap = (first_start - start_off).total_seconds()
                if gap >= 900:
                    day_breaks.append({'s': start_off, 'e': first_start, 'dur': gap})
                    day_break_sec += gap
            if len(timed_group) > 1:
                for i in range(len(timed_group)-1):
                    gap_s, gap_e = timed_group['call_endtime'].iloc[i], timed_group['call_starttime'].iloc[i+1]
                    if gap_e > gap_s:
                        gap = (gap_e - gap_s).total_seconds()
                        if gap >= 900:
                            day_breaks.append({'s': gap_s, 'e': gap_e, 'dur': gap})
                            day_break_sec += gap
            if last_end < end_off:
                gap = (end_off - last_end).total_seconds()
                if gap >= 900:
                    day_breaks.append({'s': last_end, 'e': end_off, 'dur': gap})
                    day_break_sec += gap

            total_break_sec_all_days += day_break_sec
            if day_breaks:
                b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks ({format_dur_hm(day_break_sec)})"
                daily_break_list.append(b_str)
            
            if first_start > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
            if last_end < end_off: all_issues.append("Early Check-Out")
            if (36000 - day_break_sec) < 18000: all_issues.append("Less Productive")
                
        total_duration_agg += agent_valid_dur
        prod_sec_total = (36000 * total_active_days) - total_break_sec_all_days
        
        agents_list.append({
            "IN/OUT TIME": "\n".join(daily_io_list), "CALLER": owner,
            "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others",
            "TOTAL CALLS": int(total_calls), "CALL STATUS": f"{total_ans} Ans / {total_miss} Unans",
            "PICK UP RATIO %": f"{round((total_ans/total_calls*100)) if total_calls>0 else 0}%",
            "CALLS > 3 MINS": int(total_above_3min), "CALLS 15-20 MINS": int(total_mid_calls),
            "20+ MIN CALLS": int(total_long_calls), "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur),
            "PRODUCTIVE HOURS": format_dur_hm(prod_sec_total), "BREAKS (>=15 MINS)": "\n---\n".join(daily_break_list) if daily_break_list else "0",
            "REMARKS": ", ".join(sorted(list(set(all_issues)))) if all_issues else "None", "raw_prod_sec": prod_sec_total,
            "raw_dur_sec": agent_valid_dur
        })
    return pd.DataFrame(agents_list), total_duration_agg

# --- 4. Sidebar Filters ---
st.sidebar.header("Report Filters")
min_d, max_d = get_available_dates()
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_d, max_d), min_value=min_d, max_value=max_d)
teams, verticals, df_team_mapping = get_metadata()
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
selected_vertical = st.sidebar.multiselect("Filter by Vertical", options=verticals)
search_query = st.sidebar.text_input("🔍 Search Name")
gen_dynamic = st.sidebar.button("Generate Dynamic Report")
gen_static = st.sidebar.button("Generate Static Report")

# --- 5. Main UI Header ---
last_update_str = get_global_last_update()
st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>DURATION METRICS - LAWSIKHO & SKILL ARBITRAGE</h1>", unsafe_allow_html=True)

# Restoring the Report Period and Last Updated header cards
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    d_start, d_end = selected_dates[0].strftime('%d-%m-%Y'), selected_dates[1].strftime('%d-%m-%Y')
else:
    d_start = d_end = selected_dates.strftime('%d-%m-%Y')

h_col1, h_col2 = st.columns([3, 1])
with h_col1:
    st.markdown(f"<p style='color: #A0A0A0;'>Report Period: <b>{d_start}</b> to <b>{d_end}</b></p>", unsafe_allow_html=True)
with h_col2:
    st.markdown(f"<p style='color: #A0A0A0; text-align: right;'>Last Updated: <b>{last_update_str}</b></p>", unsafe_allow_html=True)
st.divider()

tab1, tab2 = st.tabs(["🚀 Dynamic Dashboard", "📅 Duration Report"])

with tab1:
    if gen_dynamic:
        df_raw = fetch_call_data(selected_dates[0], selected_dates[1])
        if not df_raw.empty:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False)]

            report_df, total_dur = process_metrics_logic(df)
            
            # FULL Detailed Summary Metrics (Restored)
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            m_col1.metric("Total Calls", len(df))
            m_col2.metric("Acefone Calls", len(df[df['source'] == 'Acefone']))
            m_col3.metric("Ozonetel Calls", len(df[df['source'] == 'Ozonetel']))
            m_col4.metric("Manual Calls", len(df[df['source'] == 'Manual']))
            
            m_col5, m_col6, m_col7, m_col8 = st.columns(4)
            m_col5.metric("Unique Leads", df['unique_lead_id'].nunique())
            ans_count = len(df[df['status'] == 'answered'])
            m_col6.metric("Pick Up %", f"{round(ans_count/len(df)*100)}%" if len(df)>0 else "0%")
            m_col7.metric("Avg Prod Hrs", format_dur_hm(report_df["raw_prod_sec"].mean()))
            m_col8.metric("Total Duration", format_dur_hm(total_dur))

            # Dynamic Table
            total_row = pd.DataFrame([{
                "CALLER": "TOTAL", "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                "CALL STATUS": "-", "PICK UP RATIO %": "-", "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                "CALLS 15-20 MINS": int(report_df["CALLS 15-20 MINS"].sum()), "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                "CALL DURATION > 3 MINS": format_dur_hm(total_dur), "PRODUCTIVE HOURS": format_dur_hm(report_df["raw_prod_sec"].sum())
            }])
            st.dataframe(pd.concat([report_df, total_row], ignore_index=True).style.apply(style_total, axis=1), use_container_width=True, hide_index=True)
            
            csv_data = df[["client_number", "call_starttime_clean", "call_endtime_clean", "call_duration", "status", "Team Name", "Vertical", "source"]].to_csv(index=False)
            st.download_button("📥 Download CDR", data=csv_data, file_name="CDR_LOG.csv")

            # --- STACKED CHART: CALLS BY VERTICAL (X=Count, Y=Vertical) ---
            st.divider()
            st.subheader("📊 Vertical Performance breakdown by Team")
            
            # Preparing chart data with Answered/Missed hover logic
            chart_df = df.groupby(['Vertical', 'Team Name']).agg(
                Total_Calls=('status', 'count'),
                Answered=('status', lambda x: (x.str.lower() == 'answered').sum()),
                Missed=('status', lambda x: (x.str.lower() == 'missed').sum())
            ).reset_index()

            fig = px.bar(chart_df, x="Total_Calls", y="Vertical", color="Team Name",
                         orientation='h',
                         hover_data=["Answered", "Missed"],
                         title="Call Volume: Verticals Stacked by Teams",
                         color_discrete_sequence=px.colors.qualitative.Prism)
            
            fig.update_layout(xaxis_title="Call Count", yaxis_title="Vertical Name", barmode='stack')
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    if gen_static:
        df_raw = fetch_call_data(selected_dates[0], selected_dates[1])
        if not df_raw.empty:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df_s = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df_s['call_owner'] = df_s['Caller Name'].fillna(df_s['call_owner'])
            
            for team in sorted(df_s['Team Name'].dropna().unique()):
                team_df = df_s[df_s['Team Name'] == team]
                rep, dur = process_metrics_logic(team_df)
                st.markdown(f"<div class='static-team-header'>DURATION REPORT - {team.upper()}</div>", unsafe_allow_html=True)
                st.dataframe(rep[["CALLER", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "CALL DURATION > 3 MINS"]], use_container_width=True, hide_index=True)
                st.divider()
