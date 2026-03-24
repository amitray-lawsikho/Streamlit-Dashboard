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

# --- CLEAN UI CSS ---
st.markdown("""
<style>
header[data-testid="stHeader"] { visibility: visible !important; }
footer {visibility: hidden;}
[data-testid="stMainViewContainer"] { padding-top: 2rem; }

div[data-testid="stDataFrame"] thead tr th {
    white-space: normal !important;
    word-wrap: break-word !important;
    text-align: center !important;
    vertical-align: middle !important;
    min-width: 100px !important;
    line-height: 1.2 !important;
    height: auto !important;
    padding: 10px !important;
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
    query = """
    SELECT MAX(upd) as last_update FROM (
        SELECT MAX(updated_at_ampm) as upd FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT MAX(updated_at_ampm) as upd FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
    )
    """
    try:
        res = client.query(query).to_dataframe()
        return str(res['last_update'].iloc[0]) if not res.empty else "N/A"
    except:
        return "N/A"

@st.cache_data(ttl=3600)
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

@st.cache_data(ttl=600)
def fetch_call_data(start_date, end_date):
    # 1. Fetch Acefone
    q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
    df_ace = client.query(q_ace).to_dataframe()
    if not df_ace.empty:
        df_ace['source'] = 'Acefone'

    # 2. Fetch Ozonetel
    q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
    df_ozo = client.query(q_ozo).to_dataframe()
    if not df_ozo.empty:
        df_ozo = df_ozo.rename(columns={
            'CallID': 'call_id',
            'AgentName': 'call_owner',
            'phone_number': 'client_number',
            'StartTime': 'call_datetime',
            'CallDate': 'Call Date',
            'duration_sec': 'call_duration',
            'Status': 'status',
            'Type': 'direction',
            'Disposition': 'reason'
        })
        df_ozo['status'] = df_ozo['status'].str.lower().replace({'unanswered': 'missed'})
        df_ozo['direction'] = df_ozo['direction'].str.lower().replace({'manual': 'outbound'})
        df_ozo['source'] = 'Ozonetel'

    # 3. Combine both
    df = pd.concat([df_ace, df_ozo], ignore_index=True)
    
    if not df.empty:
        df['call_datetime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
        # CRITICAL FIX: Ensure duration is numeric so your later `df['call_duration'] > 0` logic doesn't fail
        df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
        df = df.sort_values(['call_owner', 'call_datetime'], ascending=[True, True])
    return df

def format_dur_hm(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0:
        return "0h 0m"
    total_minutes = int(round(total_seconds / 60))
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

def get_display_gap_seconds(start_time, end_time):
    s = start_time.replace(second=0, microsecond=0)
    e = end_time.replace(second=0, microsecond=0)
    return (e - s).total_seconds()

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
with col_sub_l:
    st.markdown(f"<p style='color: #A0A0A0;'>Report Period: <b>{display_start}</b> to <b>{display_end}</b></p>", unsafe_allow_html=True)
with col_sub_r:
    st.markdown(f"<p style='color: #A0A0A0; text-align: right;'>Last Updated: <b>{get_global_last_update()}</b></p>", unsafe_allow_html=True)
st.divider()

# --- 6. Main Logic ---
if st.sidebar.button("Generate Report"):
    with st.spinner('Calculating metrics...'):
        df_raw = fetch_call_data(start_date, end_date)
        if df_raw.empty:
            st.warning("No data found for selection.")
        else:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            
            df = df[df['call_owner'].notna() & (df['call_owner'] != '')]
            
            if selected_team:
                df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical:
                df = df[df['Vertical'].isin(selected_vertical)]
            if search_query:
                df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]
                
            if df.empty:
                st.error("No results match filters.")
            else:
                active_callers = df[df['call_duration'] > 0]['call_owner'].unique()
                df_filtered = df[df['call_owner'].isin(active_callers)]
                
                if df_filtered.empty:
                    st.warning("No active talk-time found for selected agents.")
                else:
                    agents_list = []
                    total_duration_agg = 0
                    ist_tz = pytz.timezone("Asia/Kolkata")
                    
                    for owner, agent_group in df_filtered.groupby('call_owner'):
                        total_ans, total_miss, total_calls = 0, 0, 0
                        total_above_3min, total_mid_calls, total_long_calls, agent_valid_dur = 0, 0, 0, 0
                        total_break_sec_all_days = 0
                        total_active_days = 0
                        daily_io_list, daily_break_list, all_issues = [], [], []
                        
                        for c_date, day_group in agent_group.groupby('Call Date'):
                            day_group = day_group.sort_values('call_datetime')
                            total_active_days += 1
                            ans = len(day_group[day_group['status'].str.lower() == 'answered'])
                            miss = len(day_group[day_group['status'].str.lower() == 'missed'])
                            total_ans += ans; total_miss += miss; total_calls += len(day_group)
                            
                            total_above_3min += len(day_group[day_group['call_duration'] >= 180])
                            total_mid_calls += len(day_group[(day_group['call_duration'] >= 900) & (day_group['call_duration'] < 1200)])
                            total_long_calls += len(day_group[day_group['call_duration'] >= 1200])
                            
                            day_dur = day_group.loc[day_group['call_duration'] >= 1
