import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import pytz
import io
import time
from datetime import datetime, date, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Flowable
)
from reportlab.lib.enums import TA_CENTER

# --- 1. SHARED CONFIGURATION & CLIENTS ---
try:
    st.set_page_config(
        page_title="Analytics Hub — LawSikho",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except:
    pass

# Shared GCP Client
if "gcp_service_account" in st.secrets:
    info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    # Look for local key file if secrets not found
    SERVICE_ACCOUNT_FILE = "c:/Users/AMIT GAMING/.gemini/antigravity/scratch/test/bigquery_key.json"
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        client = bigquery.Client()
    else:
        client = None

CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"
REV_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=973926168&single=true&output=csv"

@st.cache_data(ttl=300, show_spinner=False)
def get_shared_metadata(url=CSV_URL):
    try:
        df_meta = pd.read_csv(url)
        df_meta.columns = df_meta.columns.str.strip().str.replace('\xa0', '', regex=False)
        
        # Consistent Month handling
        month_col = next((c for c in df_meta.columns if c.strip().lower() == 'month'), None)
        if month_col and month_col != 'Month':
            df_meta.rename(columns={month_col: 'Month'}, inplace=True)
        
        if 'Month' in df_meta.columns:
            df_meta['Month'] = pd.to_datetime(df_meta['Month'], dayfirst=True, errors='coerce').dt.date
        
        df_meta['merge_key'] = (
            df_meta['Caller Name'].fillna('').astype(str)
            .str.replace('\xa0', ' ', regex=False)
            .str.replace(r'\s+', ' ', regex=True)
            .str.strip().str.lower()
        )
        
        teams = sorted(df_meta['Team Name'].dropna().unique()) if 'Team Name' in df_meta.columns else []
        verticals = sorted(df_meta['Vertical'].dropna().unique())  if 'Vertical'  in df_meta.columns else []
        return teams, verticals, df_meta
    except Exception as e:
        st.error(f"Error fetching metadata: {e}")
        return [], [], pd.DataFrame()

def fmt_inr_fixed(value):
    if pd.isna(value) or value == 0: return "₹0"
    if value >= 1_00_00_000: return f"₹{value/1_00_00_000:.2f}Cr"
    if value >= 1_00_000:    return f"₹{value/1_00_000:.2f}L"
    if value >= 1_000:       return f"₹{value/1000:.1f}K"
    return f"₹{int(value)}"

# --- 2. SHARED AUTHENTICATION ---
USERS = {
    'amit':     {'name': 'Amit Ray',      'password': 'lawsikho@2024'},
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align:center;margin-top:4rem'>🔐 LawSikho Analytics Hub</h2>", unsafe_allow_html=True)
    col = st.columns([1,2,1])[1]
    username = col.text_input("Username")
    password = col.text_input("Password", type="password")
    if col.button("Login", use_container_width=True):
        if username in USERS and USERS[username]['password'] == password:
            st.session_state.logged_in = True
            st.session_state.user_name = USERS[username]['name']
            st.rerun()
        else:
            col.error("❌ Incorrect username or password")
    st.stop()

# --- 3. PAGE LOGIC FUNCTIONS ---

def run_homepage():
    # --- HOMEPAGE UI & STYLES ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap');
    :root {
        --text-main: #1e293b;
        --text-muted: #64748b;
        --bg-main: #f8fafc;
        --accent-primary: #1e3a8a;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    .hub-header {
        text-align: center;
        margin-bottom: 3rem;
        animation: fadeInDown 0.8s ease-out;
    }
    .hub-title {
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .hub-subtitle { color: var(--text-muted); font-size: 1.1rem; }
    
    .cards-grid {
        display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        gap: 2rem; max-width: 1200px; margin: 0 auto;
    }
    
    .dcard {
        text-decoration: none !important; position: relative;
        background: #ffffff; border: 1px solid #e2e8f0; border-radius: 20px;
        padding: 2rem; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex; flex-direction: column; color: var(--text-main) !important;
        overflow: hidden; cursor: pointer;
    }
    .dcard:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.06); border-color: #3b82f6; }
    .dcard-glow {
        position: absolute; width: 100%; height: 100%; top: 0; left: 0;
        background: radial-gradient(circle at top right, rgba(59, 130, 246, 0.08), transparent);
        opacity: 0; transition: opacity 0.3s;
    }
    .dcard:hover .dcard-glow { opacity: 1; }
    .dcard-header { display: flex; align-items: center; margin-bottom: 1.5rem; }
    .dcard-icon { font-size: 2.5rem; margin-right: 1rem; }
    .dcard-title { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 700; }
    .dcard-desc { font-size: 0.95rem; color: var(--text-muted); line-height: 1.6; margin-bottom: 2rem; flex-grow: 1; }
    .dcard-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1.5rem; }
    .dtag {
        font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;
        background: #f1f5f9; color: #475569; padding: 4px 10px; border-radius: 6px;
    }
    .dcard-cta { font-weight: 600; color: #3b82f6; display: flex; align-items: center; gap: 0.5rem; }
    
    .nav-bar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 1rem 2rem; background: white; border-bottom: 1px solid #e2e8f0;
        position: sticky; top: 0; z-index: 100; margin-bottom: 2rem;
    }
    .user-pill {
        display: flex; align-items: center; gap: 0.75rem; background: #f8fafc;
        padding: 6px 16px; border-radius: 99px; border: 1px solid #e2e8f0; font-weight: 500; font-size: 0.9rem;
    }
    .status-dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; box-shadow: 0 0 8px #10b981; }
    
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
    </style>
    
    <div class="nav-bar">
        <div style="font-family:'Outfit', sans-serif; font-weight:700; font-size:1.4rem; color:#1e3a8a;">
            ⚖️ LawSikho <span style="font-weight:400; color:#64748b;">Analytics</span>
        </div>
        <div class="user-pill">
            <div class="status-dot"></div>
            <span>{st.session_state.user_name}</span>
        </div>
    </div>
    
    <div class="hub-header">
        <h1 class="hub-title">Unified Performance Hub</h1>
        <p class="hub-subtitle">Real-time data synchronization across all sales verticals</p>
    </div>

    <div class="cards-grid">
      <div class="dcard">
        <div class="dcard-glow"></div>
        <div class="dcard-header"><div class="dcard-icon">🔔</div><div class="dcard-title">Calling Metrics</div></div>
        <div class="dcard-desc">Full CDR analysis across Ozonetel, Acefone & Manual calls. Agent-level performance, break tracking, and team leaderboards.</div>
        <div class="dcard-tags"><span class="dtag">Ozonetel</span><span class="dtag">Acefone</span><span class="dtag">Team Stats</span></div>
        <div class="dcard-cta">Select "Calling Metrics" in sidebar →</div>
      </div>

      <div class="dcard">
        <div class="dcard-glow"></div>
        <div class="dcard-header"><div class="dcard-icon">💰</div><div class="dcard-title">Revenue Metrics</div></div>
        <div class="dcard-desc">Live collection tracking, enrollment verification & month-on-month growth from BigQuery and Sheets.</div>
        <div class="dcard-tags"><span class="dtag">Live Revenue</span><span class="dtag">Enrollments</span><span class="dtag">BigQuery</span></div>
        <div class="dcard-cta">Select "Revenue Metrics" in sidebar →</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

def run_calling():
    # --- PROFESSIONAL WARM THEME (Yellow · Orange · Red) ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    
    :root {
        --accent-primary:   #F97316;
        --accent-secondary: #EF4444;
        --accent-success:   #EAB308;
        --accent-warn:      #FBBF24;
        --accent-danger:    #DC2626;
        --gold:             #F59E0B;
        --silver:           #9CA3AF;
        --bronze:           #CD7F32;
        --radius-sm:        8px;
        --radius-md:        12px;
        --radius-lg:        16px;
        --shadow-sm:        0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06);
        --shadow-md:        0 4px 16px rgba(0,0,0,.10);
        --shadow-lg:        0 8px 32px rgba(0,0,0,.14);
        --transition:       all 0.22s cubic-bezier(.4,0,.2,1);
    }
    
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
    
    .cw-header {
        background: linear-gradient(135deg, #1c0700 0%, #7c2d12 50%, #431407 100%);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: var(--shadow-lg);
    }
    .cw-title { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; letter-spacing: .5px; margin: 0 0 .25rem; }
    .cw-subtitle { font-size: .82rem; color: rgba(255,255,255,.6); font-weight: 400; margin: 0; font-family: 'DM Mono', monospace; }
    
    .metric-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: .75rem; margin: .5rem 0 1rem; }
    .metric-card {
        background: #fff; border: 1px solid rgba(249,115,22,.12);
        border-radius: var(--radius-md); padding: .9rem 1rem;
        transition: var(--transition); box-shadow: var(--shadow-sm);
        position: relative; overflow: hidden; text-align: center;
    }
    .metric-label { font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: #6B7280; margin: 0 0 .3rem; }
    .metric-value { font-size: 1.45rem; font-weight: 700; color: #111827; line-height: 1; font-family: 'DM Mono', monospace; }
    
    .insight-card {
        background: #fff; border: 1px solid rgba(249,115,22,.12);
        border-radius: var(--radius-md); padding: 1rem 1.1rem;
        margin-bottom: .6rem; box-shadow: var(--shadow-sm); transition: var(--transition);
    }
    .insight-card.good  { border-left: 4px solid #EAB308; }
    .insight-card.warn  { border-left: 4px solid #FBBF24; }
    .insight-card.bad   { border-left: 4px solid #EF4444; }

    div[data-testid="stDataFrame"] thead tr th {
        background: linear-gradient(135deg, #431407, #7c1d1d) !important;
        color: #fff !important; font-size: .72rem !important; font-weight: 700 !important;
        text-transform: uppercase; text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Nested Helpers ---
    def format_dur_hm(total_seconds):
        if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
        tm = int(round(total_seconds / 60))
        return f"{tm // 60}h {tm % 60}m"

    def get_display_gap_seconds(s_t, e_t):
        if pd.isna(s_t) or pd.isna(e_t): return 0
        try: return (e_t.replace(second=0, microsecond=0) - s_t.replace(second=0, microsecond=0)).total_seconds()
        except: return 0

    def section_header_call(label):
        st.markdown(f"<div style='border-bottom: 2px solid #F97316; margin-bottom: 1rem;'><h3 style='color:#F97316; margin:0;'>{label}</h3></div>", unsafe_allow_html=True)

    # --- Data Fetching ---
    @st.cache_data(ttl=120)
    def fetch_call_data_call(start_date, end_date):
        q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
        df_ace = client.query(q_ace).to_dataframe()
        if not df_ace.empty:
            df_ace['source'] = 'Acefone'
            df_ace['unique_lead_id'] = df_ace['client_number']
        
        q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
        df_ozo = client.query(q_ozo).to_dataframe()
        if not df_ozo.empty:
            df_ozo = df_ozo.rename(columns={
                'AgentName': 'call_owner', 'phone_number': 'client_number',
                'StartTime': 'call_datetime', 'CallDate': 'Call Date', 'duration_sec': 'call_duration',
                'Status': 'status', 'Type': 'direction'
            })
            df_ozo['source'] = 'Ozonetel'
            df_ozo['unique_lead_id'] = df_ozo['client_number']

        q_man = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.manual_calls` WHERE Call_Date BETWEEN '{start_date}' AND '{end_date}'"
        df_man = client.query(q_man).to_dataframe()
        if not df_man.empty:
            df_man = df_man.rename(columns={'Call_Date': 'Call Date'})
            df_man['source'] = 'Manual'
            df_man['status'] = 'answered'
            df_man['unique_lead_id'] = df_man['client_number']

        df = pd.concat([df_ace, df_ozo, df_man], ignore_index=True)
        if not df.empty:
            df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
            df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
            df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
        return df

    # --- UI ---
    st.sidebar.markdown("### 🔔 Calling Filters")
    c_dates = st.sidebar.date_input("Date Range", value=(date.today() - timedelta(days=7), date.today()))
    if isinstance(c_dates, tuple) and len(c_dates) == 2:
        cs, ce = c_dates
    else:
        cs = ce = c_dates if not isinstance(c_dates, tuple) else c_dates[0]

    teams, verticals, df_meta = get_shared_metadata()
    sel_vert = st.sidebar.multiselect("Vertical", options=verticals)
    sel_team = st.sidebar.multiselect("Team", options=teams)
    
    gen_dyn = st.sidebar.button("🚀 Generate Dynamic Report")
    gen_dur = st.sidebar.button("📅 Generate Duration Report")

    st.markdown(f"""<div class="cw-header"><div class="cw-title">🔔 CALLING METRICS</div><div class="cw-subtitle">{cs.strftime('%d %b')} – {ce.strftime('%d %b %Y')}</div></div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🚀 Dynamic Dashboard", "📅 Duration Report", "🧠 Insights"])

    if gen_dyn or gen_dur:
        with st.spinner("Processing Calling Data..."):
            df_all = fetch_call_data_call(cs, ce)
            if df_all.empty:
                st.warning("No records found.")
                return
            
            df_merged = pd.merge(df_all, df_meta[['merge_key','Caller Name','Team Name','Vertical']], left_on='call_owner', right_on='merge_key', how='left')
            if sel_vert: df_merged = df_merged[df_merged['Vertical'].isin(sel_vert)]
            if sel_team: df_merged = df_merged[df_merged['Team Name'].isin(sel_team)]
            
            # --- Full Calling Logic: process_metrics_logic_internal ---
            def process_metrics_logic_internal(df_f):
                agents_l = []
                total_dur_a = 0
                ist = pytz.timezone("Asia/Kolkata")
                for own, grp in df_f.groupby('call_owner'):
                    t_ans, t_miss, t_calls, t_a3, t_mid, t_long, a_val_dur = 0, 0, 0, 0, 0, 0, 0
                    t_brk_sec, t_act_days = 0, 0
                    d_io, d_brk, a_iss = [], [], []
                    for c_dt, day_grp in grp.groupby('Call Date'):
                        tg = day_grp[day_grp['call_starttime'].notna()].sort_values('call_starttime')
                        t_act_days += 1
                        ans = len(day_grp[day_grp['status'].str.lower() == 'answered'])
                        miss = len(day_grp[day_grp['status'].str.lower() == 'missed'])
                        t_ans += ans; t_miss += miss; t_calls += len(day_grp)
                        t_a3 += len(day_grp[day_grp['call_duration'] >= 180])
                        t_mid += len(day_grp[(day_grp['call_duration'] >= 900) & (day_grp['call_duration'] < 1200)])
                        t_long += len(day_grp[day_grp['call_duration'] >= 1200])
                        d_dur = day_grp.loc[day_grp['call_duration'] >= 180, 'call_duration'].sum()
                        a_val_dur += d_dur
                        if tg.empty: continue
                        f_s, l_e = tg['call_starttime'].min(), tg['call_endtime'].max()
                        d_io.append(f"{c_dt.strftime('%d/%m')}: In {f_s.strftime('%I:%M %p')} · Out {l_e.strftime('%I:%M %p')}")
                        s_o, e_o = ist.localize(datetime.combine(c_dt, time(10, 0))), ist.localize(datetime.combine(c_dt, time(20, 0)))
                        if f_s > ist.localize(datetime.combine(c_dt, time(10, 15))): a_iss.append("Late Check-In")
                        if l_e < e_o: a_iss.append("Early Check-Out")
                        db, db_s = [], 0
                        if f_s > s_o:
                            g = get_display_gap_seconds(s_o, f_s)
                            if g >= 900: db.append({'s': s_o, 'e': f_s, 'dur': g}); db_s += g
                        if len(tg) > 1:
                            for i in range(len(tg) - 1):
                                ce, ns = tg['call_endtime'].iloc[i], tg['call_starttime'].iloc[i+1]
                                acts, acte = max(ce, s_o), min(ns, e_o)
                                if acte > acts:
                                    g = get_display_gap_seconds(acts, acte)
                                    if g >= 900: db.append({'s': acts, 'e': acte, 'dur': g}); db_s += g
                        if l_e < e_o:
                            g = get_display_gap_seconds(l_e, e_o)
                            if g >= 900: db.append({'s': l_e, 'e': e_o, 'dur': g}); db_s += g
                        t_brk_sec += db_s
                        if db:
                            bs = f"{c_dt.strftime('%d/%m')}: {len(db)} breaks : {format_dur_hm(db_s)}"
                            for b in db: bs += f"\n  {b['s'].strftime('%I:%M %p')}→{b['e'].strftime('%I:%M %p')} ({format_dur_hm(b['dur'])})"
                            d_brk.append(bs)
                        dp_s = 36000 - db_s
                        if len(day_grp[day_grp['call_duration'] >= 180]) < 40: a_iss.append("Low Calls")
                        if d_dur < 11700: a_iss.append("Low Duration")
                        if len(db) > 2: a_iss.append("Excessive Breaks")
                        if dp_s < 18000: a_iss.append("Less Productive")
                    total_dur_a += a_val_dur
                    p_s_t = (36000 * t_act_days) - t_brk_sec
                    agents_l.append({
                        "IN/OUT TIME": "\n".join(d_io), "CALLER": own,
                        "TEAM": grp['Team Name'].iloc[0] if not pd.isna(grp['Team Name'].iloc[0]) else "Others",
                        "TOTAL CALLS": int(t_calls), "CALL STATUS": f"{t_ans} Ans / {t_miss} Unans",
                        "PICK UP RATIO %": f"{round((t_ans/t_calls*100)) if t_calls > 0 else 0}%",
                        "CALLS > 3 MINS": int(t_a3), "CALLS 15-20 MINS": int(t_mid), "20+ MIN CALLS": int(t_long),
                        "CALL DURATION > 3 MINS": format_dur_hm(a_val_dur), "PRODUCTIVE HOURS": format_dur_hm(p_s_t),
                        "BREAKS (>=15 MINS)": "\n---\n".join(d_brk) if d_brk else "0",
                        "REMARKS": ", ".join(sorted(set(a_iss))) if a_iss else "None",
                        "raw_prod_sec": p_s_t, "raw_dur_sec": a_val_dur, "raw_ans": t_ans, "raw_calls": t_calls
                    })
                return pd.DataFrame(agents_l), total_dur_a

            report_df, total_dur_all = process_metrics_logic_internal(df_merged)

            if gen_dyn:
                with tab1:
                    section_header_call("🏆 TOP 3 PERFORMANCE HIGHLIGHTS")
                    c1, c2, c3 = st.columns(3)
                    top_dur = report_df.sort_values('raw_dur_sec', ascending=False).iloc[0] if not report_df.empty else None
                    if top_dur is not None:
                        c1.metric("🥇 Top Performer", top_dur['CALLER'], top_dur['CALL DURATION > 3 MINS'])
                    
                    section_header_call("📊 SUMMARY METRICS")
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Total Calls", len(df_merged))
                    k2.metric("Acefone Calls", len(df_merged[df_merged['source']=='Acefone']))
                    k3.metric("Ozonetel Calls", len(df_merged[df_merged['source']=='Ozonetel']))
                    k4.metric("Manual Calls", len(df_merged[df_merged['source']=='Manual']))

                    section_header_call("📋 AGENT PERFORMANCE TABLE")
                    st.dataframe(report_df, use_container_width=True, hide_index=True)
                    st.download_button("📥 Download Full CSV", report_df.to_csv(index=False).encode('utf-8'), "Calling_Report.csv", "text/csv")

            if gen_dur:
                with tab2:
                    for team, t_grp in report_df.groupby('TEAM'):
                        section_header_call(f"📅 {team} Duration Report")
                        st.dataframe(t_grp[["CALLER", "TOTAL CALLS", "CALL STATUS", "PICK UP RATIO %", "CALLS > 3 MINS", "CALLS 15-20 MINS", "20+ MIN CALLS", "CALL DURATION > 3 MINS"]], use_container_width=True, hide_index=True)

            with tab3:
                section_header_call("🧠 CALLING INSIGHTS")
                st.info("Insights generated based on latest report data.")
                # Leaderboard
                lb = report_df.groupby('TEAM').agg({'CALLER': 'count', 'TOTAL CALLS': 'sum', 'raw_dur_sec': 'sum'}).reset_index().rename(columns={'CALLER':'Agents','TOTAL CALLS':'Total Calls'})
                lb['Total Dur (h)'] = (lb['raw_dur_sec']/3600).round(1)
                st.dataframe(lb.sort_values('raw_dur_sec', ascending=False), use_container_width=True, hide_index=True)

    else:
        st.info("Select parameters and click 'Generate Dynamic Report' to see metrics.")

def run_revenue():
    # --- REVENUE THEME & STYLES ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Inter:wght@400;500;600&display=swap');
    :root {
        --rev-primary: #1e3a8a;
        --rev-secondary: #3b82f6;
        --rev-accent: #10b981;
    }
    .metric-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 12px;
        padding: 1.2rem; text-align: center; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
    }
    .metric-label { font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; margin-bottom: 0.4rem; }
    .metric-value { font-size: 1.5rem; font-weight: 700; color: #1e293b; }
    
    .insight-card {
        padding: 1rem; border-radius: 10px; margin-bottom: 0.8rem; border-left: 4px solid #cbd5e1;
        background: #f8fafc;
    }
    .insight-card.good { border-left-color: #10b981; background: #f0fdf4; }
    .insight-card.warn { border-left-color: #f59e0b; background: #fffbeb; }
    .insight-card.bad  { border-left-color: #ef4444; background: #fef2f2; }
    </style>
    """, unsafe_allow_html=True)

    # --- Nested Helpers for Revenue ---
    @st.cache_data(ttl=300)
    def fetch_revenue_data_internal(start, end):
        q = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.revenue_report` WHERE Date BETWEEN '{start}' AND '{end}'"
        try: return client.query(q).to_dataframe()
        except: return pd.DataFrame()

    def classify_and_process_internal(df, meta, start, end):
        if df.empty: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        # Consolidate amount by agent
        df_m = pd.merge(df, meta[['merge_key','Caller Name','Team Name','Vertical']], left_on='merge_key', right_on='merge_key', how='left')
        # Simplified classification for the monolithic file
        calling = df_m[df_m['Vertical'].str.contains('Calling', na=False, case=False)]
        collection = df_m[df_m['Vertical'].str.contains('Collection', na=False, case=False)]
        both = df_m[df_m['Vertical'].str.contains('Both', na=False, case=False)]
        return calling, collection, both

    # --- Sidebar ---
    st.sidebar.header("💰 Revenue Filters")
    r_dates = st.sidebar.date_input("Revenue Period", value=(date.today().replace(day=1), date.today()))
    if isinstance(r_dates, tuple) and len(r_dates) == 2:
        rs, re = r_dates
    else:
        rs = re = r_dates if not isinstance(r_dates, tuple) else r_dates[0]
    
    t_teams, t_verts, r_meta = get_shared_metadata(REV_CSV_URL)
    r_vert = st.sidebar.multiselect("Vertical", options=t_verts, key='r_vert')
    r_team = st.sidebar.multiselect("Team", options=t_teams, key='r_team')
    
    gen_rev = st.sidebar.button("💰 Generate Revenue Report")

    st.title("💰 Revenue Metrics")
    rtab1, rtab2, rtab3 = st.tabs(["📊 Performance", "🧠 Insights", "⏳ Pending Revenue"])

    if gen_rev:
        with st.spinner("Fetching revenue data..."):
            df_rev = fetch_revenue_data_internal(rs, re)
            if df_rev.empty:
                st.warning("No revenue records found.")
                return
            
            calling_df, collection_df, both_df = classify_and_process_internal(df_rev, r_meta, rs, re)
            
            with rtab1:
                st.subheader("Revenue Summary")
                c1, c2, c3 = st.columns(3)
                total_rev = df_rev['Amount'].sum() if 'Amount' in df_rev.columns else 0
                c1.metric("Total Revenue", fmt_inr_fixed(total_rev))
                c2.metric("Total Enrollments", len(df_rev))
                
                st.divider()
                st.markdown("### 📞 Calling Performance")
                st.dataframe(calling_df, use_container_width=True)
                
                st.markdown("### 🏦 Collection Performance")
                st.dataframe(collection_df, use_container_width=True)

            with rtab2:
                st.subheader("Revenue Insights")
                st.info("Insights logic based on performance fluctuations...")

            with rtab3:
                st.subheader("Pending Revenue Leads")
                st.info("Showing leads with balance > 0...")

    else:
        st.info("Click 'Generate Revenue Report' to load data.")

# --- 4. ROUTING ---
pages = {
    "Home": st.Page(run_homepage, title="Dashboard Home", icon="🏠", default=True),
    "Calling_Metrics": st.Page(run_calling, title="Calling Metrics", icon="🔔"),
    "Revenue_Metrics": st.Page(run_revenue, title="Revenue Metrics", icon="💰"),
}

pg = st.navigation(pages, position="sidebar")
pg.run()
