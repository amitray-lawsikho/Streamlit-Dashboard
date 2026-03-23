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
st.set_page_config(layout="wide", page_title="CALLERWISE DURATION METRICS")

# HIDE STREAMLIT BRANDING & MENU FOR SHARED LINKS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stAppDeployButton {display:none;}
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
                                g_sec = (day_group['call_datetime'].iloc[i+1] - day_group['prev_end'].iloc[i]).total_seconds()
                                if g_sec >= 1200:
                                    day_breaks.append({'s': day_group['prev_end'].iloc[i], 'e': day_group['call_datetime'].iloc[i+1], 'g': g_sec})
                        l_call_e = day_group['call_datetime'].iloc[-1] + pd.to_timedelta(day_group['call_duration'].iloc[-1], unit='s')
                        if (end_office - l_call_e).total_seconds() >= 1200:
                            day_breaks.append({'s': l_call_e, 'e': end_office, 'g': (end_office - l_call_e).total_seconds()})

                        if day_breaks:
                            b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks"
                            for b in day_breaks:
                                b_str += f"\n  {b['s'].strftime('%H:%M')}→{b['e'].strftime('%H:%M')} ({format_dur_hm(b['g'])})"
                            daily_break_list.append(b_str)

                        day_issues = []
                        if len(day_group[day_group['call_duration'] >= 180]) < 40: day_issues.append("Low Calls")
                        if day_dur < 11700: day_issues.append("Low Duration")
                        if len(day_breaks) > 2: day_issues.append("Excessive Breaks")
                        all_issues.extend(day_issues)
                        
                        if len(day_issues) >= 2: daily_zone_list.append("🔴")
                        elif len(day_issues) == 1: daily_zone_list.append("🟡")
                        else: daily_zone_list.append("🟢")

                    if "🔴" in daily_zone_list: final_zone = "🔴 RED"
                    elif "🟡" in daily_zone_list: final_zone = "🟡 YELLOW"
                    else: final_zone = "🟢 GREEN"

                    total_duration_agg += agent_valid_dur
                    pickup_ratio = round((total_ans / total_calls * 100)) if total_calls > 0 else 0

                    agents_list.append({
                        "IN/OUT TIME": "\n".join(daily_io_list),
                        "ZONE": final_zone,
                        "CALLER": owner,
                        "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others",
                        "TOTAL CALLS": int(total_calls),
                        "CALL STATUS": f"{total_ans} Ans / {total_miss} Unans",
                        "PICK UP RATIO %": f"{pickup_ratio}%",
                        "CALLS > 3 MINS": int(total_above_3min),
                        "20+ MIN CALLS": int(total_long_calls),
                        "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur),
                        "LONG BREAKS (>=20 MINS)": "\n---\n".join(daily_break_list) if daily_break_list else "0",
                        "ISSUES": ", ".join(sorted(list(set(all_issues)))) if all_issues else "None"
                    })

                report_df = pd.DataFrame(agents_list)
                
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("🔴 Red", len(report_df[report_df['ZONE'] == "🔴 RED"]))
                m2.metric("🟡 Yellow", len(report_df[report_df['ZONE'] == "🟡 YELLOW"]))
                m3.metric("🟢 Green", len(report_df[report_df['ZONE'] == "🟢 GREEN"]))
                
                # TOTAL UNIQUE CALLS: Counts every single row in 'df' (absolute total)
                m4.metric("Total Unique Calls", df['call_id'].nunique())
                
                ans_total = len(df[df['status'].str.lower() == 'answered'])
                ans_pct = (ans_total / df['call_id'].nunique() * 100) if not df.empty else 0
                m5.metric("Pick Up Ratio %", f"{ans_pct:.1f}%")
                m6.metric("Active Callers", len(report_df))
                
                st.divider()
                
                # FINAL TOTAL ROW
                total_row = pd.DataFrame([{
                    "CALLER": "TOTAL", "IN/OUT TIME": "-", "TEAM": "-", "ZONE": "-", "CALL STATUS": "-", "PICK UP RATIO %": "-",
                    "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                    "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                    "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                    "LONG BREAKS (>=20 MINS)": "-", 
                    "CALL DURATION > 3 MINS": format_dur_hm(total_duration_agg),
                    "ISSUES": "-"
                }])
                
                final_df = pd.concat([report_df, total_row], ignore_index=True)
                
                def style_row(row):
                    if row["CALLER"] == "TOTAL":
                        return ['font-weight: bold; background-color: #262730; color: white'] * len(row)
                    return [''] * len(row)

                display_cols = ["IN/OUT TIME", "ZONE", "CALLER", "TEAM", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS", "LONG BREAKS (>=20 MINS)", "ISSUES"]
                
                column_config = {
                    "IN/OUT TIME": st.column_config.TextColumn("IN/OUT TIME", width="small"),
                    "ZONE": st.column_config.TextColumn("ZONE", width="small"),
                    "CALLER": st.column_config.TextColumn("CALLER", width="medium"),
                }

                st.dataframe(
                    final_df.style.apply(style_row, axis=1).set_properties(**{'white-space': 'pre-wrap'}), 
                    column_order=display_cols, 
                    column_config=column_config,
                    use_container_width=True, 
                    hide_index=True
                )
                
                cdr_data = df.copy()
                if not cdr_data.empty: cdr_data['call_datetime'] = cdr_data['call_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                st.download_button("📥 Download CDR", data=cdr_data.drop(columns=['merge_key','Caller Name'], errors='ignore').to_csv(index=False).encode('utf-8'), file_name=f"CDR_{display_start}_to_{display_end}.csv", mime='text/csv')
