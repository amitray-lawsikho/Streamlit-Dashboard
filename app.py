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
def fetch_call_data(start_date, end_date):
    # Acefone
    q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
    df_ace = client.query(q_ace).to_dataframe()
    if not df_ace.empty: 
        df_ace['source'] = 'Acefone'
        df_ace['unique_lead_id'] = df_ace['client_number']

    # Ozonetel
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

    # Manual
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
        # Timezone Handling & Column Renaming
        df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
        df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
        df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
        
        # CLEAN Timestamps (Remove +05:30)
        df['call_starttime_clean'] = df['call_starttime'].dt.tz_localize(None)
        df['call_endtime_clean'] = df['call_endtime'].dt.tz_localize(None)
        
    return df

def process_metrics_logic(df_filtered):
    agents_list = []
    heatmap_data = []
    total_duration_agg = 0
    ist_tz = pytz.timezone("Asia/Kolkata")
    
    for owner, agent_group in df_filtered.groupby('call_owner'):
        total_ans, total_calls = 0, 0
        total_above_3min, agent_valid_dur = 0, 0
        total_break_sec_all_days, total_active_days = 0, 0
        daily_io_list, daily_break_list, all_issues = [], [], []
        
        for c_date, day_group in agent_group.groupby('Call Date'):
            timed_group = day_group[day_group['call_starttime'].notna()].sort_values('call_starttime')
            total_active_days += 1
            
            # Simple aggregations
            ans = len(day_group[day_group['status'].str.lower() == 'answered'])
            total_ans += ans; total_calls += len(day_group)
            total_above_3min += len(day_group[day_group['call_duration'] >= 180])
            agent_valid_dur += day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
            
            if timed_group.empty: continue

            first_start = timed_group['call_starttime'].min()
            last_end = timed_group['call_endtime'].max()
            daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {first_start.strftime('%I:%M %p')} · Out {last_end.strftime('%I:%M %p')}")
            
            # Office Boundaries
            start_off = ist_tz.localize(datetime.combine(c_date, time(10, 0)))
            end_off = ist_tz.localize(datetime.combine(c_date, time(20, 0)))
            
            day_breaks, day_break_sec = [], 0

            # 1. Start Gap (10 AM to First Call)
            if first_start > start_off:
                gap = (first_start - start_off).total_seconds()
                if gap >= 900:
                    day_breaks.append({'s': start_off, 'e': first_start, 'dur': gap})
                    day_break_sec += gap
                    heatmap_data.append({"Caller": owner, "Hour": 10, "Duration": gap/60})

            # 2. Mid Gaps (End of Call A to Start of Call B)
            if len(timed_group) > 1:
                for i in range(len(timed_group)-1):
                    gap_s, gap_e = timed_group['call_endtime'].iloc[i], timed_group['call_starttime'].iloc[i+1]
                    if gap_e > gap_s:
                        gap = (gap_e - gap_s).total_seconds()
                        if gap >= 900:
                            day_breaks.append({'s': gap_s, 'e': gap_e, 'dur': gap})
                            day_break_sec += gap
                            heatmap_data.append({"Caller": owner, "Hour": gap_s.hour, "Duration": gap/60})

            # 3. End Gap (Last Call to 8 PM)
            if last_end < end_off:
                gap = (end_off - last_end).total_seconds()
                if gap >= 900:
                    day_breaks.append({'s': last_end, 'e': end_off, 'dur': gap})
                    day_break_sec += gap
                    heatmap_data.append({"Caller": owner, "Hour": last_end.hour, "Duration": gap/60})

            total_break_sec_all_days += day_break_sec
            if day_breaks:
                b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks ({format_dur_hm(day_break_sec)})"
                for b in day_breaks: b_str += f"\n  {b['s'].strftime('%I:%M %p')}→{b['e'].strftime('%I:%M %p')}"
                daily_break_list.append(b_str)
            
            if first_start > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
            if last_end < end_off: all_issues.append("Early Check-Out")
            if (36000 - day_break_sec) < 18000: all_issues.append("Less Productive")

        total_duration_agg += agent_valid_dur
        prod_sec_total = (36000 * total_active_days) - total_break_sec_all_days
        
        agents_list.append({
            "IN/OUT TIME": "\n".join(daily_io_list), "CALLER": owner,
            "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others",
            "TOTAL CALLS": int(total_calls), 
            "PICK UP RATIO %": f"{round((total_ans/total_calls*100)) if total_calls>0 else 0}%",
            "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur),
            "PRODUCTIVE HOURS": format_dur_hm(prod_sec_total), 
            "BREAKS (>=15 MINS)": "\n---\n".join(daily_break_list) if daily_break_list else "None",
            "REMARKS": ", ".join(sorted(list(set(all_issues)))) if all_issues else "Perfect",
            "raw_prod_sec": prod_sec_total, "raw_dur_sec": agent_valid_dur
        })
    return pd.DataFrame(agents_list), total_duration_agg, pd.DataFrame(heatmap_data)

# --- 4. Sidebar ---
st.sidebar.header("Report Filters")
teams, verticals, df_team_mapping = get_metadata()
selected_dates = st.sidebar.date_input("Select Date Range", value=(date.today(), date.today()))
selected_team = st.sidebar.multiselect("Filter by Team", options=teams)
search_query = st.sidebar.text_input("🔍 Search Name")
gen_dynamic = st.sidebar.button("Generate Dynamic Report")

# --- 5. Main UI ---
st.markdown("<h1 style='text-align: center;'>DURATION METRICS</h1>", unsafe_allow_html=True)
tab1, tab2 = st.tabs(["🚀 Dynamic Dashboard", "📅 Duration Report"])

with tab1:
    if gen_dynamic:
        df_raw = fetch_call_data(selected_dates[0], selected_dates[1])
        if not df_raw.empty:
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_team_mapping, on='merge_key', how='left')
            df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
            
            if selected_team: df = df[df['Team Name'].isin(selected_team)]
            if search_query: df = df[df['call_owner'].str.contains(search_query, case=False)]

            report_df, total_dur, heat_df = process_metrics_logic(df)
            
            # Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Calls", len(df))
            m2.metric("Active Callers", len(report_df))
            m3.metric("Avg Prod Hrs", format_dur_hm(report_df["raw_prod_sec"].mean()))
            m4.metric("Total Duration", format_dur_hm(total_dur))

            # Table
            st.dataframe(report_df.style.apply(style_total, axis=1), use_container_width=True, hide_index=True)
            
            # CSV Download
            csv = df[["client_number", "call_starttime_clean", "call_endtime_clean", "call_duration", "status", "source"]].to_csv(index=False)
            st.download_button("📥 Download CDR", data=csv, file_name="CDR_LOG.csv", mime="text/csv")
            
            # --- BREAK HEATMAP ---
            st.divider()
            st.subheader("🔥 Break Distribution Heatmap")
            if not heat_df.empty:
                # Pivot for Heatmap
                fig = px.density_heatmap(
                    heat_df, x="Hour", y="Caller", z="Duration",
                    title="Break Frequency & Duration by Hour",
                    labels={'Hour': 'Hour of Day (24h)', 'Caller': 'Agent Name', 'Duration': 'Total Break Mins'},
                    color_continuous_scale="Viridis", text_auto=True,
                    range_x=[10, 20] # Focus on 10 AM to 8 PM
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No breaks >= 15 mins detected to display on heatmap.")
