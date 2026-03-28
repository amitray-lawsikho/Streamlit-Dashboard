import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import base64
import os

# ─────────────────────────────────────────────
# CREDENTIALS
# ─────────────────────────────────────────────
if "gcp_service_account" in st.secrets:
    info        = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client      = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    SERVICE_ACCOUNT_FILE = "/content/drive/MyDrive/Lawsikho/credentials/bigquery_key.json"
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        client = bigquery.Client()
    else:
        st.error("Credentials not found!")

# ─────────────────────────────────────────────
# LOAD LOGOS FROM FILES  (put logos in assets/ folder in your repo)
# ─────────────────────────────────────────────
def load_b64(path: str) -> str:
    """Load a local image file and return base64 string. Returns '' if file missing."""
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return ""

LAWSIKHO_B64 = load_b64("assets/lawsikho.png")   # place your logo here
SA_B64       = load_b64("assets/sa.png")           # place your logo here

CALLING_URL = "https://dashboard-lawsikho-call.streamlit.app/"
REVENUE_URL = "https://dashboard-lawsikho-revenue.streamlit.app/"
LEADS_URL   = "#"

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="DASHBOARD HUB · LAWSIKHO",
    page_icon="🏠",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,400&family=DM+Mono:wght@400;500&family=DM+Serif+Display:ital@0;1&display=swap');

*, *::before, *::after { box-sizing:border-box; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif !important; }

footer, #MainMenu, [data-testid="stStatusWidget"],
[data-testid="stSidebarNav"], [data-testid="collapsedControl"],
.stStatusWidget { visibility:hidden; display:none !important; }

[data-testid="stMainViewContainer"] { padding-top:0 !important; }
[data-testid="stAppViewContainer"]  { background:#0C0A08 !important; }
section[data-testid="stSidebar"]    { display:none !important; }
.block-container { padding:0 2rem 4rem !important; max-width:100% !important; }

/* ── BACKGROUND GLOW ── */
[data-testid="stAppViewContainer"]::before {
    content:""; position:fixed; inset:0; z-index:0; pointer-events:none;
    background:
        radial-gradient(ellipse 70% 55% at 15% 15%, rgba(249,115,22,.16) 0%, transparent 65%),
        radial-gradient(ellipse 55% 45% at 85% 85%, rgba(239,68,68,.11) 0%, transparent 65%),
        radial-gradient(ellipse 40% 35% at 55% 45%, rgba(234,179,8,.05) 0%, transparent 70%),
        #0C0A08;
}

/* ── LOGO STRIP ── */
.logo-strip {
    display:flex; align-items:center; justify-content:center;
    gap:1.5rem; padding:2.2rem 2rem 0; width:100%;
    position:relative; z-index:10;
}

/* Box that holds each logo — no background, fully transparent */
.logo-box {
    display:flex; align-items:center; justify-content:center;
    background:transparent;
    border:1px solid rgba(255,255,255,.09);
    border-radius:14px; padding:.7rem 1.5rem;
    backdrop-filter:blur(10px);
    transition:all .3s ease;
}
.logo-box:hover {
    border-color:rgba(249,115,22,.3);
    box-shadow:0 6px 28px rgba(249,115,22,.1);
    transform:translateY(-2px);
}

/*
 * KEY FIX — make JPEG/PNG logos appear on dark background:
 *   brightness(0)  → turns all pixels black
 *   invert(1)      → turns all black pixels white
 * Result: both logos become clean white silhouettes on the dark page.
 * If you have PNG logos with transparent backgrounds, remove these filters.
 */
.logo-box img {
    height:30px; width:auto; object-fit:contain;
    filter:brightness(0) invert(1);
    opacity:.85;
    transition:opacity .3s;
}
.logo-box:hover img { opacity:1; }

.logo-sep {
    width:1px; height:28px;
    background:linear-gradient(180deg,transparent,rgba(249,115,22,.35),transparent);
}
.logo-byline {
    font-size:.68rem; font-weight:700; letter-spacing:1.2px;
    text-transform:uppercase; color:rgba(255,255,255,.22);
    font-family:'DM Mono',monospace;
}

/* ── HERO ── */
.hero-wrap {
    position:relative; z-index:10;
    text-align:center; padding:2rem 1rem 0;
    max-width:680px; margin:0 auto;
    animation:fade-up .7s ease both;
}
@keyframes fade-up {
    from{opacity:0;transform:translateY(20px)}
    to  {opacity:1;transform:translateY(0)}
}
.hero-pill {
    display:inline-flex; align-items:center; gap:6px;
    background:rgba(249,115,22,.09);
    border:1px solid rgba(249,115,22,.18);
    border-radius:999px; padding:4px 14px;
    font-size:.68rem; font-weight:700;
    letter-spacing:1.4px; text-transform:uppercase;
    color:#F97316; font-family:'DM Mono',monospace;
    margin-bottom:1.2rem;
}
.hero-dot {
    width:5px; height:5px; background:#F97316; border-radius:50%;
    animation:pdot 1.8s ease-in-out infinite;
}
@keyframes pdot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(1.6)}}

