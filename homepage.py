import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import os

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# BIGQUERY — fetch live stats
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def get_live_stats():
    try:
        if "gcp_service_account" in st.secrets:
            info        = dict(st.secrets["gcp_service_account"])
            credentials = service_account.Credentials.from_service_account_info(info)
            client      = bigquery.Client(credentials=credentials, project=info["project_id"])
        else:
            client = bigquery.Client()

        # Calling stats
        call_q = """
            SELECT updated_at_ampm, COUNT(*) as cnt
            FROM (
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                UNION ALL
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
            )
            GROUP BY updated_at_ampm
            ORDER BY 1 DESC LIMIT 1
        """
        call_res  = client.query(call_q).to_dataframe()
        call_time = call_res["updated_at_ampm"].iloc[0] if not call_res.empty else "N/A"
        call_cnt  = client.query(
            "SELECT COUNT(*) as c FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls` UNION ALL "
            "SELECT COUNT(*) as c FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`"
        ).to_dataframe()["c"].sum()

        # Revenue stats
        rev_q = """
            SELECT updated_at_ampm, COUNT(*) as cnt
            FROM `studious-apex-488820-c3.crm_dashboard.revenue_data`
            GROUP BY updated_at_ampm ORDER BY 1 DESC LIMIT 1
        """
        try:
            rev_res  = client.query(rev_q).to_dataframe()
            rev_time = rev_res["updated_at_ampm"].iloc[0] if not rev_res.empty else "N/A"
            rev_cnt  = rev_res["cnt"].iloc[0] if not rev_res.empty else 0
        except Exception:
            rev_time = "N/A"
            rev_cnt  = 0

        return {
            "call_time": call_time,
            "call_cnt" : f"{int(call_cnt):,}",
            "rev_time" : rev_time,
            "rev_cnt"  : f"{int(rev_cnt):,}",
        }
    except Exception:
        return {
            "call_time": "N/A", "call_cnt": "—",
            "rev_time" : "N/A", "rev_cnt" : "—",
        }

stats = get_live_stats()

# ─────────────────────────────────────────────
# !! REPLACE THESE WITH YOUR ACTUAL RAW GITHUB URLS !!
# Format: https://raw.githubusercontent.com/USERNAME/REPO/main/assets/filename.png
# ─────────────────────────────────────────────
LAWSIKHO_LOGO_URL      = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/lawsikho_logo.png"
SKILLARBITRAGE_LOGO_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/skillarbitrage_logo.png"

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset & base ── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

/* ── Hide Streamlit chrome ── */
footer                              { visibility: hidden; }
[data-testid="stStatusWidget"]      { display: none !important; }
#MainMenu                           { display: none !important; }
[data-testid="collapsedControl"]    { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }

/* ── Full-page dark background ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background: #0A0A0F !important; }

/* ── CRITICAL: push content below Streamlit toolbar (~58px) ── */
[data-testid="stMainViewContainer"] {
    padding-top: 0 !important;
}
[data-testid="stMain"] > div:first-child {
    padding-top: 0 !important;
}
section[data-testid="stMain"] > div {
    padding-top: 0 !important;
    padding-left: 0 !important;
    padding-right: 0 !important;
}
/* The toolbar itself is ~58px — we add that as margin-top on our hub wrapper */
.hub-wrapper {
    margin-top: 58px;   /* clears the Streamlit toolbar */
    min-height: calc(100vh - 58px);
    background: linear-gradient(160deg, #0A0A0F 0%, #110A1F 40%, #0A0F1A 100%);
    padding: 0 0 4rem;
}

/* ── Stars/particle background ── */
.hub-wrapper::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image:
        radial-gradient(1px 1px at 15% 25%, rgba(255,255,255,.18) 0%, transparent 100%),
        radial-gradient(1px 1px at 72% 14%, rgba(255,255,255,.14) 0%, transparent 100%),
        radial-gradient(1px 1px at 44% 68%, rgba(255,255,255,.12) 0%, transparent 100%),
        radial-gradient(1px 1px at 88% 55%, rgba(255,255,255,.10) 0%, transparent 100%),
        radial-gradient(1px 1px at 30% 82%, rgba(255,255,255,.16) 0%, transparent 100%),
        radial-gradient(2px 2px at 60% 40%, rgba(249,115,22,.15) 0%, transparent 100%),
        radial-gradient(2px 2px at 20% 60%, rgba(167,139,250,.10) 0%, transparent 100%);
    pointer-events: none;
    z-index: 0;
}

