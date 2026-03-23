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
    except:
        return "N/A"

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
            
            # Remove None/Blank callers
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
                # --- SYNC LOGIC ---
                # 1. Identify agents who have at least one answered call (duration > 0)
                active_callers = df[df['call_duration'] > 0]['call_owner'].unique()
                
                # 2. Filter the main data to ONLY these agents
                # This ensures top metrics and table sums match exactly
                df_filtered = df[df['call_owner'].isin(active_callers)]
                
                if df_filtered.empty:
                    st.warning("No active talk-time found for selected agents.")
                else:
                    agents_list = []
                    total_duration_agg = 0
                    ist_tz = pytz.timezone("Asia/Kolkata")
                    
                    for owner, agent_group in df_filtered.groupby('call_owner'):
                        total_ans, total_miss, total_calls = 0, 0, 0
                        total_above_3min, total_long_calls, agent_valid_dur = 0, 0, 0
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
                            total_long_calls += len(day_group[day_group['call_duration'] >= 1200])
                            day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum()
                            agent_valid_dur += day_dur
                            
                            first_call_start = day_group['call_datetime'].min()
                            # Calculate actual end of the last call of the day
                            last_call_end_time = (day_group['call_datetime'] + pd.to_timedelta(day_group['call_duration'], unit='s')).max()
                            
                            in_t_str = first_call_start.strftime('%I:%M %p')
                            out_t_str = last_call_end_time.strftime('%I:%M %p')
                            daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {in_t_str} · Out {out_t_str}")
                            
                            start_office = ist_tz.localize(datetime.combine(c_date, time(10, 0)))
                            end_office = ist_tz.localize(datetime.combine(c_date, time(20, 0)))
                            late_threshold = ist_tz.localize(datetime.combine(c_date, time(10, 15)))
                            
                            if first_call_start > late_threshold:
                                all_issues.append("Late Check-In")
                            if last_call_end_time < end_office:
                                all_issues.append("Early Check-Out")

                            day_breaks = []
                            day_break_sec = 0
                            day_group['actual_end'] = day_group['call_datetime'] + pd.to_timedelta(day_group['call_duration'], unit='s')
                            
                            if first_call_start > start_office:
                                g_start_sec = get_display_gap_seconds(start_office, first_call_start)
                                if g_start_sec >= 1200:
                                    day_breaks.append({'s': start_office, 'e': first_call_start, 'dur': g_start_sec})
                                    day_break_sec += g_start_sec
                                    
                            if len(day_group) > 1:
                                for i in range(len(day_group)-1):
                                    gap_s = day_group['actual_end'].iloc[i]
                                    gap_e = day_group['call_datetime'].iloc[i+1]
                                    act_s = max(gap_s, start_office)
                                    act_e = min(gap_e, end_office)
                                    if act_e > act_s:
                                        g_mid_sec = get_display_gap_seconds(act_s, act_e)
                                        if g_mid_sec >= 1200:
                                            day_breaks.append({'s': act_s, 'e': act_e, 'dur': g_mid_sec})
                                            day_break_sec += g_mid_sec
                                            
                            if last_call_end_time < end_office:
                                g_end_sec = get_display_gap_seconds(last_call_end_time, end_office)
                                if g_end_sec >= 1200:
                                    day_breaks.append({'s': last_call_end_time, 'e': end_office, 'dur': g_end_sec})
                                    day_break_sec += g_end_sec
                                    
                            total_break_sec_all_days += day_break_sec
                            
                            if day_breaks:
                                day_sum_formatted = format_dur_hm(day_break_sec)
                                b_str = f"{c_date.strftime('%d/%m')}: {len(day_breaks)} breaks : {day_sum_formatted}"
                                for b in day_breaks:
                                    b_str += f"\n  {b['s'].strftime('%H:%M')}→{b['e'].strftime('%H:%M')} ({format_dur_hm(b['dur'])})"
                                daily_break_list.append(b_str)
                                
                            day_prod_sec = 36000 - day_break_sec
                            if len(day_group[day_group['call_duration'] >= 180]) < 40:
                                all_issues.append("Low Calls")
                            if day_dur < 11700:
                                all_issues.append("Low Duration")
                            if len(day_breaks) > 2:
                                all_issues.append("Excessive Breaks")
                            if day_prod_sec < 18000:
                                all_issues.append("Less Productive")
                                
                        total_duration_agg += agent_valid_dur
                        pickup_ratio = round((total_ans / total_calls * 100)) if total_calls > 0 else 0
                        prod_sec_total = (36000 * total_active_days) - total_break_sec_all_days
                        
                        agents_list.append({
                            "IN/OUT TIME": "\n".join(daily_io_list),
                            "CALLER": owner,
                            "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others",
                            "TOTAL CALLS": int(total_calls),
                            "CALL STATUS": f"{total_ans} Ans / {total_miss} Unans",
                            "PICK UP RATIO %": f"{pickup_ratio}%",
                            "CALLS > 3 MINS": int(total_above_3min),
                            "20+ MIN CALLS": int(total_long_calls),
                            "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur),
                            "PRODUCTIVE HOURS": format_dur_hm(prod_sec_total),
                            "LONG BREAKS (>=20 MINS)": "\n---\n".join(daily_break_list) if daily_break_list else "0",
                            "REMARKS": ", ".join(sorted(list(set(all_issues)))) if all_issues else "None",
                            "raw_prod": prod_sec_total
                        })
                        
                    report_df = pd.DataFrame(agents_list)
                    m1, m2, m3, m4 = st.columns(4)
                    
                    # Top Metrics now only count data from df_filtered
                    total_filtered_calls = df_filtered['call_id'].nunique()
                    m1.metric("Total Unique Calls", total_filtered_calls)
                    
                    ans_total = len(df_filtered[df_filtered['status'].str.lower() == 'answered'])
                    ans_pct = (ans_total / total_filtered_calls * 100) if total_filtered_calls > 0 else 0
                    m2.metric("Pick Up Ratio %", f"{ans_pct:.1f}%")
                    
                    m3.metric("Active Callers", len(report_df))
                    m4.metric("Avg Productive Hrs", format_dur_hm(report_df["raw_prod"].mean()))
                    st.divider()
                    
                    total_row = pd.DataFrame([{
                        "IN/OUT TIME": "-",
                        "CALLER": "TOTAL",
                        "TEAM": "-",
                        "TOTAL CALLS": int(report_df["TOTAL CALLS"].sum()),
                        "CALL STATUS": "-",
                        "PICK UP RATIO %": "-",
                        "CALLS > 3 MINS": int(report_df["CALLS > 3 MINS"].sum()),
                        "20+ MIN CALLS": int(report_df["20+ MIN CALLS"].sum()),
                        "CALL DURATION > 3 MINS": format_dur_hm(total_duration_agg),
                        "PRODUCTIVE HOURS": format_dur_hm(report_df["raw_prod"].sum()),
                        "LONG BREAKS (>=20 MINS)": "-",
                        "REMARKS": "-"
                    }])
                    final_df = pd.concat([report_df, total_row], ignore_index=True)
                    
                    def style_total_row(row):
                        if row["CALLER"] == "TOTAL":
                            return ['font-weight: bold; background-color: #262730; color: white'] * len(row)
                        return [''] * len(row)
                        
                    display_cols = ["IN/OUT TIME", "CALLER", "TEAM", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS", "PRODUCTIVE HOURS", "LONG BREAKS (>=20 MINS)", "REMARKS"]
                    
                    st.dataframe(final_df.style.apply(style_total_row, axis=1).set_properties(**{'white-space': 'pre-wrap'}), column_order=display_cols, use_container_width=True, hide_index=True)
                    st.divider()
                    
                    cdr_csv = df_filtered.copy()
                    if not cdr_csv.empty:
                        cols_to_drop = ['merge_key', 'Caller Name', 'raw_prod']
                        cdr_csv = cdr_csv.drop(columns=[c for c in cols_to_drop if c in cdr_csv.columns])
                        if 'call_datetime' in cdr_csv.columns:
                            cdr_csv['call_datetime'] = cdr_csv['call_datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
                        st.download_button(label="📥 Download CDR CSV", data=cdr_csv.to_csv(index=False).encode('utf-8'), file_name=f"CDR_{display_start}_to_{display_end}.csv", mime='text/csv')
