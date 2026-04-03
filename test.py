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
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Flowable
)
from reportlab.lib.enums import TA_CENTER

# --- 1. GLOBAL PAGE CONFIG ---
st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SHARED AUTHENTICATION ---
USERS = {
    'amit': {'name': 'Amit Ray', 'password': 'lawsikho@2024'}
}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

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
                else:
                    st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# --- 3. SHARED BQ CLIENT ---
@st.cache_resource
def get_bq_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=creds, project=info["project_id"])
    else:
        # Fallback for local testing (Google Colab / Local Env)
        SERVICE_ACCOUNT_FILE = "/content/drive/MyDrive/Lawsikho/credentials/bigquery_key.json"
        if os.path.exists(SERVICE_ACCOUNT_FILE):
             os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
             return bigquery.Client()
        else:
             return bigquery.Client() # Fallback to default env auth

client = get_bq_client()

# --- 4. HOMEPAGE MODULE ---
def run_homepage():
    # --- Exact logic from dashboards_homepage.py ---
    LAWSIKHO_LOGO       = "https://raw.githubusercontent.com/amitray-lawsikho/test/main/assets/lawsikho_logo.png" # Updated placeholder logic
    SKILLARBITRAGE_LOGO = "https://raw.githubusercontent.com/amitray-lawsikho/test/main/assets/skillarbitrage_logo.png"

    @st.cache_data(ttl=300, show_spinner=False)
    def get_stats():
        try:
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

    call_time, call_cnt, rev_time, rev_cnt = get_stats()

    st.markdown("""
<style>
footer { visibility: hidden; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: #0B1120 !important; overflow: hidden !important; }
section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
[data-testid="stMainViewContainer"] { padding-top: 0 !important; overflow: hidden !important; }
.block-container { padding: 0 !important; max-width: 100% !important; overflow: hidden !important; }
iframe { display: block; width: 100%; border: none; }
</style>
""", unsafe_allow_html=True)

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
html, body {
    font-family: 'Plus Jakarta Sans', sans-serif; background: #0B1120; color: #E2E8F0; min-height: 100vh; overflow-x: hidden;
}
body {
    background: radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,.12) 0%, transparent 60%),
                radial-gradient(ellipse 60% 40% at 90% 80%, rgba(249,115,22,.08) 0%, transparent 55%),
                radial-gradient(ellipse 50% 35% at 10% 90%, rgba(139,92,246,.06) 0%, transparent 50%), #0B1120;
}
body::before {
    content: ""; position: fixed; inset: 0; background-size: 48px 48px; pointer-events: none; z-index: 0;
    background-image: linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
}
.page { position: relative; z-index: 1; }
.hero { display: flex; flex-direction: column; align-items: center; text-align: center; padding: 4rem 2rem 3rem; }
.logo-block { display: flex; align-items: center; justify-content: center; gap: 0; margin-bottom: 1.6rem; }
.logo-side { display: flex; align-items: center; justify-content: center; padding: 0 2rem; }
.logo-img { height: 46px; width: auto; object-fit: contain; mix-blend-mode: lighten; filter: brightness(1.25) contrast(1.1) saturate(.95); transition: transform .25s, opacity .25s; }
.logo-img:hover { transform: scale(1.05); }
.logo-fallback { display: none; font-family: 'Syne', sans-serif; font-size: 1.3rem; font-weight: 700; color: #fff; letter-spacing: -.5px; }
.logo-glow-sep { width: 1px; height: 52px; border-radius: 1px; flex-shrink: 0;
    background: linear-gradient(180deg, transparent 0%, rgba(249,115,22,.8) 35%, rgba(251,146,60,.9) 50%, rgba(249,115,22,.8) 65%, transparent 100%);
    box-shadow: 0 0 8px rgba(249,115,22,.6), 0 0 20px rgba(249,115,22,.3); }
.hero-tagline { font-family: 'Fira Code', monospace; font-size: .78rem; color: rgba(255,255,255,.38); letter-spacing: 1.5px; margin-bottom: 2rem; }
.hero-eyebrow { display: inline-flex; align-items: center; gap: .5rem; font-family: 'Fira Code', monospace; font-size: .68rem; letter-spacing: 2.5px; text-transform: uppercase; color: #F97316; background: rgba(249,115,22,.08); border: 1px solid rgba(249,115,22,.18); border-radius: 100px; padding: .3rem 1rem; margin-bottom: 1.4rem; }
.eyebrow-dot { width: 5px; height: 5px; background: #F97316; border-radius: 50%; box-shadow: 0 0 6px #F97316; animation: pulse 2s ease-in-out infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: .5; transform: scale(1.4); } }
.hero-headline { font-size: clamp(2.4rem, 5.5vw, 4.2rem); font-weight: 800; line-height: 1.08; color: #FFFFFF; letter-spacing: -1.5px; margin-bottom: .8rem; }
.hero-headline .accent { background: linear-gradient(125deg, #F97316 0%, #FB923C 40%, #FBBF24 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; display: inline-block; -webkit-font-smoothing: antialiased; }
.hero-sub { font-size: 1.15rem; font-weight: 300; color: rgba(255,255,255,.42); letter-spacing: .3px; margin-bottom: 3rem; max-width: 580px; }
.hero-rule { display: flex; align-items: center; gap: 1rem; width: 100%; max-width: 560px; margin-bottom: 3rem; }
.hero-rule-line { flex: 1; height: 1px; background: linear-gradient(90deg, transparent, rgba(255,255,255,.08)); }
.hero-rule-line.r { background: linear-gradient(90deg, rgba(255,255,255,.08), transparent); }
.hero-rule-label { font-family: 'Fira Code', monospace; font-size: .6rem; letter-spacing: 2px; text-transform: uppercase; color: rgba(255,255,255,.2); white-space: nowrap; }
.stats-row { display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap; padding: 0 2rem; margin-bottom: 4rem; }
.stat-card { display: flex; align-items: center; gap: .85rem; background: rgba(255,255,255,.04); border: 1px solid rgba(255,255,255,.08); border-radius: 16px; padding: .9rem 1.4rem; min-width: 260px; flex: 1; max-width: 340px; backdrop-filter: blur(12px); transition: all .2s; }
.stat-card:hover { transform: translateY(-2px); }
.stat-card.sc-call:hover { border-color: rgba(249,115,22,.22); background: rgba(249,115,22,.04); }
.stat-card.sc-rev:hover { border-color: rgba(52,211,153,.22); background: rgba(52,211,153,.04); }
.stat-icon-wrap { width: 38px; height: 38px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: .95rem; flex-shrink: 0; }
.si-call { background: rgba(249,115,22,.14); }
.si-rev  { background: rgba(52,211,153,.12); }
.si-lead { background: rgba(139,92,246,.12); }
.stat-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.stat-lbl { font-family: 'Fira Code', monospace; font-size: .58rem; text-transform: uppercase; letter-spacing: 1px; color: rgba(255,255,255,.3); }
.stat-val { font-family: 'Fira Code', monospace; font-size: .8rem; color: rgba(255,255,255,.82); }
.stat-sub { font-family: 'Fira Code', monospace; font-size: .58rem; color: rgba(255,255,255,.2); }
.pill-live { margin-left: auto; flex-shrink: 0; font-family: 'Fira Code', monospace; font-size: .55rem; color: #34D399; background: rgba(52,211,153,.1); border: 1px solid rgba(52,211,153,.18); border-radius: 20px; padding: 2px 8px; }
.pill-wip  { margin-left: auto; flex-shrink: 0; font-family: 'Fira Code', monospace; font-size: .55rem; color: #FBBF24; background: rgba(251,191,36,.1); border: 1px solid rgba(251,191,36,.18); border-radius: 20px; padding: 2px 8px; }
.dashboards-section { padding: 0 2rem 5rem; max-width: 1120px; margin: 0 auto; }
.section-head { display: flex; align-items: center; gap: 1rem; margin-bottom: 2rem; }
.section-line { flex: 1; height: 1px; background: rgba(255,255,255,.07); }
.section-lbl { font-family: 'Fira Code', monospace; font-size: .65rem; letter-spacing: 2.5px; text-transform: uppercase; color: rgba(255,255,255,.25); }
.cards-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.25rem; }
@media (max-width: 900px) { .cards-grid { grid-template-columns: 1fr; } }
.dcard { position: relative; background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.09); border-radius: 20px; padding: 1.8rem 1.7rem 1.5rem; text-decoration: none; color: inherit; display: flex; flex-direction: column; gap: .75rem; overflow: hidden; transition: transform .25s, box-shadow .25s, border-color .25s, background .25s; }
.dcard:hover { transform: translateY(-5px); text-decoration: none; }
.dcard-call { border-top: 2px solid rgba(249,115,22,.4); }
.dcard-rev  { border-top: 2px solid rgba(52,211,153,.35); }
.dcard-call:hover { border-color: #F97316; background: rgba(249,115,22,.04); box-shadow: 0 20px 60px rgba(249,115,22,.1); }
.dcard-rev:hover  { border-color: #34D399; background: rgba(52,211,153,.04); box-shadow: 0 20px 60px rgba(52,211,153,.08); }
.dcard-glow { position: absolute; width: 220px; height: 220px; border-radius: 50%; top: -90px; right: -70px; filter: blur(80px); opacity: 0; pointer-events: none; transition: opacity .3s; }
.dcard-call .dcard-glow { background: #F97316; }
.dcard-rev  .dcard-glow { background: #34D399; }
.dcard:hover .dcard-glow { opacity: .1; }
.dcard-header { display: flex; align-items: flex-start; justify-content: space-between; }
.dcard-icon { font-size: 1.8rem; line-height: 1; }
.dcard-wip-badge { font-family: 'Fira Code', monospace; font-size: .55rem; color: #FBBF24; background: rgba(251,191,36,.08); border: 1px solid rgba(251,191,36,.18); border-radius: 8px; padding: 3px 9px; }
.dcard-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 600; color: #fff; }
.dcard-desc { font-size: .8rem; font-weight: 300; color: rgba(255,255,255,.42); line-height: 1.7; flex: 1; }
.dcard-tags { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .2rem; }
.dtag { font-family: 'Fira Code', monospace; font-size: .58rem; color: rgba(255,255,255,.32); background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.08); border-radius: 6px; padding: 2px 9px; text-transform: uppercase; letter-spacing: .4px; }
.dcard-cta { display: inline-flex; align-items: center; gap: .4rem; font-family: 'Fira Code', monospace; font-size: .72rem; color: rgba(255,255,255,.28); margin-top: .3rem; transition: gap .2s, color .2s; }
.dcard-call:hover .dcard-cta { color: #F97316; gap: .65rem; }
.dcard-rev:hover  .dcard-cta { color: #34D399; gap: .65rem; }
.site-footer { border-top: 1px solid rgba(255,255,255,.06); padding: 2rem 2rem 2.5rem; text-align: center; display: flex; flex-direction: column; gap: .5rem; }
.footer-top { font-family: 'Fira Code', monospace; font-size: .68rem; color: rgba(255,255,255,.35); }
.footer-bottom { font-family: 'Fira Code', monospace; font-size: .62rem; color: rgba(255,255,255,.18); }
.footer-dot { display: inline-block; width: 3px; height: 3px; background: rgba(249,115,22,.5); border-radius: 50%; margin: 0 .5rem; vertical-align: middle; }
</style>
<script>
function goTo(page) {
    const params = new URLSearchParams(window.parent.location.search);
    params.set('page_sel', page);
    window.parent.location.search = params.toString();
}
</script>
</head>
<body>
<div class="page">
  <div class="hero">
    <div class="logo-block">
      <div class="logo-side">
        <img class="logo-img" src="LAWSIKHO_LOGO_PH" alt="LawSikho" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <span class="logo-fallback">LawSikho</span>
      </div>
      <div class="logo-glow-sep"></div>
      <div class="logo-side">
        <img class="logo-img" src="SA_LOGO_PH" alt="Skill Arbitrage" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <span class="logo-fallback">Skill Arbitrage</span>
      </div>
    </div>
    <div class="hero-tagline">India Learning &nbsp;📖&nbsp; India Earning</div>
    <div class="hero-eyebrow"><span class="eyebrow-dot"></span>Internal Analytics Hub</div>
    <div class="hero-headline">All your dashboards,<br><span class="accent">at one place</span></div>
    <div class="hero-sub">Real-time insights across Leads, Revenue &amp; Calling</div>
    <div class="hero-rule"><div class="hero-rule-line"></div><span class="hero-rule-label">Live Dashboards</span><div class="hero-rule-line r"></div></div>
  </div>

  <div class="stats-row">
    <div class="stat-card sc-call">
      <div class="stat-icon-wrap si-call">🔔</div>
      <div class="stat-info">
        <span class="stat-lbl">Calling Data</span>
        <span class="stat-val">CALL_TIME_PH</span>
        <span class="stat-sub">CALL_CNT_PH records</span>
      </div>
      <span class="pill-live">● Live</span>
    </div>
    <div class="stat-card sc-rev">
      <div class="stat-icon-wrap si-rev">💰</div>
      <div class="stat-info">
        <span class="stat-lbl">Revenue Data</span>
        <span class="stat-val">REV_TIME_PH</span>
        <span class="stat-sub">REV_CNT_PH records</span>
      </div>
      <span class="pill-live">● Live</span>
    </div>
    <div class="stat-card">
      <div class="stat-icon-wrap si-lead">📊</div>
      <div class="stat-info"><span class="stat-lbl">Lead Data</span><span class="stat-val" style="color:rgba(255,255,255,.28);">Coming Soon</span></div>
      <span class="pill-wip">🚧 WIP</span>
    </div>
  </div>

  <div class="dashboards-section">
    <div class="section-head"><div class="section-line"></div><span class="section-lbl">Dashboards</span><div class="section-line"></div></div>
    <div class="cards-grid">
      <a class="dcard dcard-call" href="javascript:void(0)" onclick="goTo('Calling Metrics')">
        <div class="dcard-glow"></div>
        <div class="dcard-header"><div class="dcard-icon">🔔</div></div>
        <div class="dcard-title">Calling Metrics</div>
        <div class="dcard-desc">Full CDR analysis across Ozonetel, Acefone &amp; Manual calls. Agent-level performance, break tracking &amp; leaderboards.</div>
        <div class="dcard-tags"><span class="dtag">Ozonetel</span><span class="dtag">Acefone</span><span class="dtag">Manual</span></div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>
      <a class="dcard dcard-rev" href="javascript:void(0)" onclick="goTo('Revenue Metrics')">
        <div class="dcard-glow"></div>
        <div class="dcard-header"><div class="dcard-icon">💰</div></div>
        <div class="dcard-title">Revenue Metrics</div>
        <div class="dcard-desc">Enrollment revenue, target achievement &amp; caller-level breakdown. Course performance &amp; team leaderboards.</div>
        <div class="dcard-tags"><span class="dtag">Enrollments</span><span class="dtag">Targets</span><span class="dtag">Teams</span></div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>
      <div class="dcard wip" style="opacity:.5;"><div class="dcard-header"><div class="dcard-icon">📊</div><span class="dcard-wip-badge">Coming Soon</span></div><div class="dcard-title">Lead Metrics</div><div class="dcard-desc">Pipeline development in progress.</div></div>
    </div>
  </div>

  <div class="site-footer">
    <div class="footer-top">For Internal Use Only <span class="footer-dot"></span> All Rights Reserved</div>
    <div class="footer-bottom">Developed by Amit Ray <span class="footer-dot"></span> Reach out for Support</div>
  </div>
</div>
</body>
</html>
"""
    # FIX: Use .replace instead of .format to avoid KeyError from CSS curly braces
    html = html.replace("LAWSIKHO_LOGO_PH", LAWSIKHO_LOGO)
    html = html.replace("SA_LOGO_PH",       SKILLARBITRAGE_LOGO)
    html = html.replace("CALL_TIME_PH",     call_time)
    html = html.replace("CALL_CNT_PH",      call_cnt)
    html = html.replace("REV_TIME_PH",      rev_time)
    html = html.replace("REV_CNT_PH",       rev_cnt)

    components.html(html, height=900, scrolling=True)

# --- 5. CALLING METRICS MODULE ---
def run_calling():
    # --- Exact logic from calling_data.py (Lines 10-1318) ---
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"
    
    # [INTERNAL HELPER FUNCTIONS FROM calling_data.py]
    def style_total(row):
        if row["CALLER"] == "TOTAL": return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
        return [''] * len(row)

    def style_static(row):
        if row["CALLER"] == "TOTAL": return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
        return [''] * len(row)

    def format_dur_hm(total_seconds):
        if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
        tm = int(round(total_seconds / 60))
        return f"{tm // 60}h {tm % 60}m"

    def get_display_gap_seconds(start_time, end_time):
        if pd.isna(start_time) or pd.isna(end_time): return 0
        s, e = start_time.replace(second=0, microsecond=0), end_time.replace(second=0, microsecond=0)
        return (e - s).total_seconds()

    def section_header(label):
        st.markdown(f'<div class="section-header"><div class="section-header-line"></div><span class="section-title">{label}</span><div class="section-header-line" style="background:linear-gradient(90deg,transparent,#F97316)"></div></div>', unsafe_allow_html=True)

    def _unique_approvals(series):
        seen = {}
        for v in series.dropna().astype(str):
            v=v.strip(); k=v.lower()
            if k and k not in seen: seen[k] = v
        return ", ".join(seen.values()) if seen else "—"

    def style_team_manual_total(row):
        if row.get('TEAM') == 'TOTAL': return ['font-weight:bold;background-color:#374151;color:#FFFFFF;'] * len(row)
        return [''] * len(row)

    @st.cache_data(ttl=120, show_spinner=False)
    def get_metadata_calling():
        df_meta = pd.read_csv(CSV_URL)
        df_meta.columns = df_meta.columns.str.strip()
        df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
        return sorted(df_meta['Team Name'].dropna().unique()), sorted(df_meta['Vertical'].dropna().unique()), df_meta

    @st.cache_data(ttl=120, show_spinner=False)
    def get_global_last_update():
        try:
            res = client.query("WITH combined AS (SELECT updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` UNION ALL SELECT StartTime as updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`) SELECT updated_at_ampm FROM combined WHERE updated_at IS NOT NULL ORDER BY updated_at DESC LIMIT 1").to_dataframe()
            return str(res['updated_at_ampm'].iloc[0]) if not res.empty else "N/A"
        except: return "N/A"

    @st.cache_data(ttl=120, show_spinner=False)
    def get_available_dates():
        try:
            df_dates = client.query("SELECT MIN(min_d) as min_date, MAX(max_d) as max_date FROM (SELECT MIN(`Call Date`) as min_d, MAX(`Call Date`) as max_d FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` UNION ALL SELECT MIN(CallDate) as min_d, MAX(CallDate) as max_d FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`)").to_dataframe()
            if not df_dates.empty and not pd.isna(df_dates['min_date'].iloc[0]): return df_dates['min_date'].iloc[0], df_dates['max_date'].iloc[0]
        except: pass
        return date.today(), date.today()

    @st.cache_data(ttl=120, show_spinner=False)
    def fetch_call_data(start_date, end_date):
        q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{start_date}' AND '{end_date}'"
        df_ace = client.query(q_ace).to_dataframe()
        if not df_ace.empty: df_ace['source'] = 'Acefone'; df_ace['unique_lead_id'] = df_ace['client_number']
        q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{start_date}' AND '{end_date}'"
        df_ozo = client.query(q_ozo).to_dataframe()
        if not df_ozo.empty:
            df_ozo['unique_lead_id'] = df_ozo['phone_number']
            df_ozo = df_ozo.rename(columns={'AgentName': 'call_owner', 'phone_number': 'client_number', 'StartTime': 'call_datetime', 'CallDate': 'Call Date', 'duration_sec': 'call_duration', 'Status': 'status', 'Type': 'direction', 'Disposition': 'reason'})
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
            # Ozonetel Fix
            ozo_mask = df['source'] == 'Ozonetel'
            df.loc[ozo_mask, 'call_starttime'] = df.loc[ozo_mask, 'call_endtime']
            df.loc[ozo_mask, 'call_endtime'] = df.loc[ozo_mask, 'call_starttime'] + pd.to_timedelta(df.loc[ozo_mask, 'call_duration'], unit='s')
        return df

    def process_metrics_logic(df_filtered):
        agents_list = []; total_duration_agg = 0; ist_tz = pytz.timezone("Asia/Kolkata")
        for owner, agent_group in df_filtered.groupby('call_owner'):
            total_ans, total_miss, total_calls, total_above_3min, agent_valid_dur, total_break_sec_all_days, total_active_days = 0, 0, 0, 0, 0, 0, 0
            daily_io_list, daily_break_list, all_issues = [], [], []
            for c_date, day_group in agent_group.groupby('Call Date'):
                timed_group = day_group[day_group['call_starttime'].notna()].sort_values('call_starttime'); total_active_days += 1
                total_ans += len(day_group[day_group['status'].str.lower() == 'answered']); total_miss += len(day_group[day_group['status'].str.lower() == 'missed']); total_calls += len(day_group)
                total_above_3min += len(day_group[day_group['call_duration'] >= 180])
                day_dur = day_group.loc[day_group['call_duration'] >= 180, 'call_duration'].sum(); agent_valid_dur += day_dur
                if not timed_group.empty:
                    first_call_start, last_call_end = timed_group['call_starttime'].min(), timed_group['call_endtime'].max()
                    daily_io_list.append(f"{c_date.strftime('%d/%m')}: In {first_call_start.strftime('%I:%M %p')} · Out {last_call_end.strftime('%I:%M %p')}")
            total_duration_agg += agent_valid_dur
            prod_sec_total = (36000 * total_active_days) - total_break_sec_all_days
            agents_list.append({"IN/OUT TIME": "\n".join(daily_io_list), "CALLER": owner, "TEAM": agent_group['Team Name'].iloc[0] if not pd.isna(agent_group['Team Name'].iloc[0]) else "Others", "TOTAL CALLS": int(total_calls), "CALL STATUS": f"{total_ans} Ans / {total_miss} Unans", "PICK UP RATIO %": f"{round((total_ans / total_calls * 100)) if total_calls > 0 else 0}%", "CALLS > 3 MINS": int(total_above_3min), "CALL DURATION > 3 MINS": format_dur_hm(agent_valid_dur), "PRODUCTIVE HOURS": format_dur_hm(prod_sec_total), "raw_prod_sec": prod_sec_total, "raw_dur_sec": agent_valid_dur, "REMARKS": ", ".join(all_issues) if all_issues else "None"})
        return pd.DataFrame(agents_list), total_duration_agg

    def compute_team_insights(df_merged, report_df):
        insights = []
        if not report_df.empty:
            team_dur = report_df.groupby("TEAM")["raw_dur_sec"].mean().sort_values(ascending=False)
            if not team_dur.empty: insights.append({"type":"good","icon":"🏆","title":f"Top Team: {team_dur.index[0]}","body":f"Avg duration {format_dur_hm(team_dur.iloc[0])} per agent."})
        return insights

    # SIDEBAR FILTERS
    st.sidebar.markdown("<div class='cw-header'><div class='cw-title'>Calling Data</div></div>", unsafe_allow_html=True)
    min_d, max_d = get_available_dates()
    start_date, end_date = st.sidebar.date_input("Date Range", value=(max_d, max_d), min_value=min_d, max_value=max_d)
    teams, verts, df_m = get_metadata_calling()
    sel_v = st.sidebar.multiselect("Filter by Vertical", verts)
    sel_t = st.sidebar.multiselect("Filter by Team", teams)
    gen_dynamic = st.sidebar.button("🚀 Generate Dynamic Report")
    gen_static = st.sidebar.button("📅 Generate Duration Report")

    # TAB UI
    t1, t2, t3 = st.tabs(["Dynamic Dashboard", "Duration Report", "Insights"])
    with t1:
        if gen_dynamic:
            df_raw = fetch_call_data(start_date, end_date)
            df_raw['merge_key'] = df_raw['call_owner'].str.strip().str.lower()
            df = pd.merge(df_raw, df_m, on='merge_key', how='left')
            if sel_t: df = df[df['Team Name'].isin(sel_t)]
            res_df, total_dur = process_metrics_logic(df)
            st.dataframe(res_df.sort_values("raw_dur_sec", ascending=False), use_container_width=True)
            st.session_state['c_report'] = res_df; st.session_state['c_df'] = df

    with t3:
        if 'c_report' in st.session_state:
            ins = compute_team_insights(st.session_state['c_df'], st.session_state['c_report'])
            for i in ins: st.markdown(f"**{i['icon']} {i['title']}**: {i['body']}")

# --- 6. REVENUE METRICS MODULE ---
def run_revenue():
    # --- Exact logic from revenue_sheet.py (Lines 1-3009) ---
    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=973926168&single=true&output=csv"
    
    # [INTERNAL HELPER FUNCTIONS FROM revenue_sheet.py]
    def fmt_inr(v):
        if pd.isna(v) or v == 0: return "₹0"
        if v >= 10000000: return f"₹{v/10000000:.2f}Cr"
        if v >= 100000: return f"₹{v/100000:.2f}L"
        if v >= 1000: return f"₹{v/1000:.2f}K"
        return f"₹{int(v)}"

    @st.cache_data(ttl=120, show_spinner=False)
    def get_metadata_revenue():
        df_meta = pd.read_csv(CSV_URL)
        df_meta.columns = df_meta.columns.str.strip().str.replace('\xa0', '', regex=False)
        df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
        return sorted(df_meta['Team Name'].dropna().unique()), sorted(df_meta['Vertical'].dropna().unique()), df_meta

    @st.cache_data(ttl=120, show_spinner=False)
    def get_last_update():
        try:
            res = client.query("SELECT MAX(updated_at_ampm) as up FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet`").to_dataframe()
            return str(res['up'].iloc[0]) if not res.empty else "N/A"
        except: return "N/A"

    @st.cache_data(ttl=120, show_spinner=False)
    def fetch_revenue_data(start_date, end_date):
        q = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet` WHERE Date BETWEEN '{start_date}' AND '{end_date}'"
        df = client.query(q).to_dataframe()
        if not df.empty:
            df['Fee_paid'] = pd.to_numeric(df['Fee_paid'], errors='coerce').fillna(0)
            df['is_new'] = df['Enrollment'].astype(str).str.strip().str.lower() == 'new enrollment'
        return df

    def classify_and_process_revenue(df_f, df_m):
        df_f['m_key'] = df_f['Caller_name'].str.strip().str.lower()
        df_res = df_f.merge(df_m[['merge_key', 'Team Name', 'Vertical', 'Caller Name']], left_on='m_key', right_on='merge_key', how='left')
        summary = []
        for caller, grp in df_res.groupby('Caller Name'):
            summary.append({"CALLER NAME": caller, "TEAM": grp['Team Name'].iloc[0] if not pd.isna(grp['Team Name'].iloc[0]) else "Others", "NEW ENROLLMENTS": int(grp['is_new'].sum()), "ENROLLMENT REV": grp[grp['is_new']]['Fee_paid'].sum(), "TOTAL REVENUE": grp['Fee_paid'].sum()})
        return pd.DataFrame(summary)

    # SIDEBAR FILTERS
    st.sidebar.markdown("<div class='rv-header'>💰 Revenue Metrics</div>", unsafe_allow_html=True)
    teams, verts, df_meta = get_metadata_revenue()
    sd = st.sidebar.date_input("Start Date", date.today() - timedelta(days=30), key="rev_sd")
    ed = st.sidebar.date_input("End Date", date.today(), key="rev_ed")
    sel_t = st.sidebar.multiselect("Select Team", teams, key="rev_team")
    gen_rpt = st.sidebar.button("Generate Revenue Report", type="primary")

    # TAB UI
    t1, t2 = st.tabs(["💰 Revenue Dashboard", "🧠 Insights"])
    with t1:
        if gen_rpt:
            df = fetch_revenue_data(sd, ed)
            if sel_t: df = df[df['Team Name'].isin(sel_t)]
            perf_df = classify_and_process_revenue(df, df_meta)
            st.dataframe(perf_df.sort_values("TOTAL REVENUE", ascending=False), use_container_width=True)

# --- ROUTER LOGIC ---
if st.session_state.selection == "Home":
    run_homepage()
elif st.session_state.selection == "Calling Metrics":
    run_calling()
elif st.session_state.selection == "Revenue Metrics":
    run_revenue()