.hero-title {
    font-family:'DM Serif Display',serif;
    font-size:clamp(2.2rem,4.5vw,3.4rem);
    font-weight:400; color:#FFFFFF;
    line-height:1.1; margin-bottom:.7rem; letter-spacing:-.4px;
}
.hero-title em {
    font-style:italic;
    background:linear-gradient(135deg,#F97316 0%,#EF4444 50%,#FBBF24 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text;
}
.hero-sub {
    font-size:.92rem; color:rgba(255,255,255,.38);
    font-weight:400; line-height:1.7;
    max-width:420px; margin:0 auto 2.5rem;
}

/* ── APP CARDS ── */
.cards-row {
    position:relative; z-index:10;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(270px,1fr));
    gap:1.25rem;
    max-width:900px; margin:0 auto;
    padding:0 1rem;
    animation:fade-up .7s .15s ease both;
}
.app-card {
    position:relative;
    background:rgba(255,255,255,.03);
    border:1px solid rgba(255,255,255,.08);
    border-radius:18px; padding:1.75rem;
    text-decoration:none !important; display:block;
    overflow:hidden;
    transition:all .32s cubic-bezier(.4,0,.2,1);
}
.app-card::after {
    content:""; position:absolute; inset:0; border-radius:18px;
    opacity:0; transition:opacity .32s;
}
.app-card:hover { transform:translateY(-5px); }
.app-card:hover::after { opacity:1; }

.card-call::after  { background:linear-gradient(135deg,rgba(249,115,22,.07),rgba(239,68,68,.05)); }
.card-call:hover   { box-shadow:0 18px 50px rgba(249,115,22,.16),0 0 0 1px rgba(249,115,22,.22); border-color:rgba(249,115,22,.28); }
.card-rev::after   { background:linear-gradient(135deg,rgba(16,185,129,.07),rgba(6,78,59,.05)); }
.card-rev:hover    { box-shadow:0 18px 50px rgba(16,185,129,.14),0 0 0 1px rgba(16,185,129,.22); border-color:rgba(16,185,129,.28); }
.card-leads::after { background:linear-gradient(135deg,rgba(139,92,246,.07),rgba(79,70,229,.05)); }
.card-leads:hover  { box-shadow:0 18px 50px rgba(139,92,246,.12),0 0 0 1px rgba(139,92,246,.2); border-color:rgba(139,92,246,.25); }

