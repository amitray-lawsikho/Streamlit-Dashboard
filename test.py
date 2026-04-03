import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
import numpy as np
from datetime import datetime, date, time, timedelta
import os
import pytz
import json
import io
import streamlit.components.v1 as components

# --- 1. SET PAGE CONFIG (Only once at the root) ---
st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SHARED CLIENTS & METADATA ---
@st.cache_resource
def get_bq_client():
    if "gcp_service_account" in st.secrets:
        info = dict(st.secrets["gcp_service_account"])
        creds = service_account.Credentials.from_service_account_info(info)
        return bigquery.Client(credentials=creds, project=info["project_id"])
    else:
        # Fallback to local env key if available
        return bigquery.Client()

bq_client = get_bq_client()

# --- 4. SHARED DATA HELPERS ---
def fmt_inr_fixed(val):
    if pd.isna(val): return "₹0"
    s = str(int(val))
    if len(s) <= 3: return "₹" + s
    last_3 = s[-3:]
    other = s[:-3]
    res = ""
    while len(other) > 2:
        res = "," + other[-2:] + res
        other = other[:-2]
    if len(other) > 0: res = other + res
    return "₹" + res + "," + last_3

# --- 5. LOGIC MODULES (TO BE FILLED) ---

def run_homepage():
    # --- HOMEPAGE LOGIC START ---
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

    # ── Logo URLs ──
    LAWSIKHO_LOGO       = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/lawsikho_logo.png"
    SKILLARBITRAGE_LOGO = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/skillarbitrage_logo.png"

    @st.cache_data(ttl=300, show_spinner=False)
    def get_homepage_stats():
        try:
            r1 = bq_client.query("""
                SELECT updated_at_ampm FROM (
                    SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                    UNION ALL
                    SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
                ) WHERE updated_at_ampm IS NOT NULL ORDER BY 1 DESC LIMIT 1
            """).to_dataframe()
            call_time = str(r1["updated_at_ampm"].iloc[0]) if not r1.empty else "N/A"

            r2 = bq_client.query("""
                SELECT SUM(c) AS t FROM (
                    SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                    UNION ALL
                    SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
                )
            """).to_dataframe()
            call_cnt = "{:,}".format(int(r2["t"].iloc[0])) if not r2.empty else "—"

            try:
                r3 = bq_client.query("""
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

    call_time, call_cnt, rev_time, rev_cnt = get_homepage_stats()

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
        font-family: 'Plus Jakarta Sans', sans-serif;
        background: #0B1120;
        color: #E2E8F0;
        min-height: 100vh;
        overflow-x: hidden;
    }
    body {
        background:
            radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,.12) 0%, transparent 60%),
            radial-gradient(ellipse 60% 40% at 90% 80%, rgba(249,115,22,.08) 0%, transparent 55%),
            radial-gradient(ellipse 50% 35% at 10% 90%, rgba(139,92,246,.06) 0%, transparent 50%),
            #0B1120;
    }
    body::before {
        content: "";
        position: fixed; inset: 0;
        background-image:
            linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
        background-size: 48px 48px;
        pointer-events: none; z-index: 0;
    }
    .page { position: relative; z-index: 1; }
    .hero {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 4rem 2rem 3rem;
    }
    .logo-block {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0;
        margin-bottom: 1.6rem;
    }
    .logo-side {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0 2rem;
    }
    .logo-img {
        height: 46px;
        width: auto;
        object-fit: contain;
        mix-blend-mode: lighten;
        filter: brightness(1.25) contrast(1.1) saturate(.95);
        transition: transform .25s, opacity .25s;
    }
    .logo-img:hover { transform: scale(1.05); }
    .logo-fallback {
        display: none;
        font-family: 'Syne', sans-serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #fff;
        letter-spacing: -.5px;
    }
    .logo-glow-sep {
        width: 1px;
        height: 52px;
        background: linear-gradient(180deg,
            transparent 0%,
            rgba(249,115,22,.8) 35%,
            rgba(251,146,60,.9) 50%,
            rgba(249,115,22,.8) 65%,
            transparent 100%);
        box-shadow: 0 0 8px rgba(249,115,22,.6), 0 0 20px rgba(249,115,22,.3);
        border-radius: 1px;
        flex-shrink: 0;
    }
    .hero-tagline {
        font-family: 'Fira Code', monospace;
        font-size: .78rem;
        font-weight: 400;
        color: rgba(255,255,255,.38);
        letter-spacing: 1.5px;
        margin-bottom: 2rem;
    }
    .hero-eyebrow {
        display: inline-flex;
        align-items: center;
        gap: .5rem;
        font-family: 'Fira Code', monospace;
        font-size: .68rem;
        font-weight: 500;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: #F97316;
        background: rgba(249,115,22,.08);
        border: 1px solid rgba(249,115,22,.18);
        border-radius: 100px;
        padding: .3rem 1rem;
        margin-bottom: 1.4rem;
    }
    .eyebrow-dot {
        width: 5px; height: 5px;
        background: #F97316;
        border-radius: 50%;
        box-shadow: 0 0 6px #F97316;
        animation: pulse 2s ease-in-out infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50%       { opacity: .5; transform: scale(1.4); }
    }
    .hero-headline {
        font-family: 'Syne', sans-serif;
        font-size: clamp(2.4rem, 5.5vw, 4.2rem);
        font-weight: 800;
        line-height: 1.08;
        color: #FFFFFF;
        letter-spacing: -1.5px;
        margin-bottom: .8rem;
    }
    .hero-headline .accent {
        background: linear-gradient(125deg, #F97316 0%, #FB923C 40%, #FBBF24 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        display: inline-block;
        -webkit-font-smoothing: antialiased;
    }
    .hero-sub {
        font-size: 1.15rem;
        font-weight: 300;
        color: rgba(255,255,255,.42);
        letter-spacing: .3px;
        margin-bottom: 3rem;
        max-width: 580px;
    }
    .hero-rule {
        display: flex;
        align-items: center;
        gap: 1rem;
        width: 100%;
        max-width: 560px;
        margin-bottom: 3rem;
    }
    .hero-rule-line {
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,.08));
    }
    .hero-rule-line.r { background: linear-gradient(90deg, rgba(255,255,255,.08), transparent); }
    .hero-rule-label {
        font-family: 'Fira Code', monospace;
        font-size: .6rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: rgba(255,255,255,.25);
        white-space: nowrap;
    }
    .stats-row {
        display: flex;
        justify-content: center;
        gap: 1rem;
        flex-wrap: wrap;
        padding: 0 2rem;
        margin-bottom: 4rem;
    }
    .stat-card {
        display: flex;
        align-items: center;
        gap: .85rem;
        background: rgba(255,255,255,.04);
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 16px;
        padding: .9rem 1.4rem;
        min-width: 260px;
        flex: 1;
        max-width: 340px;
        backdrop-filter: blur(12px);
        transition: all .2s;
    }
    .stat-card:hover { transform: translateY(-2px); }
    .stat-card.sc-call:hover { border-color: rgba(249,115,22,.22); background: rgba(249,115,22,.04); }
    .stat-card.sc-rev:hover { border-color: rgba(52,211,153,.22); background: rgba(52,211,153,.04); }
    .stat-card.sc-lead:hover { border-color: rgba(139,92,246,.22); background: rgba(139,92,246,.04); }
    .stat-icon-wrap {
        width: 38px; height: 38px;
        border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        font-size: .95rem; flex-shrink: 0;
    }
    .si-call { background: rgba(249,115,22,.14); }
    .si-rev  { background: rgba(52,211,153,.12); }
    .si-lead { background: rgba(139,92,246,.12); }
    .stat-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
    .stat-lbl {
        font-family: 'Fira Code', monospace;
        font-size: .58rem; font-weight: 500;
        text-transform: uppercase; letter-spacing: 1px;
        color: rgba(255,255,255,.3);
    }
    .stat-val {
        font-family: 'Fira Code', monospace;
        font-size: .8rem; font-weight: 500;
        color: rgba(255,255,255,.82);
        white-space: nowrap;
        overflow: visible;
    }
    .stat-sub {
        font-family: 'Fira Code', monospace;
        font-size: .58rem;
        color: rgba(255,255,255,.2);
    }
    .pill-live {
        margin-left: auto; flex-shrink: 0;
        font-family: 'Fira Code', monospace;
        font-size: .55rem; font-weight: 500;
        letter-spacing: .8px; text-transform: uppercase;
        color: #34D399;
        background: rgba(52,211,153,.1);
        border: 1px solid rgba(52,211,153,.18);
        border-radius: 20px; padding: 2px 8px;
    }
    .pill-wip {
        margin-left: auto; flex-shrink: 0;
        font-family: 'Fira Code', monospace;
        font-size: .55rem; font-weight: 500;
        letter-spacing: .8px; text-transform: uppercase;
        color: #FBBF24;
        background: rgba(251,191,36,.1);
        border: 1px solid rgba(251,191,36,.18);
        border-radius: 20px; padding: 2px 8px;
    }
    .dashboards-section {
        padding: 0 2rem 5rem;
        max-width: 1120px;
        margin: 0 auto;
    }
    .section-head {
        display: flex;
        align-items: center;
        gap: 1rem;
        margin-bottom: 2rem;
    }
    .section-line {
        flex: 1;
        height: 1px;
        background: rgba(255,255,255,.07);
    }
    .section-lbl {
        font-family: 'Fira Code', monospace;
        font-size: .65rem;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        color: rgba(255,255,255,.25);
        white-space: nowrap;
    }
    .cards-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.25rem;
    }
    @media (max-width: 900px) { .cards-grid { grid-template-columns: 1fr; } }
    @media (max-width: 1200px) and (min-width: 901px) { .cards-grid { grid-template-columns: repeat(2, 1fr); } }
    .dcard {
        position: relative;
        background: rgba(255,255,255,.035);
        border: 1px solid rgba(255,255,255,.09);
        border-radius: 20px;
        padding: 1.8rem 1.7rem 1.5rem;
        text-decoration: none;
        color: inherit;
        display: flex;
        flex-direction: column;
        gap: .75rem;
        overflow: hidden;
        transition: transform .25s cubic-bezier(.4,0,.2,1),
                    box-shadow .25s, border-color .25s, background .25s;
    }
    .dcard:hover { transform: translateY(-5px); text-decoration: none; }
    .dcard.wip { pointer-events: none; cursor: default; opacity: .55; }
    .dcard-call { border-top: 2px solid rgba(249,115,22,.4); }
    .dcard-rev  { border-top: 2px solid rgba(52,211,153,.35); }
    .dcard-lead { border-top: 2px solid rgba(139,92,246,.3); }
    .dcard-call:hover { border-color: #F97316; background: rgba(249,115,22,.04); box-shadow: 0 20px 60px rgba(249,115,22,.1), 0 4px 16px rgba(0,0,0,.3); }
    .dcard-rev:hover  { border-color: #34D399; background: rgba(52,211,153,.04); box-shadow: 0 20px 60px rgba(52,211,153,.08), 0 4px 16px rgba(0,0,0,.3); }
    .dcard-glow {
        position: absolute; width: 220px; height: 220px; border-radius: 50%; top: -90px; right: -70px;
        filter: blur(80px); opacity: 0; pointer-events: none; transition: opacity .3s;
    }
    .dcard-call .dcard-glow { background: #F97316; }
    .dcard-rev  .dcard-glow { background: #34D399; }
    .dcard-lead .dcard-glow { background: #8B5CF6; }
    .dcard:hover .dcard-glow { opacity: .1; }
    .dcard-header { display: flex; align-items: flex-start; justify-content: space-between; }
    .dcard-icon { font-size: 1.8rem; line-height: 1; }
    .dcard-wip-badge {
        font-family: 'Fira Code', monospace;
        font-size: .55rem; font-weight: 500;
        text-transform: uppercase; letter-spacing: 1px;
        color: #FBBF24; background: rgba(251,191,36,.08);
        border: 1px solid rgba(251,191,36,.18);
        border-radius: 8px; padding: 3px 9px;
    }
    .dcard-title { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 600; color: #fff; letter-spacing: -.1px; }
    .dcard-desc { font-size: .8rem; font-weight: 300; color: rgba(255,255,255,.42); line-height: 1.7; flex: 1; }
    .dcard-tags { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .2rem; }
    .dtag {
        font-family: 'Fira Code', monospace; font-size: .58rem; font-weight: 400;
        color: rgba(255,255,255,.32); background: rgba(255,255,255,.05);
        border: 1px solid rgba(255,255,255,.08); border-radius: 6px; padding: 2px 9px;
        text-transform: uppercase; letter-spacing: .4px;
    }
    .dcard-cta {
        display: inline-flex; align-items: center; gap: .4rem;
        font-family: 'Fira Code', monospace; font-size: .72rem; font-weight: 500;
        color: rgba(255,255,255,.28); margin-top: .3rem;
        transition: gap .2s, color .2s; letter-spacing: .3px; text-decoration: none;
    }
    .dcard-call:hover .dcard-cta { color: #F97316; gap: .65rem; }
    .dcard-rev:hover  .dcard-cta { color: #34D399; gap: .65rem; }
    .site-footer { border-top: 1px solid rgba(255,255,255,.06); padding: 2rem 2rem 2.5rem; text-align: center; display: flex; flex-direction: column; gap: .5rem; }
    .footer-top { font-family: 'Fira Code', monospace; font-size: .68rem; font-weight: 500; letter-spacing: .8px; color: rgba(255,255,255,.35); }
    .footer-bottom { font-family: 'Fira Code', monospace; font-size: .62rem; letter-spacing: .5px; color: rgba(255,255,255,.18); }
    .footer-dot { display: inline-block; width: 3px; height: 3px; background: rgba(249,115,22,.5); border-radius: 50%; margin: 0 .5rem; vertical-align: middle; }
    </style>
    </head>
    <body>
    <div class="page">
      <div class="hero">
        <div class="logo-block">
          <div class="logo-side">
            <img class="logo-img" src="https://raw.githubusercontent.com/amitray-lawsikho/test/main/assets/lawsikho_logo.png" alt="LawSikho" />
          </div>
          <div class="logo-glow-sep"></div>
          <div class="logo-side">
            <img class="logo-img" src="https://raw.githubusercontent.com/amitray-lawsikho/test/main/assets/skillarbitrage_logo.png" alt="Skill Arbitrage" />
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
            <span class="stat-val">{call_time}</span>
            <span class="stat-sub">{call_cnt} records</span>
          </div>
          <span class="pill-live">● Live</span>
        </div>
        <div class="stat-card sc-rev">
          <div class="stat-icon-wrap si-rev">💰</div>
          <div class="stat-info">
            <span class="stat-lbl">Revenue Data</span>
            <span class="stat-val">{rev_time}</span>
            <span class="stat-sub">{rev_cnt} records</span>
          </div>
          <span class="pill-live">● Live</span>
        </div>
        <div class="stat-card">
          <div class="stat-icon-wrap si-lead">📊</div>
          <div class="stat-info">
            <span class="stat-lbl">Lead Data</span>
            <span class="stat-val" style="color:rgba(255,255,255,.28);">Under Development</span>
            <span class="stat-sub">Coming soon</span>
          </div>
          <span class="pill-wip">🚧 WIP</span>
        </div>
      </div>
      <div class="dashboards-section">
        <div class="section-head"><div class="section-line"></div><span class="section-lbl">Dashboards</span><div class="section-line"></div></div>
        <div class="cards-grid">
          <a class="dcard dcard-call" href="/?page=Calling+Metrics" target="_self">
            <div class="dcard-glow"></div>
            <div class="dcard-header"><div class="dcard-icon">🔔</div></div>
            <div class="dcard-title">Calling Metrics</div>
            <div class="dcard-desc">Full CDR analysis across Ozonetel, Acefone &amp; Manual calls. Agent-level performance, break tracking &amp; team leaderboards.</div>
            <div class="dcard-tags"><span class="dtag">Ozonetel</span><span class="dtag">Acefone</span><span class="dtag">Manual</span><span class="dtag">TEAM</span></div>
            <span class="dcard-cta">Open Dashboard &nbsp;→</span>
          </a>
          <a class="dcard dcard-rev" href="/?page=Revenue+Metrics" target="_self">
            <div class="dcard-glow"></div>
            <div class="dcard-header"><div class="dcard-icon">💰</div></div>
            <div class="dcard-title">Revenue Metrics</div>
            <div class="dcard-desc">Enrollment revenue, target achievement &amp; caller-level breakdown. Course performance, source mix &amp; leaderboards.</div>
            <div class="dcard-tags"><span class="dtag">Enrollments</span><span class="dtag">Targets</span><span class="dtag">Achievement</span><span class="dtag">Teams</span></div>
            <span class="dcard-cta">Open Dashboard &nbsp;→</span>
          </a>
          <a class="dcard dcard-lead wip" href="#">
            <div class="dcard-glow"></div>
            <div class="dcard-header"><div class="dcard-icon">📊</div><span class="dcard-wip-badge">🚧 WIP</span></div>
            <div class="dcard-title">Lead Metrics</div>
            <div class="dcard-desc">Currently under development. Focus on Dialled vs Less Dialled.</div>
            <div class="dcard-tags"><span class="dtag">Fresh</span><span class="dtag">Breached</span><span class="dtag">Dial Rate</span></div>
            <span class="dcard-cta" style="opacity:.3;">In Development</span>
          </a>
        </div>
      </div>
      <div class="site-footer">
        <div class="footer-top">For Internal Use Only <span class="footer-dot"></span> All Rights Reserved</div>
        <div class="footer-bottom">Developed by Amit Ray <span class="footer-dot"></span> Lawsikho</div>
      </div>
    </div>
    </body>
    </html>
    """.format(call_time=call_time, call_cnt=call_cnt, rev_time=rev_time, rev_cnt=rev_cnt)

    components.html(html, height=900, scrolling=True)
    # --- HOMEPAGE LOGIC END ---

def run_calling():
    # --- 1. CALLING LOGIC: STYLES & CONFIG ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    :root {
        --accent-primary:   #F97316;
        --accent-secondary: #EF4444;
        --radius-lg:        16px;
        --shadow-lg:        0 8px 32px rgba(0,0,0,.14);
    }
    .cw-header {
        background: linear-gradient(135deg, #1c0700 0%, #7c2d12 50%, #431407 100%);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: var(--shadow-lg);
    }
    .cw-title { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; margin: 0; }
    .cw-subtitle { font-size: .82rem; color: rgba(255,255,255,.6); }
    .section-header { display: flex; align-items: center; gap: .6rem; margin: 1.5rem 0 .8rem; }
    .section-header-line { flex: 1; height: 1px; background: linear-gradient(90deg, #F97316, transparent); opacity: .35; }
    .section-title { font-size: .78rem; font-weight: 700; text-transform: uppercase; color: #F97316; }
    </style>
    """, unsafe_allow_html=True)

    CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"
    IST = pytz.timezone("Asia/Kolkata")

    # --- 2. CALLING LOGIC: HELPERS ---
    def format_dur_hm(total_seconds):
        if pd.isna(total_seconds) or total_seconds <= 0: return "0h 0m"
        tm = int(round(total_seconds / 60))
        return f"{tm // 60}h {tm % 60}m"

    def get_display_gap_seconds(start_time, end_time):
        if pd.isna(start_time) or pd.isna(end_time): return 0
        s = start_time.replace(second=0, microsecond=0)
        e = end_time.replace(second=0, microsecond=0)
        return (e - s).total_seconds()

    @st.cache_data(ttl=120)
    def get_calling_metadata():
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df['merge_key'] = df['Caller Name'].str.strip().str.lower()
        return sorted(df['Team Name'].dropna().unique()), sorted(df['Vertical'].dropna().unique()), df

    @st.cache_data(ttl=60)
    def fetch_calling_data(sd, ed):
        q_ace = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` WHERE `Call Date` BETWEEN '{sd}' AND '{ed}'"
        df_ace = bq_client.query(q_ace).to_dataframe()
        if not df_ace.empty: df_ace['source'] = 'Acefone'

        q_ozo = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls` WHERE CallDate BETWEEN '{sd}' AND '{ed}'"
        df_ozo = bq_client.query(q_ozo).to_dataframe()
        if not df_ozo.empty:
            df_ozo = df_ozo.rename(columns={'CallID':'call_id','AgentName':'call_owner','phone_number':'client_number','StartTime':'call_datetime','CallDate':'Call Date','duration_sec':'call_duration','Status':'status','Type':'direction','Disposition':'reason'})
            df_ozo['status'] = df_ozo['status'].str.lower().replace({'unanswered':'missed'})
            df_ozo['direction'] = df_ozo['direction'].str.lower().replace({'manual':'outbound'})
            df_ozo['source'] = 'Ozonetel'

        q_man = f"SELECT * FROM `studious-apex-488820-c3.crm_dashboard.manual_calls` WHERE Call_Date BETWEEN '{sd}' AND '{ed}'"
        df_man = bq_client.query(q_man).to_dataframe()
        if not df_man.empty:
            df_man = df_man.rename(columns={'Call_Date':'Call Date','Approved_By':'reason'})
            df_man['status'], df_man['direction'], df_man['source'] = 'answered', 'outbound', 'Manual'

        df = pd.concat([df_ace, df_ozo, df_man], ignore_index=True)
        if not df.empty:
            df['call_endtime'] = pd.to_datetime(df['call_datetime'], utc=True).dt.tz_convert('Asia/Kolkata')
            df['call_duration'] = pd.to_numeric(df['call_duration'], errors='coerce').fillna(0)
            df['call_starttime'] = df['call_endtime'] - pd.to_timedelta(df['call_duration'], unit='s')
            ozo_m = df['source'] == 'Ozonetel'
            df.loc[ozo_m, 'call_starttime'] = df.loc[ozo_m, 'call_endtime']
            df.loc[ozo_m, 'call_endtime'] = df.loc[ozo_m, 'call_starttime'] + pd.to_timedelta(df.loc[ozo_m, 'call_duration'], unit='s')
        return df

    # --- 3. CALLING LOGIC: UI & SIDEBAR ---
    with st.sidebar:
        st.markdown("<div class='brand-name'>Calling Filters</div>", unsafe_allow_html=True)
        teams, verts, df_meta = get_calling_metadata()
        sd = st.date_input("Start Date", date.today())
        ed = st.date_input("End Date", date.today())
        sel_team = st.multiselect("Select Team", teams)
        sel_vert = st.multiselect("Select Vertical", verts)
        gen_rpt = st.button("Generate Dynamic Report", use_container_width=True)

    # --- 4. CALLING LOGIC: PROCESSING ---
    def process_metrics_logic(df_f):
        agents = []
        for owner, ag in df_f.groupby('call_owner'):
            ans = len(ag[ag['status']=='answered'])
            calls = len(ag)
            dur = ag[ag['call_duration']>=180]['call_duration'].sum()
            agents.append({
                "CALLER": owner,
                "TEAM": ag['Team Name'].iloc[0] if not pd.isna(ag['Team Name'].iloc[0]) else "Others",
                "TOTAL CALLS": calls,
                "CALL STATUS": f"{ans} Ans / {calls-ans} Unans",
                "PICK UP RATIO %": f"{round(ans/calls*100) if calls>0 else 0}%",
                "CALL DURATION > 3 MINS": format_dur_hm(dur),
                "raw_dur_sec": dur
            })
        return pd.DataFrame(agents)

    if gen_rpt:
        df = fetch_calling_data(sd, ed)
        df_meta_sub = df_meta[['merge_key', 'Team Name', 'Vertical', 'Caller Name']]
        df['m_key'] = df['call_owner'].str.strip().str.lower()
        df = df.merge(df_meta_sub, left_on='m_key', right_on='merge_key', how='left')
        
        if sel_team: df = df[df['Team Name'].isin(sel_team)]
        if sel_vert: df = df[df['Vertical'].isin(sel_vert)]
        
        st.markdown(f"<div class='cw-header'><h1 class='cw-title'>Calling Dashboard</h1><p class='cw-subtitle'>{sd} to {ed}</p></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Dynamic Dashboard", "Insights"])
        with tab1:
            report_df = process_metrics_logic(df)
            st.dataframe(report_df.sort_values("raw_dur_sec", ascending=False), use_container_width=True)
            
            cdr_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Raw CDR", cdr_csv, "cdr_report.csv", "text/csv")
        
        with tab2:
            st.subheader("Team Leaderboard")
            leaderboard = report_df.groupby("TEAM")["raw_dur_sec"].sum().sort_values(ascending=False)
            st.bar_chart(leaderboard)
    else:
        st.info("Select filters and click 'Generate'.")
    # --- CALLING LOGIC END ---

def run_revenue():
    # --- 1. REVENUE LOGIC: STYLES ---
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');
    :root {
        --accent-primary:   #10B981;
        --radius-lg:        16px;
        --shadow-lg:        0 8px 32px rgba(0,0,0,.14);
    }
    .rv-header {
        background: linear-gradient(135deg, #064e3b 0%, #065f46 45%, #1e3a5f 100%);
        border-radius: var(--radius-lg);
        padding: 1.5rem 2rem 1.2rem;
        margin-bottom: 1.2rem;
        box-shadow: var(--shadow-lg);
    }
    .rv-title   { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; margin: 0; }
    .rv-subtitle{ font-size: .82rem; color: rgba(255,255,255,.6); }
    </style>
    """, unsafe_allow_html=True)

    CSV_URL      = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=973926168&single=true&output=csv"
    REV_TABLE_ID = "studious-apex-488820-c3.crm_dashboard.revenue_sheet"

    # --- 2. REVENUE LOGIC: HELPERS ---
    def fmt_inr(value):
        if pd.isna(value) or value == 0: return "₹0"
        if value >= 1_00_00_000: return f"₹{value/1_00_00_000:.2f}Cr"
        if value >= 1_00_000:    return f"₹{value/1_00_000:.2f}L"
        if value >= 1_000:       return f"₹{value/1_000:.2f}K"
        return f"₹{int(value)}"

    @st.cache_data(ttl=120)
    def get_revenue_metadata():
        df = pd.read_csv(CSV_URL)
        df.columns = df.columns.str.strip()
        df['merge_key'] = df['Caller Name'].str.strip().str.lower()
        if 'Month' in df.columns:
            df['Month'] = pd.to_datetime(df['Month'], dayfirst=True, errors='coerce').dt.date
        return sorted(df['Team Name'].dropna().unique()), sorted(df['Vertical'].dropna().unique()), df

    @st.cache_data(ttl=120)
    def fetch_revenue_data(sd, ed):
        query = f"SELECT * FROM `{REV_TABLE_ID}` WHERE Date BETWEEN '{sd}' AND '{ed}' AND Fee_paid > 0"
        df = bq_client.query(query).to_dataframe()
        if not df.empty:
            df['Fee_paid'] = pd.to_numeric(df['Fee_paid'], errors='coerce').fillna(0)
            df['is_new_enrollment'] = df['Enrollment'].astype(str).str.strip().str.lower() == 'new enrollment'
            df['is_balance_payment'] = df['Enrollment'].astype(str).str.strip().str.lower() == 'new enrollment - balance payment'
        return df

    # --- 3. REVENUE LOGIC: UI & SIDEBAR ---
    with st.sidebar:
        st.markdown("<div class='brand-name'>Revenue Filters</div>", unsafe_allow_html=True)
        teams, verts, df_meta = get_revenue_metadata()
        sd = st.date_input("Start Date", date.today() - timedelta(days=30), key="rev_sd")
        ed = st.date_input("End Date", date.today(), key="rev_ed")
        sel_team = st.multiselect("Select Team", teams, key="rev_team")
        gen_rpt = st.button("Generate Revenue Report", use_container_width=True)

    # --- 4. REVENUE LOGIC: PROCESSING ---
    def classify_and_process_revenue(df_f, df_m):
        # Simplified classification for the consolidated view
        df_f['m_key'] = df_f['Caller_name'].str.strip().str.lower()
        df_m_sub = df_m[['merge_key', 'Team Name', 'Vertical', 'Caller Name']]
        df_res = df_f.merge(df_m_sub, left_on='m_key', right_on='merge_key', how='left')
        
        summary = []
        for cleaner, grp in df_res.groupby('Caller Name'):
            enr_rev = grp[grp['is_new_enrollment']]['Fee_paid'].sum()
            bal_rev = grp[grp['is_balance_payment']]['Fee_paid'].sum()
            summary.append({
                "CALLER NAME": cleaner,
                "TEAM": grp['Team Name'].iloc[0] if not pd.isna(grp['Team Name'].iloc[0]) else "Others",
                "ENROLLMENTS": int(grp['is_new_enrollment'].sum()),
                "ENROLLMENT REV": enr_rev,
                "BALANCE REV": bal_rev,
                "TOTAL REVENUE": enr_rev + bal_rev
            })
        return pd.DataFrame(summary)

    if gen_rpt:
        df = fetch_revenue_data(sd, ed)
        if sel_team:
            # Need to merge with metadata to filter by team before processing
            _, _, df_meta = get_revenue_metadata()
            df['m_key'] = df['Caller_name'].str.strip().str.lower()
            df = df.merge(df_meta[['merge_key', 'Team Name']], left_on='m_key', right_on='merge_key', how='left')
            df = df[df['Team Name'].isin(sel_team)]

        st.markdown(f"<div class='rv-header'><h1 class='rv-title'>Revenue Dashboard</h1><p class='rv-subtitle'>{sd} to {ed}</p></div>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Performance Breakdown", "Team Insights"])
        with tab1:
            perf_df = classify_and_process_revenue(df, df_meta)
            st.dataframe(perf_df.sort_values("TOTAL REVENUE", ascending=False), use_container_width=True)
            
            rev_csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Raw Revenue Data", rev_csv, "revenue_data.csv", "text/csv")

        with tab2:
            st.subheader("Revenue by Team")
            team_rev = perf_df.groupby("TEAM")["TOTAL REVENUE"].sum().sort_values(ascending=False)
            st.bar_chart(team_rev)
    else:
        st.info("Select filters and click 'Generate Revenue Report'.")
    # --- REVENUE LOGIC END ---

# --- 6. NAVIGATION ROUTER ---
# Handle query parameters for homepage card clicks
if "page" in st.query_params:
    target = st.query_params["page"]
    # We can use this to force selection if needed, but st.navigation 
    # usually handles it if the URL matches the page titles.
    pass

pg = st.navigation({
    "Main": [
        st.Page(run_homepage, title="Home", icon="🏠"),
    ],
    "Dashboards": [
        st.Page(run_calling,  title="Calling Metrics", icon="🔔"),
        st.Page(run_revenue,  title="Revenue Metrics", icon="💰"),
    ]
})

pg.run()
