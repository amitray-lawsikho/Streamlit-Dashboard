import streamlit as st
import streamlit.components.v1 as components
from google.cloud import bigquery
from google.oauth2 import service_account

st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
footer { visibility: hidden; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: #0B1120 !important; }
section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
[data-testid="stMainViewContainer"] { padding-top: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
iframe { display: block; }
</style>
""", unsafe_allow_html=True)

# ── Logo URLs — replace with your actual GitHub raw URLs ──
LAWSIKHO_LOGO       = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/lawsikho_logo.png"
SKILLARBITRAGE_LOGO = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/skillarbitrage_logo.png"

@st.cache_data(ttl=300, show_spinner=False)
def get_stats():
    try:
        if "gcp_service_account" in st.secrets:
            info  = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(info)
            bq    = bigquery.Client(credentials=creds, project=info["project_id"])
        else:
            bq = bigquery.Client()

        r1 = bq.query("""
            SELECT updated_at_ampm FROM (
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                UNION ALL
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
            ) WHERE updated_at_ampm IS NOT NULL ORDER BY 1 DESC LIMIT 1
        """).to_dataframe()
        call_time = str(r1["updated_at_ampm"].iloc[0]) if not r1.empty else "N/A"

        r2 = bq.query("""
            SELECT SUM(c) AS t FROM (
                SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                UNION ALL
                SELECT COUNT(*) AS c FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
            )
        """).to_dataframe()
        call_cnt = "{:,}".format(int(r2["t"].iloc[0])) if not r2.empty else "—"

        try:
            r3 = bq.query("""
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

/* ── Moderate professional background ── */
body {
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(59,130,246,.12) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 80%, rgba(249,115,22,.08) 0%, transparent 55%),
        radial-gradient(ellipse 50% 35% at 10% 90%, rgba(139,92,246,.06) 0%, transparent 50%),
        #0B1120;
}

/* Subtle grid overlay */
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

/* ════════════════════════════
   HERO
════════════════════════════ */
.hero {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 4rem 2rem 3rem;
}

/* ── Logo block ── */
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

/* Fallback text if image fails */
.logo-fallback {
    display: none;
    font-family: 'Syne', sans-serif;
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
    letter-spacing: -.5px;
}

/* Glowing vertical separator */
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

/* ── Tagline ── */
.hero-tagline {
    font-family: 'Fira Code', monospace;
    font-size: .78rem;
    font-weight: 400;
    color: rgba(255,255,255,.38);
    letter-spacing: 1.5px;
    margin-bottom: 2rem;
}

/* ── Eyebrow ── */
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

/* ── Headline ── */
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
    font-size: .95rem;
    font-weight: 300;
    color: rgba(255,255,255,.42);
    letter-spacing: .3px;
    margin-bottom: 3rem;
    max-width: 480px;
}

/* ── Thin rule ── */
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
    color: rgba(255,255,255,.2);
    white-space: nowrap;
}

/* ════════════════════════════
   STAT PILLS
════════════════════════════ */
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
    padding: .9rem 1.3rem;
    min-width: 220px;
    flex: 1;
    max-width: 300px;
    backdrop-filter: blur(12px);
    transition: all .2s;
}
.stat-card:hover {
    border-color: rgba(249,115,22,.22);
    background: rgba(249,115,22,.04);
    transform: translateY(-2px);
}
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
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
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

/* ════════════════════════════
   DASHBOARDS SECTION
════════════════════════════ */
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

/* 3 equal separate cards */
.cards-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.25rem;
}

@media (max-width: 900px) {
    .cards-grid { grid-template-columns: 1fr; }
}
@media (max-width: 1200px) and (min-width: 901px) {
    .cards-grid { grid-template-columns: repeat(2, 1fr); }
}

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
.dcard:hover {
    transform: translateY(-5px);
    text-decoration: none;
}
.dcard.wip {
    pointer-events: none;
    cursor: default;
    opacity: .55;
}

/* Top accent line per card */
.dcard-call { border-top: 2px solid rgba(249,115,22,.4); }
.dcard-rev  { border-top: 2px solid rgba(52,211,153,.35); }
.dcard-lead { border-top: 2px solid rgba(139,92,246,.3); }

.dcard-call:hover {
    border-color: #F97316;
    background: rgba(249,115,22,.04);
    box-shadow: 0 20px 60px rgba(249,115,22,.1), 0 4px 16px rgba(0,0,0,.3);
}
.dcard-rev:hover {
    border-color: #34D399;
    background: rgba(52,211,153,.04);
    box-shadow: 0 20px 60px rgba(52,211,153,.08), 0 4px 16px rgba(0,0,0,.3);
}