.card-bg-glow {
    position:absolute; top:-50px; right:-50px;
    width:130px; height:130px; border-radius:50%;
    opacity:.14; pointer-events:none; transition:opacity .32s;
}
.app-card:hover .card-bg-glow { opacity:.28; }
.card-call  .card-bg-glow { background:radial-gradient(circle,#F97316,transparent 70%); }
.card-rev   .card-bg-glow { background:radial-gradient(circle,#10B981,transparent 70%); }
.card-leads .card-bg-glow { background:radial-gradient(circle,#8B5CF6,transparent 70%); }

.card-icon {
    width:46px; height:46px; border-radius:12px;
    display:flex; align-items:center; justify-content:center;
    font-size:1.3rem; margin-bottom:1.1rem;
    position:relative; z-index:1;
}
.card-call  .card-icon { background:rgba(249,115,22,.14); border:1px solid rgba(249,115,22,.2); }
.card-rev   .card-icon { background:rgba(16,185,129,.14);  border:1px solid rgba(16,185,129,.2); }
.card-leads .card-icon { background:rgba(139,92,246,.14);  border:1px solid rgba(139,92,246,.2); }

.card-title {
    font-size:1.05rem; font-weight:700; color:#fff;
    margin-bottom:.35rem; position:relative; z-index:1; letter-spacing:-.15px;
}
.card-desc {
    font-size:.78rem; color:rgba(255,255,255,.38);
    line-height:1.65; margin-bottom:1.2rem; position:relative; z-index:1;
}
.card-chips {
    display:flex; flex-wrap:wrap; gap:.35rem;
    margin-bottom:1.2rem; position:relative; z-index:1;
}
.chip {
    font-size:.6rem; font-weight:700; letter-spacing:.6px;
    text-transform:uppercase; padding:2px 7px; border-radius:5px;
    font-family:'DM Mono',monospace;
}
.card-call  .chip { background:rgba(249,115,22,.12); color:#FB923C; border:1px solid rgba(249,115,22,.15); }
.card-rev   .chip { background:rgba(16,185,129,.12);  color:#34D399; border:1px solid rgba(16,185,129,.15); }
.card-leads .chip { background:rgba(139,92,246,.12);  color:#A78BFA; border:1px solid rgba(139,92,246,.15); }

.card-link {
    display:inline-flex; align-items:center; gap:5px;
    font-size:.75rem; font-weight:700; letter-spacing:.3px;
    position:relative; z-index:1; transition:gap .22s;
}
.card-call  .card-link { color:#F97316; }
.card-rev   .card-link { color:#10B981; }
.card-leads .card-link { color:#8B5CF6; }
.app-card:hover .card-link { gap:9px; }

.wip-badge {
    display:inline-flex; align-items:center; gap:4px;
    background:rgba(139,92,246,.1); border:1px solid rgba(139,92,246,.2);
    border-radius:999px; padding:3px 9px;
    font-size:.62rem; font-weight:700; letter-spacing:.6px;
    text-transform:uppercase; color:#A78BFA;
    font-family:'DM Mono',monospace; margin-bottom:.8rem;
}

/* ── DIVIDER ── */
.section-div {
    width:100%; max-width:900px; height:1px;
    background:linear-gradient(90deg,transparent,rgba(255,255,255,.07),transparent);
    margin:2rem auto 0; position:relative; z-index:10;
}

/* ── STATUS CARDS ── */
.status-row {
    position:relative; z-index:10;
    display:grid;
    grid-template-columns:repeat(auto-fit,minmax(240px,1fr));
    gap:1rem; max-width:900px; margin:1.5rem auto 0; padding:0 1rem;
    animation:fade-up .7s .3s ease both;
}
.stat-card {
    background:rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.07);
    border-radius:13px; padding:.9rem 1.1rem;
    display:flex; align-items:center; gap:.9rem;
    transition:all .28s ease;
}
.stat-card:hover {
    background:rgba(255,255,255,.04);
    border-color:rgba(255,255,255,.11);
}
.stat-icon {
    width:34px; height:34px; border-radius:9px;
    display:flex; align-items:center; justify-content:center;
    font-size:.95rem; flex-shrink:0;
}
.stat-icon.call { background:rgba(249,115,22,.12); }
.stat-icon.rev  { background:rgba(16,185,129,.12);  }
.stat-icon.lead { background:rgba(139,92,246,.12);  }

.stat-body { flex:1; min-width:0; }
.stat-label {
    font-size:.6rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.8px; color:rgba(255,255,255,.28);
    font-family:'DM Mono',monospace; margin-bottom:.15rem;
}
.stat-val {
    font-size:.8rem; font-weight:600; color:rgba(255,255,255,.7);
    font-family:'DM Mono',monospace;
    white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.live-pill {
    flex-shrink:0; display:inline-flex; align-items:center; gap:3px;
    font-size:.58rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.5px; padding:2px 7px; border-radius:999px;
    font-family:'DM Mono',monospace;
    background:rgba(52,211,153,.1); color:#34D399;
    border:1px solid rgba(52,211,153,.18);
}
.wip-pill {
    flex-shrink:0; display:inline-flex; align-items:center; gap:3px;
    font-size:.58rem; font-weight:700; text-transform:uppercase;
    letter-spacing:.5px; padding:2px 7px; border-radius:999px;
    font-family:'DM Mono',monospace;
    background:rgba(139,92,246,.1); color:#A78BFA;
    border:1px solid rgba(139,92,246,.18);
}

/* ── FOOTER ── */
.hfooter {
    position:relative; z-index:10; text-align:center;
    padding:2.5rem 1rem 2rem;
    font-size:.68rem; color:rgba(255,255,255,.18);
    font-family:'DM Mono',monospace; letter-spacing:.5px;
    animation:fade-up .7s .45s ease both;
}
.hfooter a { color:#F97316; text-decoration:none; }
.hfooter a:hover { text-decoration:underline; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# DATA — Last update times
# ─────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_calling_update():
    q = """
    WITH c AS (
        SELECT updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT StartTime AS updated_at, updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
    )
    SELECT updated_at_ampm FROM c WHERE updated_at IS NOT NULL ORDER BY updated_at DESC LIMIT 1
    """
    try:
        r = client.query(q).to_dataframe()
        return str(r['updated_at_ampm'].iloc[0]) if not r.empty else "N/A"
    except: return "N/A"

@st.cache_data(ttl=120, show_spinner=False)
def get_revenue_update():
    q = """
    SELECT updated_at_ampm FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet`
    WHERE updated_at IS NOT NULL ORDER BY updated_at DESC LIMIT 1
    """
    try:
        r = client.query(q).to_dataframe()
        return str(r['updated_at_ampm'].iloc[0]) if not r.empty else "N/A"
    except: return "N/A"

@st.cache_data(ttl=120, show_spinner=False)
def get_calling_count():
    q = """
    SELECT COUNT(*) AS n FROM (
        SELECT call_id FROM `studious-apex-488820-c3.crm_dashboard.acefone_calls`
        UNION ALL
        SELECT CallID FROM `studious-apex-488820-c3.crm_dashboard.ozonetel_calls`
    )"""
    try:
        r = client.query(q).to_dataframe()
        return f"{int(r['n'].iloc[0]):,} records"
    except: return "—"

@st.cache_data(ttl=120, show_spinner=False)
def get_revenue_count():
    q = "SELECT COUNT(*) AS n FROM `studious-apex-488820-c3.crm_dashboard.revenue_sheet` WHERE Fee_paid > 0"
    try:
        r = client.query(q).to_dataframe()
        return f"{int(r['n'].iloc[0]):,} records"
    except: return "—"

calling_update = get_calling_update()
revenue_update = get_revenue_update()
calling_count  = get_calling_count()
revenue_count  = get_revenue_count()


# ─────────────────────────────────────────────
# RENDER — LOGO STRIP
# Build img tags only if logos loaded successfully
# ─────────────────────────────────────────────

ls_img = (f'<img src="data:image/png;base64,{LAWSIKHO_B64}" alt="LawSikho">'
          if LAWSIKHO_B64 else
          '<span style="color:rgba(255,255,255,.6);font-size:.85rem;font-weight:700;letter-spacing:1px;">LAWSIKHO</span>')

sa_img = (f'<img src="data:image/png;base64,{SA_B64}" alt="Skill Arbitrage">'
          if SA_B64 else
          '<span style="color:rgba(255,255,255,.6);font-size:.85rem;font-weight:700;letter-spacing:1px;">SKILL ARBITRAGE</span>')

st.markdown(f"""
<div class="logo-strip">
    <div class="logo-box ls">{ls_img}</div>
    <div class="logo-sep"></div>
    <span class="logo-byline">&amp;</span>
    <div class="logo-sep"></div>
    <div class="logo-box sa">{sa_img}</div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RENDER — HERO
# ─────────────────────────────────────────────

st.markdown("""
<div class="hero-wrap">
    <div class="hero-pill"><span class="hero-dot"></span>Internal Analytics Hub</div>
    <div class="hero-title">One Place for<br><em>All Your Dashboards</em></div>
    <div class="hero-sub">
        Live performance dashboards for Calling, Revenue &amp; Leads —<br>
        built for LawSikho &amp; Skill Arbitrage ops teams.
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RENDER — APP CARDS
# ─────────────────────────────────────────────

st.markdown(f"""
<div class="cards-row">

    <a class="app-card card-call" href="{CALLING_URL}" target="_blank">
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

    <a class="app-card card-rev" href="{REVENUE_URL}" target="_blank">
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

    <a class="app-card card-leads" href="{LEADS_URL}" style="pointer-events:none;cursor:default;">
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
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RENDER — DIVIDER + STATUS CARDS
# ─────────────────────────────────────────────

st.markdown('<div class="section-div"></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="status-row">

    <div class="stat-card">
        <div class="stat-icon call">🔔</div>
        <div class="stat-body">
            <div class="stat-label">Calling Data — Last Updated</div>
            <div class="stat-val">{calling_update}</div>
            <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.28);margin-top:.1rem;">{calling_count}</div>
        </div>
        <span class="live-pill">● Live</span>
    </div>

    <div class="stat-card">
        <div class="stat-icon rev">💰</div>
        <div class="stat-body">
            <div class="stat-label">Revenue Data — Last Updated</div>
            <div class="stat-val">{revenue_update}</div>
            <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.28);margin-top:.1rem;">{revenue_count}</div>
        </div>
        <span class="live-pill">● Live</span>
    </div>

    <div class="stat-card">
        <div class="stat-icon lead">📊</div>
        <div class="stat-body">
            <div class="stat-label">Lead Data — Status</div>
            <div class="stat-val" style="color:rgba(255,255,255,.35);">Under Development</div>
            <div class="stat-val" style="font-size:.68rem;color:rgba(255,255,255,.2);margin-top:.1rem;">Pipeline coming soon</div>
        </div>
        <span class="wip-pill">🚧 WIP</span>
    </div>

</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RENDER — FOOTER
# ─────────────────────────────────────────────

st.markdown("""
<div class="hfooter">
    DESIGNED BY <a href="mailto:amitray@lawsikho.com">AMIT RAY</a>
    &nbsp;·&nbsp; LawSikho &amp; Skill Arbitrage Internal Tools &nbsp;·&nbsp; All rights reserved
</div>
""", unsafe_allow_html=True)
