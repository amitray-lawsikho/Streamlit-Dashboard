import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

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
# LOGO URLS
# !! Replace YOUR_USERNAME and YOUR_REPO with actual values !!
# Example: https://raw.githubusercontent.com/amitray-lawsikho/analytics-hub/main/assets/lawsikho_logo.png
# Make sure the repo is PUBLIC or the file is accessible
# ─────────────────────────────────────────────
LAWSIKHO_LOGO_URL       = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/lawsikho_logo.png"
SKILLARBITRAGE_LOGO_URL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/assets/skillarbitrage_logo.png"

# ─────────────────────────────────────────────
# LIVE STATS — fixed revenue query to use revenue_sheet
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

        # ── Calling data ──
        call_df = client.query("""
            SELECT updated_at_ampm FROM (
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                UNION ALL
                SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
            ) WHERE updated_at_ampm IS NOT NULL
            ORDER BY 1 DESC LIMIT 1
        """).to_dataframe()
        call_time = str(call_df["updated_at_ampm"].iloc[0]) if not call_df.empty else "N/A"

        call_cnt_df = client.query("""
            SELECT SUM(c) as total FROM (
                SELECT COUNT(*) as c FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
                UNION ALL
                SELECT COUNT(*) as c FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
            )
        """).to_dataframe()
        call_cnt = f"{int(call_cnt_df['total'].iloc[0]):,}" if not call_cnt_df.empty else "—"

        # ── Revenue data — fixed: uses revenue_sheet + MAX(updated_at_ampm) ──
        try:
            rev_df = client.query("""
                SELECT
                    MAX(updated_at_ampm) AS last_updated,
                    COUNT(*) AS cnt
                FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet`
            """).to_dataframe()
            rev_time = str(rev_df["last_updated"].iloc[0]) if not rev_df.empty and rev_df["last_updated"].iloc[0] else "N/A"
            rev_cnt  = f"{int(rev_df['cnt'].iloc[0]):,}" if not rev_df.empty else "0"
        except Exception as e:
            rev_time = "N/A"
            rev_cnt  = "0"

        return call_time, call_cnt, rev_time, rev_cnt

    except Exception:
        return "N/A", "—", "N/A", "—"

call_time, call_cnt, rev_time, rev_cnt = get_live_stats()


# ─────────────────────────────────────────────
# CSS — completely redesigned, elegant & editorial
# Plain string — NO f-prefix
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body, [class*="css"] { font-family: 'Outfit', sans-serif !important; }

/* ── Hide Streamlit chrome ── */
footer { visibility: hidden; }
#MainMenu { display: none !important; }
[data-testid="stStatusWidget"]            { display: none !important; }
[data-testid="collapsedControl"]          { display: none !important; }
[data-testid="stSidebarCollapsedControl"] { display: none !important; }
header[data-testid="stHeader"]            { background: transparent !important; }

