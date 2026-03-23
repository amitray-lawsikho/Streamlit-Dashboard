import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, time
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

# HIDE STREAMLIT BRANDING & LOCK SIDEBAR (User cannot hide filters)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
    
    /* This section locks the sidebar and hides the collapse button */
    [data-testid="sidebar-collapsible-control"] {
        display: none;
    }
    [data-testid="stSidebar"] {
        min-width: 300px;
        max-width: 300px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. Data Fetching Functions ---
@st.cache_data(ttl=3600)
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip()
    df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
    teams = sorted(df_meta['Team Name'].dropna().unique())
    verticals = sorted(df_meta['Vertical'].dropna().unique())
    return teams, verticals, df_meta

@st.cache_data(ttl=60)
def get_global_last_update():
    query = "SELECT MAX(updated_at_ampm) as last_update FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    try:
        res = client.query(query).to_dataframe()
        return str(res['last_update'].iloc[0]) if not res.empty else "N/A"
    except: return "N/A"

@st.cache_data(ttl=3600)
def get_available_dates():
    query = "SELECT MIN(`Call Date`) as min_date, MAX(`Call Date`) as max_date FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    df_dates = client.query(query).to_dataframe()
    if not df_dates.empty and not pd.isna(df_dates['min_date'].iloc[0]):
        return df_dates['min_date'].iloc[0], df_dates['max_date'].iloc[0]
    return date.today(), date.today()

def fetch_call_data(start_date, end_date):
    query = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}' ORDER BY call_owner, call_datetime ASC"
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['call_datetime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
    return df

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    return f"{hours}h {minutes}m"

# --- 4. Sidebar Filters ---
st.sidebar.header("Report Filters")
min_d, max_d = get_available_dates()
selected_dates = st.sidebar.date_input("Select Date Range", value=(max_d, max_d), min_value=min_d, max_value=max_d, format="DD-MM-YYYY")

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

teams, verticals, df_team_mapping = get_metadata()
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
selected_vertical = st.sidebar.multiselect("Filter by Vertical", options=verticals)
search_query = st.sidebar.text_input("🔍 Search Name")

# --- 5. Header Section ---
st.markdown("<h1 style='text-align: center; margin-bottom: 5px;'>CALLERWISE DURATION METRICS</h1>", unsafe_allow_html=True)
display_start, display_end = start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y')
col_sub_l, col_sub_r = st.columns([3, 1])
with col_sub_l: st.markdown(f"<p style='color: #A0A0A0;'>Report Period: <b>{display_start}</b> to <b>{display_end}</b></p>", unsafe_allow_html=True)
with col_sub_r: st.markdown(f"<p style='color: #A0A0A0; text-align: right;'>Last Updated: <b>{get_global_last_update()}</b></p>", unsafe_allow_html=True)
st.divider()

# --- 6. Main Logic ---
if st.sidebar.button("Generate Report"):
    with st.spinner('Calculating metrics...'):
        df_raw = fetch_call_data(start_date, end_date)
        if df_raw.empty:
            st.warning("No data found for selection.")
        else:
            # First, clean name mapping
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            
            # Apply Sidebar Filters
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]
            
            if df.empty:
                st.error("No results match filters.")
            else:
                agents_list = []
                total_duration_agg = 0 
                
                # Filter for only calls > 0s for productivity calculations
                df_prod = df[df['call_duration'] > 0]

                for owner, agent_group in df_prod.groupby('call_owner'):
                    total_ans, total_miss, total_calls = 0, 0, 0
                    total_above_3min, total_long_calls, agent_valid_dur = 0, 0, 0
                    daily_io_list, daily_break_list, daily_zone_list, all_issues = [], [], [], []

                    for c_date, day_group in agent_group.groupby('Call Date'):
                        day_group = day_group.sort_values('call_datetime')
                        
                        ans = len(day_group[day_group['status'].str.lower() == 'answered'])
                        miss = len(day_group[day_group['status'].str.lower() == 'missed'])
                        total_ans += ans
                        total_miss += miss
                        total_calls += len(day_group)
                        total_above_3min += len(day_group[day_group['call_duration'] >= 180])
                        total_long_calls += len(day_group[day_group['call_duration'] >= 1200])
                        day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
                        agent_valid_dur += day_dur

                        in_t = day_group['call_datetime'].min().strftime('%I:%M %p')
                        out_t = day_group['call_datetime'].max().strftime('%I:%M %p')
                        daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {in_t} · Out {out_t}")

                        start_office = datetime.combine(c_date, time(10, 0)).replace(tzinfo=pytz.timezone("Asia/Kolkata"))
                        end_office = datetime.combine(c_date, time(20, 0)).replace(tzinfo=pytz.timezone("Asia/Kolkata"))
                        day_breaks = []
                        f_call = day_group['call_datetime'].iloc[0]
                        if (f_call - start_office).total_seconds() >= 1200:
                            day_breaks.append({'s': start_office, 'e': f_call, 'g': (f_call - start_office).total_seconds()})
                        if len(day_group) > 1:
                            day_group['prev_end'] = day_group['call_datetime'] + pd.to_timedelta(day_group['call_duration'], unit='s')
                            for i in range(len(day_group)-1):
                                g_sec = (day_group['call_datetime'].iloc
