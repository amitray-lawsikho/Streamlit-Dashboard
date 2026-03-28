import streamlit as st
import streamlit.components.v1 as components
from google.cloud import bigquery
from google.oauth2 import service_account

# ── Must be first Streamlit call ──
st.set_page_config(
    page_title="Analytics Hub — LawSikho",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Hide ALL Streamlit chrome via st.markdown (this part works fine) ──
st.markdown("""
<style>
footer { visibility: hidden; }
#MainMenu { display: none !important; }
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
[data-testid="stAppViewContainer"],
[data-testid="stMain"], .main { background: #080810 !important; }
section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
[data-testid="stMainViewContainer"] { padding-top: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── Replace with your actual GitHub raw URLs ──
# Repo MUST be public. Format:
# https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/assets/filename.png
LAWSIKHO_LOGO       = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/lawsikho_logo.png"
SKILLARBITRAGE_LOGO = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/skillarbitrage_logo.png"

# ── Live stats from BigQuery ──
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

# ══════════════════════════════════════════════════════════════
# FULL HTML PAGE — rendered via components.html()
# This completely bypasses Streamlit's markdown parser.
# All CSS { } are literal — no escaping needed here.
# ══════════════════════════════════════════════════════════════

html = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />
<style>

* { box-sizing: border-box; margin: 0; padding: 0; }
html, body {
    font-family: 'Outfit', sans-serif;
    background: #080810;
    color: #fff;
    min-height: 100vh;
    overflow-x: hidden;
}

/* ── Background ── */
body::before {
    content: "";
    position: fixed; inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,.04) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none; z-index: 0;
}
body::after {
    content: "";
    position: fixed; inset: 0;
    background:
        radial-gradient(ellipse 60% 40% at 20% 20%, rgba(249,115,22,.07) 0%, transparent 60%),
        radial-gradient(ellipse 50% 35% at 80% 70%, rgba(99,102,241,.06) 0%, transparent 55%),
        radial-gradient(ellipse 40% 30% at 55% 85%, rgba(239,68,68,.04) 0%, transparent 50%);
    pointer-events: none; z-index: 0;
}

/* ── Layout ── */
.hub {
    position: relative; z-index: 1;
    padding-bottom: 4rem;
}

/* ── Hero ── */
.hub-hero {
    display: flex; flex-direction: column;
    align-items: center;
    padding: 3.5rem 2rem 2rem;
    text-align: center;
}

/* Logos */
.logo-row {
    display: flex; align-items: center;
    justify-content: center;
    gap: 2rem; margin-bottom: 2.5rem;
}
.logo-wrap {
    display: flex; flex-direction: column;
    align-items: center; gap: .45rem;
}
.logo-img {
    height: 50px; width: auto;
    object-fit: contain;
    mix-blend-mode: lighten;
    filter: brightness(1.2) contrast(1.1);
    opacity: .92;
    transition: opacity .25s, transform .25s;
}
.logo-img:hover { opacity: 1; transform: scale(1.04); }
.logo-fallback {
    display: none;
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.35rem; font-weight: 600;
    color: #fff; letter-spacing: 1px;
}
.logo-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: .55rem; font-weight: 500;
    letter-spacing: 2px; text-transform: uppercase;
    color: rgba(255,255,255,.25);
}
.logo-sep {
    width: 1px; height: 48px;
    background: linear-gradient(180deg,
        transparent 0%,
        rgba(249,115,22,.45) 40%,
        rgba(249,115,22,.45) 60%,
        transparent 100%);
}

/* Headline */
.hub-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: .68rem; font-weight: 500;
    letter-spacing: 3px; text-transform: uppercase;
    color: #F97316; margin-bottom: 1rem; opacity: .85;
}
.hub-headline {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 300; line-height: 1.1;
    color: #fff; letter-spacing: -.5px;
    margin-bottom: .6rem;
}
.hub-headline strong {
    font-weight: 600;
    background: linear-gradient(120deg, #fff 0%, #F97316 60%, #EF4444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hub-tagline {
    font-size: .88rem; font-weight: 300;
    color: rgba(255,255,255,.35);
    letter-spacing: .5px; margin-bottom: 2rem;
}
.hub-rule {
    width: 48px; height: 1px;
    background: linear-gradient(90deg, transparent, #F97316, transparent);
    margin: 0 auto 3rem;
}

/* ── Stat pills ── */
.stats-strip {
    display: flex; justify-content: center;
    gap: .75rem; flex-wrap: wrap;
    padding: 0 2rem; margin-bottom: 3rem;
}
.stat-pill {
    display: flex; align-items: center; gap: .7rem;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 100px;
    padding: .6rem 1.1rem .6rem .7rem;
    transition: border-color .2s, background .2s;
}
.stat-pill:hover {
    border-color: rgba(249,115,22,.2);
    background: rgba(249,115,22,.03);
}
.stat-dot {
    width: 32px; height: 32px; border-radius: 50%;
    display: flex; align-items: center;
    justify-content: center; font-size: 1rem; flex-shrink: 0;
}
.stat-dot.call { background: rgba(249,115,22,.12); }
.stat-dot.rev  { background: rgba(52,211,153,.10); }
.stat-dot.lead { background: rgba(129,140,248,.10); }
.stat-pill-body { display: flex; flex-direction: column; gap: 1px; }
.stat-pill-label {
    font-size: .6rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
    color: rgba(255,255,255,.3);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.stat-pill-val {
    font-size: .82rem; font-weight: 500;
    color: rgba(255,255,255,.85);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.stat-pill-sub {
    font-size: .6rem; color: rgba(255,255,255,.2);
    font-family: 'JetBrains Mono', monospace;
}
.badge-live {
    font-size: .55rem; font-weight: 700; letter-spacing: 1px;
    color: #34D399; background: rgba(52,211,153,.1);
    border: 1px solid rgba(52,211,153,.15);
    border-radius: 20px; padding: 1px 7px;
    margin-left: .3rem; text-transform: uppercase;
}
.badge-wip {
    font-size: .55rem; font-weight: 700; letter-spacing: 1px;
    color: #FBBF24; background: rgba(251,191,36,.1);
    border: 1px solid rgba(251,191,36,.15);
    border-radius: 20px; padding: 1px 7px;
    margin-left: .3rem; text-transform: uppercase;
}

/* ── Section label ── */
.section-label {
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: .62rem; font-weight: 500;
    letter-spacing: 3px; text-transform: uppercase;
    color: rgba(255,255,255,.2);
    margin-bottom: 1.5rem;
}

/* ── Cards ── */
.cards-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1px;
    max-width: 1080px; margin: 0 auto;
    padding: 0 2rem 3rem;
    background: rgba(255,255,255,.05);
    border-radius: 20px; overflow: hidden;
    border: 1px solid rgba(255,255,255,.05);
}
.dash-card {
    position: relative; background: #080810;
    padding: 2.2rem 2rem;
    text-decoration: none; color: inherit;
    display: flex; flex-direction: column; gap: .8rem;
    overflow: hidden;
    transition: background .2s;
}
.dash-card:hover { background: rgba(255,255,255,.025); }
.dash-card.disabled { pointer-events: none; cursor: default; opacity: .45; }
.dash-card::before {
    content: "";
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
}
.dc-call::before { background: linear-gradient(90deg, transparent, #F97316 50%, transparent); }
.dc-rev::before  { background: linear-gradient(90deg, transparent, #34D399 50%, transparent); }
.dc-lead::before { background: linear-gradient(90deg, transparent, #818CF8 50%, transparent); }
.dash-glow {
    position: absolute; width: 200px; height: 200px;
    border-radius: 50%; top: -80px; right: -60px;
    filter: blur(70px); opacity: 0;
    pointer-events: none; transition: opacity .35s;
}
.dc-call .dash-glow  { background: #F97316; }
.dc-rev  .dash-glow  { background: #34D399; }
.dc-lead .dash-glow  { background: #818CF8; }
.dash-card:hover .dash-glow { opacity: .08; }
.dc-top {
    display: flex; align-items: flex-start;
    justify-content: space-between;
}
.dc-icon { font-size: 1.6rem; line-height: 1; }
.dc-wip-tag {
    font-size: .58rem; font-weight: 700;
    letter-spacing: 1px; text-transform: uppercase;
    color: #FBBF24; background: rgba(251,191,36,.08);
    border: 1px solid rgba(251,191,36,.15);
    border-radius: 6px; padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
}
.dc-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.55rem; font-weight: 500;
    color: #fff; line-height: 1.15; letter-spacing: -.2px;
}
.dc-desc {
    font-size: .78rem; font-weight: 300;
    color: rgba(255,255,255,.38);
    line-height: 1.7; flex: 1;
}
.dc-tags { display: flex; flex-wrap: wrap; gap: .35rem; margin-top: .2rem; }
.dc-tag {
    font-size: .58rem; font-weight: 500;
    letter-spacing: .5px; color: rgba(255,255,255,.35);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 4px; padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
}
.dc-cta {
    display: flex; align-items: center; gap: .4rem;
    font-size: .75rem; font-weight: 500;
    color: rgba(255,255,255,.25);
    margin-top: .4rem;
    transition: color .2s, gap .2s;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: .3px;
    text-decoration: none;
}
.dc-call:hover .dc-cta { color: #F97316; gap: .6rem; }
.dc-rev:hover  .dc-cta { color: #34D399; gap: .6rem; }

/* ── Footer ── */
.hub-footer {
    text-align: center; padding: 2rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: .6rem; letter-spacing: 1.5px;
    text-transform: uppercase; color: rgba(255,255,255,.12);
}

</style>
</head>
<body>

<div class="hub">

  <!-- HERO -->
  <div class="hub-hero">

    <div class="logo-row">
      <div class="logo-wrap">
        <img class="logo-img"
             src="LAWSIKHO_LOGO_PLACEHOLDER"
             alt="LawSikho"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <span class="logo-fallback">LawSikho</span>
        <span class="logo-name">LawSikho</span>
      </div>
      <div class="logo-sep"></div>
      <div class="logo-wrap">
        <img class="logo-img"
             src="SA_LOGO_PLACEHOLDER"
             alt="Skill Arbitrage"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <span class="logo-fallback">Skill Arbitrage</span>
        <span class="logo-name">Skill Arbitrage</span>
      </div>
    </div>

    <div class="hub-eyebrow">Internal Analytics</div>
    <div class="hub-headline">All your dashboards,<br><strong>in one place.</strong></div>
    <div class="hub-tagline">Real-time data across calling, revenue &amp; leads — powered by BigQuery</div>
    <div class="hub-rule"></div>

  </div>

  <!-- STAT PILLS -->
  <div class="stats-strip">
    <div class="stat-pill">
      <div class="stat-dot call">🔔</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Calling <span class="badge-live">● Live</span></span>
        <span class="stat-pill-val">CALL_TIME_PLACEHOLDER</span>
        <span class="stat-pill-sub">CALL_CNT_PLACEHOLDER records</span>
      </div>
    </div>
    <div class="stat-pill">
      <div class="stat-dot rev">💰</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Revenue <span class="badge-live">● Live</span></span>
        <span class="stat-pill-val">REV_TIME_PLACEHOLDER</span>
        <span class="stat-pill-sub">REV_CNT_PLACEHOLDER records</span>
      </div>
    </div>
    <div class="stat-pill">
      <div class="stat-dot lead">📊</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Leads <span class="badge-wip">🚧 WIP</span></span>
        <span class="stat-pill-val" style="color:rgba(255,255,255,.3);">Under Development</span>
        <span class="stat-pill-sub">Pipeline coming soon</span>
      </div>
    </div>
  </div>

  <!-- SECTION LABEL -->
  <div class="section-label">— Dashboards —</div>

  <!-- CARDS -->
  <div class="cards-row">

    <a class="dash-card dc-call" href="https://dashboard-lawsikho-call.streamlit.app/" target="_blank">
      <div class="dash-glow"></div>
      <div class="dc-top"><div class="dc-icon">🔔</div></div>
      <div class="dc-title">Calling Metrics</div>
      <div class="dc-desc">Full CDR analysis across Ozonetel, Acefone &amp; Manual calls.
        Agent-level performance, break tracking, productive hours &amp; team leaderboards.</div>
      <div class="dc-tags">
        <span class="dc-tag">Ozonetel</span>
        <span class="dc-tag">Acefone</span>
        <span class="dc-tag">Manual</span>
        <span class="dc-tag">CDR</span>
      </div>
      <span class="dc-cta">Open Dashboard &nbsp;→</span>
    </a>

    <a class="dash-card dc-rev" href="https://dashboard-lawsikho-revenue.streamlit.app/" target="_blank">
      <div class="dash-glow"></div>
      <div class="dc-top"><div class="dc-icon">💰</div></div>
      <div class="dc-title">Revenue Metrics</div>
      <div class="dc-desc">Enrollment revenue, target achievement &amp; caller-level breakdown.
        Course performance, source mix &amp; team leaderboards.</div>
      <div class="dc-tags">
        <span class="dc-tag">Enrollments</span>
        <span class="dc-tag">Targets</span>
        <span class="dc-tag">Courses</span>
        <span class="dc-tag">Teams</span>
      </div>
      <span class="dc-cta">Open Dashboard &nbsp;→</span>
    </a>

    <a class="dash-card dc-lead disabled" href="#" style="pointer-events:none;cursor:default;">
      <div class="dash-glow"></div>
      <div class="dc-top">
        <div class="dc-icon">📊</div>
        <span class="dc-wip-tag">🚧 Coming Soon</span>
      </div>
      <div class="dc-title">Lead Metrics</div>
      <div class="dc-desc">Pipeline health, lead source quality, conversion rates &amp; funnel
        drop-off analysis. Currently in development.</div>
      <div class="dc-tags">
        <span class="dc-tag">Pipeline</span>
        <span class="dc-tag">Funnel</span>
        <span class="dc-tag">Conversion</span>
      </div>
      <span class="dc-cta" style="opacity:.3;">In Development</span>
    </a>

  </div>

  <!-- FOOTER -->
  <div class="hub-footer">
    Designed by Amit Ray &nbsp;·&nbsp; amitray@lawsikho.com &nbsp;·&nbsp; Internal Use Only
  </div>

</div>

</body>
</html>
"""

# ── Inject dynamic values via simple string replace — zero risk of {} conflicts ──
html = html.replace("LAWSIKHO_LOGO_PLACEHOLDER", LAWSIKHO_LOGO)
html = html.replace("SA_LOGO_PLACEHOLDER",       SKILLARBITRAGE_LOGO)
html = html.replace("CALL_TIME_PLACEHOLDER",     call_time)
html = html.replace("CALL_CNT_PLACEHOLDER",      call_cnt)
html = html.replace("REV_TIME_PLACEHOLDER",      rev_time)
html = html.replace("REV_CNT_PLACEHOLDER",       rev_cnt)

# ── Render — bypasses Streamlit markdown parser entirely ──
components.html(html, height=920, scrolling=False)