/* ── Header section ── */
.hub-header {
    position: relative;
    z-index: 1;
    text-align: center;
    padding: 3rem 2rem 2rem;
}

/* ── Logo row ── */
.logo-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    margin-bottom: 1.8rem;
    flex-wrap: wrap;
}
.logo-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: .4rem;
}
.logo-img {
    height: 52px;
    width: auto;
    object-fit: contain;
    /* Transparent blend — dark parts of logo become transparent on dark bg */
    mix-blend-mode: lighten;
    filter: brightness(1.1) contrast(1.05);
    transition: opacity .2s;
}
.logo-img:hover { opacity: .85; }
.logo-divider {
    width: 1px;
    height: 44px;
    background: linear-gradient(180deg, transparent, rgba(249,115,22,.5), transparent);
}
.logo-label {
    font-size: .6rem;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(255,255,255,.3);
    font-family: 'DM Mono', monospace;
}

/* ── Hub title ── */
.hub-title {
    font-size: clamp(1.6rem, 4vw, 2.6rem);
    font-weight: 700;
    line-height: 1.2;
    margin-bottom: .5rem;
    background: linear-gradient(135deg, #FFFFFF 0%, #F97316 50%, #EF4444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hub-subtitle {
    font-size: clamp(.78rem, 2vw, .92rem);
    color: rgba(255,255,255,.4);
    font-family: 'DM Mono', monospace;
    letter-spacing: .5px;
    margin-bottom: 2.5rem;
}

/* ── Divider line ── */
.hub-divider {
    width: 80px;
    height: 2px;
    background: linear-gradient(90deg, transparent, #F97316, transparent);
    margin: 0 auto 2.5rem;
    border-radius: 2px;
}

/* ── Live stats row ── */
.stats-row {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
    padding: 0 2rem;
    margin-bottom: 3rem;
    position: relative;
    z-index: 1;
}
.stat-card {
    display: flex;
    align-items: center;
    gap: .9rem;
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 14px;
    padding: .85rem 1.2rem;
    min-width: 240px;
    flex: 1;
    max-width: 320px;
    backdrop-filter: blur(8px);
    transition: border-color .2s, background .2s;
}
.stat-card:hover {
    border-color: rgba(249,115,22,.25);
    background: rgba(249,115,22,.04);
}
.stat-icon {
    font-size: 1.4rem;
    width: 40px; height: 40px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
}
.stat-icon.call { background: rgba(249,115,22,.12); }
.stat-icon.rev  { background: rgba(52,211,153,.10); }
.stat-icon.lead { background: rgba(167,139,250,.10); }
.stat-body { flex: 1; min-width: 0; }
.stat-label {
    font-size: .65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: rgba(255,255,255,.35);
    margin-bottom: .2rem;
}
.stat-val {
    font-size: .85rem;
    font-weight: 600;
    color: #fff;
    font-family: 'DM Mono', monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.live-pill {
    font-size: .62rem;
    font-weight: 700;
    color: #34D399;
    background: rgba(52,211,153,.12);
    border: 1px solid rgba(52,211,153,.2);
    border-radius: 20px;
    padding: 2px 9px;
    white-space: nowrap;
    flex-shrink: 0;
}
.wip-pill {
    font-size: .62rem;
    font-weight: 700;
    color: #FBBF24;
    background: rgba(251,191,36,.12);
    border: 1px solid rgba(251,191,36,.2);
    border-radius: 20px;
    padding: 2px 9px;
    white-space: nowrap;
    flex-shrink: 0;
}

/* ── Cards grid ── */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.2rem;
    padding: 0 2rem;
    max-width: 1100px;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}
.app-card {
    position: relative;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 20px;
    padding: 1.8rem 1.6rem 1.4rem;
    text-decoration: none !important;
    display: flex;
    flex-direction: column;
    gap: .6rem;
    overflow: hidden;
    transition: transform .22s cubic-bezier(.4,0,.2,1),
                border-color .22s, box-shadow .22s, background .22s;
    backdrop-filter: blur(12px);
}
.app-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 16px 48px rgba(0,0,0,.35);
    text-decoration: none !important;
}

/* Per-card accent colours */
.card-call  { border-top: 2px solid rgba(249,115,22,.5); }
.card-call:hover  { border-color: #F97316; background: rgba(249,115,22,.05); box-shadow: 0 16px 48px rgba(249,115,22,.12); }
.card-rev   { border-top: 2px solid rgba(52,211,153,.4); }
.card-rev:hover   { border-color: #34D399; background: rgba(52,211,153,.04); box-shadow: 0 16px 48px rgba(52,211,153,.10); }
.card-leads { border-top: 2px solid rgba(167,139,250,.3); opacity: .6; }

/* Glow blob */
.card-bg-glow {
    position: absolute;
    width: 180px; height: 180px;
    border-radius: 50%;
    top: -60px; right: -60px;
    filter: blur(60px);
    opacity: .12;
    pointer-events: none;
    transition: opacity .3s;
}
.card-call  .card-bg-glow { background: #F97316; }
.card-rev   .card-bg-glow { background: #34D399; }
.card-leads .card-bg-glow { background: #A78BFA; }
.app-card:hover .card-bg-glow { opacity: .22; }

.card-icon  { font-size: 2rem; line-height: 1; }
.card-title {
    font-size: 1.05rem;
    font-weight: 700;
    color: #FFFFFF;
    letter-spacing: .2px;
}
.card-desc {
    font-size: .78rem;
    color: rgba(255,255,255,.45);
    line-height: 1.6;
    flex: 1;
}
.card-chips {
    display: flex;
    flex-wrap: wrap;
    gap: .4rem;
    margin-top: .3rem;
}
.chip {
    font-size: .62rem;
    font-weight: 600;
    color: rgba(255,255,255,.5);
    background: rgba(255,255,255,.07);
    border: 1px solid rgba(255,255,255,.1);
    border-radius: 20px;
    padding: 2px 9px;
    letter-spacing: .3px;
}
.card-link {
    font-size: .75rem;
    font-weight: 700;
    color: rgba(255,255,255,.5);
    margin-top: .4rem;
    display: flex;
    align-items: center;
    gap: .3rem;
    transition: color .2s;
}
.card-call:hover  .card-link { color: #F97316; }
.card-rev:hover   .card-link { color: #34D399; }

.wip-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: .65rem;
    font-weight: 700;
    color: #FBBF24;
    background: rgba(251,191,36,.1);
    border: 1px solid rgba(251,191,36,.2);
    border-radius: 20px;
    padding: 2px 9px;
    width: fit-content;
}

/* ── Footer ── */
.hub-footer {
    text-align: center;
    margin-top: 3.5rem;
    font-size: .68rem;
    color: rgba(255,255,255,.18);
    font-family: 'DM Mono', monospace;
    letter-spacing: .5px;
    position: relative;
    z-index: 1;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RENDER
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hub-wrapper">

  <!-- ══ HEADER ══ -->
  <div class="hub-header">

    <!-- Logo row -->
    <div class="logo-row">
      <div class="logo-item">
        <img class="logo-img" src="{LAWSIKHO_LOGO_URL}" alt="LawSikho" />
        <span class="logo-label">LawSikho</span>
      </div>
      <div class="logo-divider"></div>
      <div class="logo-item">
        <img class="logo-img" src="{SKILLARBITRAGE_LOGO_URL}" alt="Skill Arbitrage" />
        <span class="logo-label">Skill Arbitrage</span>
      </div>
    </div>

    <div class="hub-title">Internal Analytics Hub</div>
    <div class="hub-subtitle">Real-time dashboards · Powered by BigQuery</div>
    <div class="hub-divider"></div>

  </div>

  <!-- ══ LIVE STATS ══ -->
  <div class="stats-row">

    <div class="stat-card">
      <div class="stat-icon call">🔔</div>
      <div class="stat-body">
        <div class="stat-label">Calling Data — Last Updated</div>
        <div class="stat-val">{stats["call_time"]}</div>
        <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.28);margin-top:.1rem;">
          {stats["call_cnt"]} records
        </div>
      </div>
      <span class="live-pill">● Live</span>
    </div>

    <div class="stat-card">
      <div class="stat-icon rev">💰</div>
      <div class="stat-body">
        <div class="stat-label">Revenue Data — Last Updated</div>
        <div class="stat-val">{stats["rev_time"]}</div>
        <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.28);margin-top:.1rem;">
          {stats["rev_cnt"]} records
        </div>
      </div>
      <span class="live-pill">● Live</span>
    </div>

    <div class="stat-card">
      <div class="stat-icon lead">📊</div>
      <div class="stat-body">
        <div class="stat-label">Lead Data — Status</div>
        <div class="stat-val" style="color:rgba(255,255,255,.35);">Under Development</div>
        <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.2);margin-top:.1rem;">
          Pipeline coming soon
        </div>
      </div>
      <span class="wip-pill">🚧 WIP</span>
    </div>

  </div>

  <!-- ══ APP CARDS ══ -->
  <div class="cards-grid">

    <a class="app-card card-call"
       href="https://dashboard-lawsikho-call.streamlit.app/" target="_blank">
      <div class="card-bg-glow"></div>
      <div class="card-icon">🔔</div>
      <div class="card-title">Calling Metrics</div>
      <div class="card-desc">
        Full CDR analysis across Ozonetel, Acefone &amp; Manual calls.
        Agent-level performance, break tracking, productive hours &amp; team leaderboards.
      </div>
      <div class="card-chips">
        <span class="chip">Ozonetel</span>
        <span class="chip">Acefone</span>
        <span class="chip">Manual</span>
        <span class="chip">Live</span>
      </div>
      <span class="card-link">Open Dashboard <span>→</span></span>
    </a>

    <a class="app-card card-rev"
       href="https://dashboard-lawsikho-revenue.streamlit.app/" target="_blank">
      <div class="card-bg-glow"></div>
      <div class="card-icon">💰</div>
      <div class="card-title">Revenue Metrics</div>
      <div class="card-desc">
        Enrollment revenue, target achievement &amp; caller-level breakdown.
        Course performance, source mix &amp; team leaderboards.
      </div>
      <div class="card-chips">
        <span class="chip">Enrollments</span>
        <span class="chip">Targets</span>
        <span class="chip">Courses</span>
        <span class="chip">Live</span>
      </div>
      <span class="card-link">Open Dashboard <span>→</span></span>
    </a>

    <a class="app-card card-leads"
       href="#" style="pointer-events:none;cursor:default;">
      <div class="card-bg-glow"></div>
      <div class="card-icon">📊</div>
      <div class="wip-badge">🚧 Work in Progress</div>
      <div class="card-title">Lead Metrics</div>
      <div class="card-desc">
        Pipeline health, lead source quality, conversion rates &amp; funnel drop-off analysis.
        Coming soon — currently in development.
      </div>
      <div class="card-chips">
        <span class="chip">Pipeline</span>
        <span class="chip">Funnel</span>
        <span class="chip">Conversion</span>
        <span class="chip">Soon</span>
      </div>
      <span class="card-link" style="opacity:.4;">Coming Soon</span>
    </a>

  </div>

  <!-- ══ FOOTER ══ -->
  <div class="hub-footer">
    DESIGNED BY AMIT RAY &nbsp;·&nbsp; amitray@lawsikho.com &nbsp;·&nbsp;
    INTERNAL USE ONLY
  </div>

</div>
""", unsafe_allow_html=True)