/* ── Page background ── */
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.main { background: #080810 !important; }

section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
[data-testid="stMainViewContainer"] { padding-top: 0 !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ══════════════════════════════════
   HUB WRAPPER
══════════════════════════════════ */
.hub {
    margin-top: 58px;
    min-height: calc(100vh - 58px);
    background: #080810;
    position: relative;
    overflow: hidden;
}

/* Dot grid texture */
.hub::before {
    content: "";
    position: fixed;
    inset: 0;
    background-image: radial-gradient(circle, rgba(255,255,255,.04) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}

/* Aurora glow blobs */
.hub::after {
    content: "";
    position: fixed;
    inset: 0;
    background:
        radial-gradient(ellipse 60% 40% at 20% 20%, rgba(249,115,22,.06) 0%, transparent 60%),
        radial-gradient(ellipse 50% 35% at 80% 70%, rgba(99,102,241,.05) 0%, transparent 55%),
        radial-gradient(ellipse 40% 30% at 55% 85%, rgba(239,68,68,.04) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* ══════════════════════════════════
   HERO SECTION
══════════════════════════════════ */
.hub-hero {
    position: relative;
    z-index: 2;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 4rem 2rem 3rem;
    text-align: center;
}

/* Logo row */
.logo-row {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 2rem;
    margin-bottom: 2.5rem;
}
.logo-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: .5rem;
}
.logo-img {
    height: 48px;
    width: auto;
    object-fit: contain;
    mix-blend-mode: lighten;
    filter: brightness(1.2) contrast(1.1) saturate(0.9);
    opacity: .9;
    transition: opacity .25s, transform .25s;
}
.logo-img:hover { opacity: 1; transform: scale(1.04); }
.logo-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: .55rem;
    font-weight: 500;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,.25);
}
.logo-sep {
    width: 1px;
    height: 48px;
    background: linear-gradient(180deg,
        transparent 0%,
        rgba(249,115,22,.4) 40%,
        rgba(249,115,22,.4) 60%,
        transparent 100%);
}

/* Eyebrow label */
.hub-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: .68rem;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #F97316;
    margin-bottom: 1rem;
    opacity: .85;
}

/* Main headline */
.hub-headline {
    font-family: 'Cormorant Garamond', serif;
    font-size: clamp(2.8rem, 6vw, 5rem);
    font-weight: 300;
    line-height: 1.1;
    color: #FFFFFF;
    letter-spacing: -.5px;
    margin-bottom: .6rem;
}
.hub-headline strong {
    font-weight: 600;
    background: linear-gradient(120deg, #FFFFFF 0%, #F97316 60%, #EF4444 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Tagline */
.hub-tagline {
    font-size: .88rem;
    font-weight: 300;
    color: rgba(255,255,255,.35);
    letter-spacing: .5px;
    margin-bottom: 2.5rem;
    font-family: 'Outfit', sans-serif;
}

/* Thin orange rule */
.hub-rule {
    width: 48px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #F97316, transparent);
    margin: 0 auto 3rem;
}

/* ══════════════════════════════════
   STAT PILLS ROW
══════════════════════════════════ */
.stats-strip {
    position: relative;
    z-index: 2;
    display: flex;
    justify-content: center;
    gap: .75rem;
    flex-wrap: wrap;
    padding: 0 2rem;
    margin-bottom: 3.5rem;
}
.stat-pill {
    display: flex;
    align-items: center;
    gap: .7rem;
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 100px;
    padding: .6rem 1.1rem .6rem .7rem;
    backdrop-filter: blur(10px);
    transition: border-color .2s, background .2s;
    min-width: 0;
}
.stat-pill:hover {
    border-color: rgba(249,115,22,.2);
    background: rgba(249,115,22,.03);
}
.stat-dot {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem;
    flex-shrink: 0;
}
.stat-dot.call { background: rgba(249,115,22,.12); }
.stat-dot.rev  { background: rgba(52,211,153,.10); }
.stat-dot.lead { background: rgba(129,140,248,.10); }
.stat-pill-body { display: flex; flex-direction: column; gap: 1px; }
.stat-pill-label {
    font-size: .6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: rgba(255,255,255,.3);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.stat-pill-val {
    font-size: .82rem;
    font-weight: 500;
    color: rgba(255,255,255,.85);
    font-family: 'JetBrains Mono', monospace;
    white-space: nowrap;
}
.stat-pill-sub {
    font-size: .6rem;
    color: rgba(255,255,255,.2);
    font-family: 'JetBrains Mono', monospace;
}
.badge-live {
    font-size: .55rem; font-weight: 700; letter-spacing: 1px;
    color: #34D399;
    background: rgba(52,211,153,.1);
    border: 1px solid rgba(52,211,153,.15);
    border-radius: 20px;
    padding: 1px 7px;
    margin-left: .3rem;
    text-transform: uppercase;
}
.badge-wip {
    font-size: .55rem; font-weight: 700; letter-spacing: 1px;
    color: #FBBF24;
    background: rgba(251,191,36,.1);
    border: 1px solid rgba(251,191,36,.15);
    border-radius: 20px;
    padding: 1px 7px;
    margin-left: .3rem;
    text-transform: uppercase;
}

/* ══════════════════════════════════
   DASHBOARD CARDS
══════════════════════════════════ */
.section-label {
    position: relative;
    z-index: 2;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: .62rem;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: rgba(255,255,255,.2);
    margin-bottom: 1.5rem;
}

.cards-row {
    position: relative;
    z-index: 2;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1px;
    max-width: 1080px;
    margin: 0 auto;
    padding: 0 2rem 4rem;
    /* 1px gaps with border creates a grid-line effect */
    background: rgba(255,255,255,.05);
    border-radius: 20px;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.05);
}

.dash-card {
    position: relative;
    background: #080810;
    padding: 2.2rem 2rem;
    text-decoration: none !important;
    display: flex;
    flex-direction: column;
    gap: .8rem;
    overflow: hidden;
    transition: background .2s;
}
.dash-card:hover { background: rgba(255,255,255,.025); text-decoration: none !important; }
.dash-card.disabled { pointer-events: none; cursor: default; opacity: .45; }

/* Accent bar at top of each card */
.dash-card::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
}
.dash-card.dc-call::before { background: linear-gradient(90deg, transparent, #F97316 50%, transparent); }
.dash-card.dc-rev::before  { background: linear-gradient(90deg, transparent, #34D399 50%, transparent); }
.dash-card.dc-lead::before { background: linear-gradient(90deg, transparent, #818CF8 50%, transparent); }

/* Glow on hover */
.dash-glow {
    position: absolute;
    width: 200px; height: 200px;
    border-radius: 50%;
    top: -80px; right: -60px;
    filter: blur(70px);
    opacity: 0;
    pointer-events: none;
    transition: opacity .35s;
}
.dc-call .dash-glow  { background: #F97316; }
.dc-rev  .dash-glow  { background: #34D399; }
.dc-lead .dash-glow  { background: #818CF8; }
.dash-card:hover .dash-glow { opacity: .08; }

/* Card top row */
.dc-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
}
.dc-icon {
    font-size: 1.6rem;
    line-height: 1;
}
.dc-wip-tag {
    font-size: .58rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #FBBF24;
    background: rgba(251,191,36,.08);
    border: 1px solid rgba(251,191,36,.15);
    border-radius: 6px;
    padding: 3px 8px;
    font-family: 'JetBrains Mono', monospace;
}

/* Card text */
.dc-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.55rem;
    font-weight: 500;
    color: #FFFFFF;
    line-height: 1.15;
    letter-spacing: -.2px;
}
.dc-desc {
    font-size: .78rem;
    font-weight: 300;
    color: rgba(255,255,255,.38);
    line-height: 1.7;
    flex: 1;
}

/* Tags */
.dc-tags {
    display: flex;
    flex-wrap: wrap;
    gap: .35rem;
    margin-top: .2rem;
}
.dc-tag {
    font-size: .58rem;
    font-weight: 500;
    letter-spacing: .5px;
    color: rgba(255,255,255,.35);
    border: 1px solid rgba(255,255,255,.08);
    border-radius: 4px;
    padding: 2px 8px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: uppercase;
}

/* CTA link */
.dc-cta {
    display: flex;
    align-items: center;
    gap: .4rem;
    font-size: .75rem;
    font-weight: 500;
    color: rgba(255,255,255,.25);
    margin-top: .4rem;
    transition: color .2s, gap .2s;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: .3px;
}
.dc-call:hover .dc-cta { color: #F97316; gap: .6rem; }
.dc-rev:hover  .dc-cta { color: #34D399; gap: .6rem; }

/* ══════════════════════════════════
   FOOTER
══════════════════════════════════ */
.hub-footer {
    position: relative;
    z-index: 2;
    text-align: center;
    padding: 2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: .6rem;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(255,255,255,.12);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HTML RENDER — f-string for live values
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="hub">

  <!-- ══ HERO ══ -->
  <div class="hub-hero">

    <!-- Logos -->
    <div class="logo-row">
      <div class="logo-wrap">
        <img class="logo-img"
             src="{LAWSIKHO_LOGO_URL}"
             alt="LawSikho"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <span style="display:none;font-family:'Cormorant Garamond',serif;font-size:1.4rem;font-weight:600;color:#fff;letter-spacing:1px;">LawSikho</span>
        <span class="logo-name">LawSikho</span>
      </div>
      <div class="logo-sep"></div>
      <div class="logo-wrap">
        <img class="logo-img"
             src="{SKILLARBITRAGE_LOGO_URL}"
             alt="Skill Arbitrage"
             onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <span style="display:none;font-family:'Cormorant Garamond',serif;font-size:1.4rem;font-weight:600;color:#fff;letter-spacing:1px;">Skill Arbitrage</span>
        <span class="logo-name">Skill Arbitrage</span>
      </div>
    </div>

    <div class="hub-eyebrow">Internal Analytics</div>

    <div class="hub-headline">
      All your dashboards,<br><strong>in one place.</strong>
    </div>

    <div class="hub-tagline">
      Real-time data across calling, revenue &amp; leads — powered by BigQuery
    </div>

    <div class="hub-rule"></div>

  </div>

  <!-- ══ STAT PILLS ══ -->
  <div class="stats-strip">

    <div class="stat-pill">
      <div class="stat-dot call">🔔</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Calling &nbsp;<span class="badge-live">● Live</span></span>
        <span class="stat-pill-val">{call_time}</span>
        <span class="stat-pill-sub">{call_cnt} records</span>
      </div>
    </div>

    <div class="stat-pill">
      <div class="stat-dot rev">💰</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Revenue &nbsp;<span class="badge-live">● Live</span></span>
        <span class="stat-pill-val">{rev_time}</span>
        <span class="stat-pill-sub">{rev_cnt} records</span>
      </div>
    </div>

    <div class="stat-pill">
      <div class="stat-dot lead">📊</div>
      <div class="stat-pill-body">
        <span class="stat-pill-label">Leads &nbsp;<span class="badge-wip">🚧 WIP</span></span>
        <span class="stat-pill-val" style="color:rgba(255,255,255,.3);">Under Development</span>
        <span class="stat-pill-sub">Pipeline coming soon</span>
      </div>
    </div>

  </div>

  <!-- ══ SECTION LABEL ══ -->
  <div class="section-label">— Dashboards —</div>

  <!-- ══ CARDS ══ -->
  <div class="cards-row">

    <a class="dash-card dc-call"
       href="https://dashboard-lawsikho-call.streamlit.app/" target="_blank">
      <div class="dash-glow"></div>
      <div class="dc-top">
        <div class="dc-icon">🔔</div>
      </div>
      <div class="dc-title">Calling Metrics</div>
      <div class="dc-desc">
        Full CDR analysis across Ozonetel, Acefone &amp; Manual calls.
        Agent-level performance, break tracking, productive hours &amp; team leaderboards.
      </div>
      <div class="dc-tags">
        <span class="dc-tag">Ozonetel</span>
        <span class="dc-tag">Acefone</span>
        <span class="dc-tag">Manual</span>
        <span class="dc-tag">CDR</span>
      </div>
      <div class="dc-cta">Open Dashboard &nbsp;→</div>
    </a>

    <a class="dash-card dc-rev"
       href="https://dashboard-lawsikho-revenue.streamlit.app/" target="_blank">
      <div class="dash-glow"></div>
      <div class="dc-top">
        <div class="dc-icon">💰</div>
      </div>
      <div class="dc-title">Revenue Metrics</div>
      <div class="dc-desc">
        Enrollment revenue, target achievement &amp; caller-level breakdown.
        Course performance, source mix &amp; team leaderboards.
      </div>
      <div class="dc-tags">
        <span class="dc-tag">Enrollments</span>
        <span class="dc-tag">Targets</span>
        <span class="dc-tag">Courses</span>
        <span class="dc-tag">Teams</span>
      </div>
      <div class="dc-cta">Open Dashboard &nbsp;→</div>
    </a>

    <a class="dash-card dc-lead disabled" href="#">
      <div class="dash-glow"></div>
      <div class="dc-top">
        <div class="dc-icon">📊</div>
        <span class="dc-wip-tag">🚧 Coming Soon</span>
      </div>
      <div class="dc-title">Lead Metrics</div>
      <div class="dc-desc">
        Pipeline health, lead source quality, conversion rates &amp; funnel drop-off analysis.
        Currently in development.
      </div>
      <div class="dc-tags">
        <span class="dc-tag">Pipeline</span>
        <span class="dc-tag">Funnel</span>
        <span class="dc-tag">Conversion</span>
      </div>
      <div class="dc-cta" style="opacity:.3;">In Development</div>
    </a>

  </div>

  <!-- ══ FOOTER ══ -->
  <div class="hub-footer">
    Designed by Amit Ray &nbsp;·&nbsp; amitray@lawsikho.com &nbsp;·&nbsp; Internal Use Only
  </div>

</div>
""", unsafe_allow_html=True)
