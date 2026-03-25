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
    white-space: normal !important;
    word-wrap: break-word !important;
    text-align: center !important;
    vertical-align: middle !important;
    min-width: 100px !important;
    line-height: 1.2 !important;
    height: auto !important;
    padding: 10px !important;
}

.static-team-header {
    text-align: center;
    margin-top: 40px;
    margin-bottom: 10px;
    padding-bottom: 5px;
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

def style_static(row):
    if row["CALLER"] == "TOTAL":
        return ['font-weight: bold; background-color: #f0f2f6; color: #000000'] * len(row)
    return [''] * len(row)

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
        df_man['service'] = 'Manual'
        df_man['call_datetime'] = pd.NaT

    df = pd.concat([df_ace, df_ozo, df_man], ignore_index=True)
    if not df.empty:
        df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
        df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
        df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
        df['call_starttime_clean'] = df['call_starttime'].dt.tz_localize(None)
        df['call_endtime_clean'] = df['call_endtime'].dt.tz_localize(None)
    return df

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    tm = int(round(total_seconds / 60))
    return f"{tm // 60}h {tm % 60}m"

def get_display_gap_seconds(start_time, end_time):
    if pd.isna(start_time) or pd.isna(end_time): return 0
    s, e = start_time.replace(second=0, microsecond=0), end_time.replace(second=0, microsecond=0)
    return (e - s).total_seconds()

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
            
            day_breaks, day_break_sec = [], 0
            if first_call_start > start_office:
                g_start_sec = get_display_gap_seconds(start_office, first_call_start)
                if g_start_sec >= 900:
                    day_breaks.append({'s': start_office, 'e': first_call_start, 'dur': g_start_sec})
                    day_break_sec += g_start_sec
            if len(timed_group) > 1:
                for i in range(len(timed_group)-1):
                    act_s, act_e = max(timed_group['call_endtime'].iloc[i], start_office), min(timed_group['call_starttime'].iloc[i+1], end_office)
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
                for b in day_breaks: b_str += f"\n  {b['s'].strftime('%I:%M %p')}→{b['e'].strftime('%I:%M %p')} ({format_dur_hm(b['dur'])})"
                daily_break_list.append(b_str)
            
            if first_call_start > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
            if last_call_end < end_office: all_issues.append("Early Check-Out")
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
            "REMARKS": ", ".join(sorted(list(set(all_issues)))) if all_issues else "None", "raw_prod_sec": prod_sec_total, "raw_dur_sec": agent_valid_dur
        })
    return pd.DataFrame(agents_list), total_duration_agg

# --- 4. Sidebar ---
st.sidebar.header("Report Filters")
min_d, max_d = get_available_dates()
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_d, max_d), min_value=min_d, max_value=max_d)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
    ds_raw, de_raw = selected_dates[0].strftime('%Y/%m/%d'), selected_dates[1].strftime('%Y/%m/%d')
else:
    start_date = end_date = selected_dates
    ds_raw = de_raw = selected_dates.strftime('%Y/%m/%d')

teams, verticals, df_team_mapping = get_metadata()
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
selected_vertical = st.sidebar.multiselect("Filter by Vertical", options=verticals)
search_query = st.sidebar.text_input("🔍 Search Name")
gen_dynamic = st.sidebar.button("Generate Dynamic Report")
gen_static = st.sidebar.button("Generate Static Report")

# --- 5. Header ---
last_update_str = get_global_last_update()
st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>DURATION METRICS - LAWSIKHO & SKILL ARBITRAGE</h1>", unsafe_allow_html=True)
col_sub_l, col_sub_r = st.columns([3, 1])
with col_sub_l:
    st.markdown(f"<p style='color: #A0A0A0;'>Report Period: <b>{start_date.strftime('%d-%m-%Y')}</b> to <b>{end_date.strftime('%d-%m-%Y')}</b></p>", unsafe_allow_html=True)
with col_sub_r:
    st.markdown(f"<p style='color: #A0A0A0; text-align: right;'>Last Updated: <b>{last_update_str}</b></p>", unsafe_allow_html=True)
st.divider()

tab1, tab2 = st.tabs(["🚀 Dynamic Dashboard", "📅 Duration Report"])

