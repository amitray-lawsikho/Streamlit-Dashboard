import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date
import os
import json

# --- 1. Cloud Credentials Setup ---
# This part checks if we are on the Cloud (Secrets) or Local (File)
if "gcp_service_account" in st.secrets:
    # For Streamlit Cloud Deployment
    info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    # For your local testing / Colab
    SERVICE_ACCOUNT_FILE = "/content/drive/MyDrive/Lawsikho/credentials/bigquery_key.json"
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        client = bigquery.Client()
    else:
        st.error("Credentials not found!")

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"

# --- 2. Page Configuration ---
st.set_page_config(layout="wide", page_title="CALLERWISE DURATION METRICS")

# --- 3. Data Fetching Functions ---
@st.cache_data(ttl=3600)
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip()
    teams = sorted(df_meta['Team Name'].dropna().unique())
    verticals = sorted(df_meta['Vertical'].dropna().unique())
    return teams, verticals, df_meta

@st.cache_data(ttl=60)
def get_global_last_update():
    query = "SELECT MAX(updated_at_ampm) as last_update FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    try:
        res = client.query(query).to_dataframe()
        return res['last_update'].iloc[0] if not res.empty else "N/A"
    except: return "N/A"

@st.cache_data(ttl=3600)
def get_available_dates():
    query = "SELECT MIN(DATE(call_datetime)) as min_date, MAX(DATE(call_datetime)) as max_date FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    df_dates = client.query(query).to_dataframe()
    if not df_dates.empty and not pd.isna(df_dates['min_date'].iloc[0]):
        return df_dates['min_date'].iloc[0], df_dates['max_date'].iloc[0]
    return date.today(), date.today()

def fetch_call_data(start_date, end_date):
    query = f"""
    SELECT *
    FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
    WHERE DATE(call_datetime) BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY call_owner, call_datetime ASC
    """
    return client.query(query).to_dataframe()

def format_duration_clean(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

# --- 4. Sidebar Filters ---
st.sidebar.header("Report Filters")
min_d, max_d = get_available_dates()
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_d, max_d), min_value=min_d, max_value=max_d)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

teams, verticals, df_team_mapping = get_metadata()
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
selected_vertical = st.sidebar.multiselect("Filter by Vertical", options=verticals)
search_query = st.sidebar.text_input("🔍 Search Agent Name")

# --- 5. Header Section ---
st.markdown("<h1 style='text-align: center; margin-bottom: 5px; font-family: sans-serif;'>CALLERWISE DURATION METRICS</h1>", unsafe_allow_html=True)
sub_style = "font-size: 15px; color: #A0A0A0; font-family: sans-serif; margin-top: 0px;"

col_sub_l, col_sub_r = st.columns([3, 1])
with col_sub_l:
    st.markdown(f"<p style='{sub_style}'>Report Period: <b>{start_date}</b> to <b>{end_date}</b></p>", unsafe_allow_html=True)
with col_sub_r:
    last_up = get_global_last_update()
    st.markdown(f"<p style='{sub_style} text-align: right;'>System Last Updated: <b>{last_up}</b></p>", unsafe_allow_html=True)

st.divider()

