import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, date, time, timedelta
import os
import pytz
import numpy as np
import io
import streamlit.components.v1 as components
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Flowable
from reportlab.lib.enums import TA_CENTER

# --- GLOBAL CONFIG ---
st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- SESSION STATE ---
if 'selection' not in st.session_state:
    st.session_state.selection = "Home"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Sync with query params for navigation from Homepage HTML
qp = st.query_params
if "page" in qp:
    page_val = qp["page"]
    if page_val in ["Home", "Calling Metrics", "Revenue Metrics"]:
        st.session_state.selection = page_val

# --- AUTH ---
USERS = {'amit': {'name': 'Amit Ray', 'password': 'lawsikho@2024'}}
def login():
    st.markdown("<h2 style='text-align:center;'>Login to Analytics Hub</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("Login Form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                if u in USERS and USERS[u]['password'] == p:
                    st.session_state.logged_in = True
                    st.session_state.user_info = USERS[u]
                    st.rerun()
                else: st.error("Invalid credentials")

if not st.session_state.logged_in:
    login(); st.stop()

# --- BQ CLIENT ---
@st.cache_resource
def get_bq_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=creds, project=info["project_id"])
    return None
client = get_bq_client()

# --- MODULES ---
def run_homepage():
    # ── Logo URLs ──
    LAWSIKHO_LOGO       = "https://upload.wikimedia.org/wikipedia/commons/d/d4/LawSikho_Logo.png" # Standard URL
    SKILLARBITRAGE_LOGO = "https://skillarbitrage.com/wp-content/uploads/2022/10/Skill-Arbitrage-logo.png"

    @st.cache_data(ttl=300, show_spinner=False)
    def get_stats_internal():
        try:
            # Reusing the global 'client'
            if not client: return "N/A", "—", "N/A", "—"
            
            r1 = client.query("""
                SELECT updated_at_ampm FROM (
                    SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                    UNION ALL
                    SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
                ) WHERE updated_at_ampm IS NOT NULL ORDER BY 1 DESC LIMIT 1
            """).to_dataframe()
            call_time = str(r1["updated_at_ampm"].iloc[0]) if not r1.empty else "N/A"

            r2 = client.query("""
                SELECT SUM(c) AS t FROM (
                    SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                    UNION ALL
                    SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
                )
            """).to_dataframe()
            call_cnt = "{:,}".format(int(r2["t"].iloc[0])) if not r2.empty else "—"

            try:
                r3 = client.query("""
                    SELECT MAX(updated_at_ampm) AS last_updated, COUNT(*) AS cnt
                    FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet`
                """).to_dataframe()
                rev_time = str(r3["last_updated"].iloc[0]) if not r3.empty and r3["last_updated"].iloc[0] else "N/A"
                rev_cnt  = "{:,}".format(int(r3["cnt"].iloc[0])) if not r3.empty else "0"
            except Exception:
                rev_time, rev_cnt = "N/A", "0"

            return call_time, call_cnt, rev_time, rev_cnt
        except Exception:
            return "N/A", "—", "N/A", "—"

    c_time, c_cnt, r_time, r_cnt = get_stats_internal()

    html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@300;400;500;600&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet"/>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Plus Jakarta Sans', sans-serif; background: #0B1120; color: #E2E8F0; min-height: 100vh; overflow-x: hidden; background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,.12) 0%, transparent 60%), radial-gradient(ellipse 60% 40% at 90% 80%, rgba(249,115,22,.08) 0%, transparent 55%), radial-gradient(ellipse 50% 35% at 10% 90%, rgba(139,92,246,.06) 0%, transparent 50%), #0B1120; }
