import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, time, timedelta
import os
import pytz

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

# --- 3. Data Fetching (NO CACHING) ---
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip()
    df_meta['merge_key'] = df_meta['Caller Name'].astype(str).str.strip().str.lower()
    return sorted(df_meta['Team Name'].dropna().unique()), sorted(df_meta['Vertical'].dropna().unique()), df_meta

def fetch_call_data(start_date, end_date):
    # Fetch Acefone
    q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
    df_ace = client.query(q_ace).to_dataframe()
    if not df_ace.empty: df_ace['source'] = 'Acefone'

    # Fetch Ozonetel
    q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
    df_ozo = client.query(q_ozo).to_dataframe()
    if not df_ozo.empty:
        df_ozo = df_ozo.rename(columns={
            'CallID': 'call_id', 'AgentName': 'call_owner', 'phone_number': 'client_number',
            'StartTime': 'call_datetime', 'CallDate': 'Call Date', 'duration_sec': 'call_duration',
            'Status': 'status', 'Type': 'direction', 'Disposition': 'reason'
        })
        df_ozo['status'] = df_ozo['status'].str.lower().replace({'unanswered': 'missed'})
        df_ozo['direction'] = df_ozo['direction'].str.lower().replace({'manual': 'outbound'})
        df_ozo['source'] = 'Ozonetel'

    df = pd.concat([df_ace, df_ozo], ignore_index=True)
    if not df.empty:
        df['call_datetime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
        df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
    return df

# Helper for Time Formatting
def format_dur_hm(s):
    if pd.isna(s) or s <= 0: return "0h 0m"
    m = int(round(s / 60))
    return f"{m // 60}h {m % 60}m"

# --- 4. Sidebar ---
teams, verticals, df_team_mapping = get_metadata()
selected_dates = st.sidebar.date_input("Select Date Range", value=(date.today(), date.today()))
start_date, end_date = selected_dates if isinstance(selected_dates, tuple) else (selected_dates, selected_dates)
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
search_query = st.sidebar.text_input("🔍 Search Name")

# --- 5. Main UI ---
st.title("CALLERWISE DURATION METRICS")

if st.sidebar.button("Generate Report"):
    df_raw = fetch_call_data(start_date, end_date)
    if df_raw.empty:
        st.warning("No data found.")
    else:
        # Standardize Names
        df_raw['merge_key'] = df_raw['call_owner'].astype(str).str.strip().str.lower()
        df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
        df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
        
        # Filtering
        if selected_team: df = df[df['Team Name'].isin(selected_team)]
        if search_query: df = df[df['call_owner'].str.contains(search_query, case=False)]
        
        # Metrics - Force 5 Columns
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Calls", len(df))
        m2.metric("Source Split", f"A: {len(df[df['source']=='Acefone'])} | O: {len(df[df['source']=='Ozonetel'])}")
        ans_pct = (len(df[df['status']=='answered']) / len(df) * 100) if len(df)>0 else 0
        m3.metric("Pick Up %", f"{ans_pct:.1f}%")
        m4.metric("Unique Agents", df['call_owner'].nunique())
        m5.metric("Total Talktime", format_dur_hm(df['call_duration'].sum()))
        
        # Main Table (Grouped Logic)
        report_data = []
        for owner, group in df.groupby('call_owner'):
            report_data.append({
                "CALLER": owner,
                "TEAM": group['Team Name'].iloc[0] if not pd.isna(group['Team Name'].iloc[0]) else "Others",
                "TOTAL CALLS": len(group),
                "DURATION": format_dur_hm(group['call_duration'].sum()),
                "SOURCE": group['source'].unique()
            })
        st.dataframe(pd.DataFrame(report_data), use_container_width=True)

        # --- DEBUG SECTION ---
        with st.expander("🛠 DEBUG: Raw Data Preview"):
            st.write("First 10 rows of merged data:")
            st.write(df[['call_owner', 'source', 'call_duration', 'Team Name']].head(10))