with tab1:
    if gen_dynamic:
        df_raw = fetch_call_data(start_date, end_date)
        if not df_raw.empty:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False)]

            report_df, total_duration_agg = process_metrics_logic(df)
            report_df = report_df.sort_values(by="raw_dur_sec", ascending=False)
            
            # Metric Cards
            m_cols = st.columns(4)
            m_cols[0].metric("Total Calls", len(df))
            m_cols[1].metric("Acefone Calls", len(df[df['source'] == 'Acefone']))
            m_cols[2].metric("Ozonetel Calls", len(df[df['source'] == 'Ozonetel']))
            m_cols[3].metric("Manual Calls", len(df[df['source'] == 'Manual']))
            
            m_cols2 = st.columns(4)
            m_cols2[0].metric("Unique Leads", df['unique_lead_id'].nunique())
            m_cols2[1].metric("Pick Up %", f"{round(len(df[df['status']=='answered'])/len(df)*100)}%" if len(df)>0 else "0%")
            m_cols2[2].metric("Avg Productive Hours", format_dur_hm(report_df["raw_prod_sec"].mean()))
            m_cols2[3].metric("Total Duration", format_dur_hm(total_duration_agg))

            st.divider()
            display_cols = ["IN/OUT TIME", "CALLER", "TEAM", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS", "PRODUCTIVE HOURS", "BREAKS (>=15 MINS)", "REMARKS"]
            total_row = pd.DataFrame([{"CALLER": "TOTAL", "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()), "CALL STATUS": "", "PICK UP RATIO %": "", "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()), "CALLS 15-20 MINS": int(report_df["CALLS 15-20 MINS"].sum()), "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()), "CALL DURATION > 3 MINS": format_dur_hm(total_duration_agg), "PRODUCTIVE HOURS": format_dur_hm(report_df["raw_prod_sec"].sum()), "REMARKS": "" }])
            st.dataframe(pd.concat([report_df[display_cols], total_row], ignore_index=True).style.apply(style_total, axis=1), use_container_width=True, hide_index=True)

            # CDR Download
            cdr_csv = df.copy()
            target_cols = ["client_number", "call_datetime", "call_starttime_clean", "call_endtime_clean", "call_duration", "status", "direction", "service", "reason", "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"]
            existing_cols = [c for c in target_cols if c in cdr_csv.columns]
            st.download_button(label="📥 Download CDR", data=cdr_csv[existing_cols].to_csv(index=False).encode('utf-8'), file_name="CDR_LOG.csv", mime='text/csv')

            # Chart
            st.divider()
            st.subheader("📊 Vertical Performance breakdown by Team")
            chart_df = df.groupby(['Vertical', 'Team Name']).size().reset_index(name='Total_Calls')
            fig = px.bar(chart_df, x="Total_Calls", y="Vertical", color="Team Name", orientation='h', text="Total_Calls", title="Call Volume: Verticals Stacked by Teams")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    if gen_static:
        df_raw = fetch_call_data(start_date, end_date)
        if not df_raw.empty:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df_static = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df_static['call_owner'] = df_static['Caller Name'].fillna(df_static['call_owner'])
            
            tl_ad_mask = pd.Series(False, index=df_static.index)
            for col in df_team_mapping.columns:
                if col in df_static.columns:
                    tl_ad_mask |= df_static[col].fillna('').astype(str).str.strip().str.upper().isin(['TL', 'ATL', 'AD', 'TEAM LEAD', 'TEAM LEADER'])

            normal_team_data = df_static[~tl_ad_mask]
            static_display_cols = ["CALLER", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS"]
            
            for team in sorted(normal_team_data['Team Name'].dropna().unique()):
                team_df = normal_team_data[normal_team_data['Team Name'] == team]
                rep, team_dur = process_metrics_logic(team_df)
                if team_dur > 0:
                    st.markdown(f"<div class='static-team-header'>DURATION REPORT - {team.upper()} ({ds_raw} To {de_raw})</div>", unsafe_allow_html=True)
                    t_total = pd.DataFrame([{"CALLER": "TOTAL", "TOTAL CALLS": int(rep["TOTAL CALLS"].sum()), "CALL STATUS": "", "PICK UP RATIO %": "", "CALLS > 3 MINS": int(rep["CALLS > 3 MINS"].sum()), "CALLS 15-20 MINS": int(rep["CALLS 15-20 MINS"].sum()), "20+ MIN CALLS": int(rep["20+ MIN CALLS"].sum()), "CALL DURATION > 3 MINS": format_dur_hm(team_dur)}])
                    st.dataframe(pd.concat([rep[static_display_cols], t_total], ignore_index=True).style.apply(style_static, axis=1), use_container_width=True, hide_index=True)
                    target_cols = ["client_number", "call_datetime", "call_duration", "status", "direction", "service", "reason", "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"]
                    existing_cols = [c for c in target_cols if c in team_df.columns]
                    st.download_button(label=f"📥 Download CDR - {team}", data=team_df[existing_cols].to_csv(index=False).encode('utf-8'), file_name=f"CDR_{team}.csv", mime='text/csv', key=f"dl_{team}")
                    st.divider()

            tl_pool = df_static[tl_ad_mask]
            if not tl_pool.empty:
                rep_tl, tl_dur = process_metrics_logic(tl_pool)
                # Filter for active TLs as per previous logic
                rep_tl = rep_tl[rep_tl['raw_dur_sec'] > 300]
                if not rep_tl.empty:
                    st.markdown(f"<div class='static-team-header'>TL'S DURATION REPORT ({ds_raw} To {de_raw})</div>", unsafe_allow_html=True)
                    tl_total = pd.DataFrame([{"CALLER": "TOTAL", "TOTAL CALLS": int(rep_tl["TOTAL CALLS"].sum()), "CALL STATUS": "", "PICK UP RATIO %": "", "CALLS > 3 MINS": int(rep_tl["CALLS > 3 MINS"].sum()), "CALLS 15-20 MINS": int(rep_tl["CALLS 15-20 MINS"].sum()), "20+ MIN CALLS": int(rep_tl["20+ MIN CALLS"].sum()), "CALL DURATION > 3 MINS": format_dur_hm(rep_tl['raw_dur_sec'].sum())}])
                    st.dataframe(pd.concat([rep_tl[static_display_cols], tl_total], ignore_index=True).style.apply(style_static, axis=1), use_container_width=True, hide_index=True)
                    target_cols = ["client_number", "call_datetime", "call_duration", "status", "direction", "service", "reason", "call_owner", "Call Date", "updated_at_ampm", "Team Name", "Vertical", "Analyst", "source"]
                    valid_tls = rep_tl['CALLER'].unique()
                    final_tl_cdr = tl_pool[tl_pool['call_owner'].isin(valid_tls)]
                    existing_cols = [c for c in target_cols if c in final_tl_cdr.columns]
                    st.download_button(label="📥 Download TL CDR", data=final_tl_cdr[existing_cols].to_csv(index=False).encode('utf-8'), file_name="CDR_TL_AD.csv", mime='text/csv', key="dl_tl")