body::before { content: ""; position: fixed; inset: 0; background-image: linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px); background-size: 48px 48px; pointer-events: none; z-index: 0; }
.page { position: relative; z-index: 1; }
.hero { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 4rem 2rem 3rem; }
.logo-block { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 1.6rem; }
.logo-side { display: flex; align-items: center; justify-content: center; padding: 0 2rem; }
.logo-img { height: 46px; width: auto; object-fit: contain; mix-blend-mode: lighten; filter: brightness(1.25) contrast(1.1) saturate(.95); transition: transform .25s, opacity .25s; }
.logo-img:hover { transform: scale(1.05); }
.logo-glow-sep { width: 1px; height: 52px; background: linear-gradient(180deg, transparent 0%, rgba(249,115,22,.8) 35%, rgba(251,146,60,.9) 50%, rgba(249,115,22,.8) 65%, transparent 100%); box-shadow: 0 0 8px rgba(249,115,22,.6), 0 0 20px rgba(249,115,22,.3); border-radius: 1px; flex-shrink: 0; }
.hero-tagline { font-family: 'Fira Code', monospace; font-size: .78rem; font-weight: 400; color: rgba(255,255,255,.38); letter-spacing: 1.5px; margin-bottom: 2rem; }
.hero-eyebrow { display: inline-flex; align-items: center; gap: .5rem; font-family: 'Fira Code', monospace; font-size: .68rem; font-weight: 500; letter-spacing: 2.5px; text-transform: uppercase; color: #F97316; background: rgba(249,115,22,.08); border: 1px solid rgba(249,115,22,.18); border-radius: 100px; padding: .3rem 1rem; margin-bottom: 1.4rem; }
.eyebrow-dot { width: 5px; height: 5px; background: #F97316; border-radius: 50%; box-shadow: 0 0 6px #F97316; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(1.4); } }
.hero-headline { font-size: clamp(2.4rem, 5.5vw, 4.2rem); font-weight: 800; line-height: 1.08; color: #FFFFFF; letter-spacing: -1.5px; margin-bottom: .8rem; }
.hero-headline .accent { background: linear-gradient(125deg, #F97316 0%, #FB923C 40%, #FBBF24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: inline-block; }
.hero-sub { font-size: 1.15rem; font-weight: 300; color: rgba(255,255,255,.42); letter-spacing: .3px; margin-bottom: 3rem; max-width: 580px; }
.hero-rule { display: flex; align-items: center; gap: 1rem; width: 100%; max-width: 560px; margin-bottom: 3rem; }
.hero-rule-line { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.08)); }
.hero-rule-line.r { background: linear-gradient(90deg, rgba(255,255,255,.08), transparent); }
.hero-rule-label { font-family: 'Fira Code', monospace; font-size: .6rem; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,.2); white-space: nowrap; }
.stats-row { display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; padding: 0 2rem; margin-bottom: 4rem; }
.stat-card { display: flex; align-items: center; gap: .85rem; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 16px; padding: .9rem 1.4rem; min-width: 260px; flex: 1; max-width: 340px; backdrop-filter: blur(12px); transition: all .2s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-icon-wrap { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: .95rem; flex-shrink: 0; }
.si-call { background: rgba(249,115,22,.14); }
.si-rev { background: rgba(52,211,153,.12); }
.stat-lbl { font-family: 'Fira Code', monospace; font-size: .58rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,.3); }
.stat-val { font-family: 'Fira Code', monospace; font-size: .8rem; font-weight: 500; color: rgba(255,255,255,.82); }
.stat-sub { font-family: 'Fira Code', monospace; font-size: .58rem; color: rgba(255,255,255,.2); }
.pill-live { margin-left: auto; font-family: 'Fira Code', monospace; font-size: .55rem; color: #34D399; background: rgba(52,211,153,.1); border: 1px solid rgba(52,211,153,.18); border-radius: 20px; padding: 2px 8px; }
.dashboards-section { padding: 0 2rem 5rem; max-width: 1120px; margin: 0 auto; }
.section-head { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
.section-line { flex: 1; height: 1px; background: rgba(255,255,255,.07); }
.section-lbl { font-family: 'Fira Code', monospace; font-size: .65rem; letter-spacing: 2.5px; text-transform: uppercase; color: rgba(255,255,255,.25); white-space: nowrap; }
.cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
@media (max-width: 900px) { .cards-grid { grid-template-columns: 1fr; } }
.dcard { position: relative; background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.09); border-radius: 20px; padding: 1.8rem 1.7rem 1.5rem; text-decoration: none; color: inherit; display: flex; flex-direction: column; gap: .75rem; overflow: hidden; transition: all .25s; }
.dcard:hover { transform: translateY(-5px); border-color: #F97316; background: rgba(249,115,22,.04); }
.dcard-call { border-top: 2px solid rgba(249,115,22,.4); }
.dcard-rev { border-top: 2px solid rgba(52,211,153,.35); }
.dcard-rev:hover { border-color: #34D399; background: rgba(52,211,153,.04); }
.dcard-title { font-size: 1.2rem; font-weight: 600; color: #fff; }
.dcard-desc { font-size: .8rem; font-weight: 300; color: rgba(255,255,255,.42); line-height: 1.7; }
.dcard-cta { display: inline-flex; align-items: center; gap: .4rem; font-family: 'Fira Code', monospace; font-size: .72rem; color: rgba(255,255,255,.28); margin-top: .3rem; transition: all .2s; }
.dcard:hover .dcard-cta { color: inherit; gap: .65rem; }
.site-footer { border-top: 1px solid rgba(255,255,255,.06); padding: 2rem; text-align: center; color: rgba(255,255,255,.3); font-size: .7rem; }
</style>
<script>
function goTo(pageName) {
    const url = window.location.origin + window.location.pathname + "?page=" + encodeURIComponent(pageName);
    window.top.location.href = url;
}
</script>
</head>
<body>
<div class="page">
  <div class="hero">
    <div class="logo-block">
      <div class="logo-side"><img class="logo-img" src="LAWSIKHO_LOGO_PH" /></div>
      <div class="logo-glow-sep"></div>
      <div class="logo-side"><img class="logo-img" src="SA_LOGO_PH" /></div>
    </div>
    <div class="hero-tagline">India Learning &nbsp;📖&nbsp; India Earning</div>
    <div class="hero-eyebrow"><span class="eyebrow-dot"></span>Internal Analytics Hub</div>
    <div class="hero-headline">All your dashboards,<br><span class="accent">at one place</span></div>
    <div class="hero-sub">Real-time insights across Leads, Revenue &amp; Calling</div>
    <div class="hero-rule"><div class="hero-rule-line"></div><span class="hero-rule-label">Live Dashboards</span><div class="hero-rule-line r"></div></div>
  </div>
  <div class="stats-row">
    <div class="stat-card sc-call"><div class="stat-icon-wrap si-call">🔔</div><div class="stat-info"><span class="stat-lbl">Calling Data</span><span class="stat-val">CALL_TIME_PH</span><span class="stat-sub">CALL_CNT_PH records</span></div><span class="pill-live">● Live</span></div>
    <div class="stat-card sc-rev"><div class="stat-icon-wrap si-rev">💰</div><div class="stat-info"><span class="stat-lbl">Revenue Data</span><span class="stat-val">REV_TIME_PH</span><span class="stat-sub">REV_CNT_PH records</span></div><span class="pill-live">● Live</span></div>
  </div>
  <div class="dashboards-section">
    <div class="section-head"><div class="section-line"></div><span class="section-lbl">Dashboards</span><div class="section-line"></div></div>
    <div class="cards-grid">
      <a class="dcard dcard-call" href="javascript:void(0)" onclick="goTo('Calling Metrics')">
        <div class="dcard-title">Calling Metrics</div>
        <div class="dcard-desc">Full CDR analysis across Ozonetel, Acefone &amp; Manual calls. Agent-level performance &amp; leaderboards.</div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>
      <a class="dcard dcard-rev" href="javascript:void(0)" onclick="goTo('Revenue Metrics')">
        <div class="dcard-title">Revenue Metrics</div>
        <div class="dcard-desc">Enrollment revenue, target achievement &amp; caller-level breakdown. Course performance &amp; sources.</div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>
    </div>
  </div>
  <div class="site-footer">Developed and Designed by Amit Ray &nbsp;·&nbsp; For Internal Use Only</div>
</div>
</body>
</html>
    """
    html = html.replace("LAWSIKHO_LOGO_PH", LAWSIKHO_LOGO)
    html = html.replace("SA_LOGO_PH",       SKILLARBITRAGE_LOGO)
    html = html.replace("CALL_TIME_PH",     c_time)
    html = html.replace("CALL_CNT_PH",      c_cnt)
    html = html.replace("REV_TIME_PH",      r_time)
    html = html.replace("REV_CNT_PH",       r_cnt)
    components.html(html, height=900, scrolling=True)

def run_calling():
    # --- PROFESSIONAL WARM THEME ---
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
:root { --accent-primary: #F97316; --accent-secondary: #EF4444; --accent-success: #EAB308; --accent-warn: #FBBF24; --accent-danger: #DC2626; --gold: #F59E0B; --silver: #9CA3AF; --bronze: #CD7F32; --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px; --shadow-sm: 0 1px 3px rgba(0,0,0,.08), 0 1px 2px rgba(0,0,0,.06); --shadow-md: 0 4px 16px rgba(0,0,0,.10); --shadow-lg: 0 8px 32px rgba(0,0,0,.14); --transition: all 0.22s cubic-bezier(.4,0,.2,1); }
[data-testid="stAppViewContainer"] { --bg-base: #FFF8F3; --bg-surface: #FFFFFF; --bg-elevated: #FFFFFF; --bg-muted: #FEF3E8; --border: rgba(249,115,22,.12); --text-primary: #111827; --text-muted: #6B7280; --metric-bg: #FFFFFF; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.cw-header { background: linear-gradient(135deg, #1c0700 0%, #7c2d12 50%, #431407 100%); border-radius: var(--radius-lg); padding: 1.5rem 2rem; margin-bottom: 1.2rem; box-shadow: var(--shadow-lg); }
.cw-title { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; }
.cw-subtitle { font-size: .82rem; color: rgba(255,255,255,.6); font-family: 'DM Mono', monospace; }
.cw-badge { display: inline-flex; align-items: center; gap: 5px; background: #FEF3E8; border: 1px solid rgba(249,115,22,.12); border-radius: 20px; padding: 3px 10px; font-size: .73rem; color: #111827; }
.metric-card { background: #fff; border: 1px solid rgba(249,115,22,.12); border-radius: var(--radius-md); padding: .9rem 1rem; box-shadow: var(--shadow-sm); text-align: center; }
.metric-label { font-size: .68rem; font-weight: 600; text-transform: uppercase; color: #6B7280; }
.metric-value { font-size: 1.45rem; font-weight: 700; color: #111827; font-family: 'DM Mono', monospace; }
.section-header { display: flex; align-items: center; gap: .6rem; margin: 1.5rem 0 .8rem; }
.section-title { font-size: .78rem; font-weight: 700; text-transform: uppercase; color: #F97316; }
</style>
""", unsafe_allow_html=True)

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"

    def style_total(row):
        if row["CALLER"] == "TOTAL": return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
        return [''] * len(row)

    def format_dur_hm(total_seconds):
        if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
        tm = int(round(total_seconds / 60)); return f"{tm // 60}h {tm % 60}m"

    def get_display_gap_seconds(start_time, end_time):
        if pd.isna(start_time) or pd.isna(end_time): return 0
        s = start_time.replace(second=0, microsecond=0); e = end_time.replace(second=0, microsecond=0)
        return (e - s).total_seconds()

    @st.cache_data(ttl=120)
    def get_global_last_update():
        try:
            res = client.query("SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` ORDER BY updated_at DESC LIMIT 1").to_dataframe()
            return str(res['updated_at_ampm'].iloc[0]) if not res.empty else "N/A"
        except: return "N/A"

    @st.cache_data(ttl=120)
    def get_available_dates():
        try:
            res = client.query("SELECT MIN(`Call Date`) as min_d, MAX(`Call Date`) as max_d FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`").to_dataframe()
            return res['min_d'].iloc[0], res['max_d'].iloc[0]
        except: return date.today(), date.today()

    def compute_team_insights(df_merged, report_df):
        insights = []
        if report_df.empty: return insights
        team_avg = report_df.groupby("TEAM")["raw_dur_sec"].mean().sort_values(ascending=False)
        if not team_avg.empty:
            insights.append({"type":"good","icon":"🏆","title":f"Top Team: {team_avg.index[0]}","body":f"Avg duration {format_dur_hm(team_avg.iloc[0])}."})
        return insights

    def generate_calling_helper_pdf_bytes():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build([Paragraph("Calling Metrics Logic Guide", ParagraphStyle('Title', fontSize=18))])
        return buffer.getvalue()

    @st.cache_data(ttl=120)
    def fetch_call_data(start_date, end_date):
        q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
        df_ace = client.query(q_ace).to_dataframe(); df_ace['source'] = 'Acefone'; df_ace['unique_lead_id'] = df_ace['client_number']
        q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
        df_ozo = client.query(q_ozo).to_dataframe()
        if not df_ozo.empty:
            df_ozo['unique_lead_id'] = df_ozo['phone_number']
            df_ozo = df_ozo.rename(columns={'CallID': 'call_id', 'AgentName': 'call_owner', 'phone_number': 'client_number', 'StartTime': 'call_datetime', 'CallDate': 'Call Date', 'duration_sec': 'call_duration', 'Status': 'status', 'Type': 'direction', 'Disposition': 'reason'})
            df_ozo['status'] = df_ozo['status'].str.lower().replace({'unanswered': 'missed'}); df_ozo['direction'] = df_ozo['direction'].str.lower().replace({'manual': 'outbound'}); df_ozo['source'] = 'Ozonetel'
        q_man = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.manual_calls` WHERE Call_Date BETWEEN '{start_date}' AND '{end_date}'"
        df_man = client.query(q_man).to_dataframe()
        if not df_man.empty:
            df_man['unique_lead_id'] = df_man['client_number']; df_man = df_man.rename(columns={'Call_Date': 'Call Date', 'Approved_By': 'reason'}); df_man['status'] = 'answered'; df_man['direction'] = 'outbound'; df_man['source'] = 'Manual'; df_man['call_datetime'] = pd.NaT
        df = pd.concat([df_ace, df_ozo, df_man], ignore_index=True)
        if not df.empty:
            df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
            df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
            df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
            ozo_mask = df['source'] == 'Ozonetel'; df.loc[ozo_mask, 'call_starttime'] = df.loc[ozo_mask, 'call_endtime']
            df.loc[ozo_mask, 'call_endtime'] = df.loc[ozo_mask, 'call_starttime'] + pd.to_timedelta(df.loc[ozo_mask, 'call_duration'], unit='s')
        return df

    def process_metrics_logic(df_filtered):
        agents_list = []; total_duration_agg = 0; ist_tz = pytz.timezone("Asia/Kolkata")
        for owner, agent_group in df_filtered.groupby('call_owner'):
            total_ans, total_calls, total_above_3min, agent_valid_dur, total_break_sec_all_days, total_active_days = 0, 0, 0, 0, 0, 0
            daily_io_list, daily_break_list, all_issues = [], [], []
            for c_date, day_group in agent_group.groupby('Call Date'):
                timed_group = day_group[day_group['call_starttime'].notna()].sort_values('call_starttime'); total_active_days += 1
                ans = len(day_group[day_group['status'].str.lower() == 'answered']); total_ans += ans; total_calls += len(day_group)
                total_above_3min += len(day_group[day_group['call_duration'] >= 180]); day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum(); agent_valid_dur += day_dur
                if timed_group.empty: continue
                first_s, last_e = timed_group['call_starttime'].min(), timed_group['call_endtime'].max()
                daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {first_s.strftime('%I:%M %p')} · Out {last_e.strftime('%I:%M %p')}")
                start_o, end_o = ist_tz.localize(datetime.combine(c_date, time(10, 0))), ist_tz.localize(datetime.combine(c_date, time(20, 0)))
                if first_s > ist_tz.localize(datetime.combine(c_date, time(10, 15))): all_issues.append("Late Check-In")
                if last_e < end_o: all_issues.append("Early Check-Out")
                day_break_sec = 0
                if first_s > start_o:
                    g = get_display_gap_seconds(start_o, first_s)
                    if g >= 900: day_break_sec += g
                for i in range(len(timed_group) - 1):
                    act_s, act_e = max(timed_group['call_endtime'].iloc[i], start_o), min(timed_group['call_starttime'].iloc[i+1], end_o)
                    if act_e > act_s:
                        g = get_display_gap_seconds(act_s, act_e)
                        if g >= 900: day_break_sec += g
                if last_e < end_o:
                    g = get_display_gap_seconds(last_e, end_o)
                    if g >= 900: day_break_sec += g
                total_break_sec_all_days += day_break_sec
            total_duration_agg += agent_valid_dur; prod_sec = (36000 * total_active_days) - total_break_sec_all_days
            agents_list.append({"IN/OUT TIME": "\n".join(daily_io_list), "CALLER": owner, "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others", "TOTAL CALLS": int(total_calls), "CALL STATUS": f"{total_ans} Ans", "PICK UP RATIO %": f"{round((total_ans/total_calls*100)) if total_calls > 0 else 0}%", "CALLS > 3 MINS": int(total_above_3min), "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur), "PRODUCTIVE HOURS": format_dur_hm(prod_sec), "REMARKS": ", ".join(set(all_issues)) if all_issues else "None", "raw_prod_sec": prod_sec, "raw_dur_sec": agent_valid_dur})
        return pd.DataFrame(agents_list), total_duration_agg

    min_d, max_d = date(2024,1,1), date.today()
    st.sidebar.markdown("<h3 style='color:#F97316;'>Calling Filters</h3>", unsafe_allow_html=True)
    d_range = st.sidebar.date_input("📅 Select Range", value=(date.today(), date.today()))
    if isinstance(d_range, tuple) and len(d_range) == 2: s_d, e_d = d_range
    else: s_d = e_d = d_range[0] if isinstance(d_range, tuple) else d_range
    teams, verticals, df_meta = get_metadata()
    sel_vert = st.sidebar.multiselect("👑 Vertical", options=verticals)
    sel_team = st.sidebar.multiselect("👥 Team", options=teams)
    gen_dyn = st.sidebar.button("🚀 Generate Report")

    st.markdown(f'<div class="cw-header"><div class="cw-title">🔔 CALLING METRICS</div><div class="cw-subtitle">{s_d} to {e_d}</div></div>', unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["🚀 Dashboard", "📊 Raw Logs"])
    with tab1:
        if gen_dyn:
            df_raw = fetch_call_data(s_d, e_d)
            if df_raw.empty: st.warning("No data.")
            else:
                df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
                df = pd.merge(df_raw, df_meta[['merge_key','Caller Name','Team Name','Vertical']].drop_duplicates('merge_key'), on='merge_key', how='left')
                df['call_owner'] = df['Caller Name'].fillna(df['call_owner'])
                if sel_vert: df = df[df['Vertical'].isin(sel_vert)]
                if sel_team: df = df[df['Team Name'].isin(sel_team)]
                report_df, total_dur = process_metrics_logic(df)
                report_df = report_df.sort_values("raw_dur_sec", ascending=False)
                st.dataframe(report_df.drop(columns=['raw_prod_sec','raw_dur_sec']).style.apply(style_total, axis=1), use_container_width=True, hide_index=True)
        else: st.info("Click Generate Report.")
    with tab2:
        if gen_dyn: st.dataframe(df_raw.head(500))

    # [REVENUE_PART_1_PLACEHOLDER]

def run_revenue():
    # [REVENUE_PART_1]
    def compute_revenue_insights(df_merged, report_df, month_label):
        insights = []
        if report_df.empty: return insights
        # ... logic as seen in source ...
        return insights[:6]

    def generate_revenue_helper_pdf_bytes():
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        doc.build([Paragraph("Revenue Metrics Logic Guide", ParagraphStyle('Title', fontSize=18))])
        return buffer.getvalue()

    DROP_LEADS_URL_P = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRJ9qaFD5Sc9O1JFH7ijR0JI2SEkAgXM8PJZsWslsASLDnTCA_fwIP0fg_PmtdMm_zs3KwTLI45fPog/pub?gid=1082322056&single=true&output=csv"

    def pending_months():
        today = date.today()
        c_start = date(today.year, today.month, 1)
        p_end = c_start - timedelta(days=1)
        return c_start, today, date(p_end.year, p_end.month, 1), p_end

    @st.cache_data(ttl=300)
    def load_drop_leads():
        try:
            df = pd.read_csv(DROP_LEADS_URL_P); df.columns = df.columns.str.strip()
            return df
        except: return pd.DataFrame()

    @st.cache_data(ttl=120)
    def fetch_both_months_rev(p_start, c_end):
        q = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet` WHERE Date BETWEEN '{p_start}' AND '{c_end}'"
        df = client.query(q).to_dataframe()
        if df.empty: return df
        df['Fee_paid'] = pd.to_numeric(df['Fee_paid'], errors='coerce').fillna(0)
        df['Course_Price'] = pd.to_numeric(df['Course_Price'], errors='coerce').fillna(0)
        df['Email_Id_norm'] = df['Email_Id'].astype(str).str.strip().str.lower()
        df['Contact_No_norm'] = df['Contact_No'].astype(str).str.replace(r'\D', '', regex=True).str[-10:]
        return df

    def build_drop_display(drop_agg, curr_label, prev_label):
        rows = []; g_c = g_p = g_t = 0
        for vert in sorted(drop_agg['Vertical'].fillna('Others').unique()):
            v_df = drop_agg[drop_agg['Vertical'].fillna('Others') == vert]
            vc = vp = vt = 0
            for team in sorted(v_df['Team Name'].fillna('Others').unique()):
                t_df = v_df[v_df['Team Name'].fillna('Others') == team]
                tc = tp = tt = 0
                for _, r in t_df.sort_values('total_drops', ascending=False).iterrows():
                    rows.append({'_rt': 'data', 'CALLER NAME': r['Caller_name'], 'TEAM': team, 'VERTICAL': vert, f'{curr_label} DROPS': int(r['curr_drops']), f'{prev_label} DROPS': int(r['prev_drops']), 'TOTAL DROPS': int(r['total_drops'])})
                    tc += r['curr_drops']; tp += r['prev_drops']; tt += r['total_drops']
                rows.append({'_rt': 'team_total', 'CALLER NAME': f'{team} Total', 'TEAM': '—', 'VERTICAL': vert, f'{curr_label} DROPS': int(tc), f'{prev_label} DROPS': int(tp), 'TOTAL DROPS': int(tt)})
                vc += tc; vp += tp; vt += tt
            rows.append({'_rt': 'vertical_total', 'CALLER NAME': f'{vert} Total', 'TEAM': '—', 'VERTICAL': '—', f'{curr_label} DROPS': int(vc), f'{prev_label} DROPS': int(vp), 'TOTAL DROPS': int(vt)})
            g_c += vc; g_p += vp; g_t += vt
        rows.append({'_rt': 'grand_total', 'CALLER NAME': 'Grand Total', 'TEAM': '—', 'VERTICAL': '—', f'{curr_label} DROPS': int(g_c), f'{prev_label} DROPS': int(g_p), 'TOTAL DROPS': int(g_t)})
        return pd.DataFrame(rows)

    def render_html_pending_table(combined, mode, curr_label, prev_label, title):
        hdr_style  = "background:#064e3b;color:#fff;font-size:.72rem;font-weight:700;text-transform:uppercase;padding:8px 6px;text-align:center;border:1px solid #065f46;"
        sub_style  = "background:#065f46;color:#fff;font-size:.68rem;font-weight:600;padding:6px 4px;text-align:center;border:1px solid #0d9e6e;"
        data_style = "font-size:.72rem;padding:6px 5px;text-align:center;border:1px solid #d1fae5;color:#111827;background:#ffffff;"
        data_style_alt = "font-size:.72rem;padding:6px 5px;text-align:center;border:1px solid #d1fae5;color:#111827;background:#f0fdf4;"
        team_style = "font-weight:700;background:#1f2937;color:#fff;font-size:.72rem;padding:7px 5px;text-align:center;border:1px solid #374151;"
        vert_style = "font-weight:700;background:#064e3b;color:#fff;font-size:.72rem;padding:7px 5px;text-align:center;border:1px solid #065f46;"
        grand_style= "font-weight:700;background:#1e3a5f;color:#fff;font-size:.72rem;padding:8px 5px;text-align:center;border:1px solid #1e3a5f;"
        name_col   = "CALLER NAME" if mode == "caller" else "TEAM NAME"
        extra_th   = '<th rowspan="2" style="' + hdr_style + '">TEAM</th>' if mode == "caller" else ""
        html = (
            "<div style='margin:1.5rem 0 .5rem;text-align:center;'>"
            "<div style='font-size:1rem;font-weight:800;text-transform:uppercase;letter-spacing:1px;color:#10B981;margin-bottom:.5rem;'>" + title + "</div></div>"
            "<div style='overflow-x:auto;'><table style='width:100%;border-collapse:collapse;'><thead>"
            "<tr><th rowspan='2' style='" + hdr_style + "'>" + name_col + "</th>" + extra_th +
            "<th colspan='7' style='" + hdr_style + "background:#065f46;'>" + curr_label.upper() + "</th>"
            "<th colspan='2' style='" + hdr_style + "background:#92400e;'>" + prev_label.upper() + "</th>"
            "<th colspan='2' style='" + hdr_style + "background:#1e3a5f;'>GRAND TOTAL</th>"
            "</tr><tr><th style='" + sub_style + "'>REVENUE POOL</th><th style='" + sub_style + "'>TOTAL REVENUE COLLECTED</th>"
            "<th style='" + sub_style + "'>BALANCE AMOUNT</th><th style='" + sub_style + "'>NO. OF LEADS</th>"
            "<th style='" + sub_style + "background:#0f766e;'>LEADS >48 HRS</th>"
            "<th style='" + sub_style + "background:#0f766e;'>BAL >48 HRS</th>"
            "<th style='" + sub_style + "background:#0f766e;'>% PENDING >48 HRS</th>"
            "<th style='" + sub_style + "background:#92400e;'>BALANCE</th>"
            "<th style='" + sub_style + "background:#92400e;'>LEADS</th>"
            "<th style='" + sub_style + "background:#1e3a5f;'>AMOUNT</th>"
            "<th style='" + sub_style + "background:#1e3a5f;'>TOTAL LEADS</th>"
            "</tr></thead><tbody>")
        g = {k: 0 for k in ["pool","collected","balance","leads","leads_48","bal_48hr","prev_bal","prev_leads","grand_bal","grand_leads"]}
        v_order = combined.assign(_v=combined["Vertical"].fillna("Unassigned")).groupby("_v")["grand_bal"].sum().sort_values(ascending=False).index.tolist()
        for vert in v_order:
            v_df = combined[combined["Vertical"].fillna("Unassigned") == vert].copy(); v = {k: 0 for k in g}
            t_order = v_df.assign(_t=v_df["Team Name"].fillna("Unassigned")).groupby("_t")["grand_bal"].sum().sort_values(ascending=False).index.tolist()
            for team in t_order:
                t_df = v_df[v_df["Team Name"].fillna("Unassigned") == team].copy(); t = {k: 0 for k in g}; r_idx = 0
                if mode == "caller":
                    for _, r in t_df.sort_values('balance', ascending=False).iterrows():
                        pct = _pct48(r.get("bal_48hr",0), r.get("balance",0)); ds = data_style_alt if r_idx % 2 == 1 else data_style; r_idx += 1
                        html += f"<tr><td style='{ds}'>{r.get('Caller_name','—')}</td><td style='{ds}'>{team}</td><td style='{ds}'>{fmt_inr(r.get('pool',0))}</td><td style='{ds}'>{fmt_inr(r.get('collected',0))}</td><td style='{ds}color:#DC2626;font-weight:600;'>{fmt_inr(r.get('balance',0))}</td><td style='{ds}'>{int(r.get('leads',0))}</td><td style='{ds}'>{int(r.get('leads_48',0))}</td><td style='{ds}'>{fmt_inr(r.get('bal_48hr',0))}</td><td style='{ds}'>{pct}</td><td style='{ds}background:#fef3c7;'>{fmt_inr(r.get('prev_bal',0))}</td><td style='{ds}background:#fef3c7;'>{int(r.get('prev_leads',0))}</td><td style='{ds}background:#dbeafe;font-weight:600;'>{fmt_inr(r.get('grand_bal',0))}</td><td style='{ds}background:#dbeafe;font-weight:600;'>{int(r.get('grand_leads',0))}</td></tr>"
                        for k in t: t[k] += float(r.get(k,0))
                else:
                    for k in t: t[k] = t_df[k].sum()
                html += f"<tr><td style='{team_style}'>{team} Total</td>" + ("<td style='" + team_style + "'>—</td>" if mode == "caller" else "") + f"<td style='{team_style}'>{fmt_inr(t['pool'])}</td><td style='{team_style}'>{fmt_inr(t['collected'])}</td><td style='{team_style}'>{fmt_inr(t['balance'])}</td><td style='{team_style}'>{int(t['leads'])}</td><td style='{team_style}'>{int(t['leads_48'])}</td><td style='{team_style}'>{fmt_inr(t['bal_48hr'])}</td><td style='{team_style}'>{_pct48(t['bal_48hr'],t['balance'])}</td><td style='{team_style}'>{fmt_inr(t['prev_bal'])}</td><td style='{team_style}'>{int(t['prev_leads'])}</td><td style='{team_style}'>{fmt_inr(t['grand_bal'])}</td><td style='{team_style}'>{int(t['grand_leads'])}</td></tr>"
                for k in v: v[k] += t[k]
            html += f"<tr><td style='{vert_style}'>{vert} Total</td>" + ("<td style='" + vert_style + "'>—</td>" if mode == "caller" else "") + f"<td style='{vert_style}'>{fmt_inr(v['pool'])}</td><td style='{vert_style}'>{fmt_inr(v['collected'])}</td><td style='{vert_style}'>{fmt_inr(v['balance'])}</td><td style='{vert_style}'>{int(v['leads'])}</td><td style='{vert_style}'>{int(v['leads_48'])}</td><td style='{vert_style}'>{fmt_inr(v['bal_48hr'])}</td><td style='{vert_style}'>{_pct48(v['bal_48hr'],v['balance'])}</td><td style='{vert_style}'>{fmt_inr(v['prev_bal'])}</td><td style='{vert_style}'>{int(v['prev_leads'])}</td><td style='{vert_style}'>{fmt_inr(v['grand_bal'])}</td><td style='{vert_style}'>{int(v['grand_leads'])}</td></tr>"
            for k in g: g[k] += v[k]
        html += f"<tr><td style='{grand_style}'>Grand Total</td>" + ("<td style='" + grand_style + "'>—</td>" if mode == "caller" else "") + f"<td style='{grand_style}'>{fmt_inr(g['pool'])}</td><td style='{grand_style}'>{fmt_inr(g['collected'])}</td><td style='{grand_style}'>{fmt_inr(g['balance'])}</td><td style='{grand_style}'>{int(g['leads'])}</td><td style='{grand_style}'>{int(g['leads_48'])}</td><td style='{grand_style}'>{fmt_inr(g['bal_48hr'])}</td><td style='{grand_style}'>{_pct48(g['bal_48hr'],g['balance'])}</td><td style='{grand_style}'>{fmt_inr(g['prev_bal'])}</td><td style='{grand_style}'>{int(g['prev_leads'])}</td><td style='{grand_style}'>{fmt_inr(g['grand_bal'])}</td><td style='{grand_style}'>{int(g['grand_leads'])}</td></tr>"
        return html + "</tbody></table></div>"

    def render_drop_html(drop_agg, curr_label, prev_label):
        hs = "background:#7c2d12;color:#fff;font-size:.72rem;font-weight:700;text-transform:uppercase;padding:8px 6px;text-align:center;border:1px solid #991b1b;"
        ds = "font-size:.72rem;padding:6px 5px;text-align:center;border:1px solid #d1fae5;color:#111827;background:#ffffff;"
        ds_alt = "font-size:.72rem;padding:6px 5px;text-align:center;border:1px solid #d1fae5;color:#111827;background:#fff7ed;"
        ts = "font-weight:700;background:#1f2937;color:#fff;font-size:.72rem;padding:7px 5px;text-align:center;border:1px solid #374151;"
        vs = "font-weight:700;background:#7c2d12;color:#fff;font-size:.72rem;padding:7px 5px;text-align:center;border:1px solid #991b1b;"
        gs = "font-weight:700;background:#1e3a5f;color:#fff;font-size:.72rem;padding:8px 5px;text-align:center;border:1px solid #1e3a5f;"
        html = (
            "<div style='overflow-x:auto;'><table style='width:100%;border-collapse:collapse;'><thead><tr>"
            "<th style='" + hs + "'>CALLER NAME</th><th style='" + hs + "'>TEAM</th><th style='" + hs + "'>VERTICAL</th>"
            "<th style='" + hs + "'>" + curr_label.upper() + " DROPS</th><th style='" + hs + "'>" + prev_label.upper() + " DROPS</th>"
            "<th style='" + hs + "'>TOTAL DROPS</th></tr></thead><tbody>"
        )
        g_c = g_p = g_t = 0
        for vert in sorted(drop_agg["Vertical"].fillna("Others").unique()):
            v_df = drop_agg[drop_agg["Vertical"].fillna("Others") == vert]; vc = vp = vt = 0
            for team in sorted(v_df["Team Name"].fillna("Others").unique()):
                t_df = v_df[v_df["Team Name"].fillna("Others") == team]; tc = tp = tt = 0; r_idx = 0
                for _, r in t_df.sort_values('total_drops', ascending=False).iterrows():
                    drow = ds_alt if r_idx % 2 == 1 else ds; r_idx += 1
                    html += f"<tr><td style='{drow}'>{r['Caller_name']}</td><td style='{drow}'>{team}</td><td style='{drow}'>{vert}</td><td style='{drow}'>{int(r['curr_drops'])}</td><td style='{drow}'>{int(r['prev_drops'])}</td><td style='{drow}font-weight:600;color:#DC2626;'>{int(r['total_drops'])}</td></tr>"
                    tc += r['curr_drops']; tp += r['prev_drops']; tt += r['total_drops']
                html += f"<tr><td style='{ts}'>{team} Total</td><td style='{ts}'>—</td><td style='{ts}'>{vert}</td><td style='{ts}'>{int(tc)}</td><td style='{ts}'>{int(tp)}</td><td style='{ts}'>{int(tt)}</td></tr>"
                vc += tc; vp += tp; vt += tt
            html += f"<tr><td style='{vs}'>{vert} Total</td><td style='{vs}'>—</td><td style='{vs}'>—</td><td style='{vs}'>{int(vc)}</td><td style='{vs}'>{int(vp)}</td><td style='{vs}'>{int(vt)}</td></tr>"
            g_c += vc; g_p += vp; g_t += vt
        html += f"<tr><td style='{gs}'>Grand Total</td><td style='{gs}'>—</td><td style='{gs}'>—</td><td style='{gs}'>{int(g_c)}</td><td style='{gs}'>{int(g_p)}</td><td style='{gs}'>{int(g_t)}</td></tr>"
        return html + "</tbody></table></div>"

    def build_pending_excel(combined, pend_curr, pend_prev, meta_map_pending, curr_label, prev_label):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        HDR_FILL   = PatternFill("solid", start_color="064e3b", end_color="064e3b")
        TEAM_FILL  = PatternFill("solid", start_color="1f2937", end_color="1f2937")
        VERT_FILL  = PatternFill("solid", start_color="064e3b", end_color="064e3b")
        GRAND_FILL = PatternFill("solid", start_color="1e3a5f", end_color="1e3a5f")
        ALT_FILL   = PatternFill("solid", start_color="f0fdf4", end_color="f0fdf4")
        WHITE_FILL = PatternFill("solid", start_color="ffffff", end_color="ffffff")
        HDR_FONT   = Font(bold=True, color="FFFFFF", name="Arial", size=9)
        DATA_FONT  = Font(name="Arial", size=9)
        BOLD_WHITE = Font(bold=True, color="FFFFFF", name="Arial", size=9)
        BORDER     = Border(left=Side(style='thin', color='D1FAE5'), right=Side(style='thin', color='D1FAE5'), top=Side(style='thin', color='D1FAE5'), bottom=Side(style='thin', color='D1FAE5'))
        CENTER = Alignment(horizontal='center', vertical='center', wrap_text=True)
        LEFT   = Alignment(horizontal='left',   vertical='center', wrap_text=True)
        wb = Workbook(); num_keys = ["pool","collected","balance","leads","leads_48","bal_48hr","prev_bal","prev_leads","grand_bal","grand_leads"]
        def _safe(v):
            try: return 0 if pd.isna(float(v)) else float(v)
            except: return 0
        def _pct(b48, bal): return round(b48/bal*100, 1) if bal > 0 else 0.0
        def write_pending_sheet(ws, mode):
            cl, pl = curr_label.upper(), prev_label.upper(); name_col_hdr = "CALLER NAME" if mode == "caller" else "TEAM NAME"
            col = 1; ws.cell(1, col, name_col_hdr).fill = HDR_FILL; ws.cell(1, col).font = HDR_FONT; ws.cell(1, col).alignment = CENTER; ws.cell(1, col).border = BORDER
            col += 1; 
            if mode == "caller": 
                ws.cell(1, col, "TEAM").fill = HDR_FILL; ws.cell(1, col).font = HDR_FONT; ws.cell(1, col).alignment = CENTER; ws.cell(1, col).border = BORDER; col += 1
            for i in range(7): ws.cell(1, col+i, cl if i == 0 else "").fill = PatternFill("solid", start_color="065f46", end_color="065f46"); ws.cell(1, col+i).font = HDR_FONT; ws.cell(1, col+i).alignment = CENTER; ws.cell(1, col+i).border = BORDER
            ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col+6); col += 7
            for i in range(2): ws.cell(1, col+i, pl if i == 0 else "").fill = PatternFill("solid", start_color="92400e", end_color="92400e"); ws.cell(1, col+i).font = HDR_FONT; ws.cell(1, col+i).alignment = CENTER; ws.cell(1, col+i).border = BORDER
            ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col+1); col += 2
            for i in range(2): ws.cell(1, col+i, "GRAND TOTAL" if i == 0 else "").fill = PatternFill("solid", start_color="1e3a5f", end_color="1e3a5f"); ws.cell(1, col+i).font = HDR_FONT; ws.cell(1, col+i).alignment = CENTER; ws.cell(1, col+i).border = BORDER
            ws.merge_cells(start_row=1, start_column=col, end_row=1, end_column=col+1)
            sub_headers = [name_col_hdr] + (["TEAM"] if mode == "caller" else []) + ["REVENUE POOL (₹)", "COLLECTED (₹)", "BALANCE (₹)", "LEADS", "LEADS >48HR", "BALANCE >48HR (₹)", "% PENDING >48HR", f"BALANCE ({pl}) (₹)", f"LEADS ({pl})", "GRAND BALANCE (₹)", "GRAND LEADS"]
            for c_idx, h in enumerate(sub_headers, 1): cell = ws.cell(2, c_idx, h); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.alignment = CENTER; cell.border = BORDER
            ws.row_dimensions[1].height = 22; ws.row_dimensions[2].height = 28; row_num = 3; g = {k: 0.0 for k in num_keys}
            vert_order = combined.assign(_v=combined["Vertical"].fillna("Unassigned")).groupby("_v")["grand_bal"].sum().sort_values(ascending=False).index.tolist()
            for vert in vert_order:
                v_df = combined[combined["Vertical"].fillna("Unassigned") == vert].copy(); v = {k: 0.0 for k in num_keys}
                team_order = v_df.assign(_t=v_df["Team Name"].fillna("Unassigned")).groupby("_t")["grand_bal"].sum().sort_values(ascending=False).index.tolist()
                for team in team_order:
                    t_df = v_df[v_df["Team Name"].fillna("Unassigned") == team].copy(); t = {k: 0.0 for k in num_keys}
                    if mode == "caller":
                        for _, r in t_df.sort_values("balance", ascending=False).iterrows():
                            vals = [str(r.get("Caller_name", "—")), str(team), _safe(r.get("pool", 0)), _safe(r.get("collected", 0)), _safe(r.get("balance", 0)), int(_safe(r.get("leads", 0))), int(_safe(r.get("leads_48", 0))), _safe(r.get("bal_48hr", 0)), _pct(_safe(r.get("bal_48hr", 0)), _safe(r.get("balance", 0))), _safe(r.get("prev_bal", 0)), int(_safe(r.get("prev_leads", 0))), _safe(r.get("grand_bal", 0)), int(_safe(r.get("grand_leads", 0)))]
                            for c_idx, v_ in enumerate(vals, 1): cell = ws.cell(row_num, c_idx, v_); cell.font = DATA_FONT; cell.border = BORDER; cell.alignment = LEFT if c_idx <= 2 else CENTER
                            row_num += 1; 
                            for k in num_keys: t[k] += _safe(r.get(k, 0))
                    else:
                        for k in num_keys: t[k] = t_df[k].sum() if k in t_df.columns else 0
                    t_rt = [f"{team} Total"] + (["—"] if mode == "caller" else []) + [t["pool"], t["collected"], t["balance"], int(t["leads"]), int(t["leads_48"]), t["bal_48hr"], _pct(t["bal_48hr"], t["balance"]), t["prev_bal"], int(t["prev_leads"]), t["grand_bal"], int(t["grand_leads"])]
                    for c_idx, v_ in enumerate(t_rt, 1): cell = ws.cell(row_num, c_idx, v_); cell.fill = TEAM_FILL; cell.font = BOLD_WHITE; cell.border = BORDER; cell.alignment = LEFT if c_idx == 1 else CENTER
                    row_num += 1; 
                    for k in num_keys: v[k] += t[k]
                v_rt = [f"{vert} Total"] + (["—"] if mode == "caller" else []) + [v["pool"], v["collected"], v["balance"], int(v["leads"]), int(v["leads_48"]), v["bal_48hr"], _pct(v["bal_48hr"], v["balance"]), v["prev_bal"], int(v["prev_leads"]), v["grand_bal"], int(v["grand_leads"])]
                for c_idx, v_ in enumerate(v_rt, 1): cell = ws.cell(row_num, c_idx, v_); cell.fill = VERT_FILL; cell.font = BOLD_WHITE; cell.border = BORDER; cell.alignment = LEFT if c_idx == 1 else CENTER
                row_num += 1; 
                for k in num_keys: g[k] += v[k]
            g_rt = ["Grand Total"] + (["—"] if mode == "caller" else []) + [g["pool"], g["collected"], g["balance"], int(g["leads"]), int(g["leads_48"]), g["bal_48hr"], _pct(g["bal_48hr"], g["balance"]), g["prev_bal"], int(g["prev_leads"]), g["grand_bal"], int(g["grand_leads"])]
            for c_idx, v_ in enumerate(g_rt, 1): cell = ws.cell(row_num, c_idx, v_); cell.fill = GRAND_FILL; cell.font = BOLD_WHITE; cell.border = BORDER; cell.alignment = LEFT if c_idx == 1 else CENTER
            cw = [28] + ([18] if mode == "caller" else []) + [16, 16, 16, 8, 10, 16, 14, 16, 10, 16, 10]
            for i, w in enumerate(cw, 1): ws.column_dimensions[get_column_letter(i)].width = w
        ws1 = wb.active; ws1.title = "Teamwise Summary"; ws1.freeze_panes = "A3"; write_pending_sheet(ws1, "team")
        ws2 = wb.create_sheet("Callerwise Summary"); ws2.freeze_panes = "A3"; write_pending_sheet(ws2, "caller")
        buf = io.BytesIO(); wb.save(buf); return buf.getvalue()

    def build_pending_leads_excel(pend_curr, pend_prev, meta_map_pending, curr_label, prev_label):
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        HDR_FILL = PatternFill("solid", start_color="064e3b", end_color="064e3b")
        HDR_FONT = Font(bold=True, color="FFFFFF", name="Arial", size=9)
        DATA_FONT= Font(name="Arial", size=9)
        BORDER   = Border(left=Side(style='thin', color='D1FAE5'), right=Side(style='thin', color='D1FAE5'), top=Side(style='thin', color='D1FAE5'), bottom=Side(style='thin', color='D1FAE5'))
        CENTER   = Alignment(horizontal='center', vertical='center', wrap_text=True)
        LEFT     = Alignment(horizontal='left',   vertical='center', wrap_text=True)
        COLS = ["DATE", "NAME", "CONTACT NO", "EMAIL ID", "COURSE", "CALLER NAME", "TEAM NAME", "VERTICAL", "COURSE PRICE (₹)", "REVENUE COLLECTED (₹)", "BALANCE (₹)"]
        meta_lkp = {str(row.get('merge_key','')).strip().lower(): {'Caller Name': row.get('Caller Name','—'), 'Team Name': row.get('Team Name','—'), 'Vertical': row.get('Vertical','—')} for _, row in meta_map_pending.iterrows()}
        def write_leads_sheet(ws, df, label):
            ws.row_dimensions[1].height = 28
            for c_idx, h in enumerate(COLS, 1): cell = ws.cell(1, c_idx, h); cell.fill = HDR_FILL; cell.font = HDR_FONT; cell.alignment = CENTER; cell.border = BORDER
            if df.empty: ws.cell(2, 1, f"No pending leads found for {label}"); return
            df = df.copy(); df['_mk'] = df['Caller_name'].astype(str).str.strip().str.lower()
            for r_idx, (_, r) in enumerate(df.sort_values('Date').iterrows(), 2):
                v_ = [str(r.get('Date','')), str(r.get('Name','')), str(r.get('Contact_No','')), str(r.get('Email_Id','')), str(r.get('Course','')), meta_lkp.get(r['_mk'],{}).get('Caller Name', r['Caller_name']), meta_lkp.get(r['_mk'],{}).get('Team Name','—'), meta_lkp.get(r['_mk'],{}).get('Vertical','—'), float(r.get('Course_Price',0)), float(r.get('Fee_paid',0)), float(r.get('balance',0))]
                for c_idx, val in enumerate(v_, 1): cell = ws.cell(r_idx, c_idx, val); cell.font = DATA_FONT; cell.border = BORDER; cell.alignment = LEFT if c_idx <= 8 else CENTER
        wb = Workbook(); write_leads_sheet(wb.active, pend_curr, curr_label); write_leads_sheet(wb.create_sheet("Prev Month"), pend_prev, prev_label)
        buf = io.BytesIO(); wb.save(buf); return buf.getvalue()

    def resolve_target(row):
        return float(row.get('Course_Price', 0) or 0)

    def compute_summary_metrics(df):
        m = {k:0 for k in ['total_rev','calling_rev','bootcamp_direct_rev','collection_rev','community_rev', 'direct_rev','dna_rev']}
        if df.empty: return m
        df_fp = df[df['Fee_paid'] > 0].copy()
        m['total_rev'] = df_fp['Fee_paid'].sum()
        enr_l = df_fp['Enrollment'].astype(str).str.strip().str.lower()
        src_l = df_fp['Source'].astype(str).str.strip().str.lower()
        cal_l = df_fp['Caller_name'].astype(str).str.strip().str.lower()
        is_funnel = enr_l.isin(['new enrollment', 'new enrollment - balance payment'])
        is_boot_coll = enr_l == 'bootcamp collections - balance payments'
        is_comm_coll = enr_l == 'community collections - balance payments'
        m['calling_rev'] = df_fp[is_funnel & ~cal_l.isin(['direct','bootcamp-direct'])]['Fee_paid'].sum()
        m['bootcamp_direct_rev'] = df_fp[(enr_l == 'new enrollment') & (cal_l == 'bootcamp-direct')]['Fee_paid'].sum()
        m['collection_rev'] = df_fp[is_boot_coll]['Fee_paid'].sum()
        m['community_rev'] = df_fp[is_comm_coll | (src_l.str.contains('community', na=False) & ( (enr_l=='other revenue') | ((enr_l=='new enrollment') & (cal_l=='direct')) ))]['Fee_paid'].sum()
        m['direct_rev'] = df_fp[(cal_l == 'direct') & ~src_l.str.contains('community', na=False) & enr_l.isin(['other revenue','new enrollment','new enrollment - balance payment'])]['Fee_paid'].sum()
        m['dna_rev'] = df_fp[df_fp['Enrollment'].astype(str).str.strip() == '']['Fee_paid'].sum()
        return m

    def compute_enrollment_metrics(df):
        m = {k:0 for k in ['total_enr','caller_enr','direct_enr','bootcamp_enr','community_enr']}
        if df.empty: return m
        df_new = df[df['Enrollment'].astype(str).str.strip().str.lower() == 'new enrollment'].copy()
        m['total_enr'] = len(df_new)
        cal_l = df_new['Caller_name'].astype(str).str.strip().str.lower()
        src_l = df_new['Source'].astype(str).str.strip().str.lower()
        m['caller_enr'] = len(df_new[~cal_l.isin(['direct','bootcamp-direct'])])
        m['direct_enr'] = len(df_new[(cal_l == 'direct') & ~src_l.str.contains('community', na=False)])
        m['bootcamp_enr'] = len(df_new[cal_l == 'bootcamp-direct'])
        m['community_enr'] = len(df_new[(cal_l == 'direct') & src_l.str.contains('community', na=False)])
        return m

    def classify_and_process(df, meta_all, s_d, e_d):
        m_dedup = meta_all.sort_values('Month', ascending=False).drop_duplicates('merge_key', keep='first')
        merged = pd.merge(df, m_dedup[['merge_key','Target','Designation']], on='merge_key', how='left')
        merged['Designation'] = merged['Designation'].fillna('Academic Counselor')
        merged['raw_target']  = merged['Target'].fillna(0).astype(float)
        
        # Split into agent types based on calling vs collection revenue
        enr_l = merged['Enrollment'].astype(str).str.strip().str.lower()
        merged['is_calling_enr'] = enr_l.isin(['new enrollment','new enrollment - balance payment'])
        merged['is_comm_coll']   = enr_l == 'community collections - balance payments'
        merged['is_boot_coll']   = enr_l == 'bootcamp collections - balance payments'
        
        agg = merged.groupby(['Caller_name','Team Name','Vertical','Designation','raw_target']).agg(
            ENR_CNT        = ('is_calling_enr', lambda x: x[enr_l.loc[x.index] == 'new enrollment'].sum()),
            ENR_REV        = ('Fee_paid', lambda x: x[merged.loc[x.index, 'is_calling_enr'] & (enr_l.loc[x.index] == 'new enrollment')].sum()),
            BAL_REV        = ('Fee_paid', lambda x: x[merged.loc[x.index, 'is_calling_enr'] & (enr_l.loc[x.index] == 'new enrollment - balance payment')].sum()),
            COMM_COLL      = ('Fee_paid', lambda x: x[merged.loc[x.index, 'is_comm_coll']].sum()),
            BOOT_COLL      = ('Fee_paid', lambda x: x[merged.loc[x.index, 'is_boot_coll']].sum())
        ).reset_index()
        
        agg['CALLING REVENUE']    = agg['ENROLLMENT REV'] + agg['BAL_REV']
        agg['COLLECTION REVENUE'] = agg['COMMUNITY COLLECTION'] + agg['BOOTCAMP COLLECTION']
        agg['TOTAL REVENUE']      = agg['CALLING REVENUE'] + agg['COLLECTION REVENUE']
        
        # Calculate till-day target
        days_passed = sum(1 for d in pd.date_range(s_d, e_d) if d.weekday() < 5)
        # Assuming 20 working days per month for till-day
        agg['TILL DAY TARGET (₹)'] = agg['raw_target'] * min(1.0, days_passed/20.0)
        
        calling = agg[(agg['CALLING REVENUE'] > 0) & (agg['COLLECTION REVENUE'] == 0)].copy()
        coll    = agg[(agg['COLLECTION REVENUE'] > 0) & (agg['CALLING REVENUE'] == 0)].copy()
        both    = agg[(agg['CALLING REVENUE'] > 0) & (agg['COLLECTION REVENUE'] > 0)].copy()
        return calling, coll, both

    def build_combined_agg(curr, prev, meta, df_rev=None):
        if df_rev is not None and not df_rev.empty:
            ni = df_rev[df_rev['is_new']].copy()
            e2c = ni.drop_duplicates('Email_Id_norm').set_index('Email_Id_norm')['Caller_name'].to_dict()
            p2c = ni.drop_duplicates('Contact_No_norm').set_index('Contact_No_norm')['Caller_name'].to_dict()
            def res(r):
                e, p = r.get('Email_Id_norm',''), r.get('Contact_No_norm','')
                return e2c.get(e, p2c.get(p, r['Caller_name']))
            curr['Caller_name'] = curr.apply(res, axis=1) if not curr.empty else curr['Caller_name']
            prev['Caller_name'] = prev.apply(res, axis=1) if not prev.empty else prev['Caller_name']
        c_agg = _raw_caller_agg(curr); p_agg = _raw_caller_agg(prev)
        if c_agg.empty and p_agg.empty: return pd.DataFrame()
        p_slim = p_agg[['Caller_name','balance','leads']].rename(columns={'balance':'prev_bal','leads':'prev_leads'}) if not p_agg.empty else pd.DataFrame(columns=['Caller_name','prev_bal','prev_leads'])
        if c_agg.empty: combined = p_slim.assign(pool=0, collected=0, balance=0, leads=0, leads_48=0, bal_48hr=0)
        elif p_slim.empty: combined = c_agg.assign(prev_bal=0, prev_leads=0)
        else: combined = c_agg.merge(p_slim, on='Caller_name', how='outer').fillna(0)
        combined['grand_bal'] = combined['balance'] + combined['prev_bal']
        combined['grand_leads'] = combined['leads'] + combined['prev_leads']
        m_dedup = meta[['merge_key','Caller Name', 'Team Name', 'Vertical']].drop_duplicates('merge_key')
        combined['mk'] = combined['Caller_name'].str.lower()
        combined = combined.merge(m_dedup.rename(columns={'merge_key':'mk'}), on='mk', how='left')
        combined['Team Name'] = combined['Team Name'].fillna('Others'); combined['Vertical'] = combined['Vertical'].fillna('Others')
        return combined

    def attribute_drops_to_callers(drop_df, df_rev, meta, c_s, c_e, p_s, p_e, cl, pl):
        if drop_df.empty or df_rev.empty: return pd.DataFrame()
        ni = df_rev[df_rev['is_new']].copy()
        e2c = ni.drop_duplicates('Email_Id_norm').set_index('Email_Id_norm')['Caller_name'].to_dict()
        p2c = ni.drop_duplicates('Contact_No_norm').set_index('Contact_No_norm')['Caller_name'].to_dict()
        def res(r): return e2c.get(r['drop_email'], p2c.get(r['drop_phone'], 'Unknown'))
        df = drop_df.copy(); df['attributed_caller'] = df.apply(res, axis=1)
        df['drop_d'] = pd.to_datetime(df['drop_date']).dt.date
        curr = df[(df['drop_d'] >= c_s) & (df['drop_d'] <= c_e)].groupby('attributed_caller').size().rename('curr_drops')
        prev = df[(df['drop_d'] >= p_s) & (df['drop_d'] <= p_e)].groupby('attributed_caller').size().rename('prev_drops')
        combined = pd.DataFrame({'curr_drops':curr, 'prev_drops':prev}).fillna(0).reset_index().rename(columns={'index':'Caller_name'})
        combined['total_drops'] = combined['curr_drops'] + combined['prev_drops']
        combined['mk'] = combined['Caller_name'].str.lower()
        m_dedup = meta[['merge_key','Team Name','Vertical']].drop_duplicates('merge_key')
        combined = combined.merge(m_dedup.rename(columns={'merge_key':'mk'}), on='mk', how='left')
        combined['Team Name'] = combined['Team Name'].fillna('Others'); combined['Vertical'] = combined['Vertical'].fillna('Others')
        return combined

    def section_header(label):
        st.markdown(f"<div class='section-header'><div class='section-header-line'></div><span class='section-title'>{label}</span><div class='section-header-line' style='background:linear-gradient(90deg,transparent,#10B981)'></div></div>", unsafe_allow_html=True)

    min_d, max_d = get_available_dates()
    month_options = {cur.strftime("%B %Y"): cur for cur in [date(min_d.year, min_d.month, 1) + timedelta(days=32*i) for i in range(24)] if cur <= date(max_d.year, max_d.month, 1)}
    
    selected_month_label = st.sidebar.selectbox("🗓️ Month", options=list(reversed(list(month_options.keys()))), key="rev_month")
    selected_month_date = month_options[selected_month_label]
    s = pd.Timestamp(selected_month_date).date()
    month_end = (s.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    selected_dates = st.sidebar.date_input("📅 Date Range", value=(max(s, min_d), min(month_end, max_d)), min_value=min_d, max_value=max_d, format="DD-MM-YYYY", key="rev_dates")
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2: s_d, e_d = selected_dates
    else: s_d = e_d = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

    teams, verticals, df_meta = get_metadata()
    sel_v = st.sidebar.multiselect("👑 Filter by Vertical", options=verticals, key="rev_v")
    sel_t = st.sidebar.multiselect("👥 Filter by Team", options=teams, key="rev_t")
    search = st.sidebar.text_input("👤 Search Caller Name", key="rev_search")
    gen_report = st.sidebar.button("💰 Generate Revenue Report", key="rev_gen")

    st.markdown(f"<div class='rv-header'><div style='display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:.75rem;'><div><div class='rv-title'>💰 REVENUE METRICS</div><div class='rv-subtitle'>REVENUE PERIOD&nbsp;·&nbsp; {s_d.strftime('%d-%m-%Y')} to {e_d.strftime('%d-%m-%Y')}</div></div><div style='display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-top:.25rem;'><span class='rv-badge'><span class='rv-pulse'></span>LIVE REVENUE DATA</span><span class='rv-badge'>🕐 UPDATED AT: {get_last_update()}</span></div></div></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["💰 Revenue Dashboard", "🧠 Insights & Leaderboard", "📊 Callerwise Pending Revenue"])

    with tab1:
        if gen_report:
            df_raw = fetch_revenue_data(s_d, e_d)
            if df_raw.empty: st.warning("No records found.")
            else:
                df = pd.merge(df_raw, df_meta[['merge_key','Caller Name','Team Name','Vertical']].drop_duplicates('merge_key'), on='merge_key', how='left')
                df['Caller_name'] = df['Caller Name'].fillna(df['Caller_name'])
                if sel_t: df = df[df['Team Name'].isin(sel_t)]
                if sel_v: df = df[df['Vertical'].isin(sel_v)]
                if search: df = df[df['Caller_name'].str.contains(search, case=False, na=False)]
                
                calling_df, coll_df, both_df = classify_and_process(df, df_meta, s_d, e_d)
                m = compute_summary_metrics(df)
                
                section_header("🏆 TOP 3 HIGHLIGHTS")
                top_cols = st.columns(3)
                for i, (title, d, col, val) in enumerate([("🥇 TOP REVENUE — CALLER", calling_df, 'CALLING REVENUE', 'accent-primary'), ("🎓 MOST ENROLLMENTS", pd.concat([d for d in [calling_df, coll_df, both_df] if not d.empty]), 'ENROLLMENTS', 'accent-primary'), ("🥇 TOP REVENUE — COLLECTION", coll_df, 'COLLECTION REVENUE', 'accent-primary')]):
                    with top_cols[i]:
                        if not d.empty:
                            top = d.sort_values(col, ascending=False).iloc[0]
                            st.markdown(f"<div class='metric-card' style='border-top:3px solid var(--{val});'><div class='metric-label'>{title}</div><div class='metric-value'>{top['CALLER NAME']}</div><div class='metric-delta'>{fmt_inr(top[col]) if 'REV' in col else top[col]} {col.title()}</div></div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div class='metric-card'><div class='metric-label'>{title}</div><div class='metric-value'>No Data</div></div>", unsafe_allow_html=True)

                section_header("💵 REVENUE SUMMARY")
                k_cols = st.columns(4)
                k_data = [("Total Revenue", m['total_rev'], "💰"), ("Calling Revenue", m['calling_rev'], "📞"), ("Collection Revenue", m['collection_rev'], "🏦"), ("Community Revenue", m['community_rev'], "🌐")]
                for i, (l, v, ico) in enumerate(k_data):
                    with k_cols[i % 4]: st.markdown(f"<div class='metric-card'><div class='metric-label'>{ico} {l}</div><div class='metric-value'>{fmt_inr(v)}</div></div>", unsafe_allow_html=True)

                st.divider()
                section_header("📞 CALLER REVENUE PERFORMANCE")
                render_perf_table(calling_df, ['DESIGNATION', 'CALLER NAME', 'TEAM', 'VERTICAL', 'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)', 'ENROLLMENTS', 'ENROLLMENT REV', 'BALANCE REV', 'CALLING REVENUE', 'ACHIEVEMENT %'], {'CALLING REVENUE': fmt_inr(calling_df['raw_calling_rev'].sum())} if not calling_df.empty else {}, 'raw_calling_rev', 'calling')
                
                section_header("🏦 COLLECTION REVENUE PERFORMANCE")
                render_perf_table(coll_df, ['DESIGNATION', 'CALLER NAME', 'TEAM', 'VERTICAL', 'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)', 'ENROLLMENTS', 'COMMUNITY COLLECTION', 'BOOTCAMP COLLECTION', 'COLLECTION REVENUE', 'ACHIEVEMENT %'], {'COLLECTION REVENUE': fmt_inr(coll_df['raw_collection_rev'].sum())} if not coll_df.empty else {}, 'raw_collection_rev', 'coll')

    with tab2:
        if gen_report:
            section_header("🧠 REVENUE INSIGHTS")
            insights = compute_revenue_insights(df, calling_df, coll_df, both_df, s_d, e_d)
            i_cols = st.columns(2)
            for i, ins in enumerate(insights):
                with i_cols[i % 2]: st.markdown(f"<div class='insight-card {ins['type']}'><div style='display:flex;align-items:center;gap:.4rem;'><span class='insight-icon'>{ins['icon']}</span><span class='insight-title'>{ins['title']}</span></div><div class='insight-body'>{ins['body']}</div></div>", unsafe_allow_html=True)

    with tab3:
        c_s, c_e, p_s, p_e = pending_months()
        cl, pl = c_s.strftime("%B %Y"), p_s.strftime("%B %Y")
        drop_df = load_drop_leads(); excl_e = set(drop_df['drop_email'].dropna()); excl_p = set(drop_df['drop_phone'].dropna())
        df_b = fetch_both_months_rev(p_s, c_e)
        if not df_b.empty:
            pend_c = pending_leads_for_month(df_b[df_b['Date'] >= c_s], excl_e, excl_p, df_b)
            pend_p = pending_leads_for_month(df_b[df_b['Date'] <= p_e], excl_e, excl_p, df_b)
            comb = build_combined_agg(pend_c, pend_p, df_meta, df_b)
            if not comb.empty:
                st.markdown(render_html_pending_table(comb, 'team', cl, pl, f"TEAMWISE PENDING REVENUE {pl.upper()} + {cl.upper()}"), unsafe_allow_html=True)
                st.markdown(render_html_pending_table(comb, 'caller', cl, pl, f"CALLERWISE PENDING REVENUE {pl.upper()} + {cl.upper()}"), unsafe_allow_html=True)
                st.download_button("📥 Download Pending Revenue Excel", data=build_pending_excel(comb, pend_c, pend_p, df_meta, cl, pl), file_name="Pending_Revenue.xlsx", key="dl_p_rev")

# --- ROUTER ---
with st.sidebar:
    st.markdown("### 🧭 Navigation")
    choice = st.selectbox("Select Page", ["Home", "Calling Metrics", "Revenue Metrics"], index=["Home", "Calling Metrics", "Revenue Metrics"].index(st.session_state.selection))
    st.session_state.selection = choice

if st.session_state.selection == "Home":
    run_homepage()
elif st.session_state.selection == "Calling Metrics":
    run_calling()
elif st.session_state.selection == "Revenue Metrics":
    run_revenue()