/* Glow orb */
.dcard-glow {
    position: absolute;
    width: 220px; height: 220px;
    border-radius: 50%;
    top: -90px; right: -70px;
    filter: blur(80px);
    opacity: 0;
    pointer-events: none;
    transition: opacity .3s;
}
.dcard-call .dcard-glow { background: #F97316; }
.dcard-rev  .dcard-glow { background: #34D399; }
.dcard-lead .dcard-glow { background: #8B5CF6; }
.dcard:hover .dcard-glow { opacity: .1; }

/* Card header */
.dcard-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}
.dcard-icon { font-size: 1.8rem; line-height: 1; }
.dcard-wip-badge {
    font-family: 'Fira Code', monospace;
    font-size: .55rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1px;
    color: #FBBF24;
    background: rgba(251,191,36,.08);
    border: 1px solid rgba(251,191,36,.18);
    border-radius: 8px; padding: 3px 9px;
}

.dcard-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.2rem; font-weight: 600;
    color: #fff; letter-spacing: -.1px;
}

.dcard-desc {
    font-size: .8rem; font-weight: 300;
    color: rgba(255,255,255,.42);
    line-height: 1.7; flex: 1;
}

/* Tags */
.dcard-tags {
    display: flex; flex-wrap: wrap; gap: .4rem;
    margin-top: .2rem;
}
.dtag {
    font-family: 'Fira Code', monospace;
    font-size: .58rem; font-weight: 400;
    color: rgba(255,255,255,.32);
    background: rgba(255,255,255,.05);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 6px; padding: 2px 9px;
    text-transform: uppercase; letter-spacing: .4px;
}

/* CTA */
.dcard-cta {
    display: inline-flex;
    align-items: center;
    gap: .4rem;
    font-family: 'Fira Code', monospace;
    font-size: .72rem; font-weight: 500;
    color: rgba(255,255,255,.28);
    margin-top: .3rem;
    transition: gap .2s, color .2s;
    letter-spacing: .3px;
    text-decoration: none;
}
.dcard-call:hover .dcard-cta { color: #F97316; gap: .65rem; }
.dcard-rev:hover  .dcard-cta { color: #34D399; gap: .65rem; }

/* ════════════════════════════
   FOOTER
════════════════════════════ */
.site-footer {
    border-top: 1px solid rgba(255,255,255,.06);
    padding: 2rem 2rem 2.5rem;
    text-align: center;
    display: flex;
    flex-direction: column;
    gap: .5rem;
}
.footer-top {
    font-family: 'Fira Code', monospace;
    font-size: .68rem;
    font-weight: 500;
    letter-spacing: .8px;
    color: rgba(255,255,255,.35);
}
.footer-bottom {
    font-family: 'Fira Code', monospace;
    font-size: .62rem;
    letter-spacing: .5px;
    color: rgba(255,255,255,.18);
}
.footer-dot {
    display: inline-block;
    width: 3px; height: 3px;
    background: rgba(249,115,22,.5);
    border-radius: 50%;
    margin: 0 .5rem;
    vertical-align: middle;
}

</style>
</head>
<body>
<div class="page">

  <!-- ════ HERO ════ -->
  <div class="hero">

    <!-- Logo row: image | glow sep | image -->
    <div class="logo-block">
      <div class="logo-side">
        <img class="logo-img"
             src="LAWSIKHO_LOGO_PH"
             alt="LawSikho"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <span class="logo-fallback">LawSikho</span>
      </div>
      <div class="logo-glow-sep"></div>
      <div class="logo-side">
        <img class="logo-img"
             src="SA_LOGO_PH"
             alt="Skill Arbitrage"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex';" />
        <span class="logo-fallback">Skill Arbitrage</span>
      </div>
    </div>

    <!-- Tagline below logos -->
    <div class="hero-tagline">India Learning &nbsp;📚&nbsp; India Earning</div>

    <!-- Eyebrow pill -->
    <div class="hero-eyebrow">
      <span class="eyebrow-dot"></span>
      Internal Analytics Hub
    </div>

    <!-- Main headline -->
    <div class="hero-headline">
      All your dashboards,<br><span class="accent">at one place</span>
    </div>

    <div class="hero-sub">
      Real-time insights across Calling, Revenue &amp; Leads
    </div>

    <div class="hero-rule">
      <div class="hero-rule-line"></div>
      <span class="hero-rule-label">Live Dashboards</span>
      <div class="hero-rule-line r"></div>
    </div>

  </div>

  <!-- ════ STAT CARDS ════ -->
  <div class="stats-row">

    <div class="stat-card">
      <div class="stat-icon-wrap si-call">🔔</div>
      <div class="stat-info">
        <span class="stat-lbl">Calling Data</span>
        <span class="stat-val">CALL_TIME_PH</span>
        <span class="stat-sub">CALL_CNT_PH records</span>
      </div>
      <span class="pill-live">● Live</span>
    </div>

    <div class="stat-card">
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
      <div class="stat-info">
        <span class="stat-lbl">Lead Data</span>
        <span class="stat-val" style="color:rgba(255,255,255,.28);">Under Development</span>
        <span class="stat-sub">Pipeline coming soon</span>
      </div>
      <span class="pill-wip">🚧 WIP</span>
    </div>

  </div>

  <!-- ════ DASHBOARD CARDS ════ -->
  <div class="dashboards-section">

    <div class="section-head">
      <div class="section-line"></div>
      <span class="section-lbl">Dashboards</span>
      <div class="section-line"></div>
    </div>

    <div class="cards-grid">

      <!-- Card 1: Calling -->
      <a class="dcard dcard-call" href="https://dashboard-lawsikho-call.streamlit.app/" target="_blank">
        <div class="dcard-glow"></div>
        <div class="dcard-header">
          <div class="dcard-icon">🔔</div>
        </div>
        <div class="dcard-title">Calling Metrics</div>
        <div class="dcard-desc">
          Full CDR analysis across Ozonetel, Acefone &amp; Manual calls.
          Agent-level performance, break tracking, productive hours &amp; team leaderboards.
        </div>
        <div class="dcard-tags">
          <span class="dtag">Ozonetel</span>
          <span class="dtag">Acefone</span>
          <span class="dtag">Manual</span>
          <span class="dtag">CDR</span>
        </div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>

      <!-- Card 2: Revenue -->
      <a class="dcard dcard-rev" href="https://dashboard-lawsikho-revenue.streamlit.app/" target="_blank">
        <div class="dcard-glow"></div>
        <div class="dcard-header">
          <div class="dcard-icon">💰</div>
        </div>
        <div class="dcard-title">Revenue Metrics</div>
        <div class="dcard-desc">
          Enrollment revenue, target achievement &amp; caller-level breakdown.
          Course performance, source mix &amp; team leaderboards.
        </div>
        <div class="dcard-tags">
          <span class="dtag">Enrollments</span>
          <span class="dtag">Targets</span>
          <span class="dtag">Courses</span>
          <span class="dtag">Teams</span>
        </div>
        <span class="dcard-cta">Open Dashboard &nbsp;→</span>
      </a>

      <!-- Card 3: Leads (WIP) -->
      <a class="dcard dcard-lead wip" href="#" style="pointer-events:none;">
        <div class="dcard-glow"></div>
        <div class="dcard-header">
          <div class="dcard-icon">📊</div>
          <span class="dcard-wip-badge">🚧 Coming Soon</span>
        </div>
        <div class="dcard-title">Lead Metrics</div>
        <div class="dcard-desc">
          Pipeline health, lead source quality, conversion rates &amp; funnel
          drop-off analysis. Currently under development.
        </div>
        <div class="dcard-tags">
          <span class="dtag">Pipeline</span>
          <span class="dtag">Funnel</span>
          <span class="dtag">Conversion</span>
        </div>
        <span class="dcard-cta" style="opacity:.3;">In Development</span>
      </a>

    </div>
  </div>

  <!-- ════ FOOTER ════ -->
  <div class="site-footer">
    <div class="footer-top">
      For Internal Use of Sales and Operations Team Only
      <span class="footer-dot"></span>
      All Rights Reserved
    </div>
    <div class="footer-bottom">
      Developed and Designed by Amit Ray
      <span class="footer-dot"></span>
      amitray@lawsikho.com
    </div>
  </div>

</div>
</body>
</html>
"""

html = html.replace("LAWSIKHO_LOGO_PH", LAWSIKHO_LOGO)
html = html.replace("SA_LOGO_PH",       SKILLARBITRAGE_LOGO)
html = html.replace("CALL_TIME_PH",     call_time)
html = html.replace("CALL_CNT_PH",      call_cnt)
html = html.replace("REV_TIME_PH",      rev_time)
html = html.replace("REV_CNT_PH",       rev_cnt)

components.html(html, height=1080, scrolling=True)