# --- 6. Main Logic ---
if st.sidebar.button("Generate Report"):
    with st.spinner('Calculating metrics...'):
        df_raw = fetch_call_data(start_date, end_date)
        
        if df_raw.empty:
            st.warning("No data found for selection.")
        else:
            df = pd.merge(df_raw, df_team_mapping, left_on='call_owner', right_on='Caller Name', how='left')
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]
            
            if df.empty:
                st.error("No results match filters.")
            else:
                agents = []
                for owner, group in df.groupby('call_owner'):
                    group = group.sort_values('call_datetime')
                    daily_max = group.groupby(group['call_datetime'].dt.date)['call_duration'].max()
                    num_active_days = len(daily_max[daily_max >= 180])
                    total_calls_count = len(group)
                    long_calls_count = len(group[group['call_duration'] >= 1200])
                    above_3min_count = len(group[group['call_duration'] >= 180])
                    valid_mask = group['call_duration'] >= 180
                    total_valid_duration = group.loc[valid_mask, 'call_duration'].sum()
                    
                    total_break_secs = 0
                    break_count = 0
                    if len(group) > 1:
                        group['prev_end'] = group['call_datetime'] + pd.to_timedelta(group['call_duration'], unit='s')
                        group['gap'] = (group['call_datetime'].shift(-1) - group['prev_end']).dt.total_seconds()
                        long_breaks = group[group['gap'] >= 1200]
                        break_count = len(long_breaks)
                        total_break_secs = long_breaks['gap'].sum()

                    target_calls = 40 * num_active_days
                    target_duration = 11700 * num_active_days
                    issues = []
                    if above_3min_count < target_calls: issues.append(f"Low Calls ({above_3min_count}/{target_calls})")
                    if total_valid_duration < target_duration: issues.append("Low Duration")
                    if break_count > 2: issues.append(f"Excessive Breaks ({break_count})")
                    
                    zone = "🟢 GREEN"
                    if num_active_days == 0: zone = "⚪ N/A"
                    elif len(issues) >= 2: zone = "🔴 RED"
                    elif len(issues) == 1: zone = "🟡 YELLOW"
                    
                    agents.append({
                        "AGENT": owner, "TEAM": group['Team Name'].iloc[0] if not pd.isna(group['Team Name'].iloc[0]) else "Others",
                        "ZONE": zone, "TOTAL CALLS": int(total_calls_count), "DAYS ACTIVE": int(num_active_days),
                        "CALLS > 3 MINS": int(above_3min_count), "20+ MIN CALLS": int(long_calls_count),
                        "LONG BREAKS": int(break_count), "LONG BREAK DURATION": format_duration_clean(total_break_secs),
                        "CALL DURATION > 3 MINS": format_duration_clean(total_valid_duration),
                        "ISSUES": ", ".join(issues) if issues else "None",
                        "raw_dur": total_valid_duration, "raw_break": total_break_secs, "is_total": 0
                    })
                
                report_df = pd.DataFrame(agents)
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("🔴 Red", len(report_df[report_df['ZONE'] == "🔴 RED"]))
                m2.metric("🟡 Yellow", len(report_df[report_df['ZONE'] == "🟡 YELLOW"]))
                m3.metric("🟢 Green", len(report_df[report_df['ZONE'] == "🟢 GREEN"]))
                m4.metric("Total Unique Calls", df['call_id'].nunique())
                ans_pct = (len(df[df['status'].str.lower()=='answered'])/df['call_id'].nunique()*100) if not df.empty else 0
                m5.metric("Pick Up Ratio %", f"{ans_pct:.1f}%")
                m6.metric("Active Agents", len(report_df))
                
                st.divider()

                total_row = pd.DataFrame([{
                    "AGENT": "TOTAL", "TEAM": "-", "ZONE": "-",
                    "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                    "DAYS ACTIVE": int(report_df["DAYS ACTIVE"].sum()),
                    "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                    "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                    "LONG BREAKS": int(report_df["LONG BREAKS"].sum()),
                    "LONG BREAK DURATION": format_duration_clean(report_df["raw_break"].sum()),
                    "CALL DURATION > 3 MINS": format_duration_clean(report_df["raw_dur"].sum()),
                    "ISSUES": "-", "is_total": 1
                }])
                
                final_df = pd.concat([report_df, total_row], ignore_index=True)

                def style_row(row):
                    if row["is_total"] == 1:
                        return ['font-weight: bold; background-color: #262730; color: white'] * len(row)
                    return [''] * len(row)

                display_cols = ["AGENT", "TEAM", "ZONE", "TOTAL CALLS", "DAYS ACTIVE", "CALLS > 3 MINS", "20+ MIN CALLS", "LONG BREAKS", "LONG BREAK DURATION", "CALL DURATION > 3 MINS", "ISSUES"]
                
                st.dataframe(final_df.style.apply(style_row, axis=1), column_order=display_cols, use_container_width=True, hide_index=True)
                
                cdr_data = df.drop(columns=['Team Name', 'Vertical', 'Caller Name', 'Team', 'Zone'], errors='ignore')
                csv_cdr = cdr_data.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download CDR", data=csv_cdr, file_name=f"CDR_{start_date}.csv", mime='text/csv')
