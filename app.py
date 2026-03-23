import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date
import os
import json
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
st.set_page_config(layout="wide", page_title="CALLERWISE DURATION METRICS")

# --- 3. Data Fetching Functions ---
@st.cache_data(ttl=3600)
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip()
    # Key for case-insensitive mapping
    df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
    teams = sorted(df_meta['Team Name'].dropna().unique())
    verticals = sorted(df_meta['Vertical'].dropna().unique())
    return teams, verticals, df_meta

@st.cache_data(ttl=60)
def get_global_last_update():
    query = "SELECT MAX(updated_at_ampm) as last_update FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    try:
        res = client.query(query).to_dataframe()
        if not res.empty:
            return str(res['last_update'].iloc[0])
        return "N/A"
    except: return "N/A"

@st.cache_data(ttl=3600)
def get_available_dates():
    query = "SELECT MIN(`Call Date`) as min_date, MAX(`Call Date`) as max_date FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`"
    df_dates = client.query(query).to_dataframe()
    if not df_dates.empty and not pd.isna(df_dates['min_date'].iloc[0]):
        return df_dates['min_date'].iloc[0], df_dates['max_date'].iloc[0]
    return date.today(), date.today()

def fetch_call_data(start_date, end_date):
    query = f"""
    SELECT *
    FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
    WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY call_owner, call_datetime ASC
    """
    df = client.query(query).to_dataframe()
    if not df.empty and 'call_datetime' in df.columns:
        df['call_datetime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
    return df

def format_duration_full(total_seconds):
    if pd.isna(total_seconds) or total_seconds <= 0: return "0s"
    total_seconds = int(total_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    parts = []
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    if seconds > 0 or not parts: parts.append(f"{seconds}s")
    return " ".join(parts)

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
search_query = st.sidebar.text_input("🔍 Search Agent Name")

# --- 5. Header Section ---
st.markdown("<h1 style='text-align: center; margin-bottom: 5px; font-family: sans-serif;'>CALLERWISE DURATION METRICS</h1>", unsafe_allow_html=True)
sub_style = "font-size: 15px; color: #A0A0A0; font-family: sans-serif; margin-top: 0px;"
display_start, display_end = start_date.strftime('%d-%m-%Y'), end_date.strftime('%d-%m-%Y')

col_sub_l, col_sub_r = st.columns([3, 1])
with col_sub_l:
    st.markdown(f"<p style='{sub_style}'>Report Period: <b>{display_start}</b> to <b>{display_end}</b></p>", unsafe_allow_html=True)
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
            # 1. Hide 0 duration calls
            df_raw = df_raw[df_raw['call_duration'] > 0]
            # 2. Case Insensitive Mapping
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            # 3. Standardize Name to Team List
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if selected_vertical: df = df[df['Vertical'].isin(selected_vertical)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False, na=False)]
            
            if df.empty:
                st.error("No results match filters.")
            else:
                agents = []
                for owner, group in df.groupby('call_owner'):
                    group = group.sort_values('call_datetime')
                    daily_max = group.groupby('Call Date')['call_duration'].max()
                    num_active_days = len(daily_max[daily_max >= 180])
                    
                    total_calls_count = len(group)
                    above_3min_count = len(group[group['call_duration'] >= 180])
                    total_valid_duration = group.loc[group['call_duration'] >= 180, 'call_duration'].sum()
                    
                    break_details_text = "0"
                    total_break_secs = 0
                    break_count = 0
                    
                    if len(group) > 1:
                        group['prev_end'] = group['call_datetime'] + pd.to_timedelta(group['call_duration'], unit='s')
                        group['gap'] = (group['call_datetime'].shift(-1) - group['prev_end']).dt.total_seconds()
                        
                        # LONG BREAKS (>=20 MINS)
                        long_breaks_df = group[group['gap'] >= 1200].copy()
                        break_count = len(long_breaks_df)
                        total_break_secs = long_breaks_df['gap'].sum()
                        
                        if break_count > 0:
                            break_lines = [f"{break_count} long breaks"]
                            for _, row in long_breaks_df.iterrows():
                                start_t = row['prev_end'].strftime('%H:%M')
                                # The break ends when the next call starts
                                next_call_start = df.loc[df.index == row.name + 1, 'call_datetime']
                                if not next_call_start.empty:
                                    end_t = next_call_start.iloc[0].strftime('%H:%M')
                                else:
                                    # Fallback if index alignment is tricky
                                    end_t = (row['prev_end'] + pd.to_timedelta(row['gap'], unit='s')).strftime('%H:%M')
                                
                                break_lines.append(f"{start_t} → {end_t}")
                                break_lines.append(f"{format_duration_full(row['gap'])}")
                            break_details_text = "\n".join(break_lines)

                    issues = []
                    if above_3min_count < (40 * num_active_days): issues.append(f"Low Calls ({above_3min_count})")
                    if total_valid_duration < (11700 * num_active_days): issues.append("Low Duration")
                    if break_count > 2: issues.append(f"Excessive Breaks ({break_count})")
                    
                    zone = "🟢 GREEN"
                    if num_active_days == 0: zone = ""
                    elif len(issues) >= 2: zone = "🔴 RED"
                    elif len(issues) == 1: zone = "🟡 YELLOW"
                    
                    agents.append({
                        "AGENT": owner, 
                        "TEAM": group['Team Name'].iloc[0] if not pd.isna(group['Team Name'].iloc[0]) else "Others",
                        "ZONE": zone, 
                        "TOTAL CALLS": int(total_calls_count), 
                        "DAYS ACTIVE": int(num_active_days),
                        "LONG BREAKS (>=20 MINS)": break_details_text, 
                        "LONG BREAK DURATION": format_duration_full(total_break_secs),
                        "CALL DURATION > 3 MINS": format_duration_full(total_valid_duration),
                        "ISSUES": ", ".join(issues) if issues else "None",
                        "raw_dur": total_valid_duration, "raw_break": total_break_secs, "is_total": 0
                    })
                
                report_df = pd.DataFrame(agents)
                # Metrics at top
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
                    "AGENT": "TOTAL", "TEAM": "-", "ZONE": "-", "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                    "DAYS ACTIVE": int(report_df["DAYS ACTIVE"].sum()),
                    "LONG BREAKS (>=20 MINS)": str(int(report_df["LONG BREAKS (>=20 MINS)"].str.split().str[0].replace('nan', 0).apply(lambda x: int(x) if str(x).isdigit() else 0).sum())),
                    "LONG BREAK DURATION": format_duration_full(report_df["raw_break"].sum()),
                    "CALL DURATION > 3 MINS": format_duration_full(report_df["raw_dur"].sum()),
                    "ISSUES": "-", "is_total": 1
                }])
                
                final_df = pd.concat([report_df, total_row], ignore_index=True)

                display_cols = ["AGENT", "TEAM", "ZONE", "TOTAL CALLS", "DAYS ACTIVE", "LONG BREAKS (>=20 MINS)", "LONG BREAK DURATION", "CALL DURATION > 3 MINS", "ISSUES"]
                
                # To show multi-line text in the dataframe, we use st.dataframe with high row height or a specific style
                st.dataframe(
                    final_df.style.set_properties(**{'white-space': 'pre-wrap'}),
                    column_order=display_cols,
                    use_container_width=True,
                    hide_index=True
                )
                
                cdr_data = df.copy()
                if not cdr_data.empty: cdr_data['call_datetime'] = cdr_data['call_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                st.download_button("📥 Download CDR", data=cdr_data.drop(columns=['merge_key','Caller Name'], errors='ignore').to_csv(index=False).encode('utf-8'), file_name=f"CDR_{display_start}_to_{display_end}.csv", mime='text/csv')
