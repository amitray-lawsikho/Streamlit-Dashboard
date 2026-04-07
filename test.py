import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import date, timedelta
import os
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable, Flowable
)
from reportlab.lib.enums import TA_CENTER

# ─────────────────────────────────────────────
# 1. CREDENTIALS
# ─────────────────────────────────────────────
if "gcp_service_account" in st.secrets:
    info        = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client      = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    SAF = "C:\\Users\\AMIT GAMING\\.gemini\\antigravity\\secrets\\bigquery_key.json"
    if os.path.exists(SAF):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SAF
    client = bigquery.Client()

# ─────────────────────────────────────────────
# 2. PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="LEAD METRICS",
    initial_sidebar_state="expanded",
    page_icon="📊"
)

# ─────────────────────────────────────────────
# 3. CONSTANTS
# ─────────────────────────────────────────────
CSV_URL     = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=0&single=true&output=csv"
LEADS_TABLE = "studious-apex-488820-c3.crm_dashboard.lsq_leads"

STAGE_MAP = {
    "FRESH"            : ["New Lead", "Re-enquired Lead", "Opportunity Created"],
    "DNP"              : ["Call Not Picking Up", "Call Not Connected"],
    "CBL"              : ["Call Back Later"],
    "FLW-UP"           : ["Follow Up For Closure"],
    "COUNSELLED"       : ["Counselled lead"],
    "DISCOVERY"        : ["Discovery Call Done"],
    "ROADMAP"          : ["Roadmap Done"],
    "MBL"              : ["May buy later"],
    "ACTUALLY-ENROLLED": ["Actually Enrolled"],
    "INVALID/NTINTRSTD": ["Irrelevant lead", "Not Interested", "Invalid"],
    "BOOKING-RCVD"     : ["Booking fees received"],
    "LOAN-PNDG"        : ["Loan pending"],
    "COLL-DNE"         : ["Collections done"],
    "PRE-SALES"        : ["Pre-Sales Registrations"],
    "COURSE ENROLLED"  : ["Course Enrolled"],
}
ALL_STAGE_COLS = list(STAGE_MAP.keys())

BREACH_MAP = {
    "CBL"       : ["Call Back Later"],
    "FLW-UP"    : ["Follow Up For Closure"],
    "COUNSELLED": ["Counselled lead"],
    "DISCOVERY" : ["Discovery Call Done"],
    "ROADMAP"   : ["Roadmap Done"],
}
BREACH_COLS   = list(BREACH_MAP.keys())
BREACH_STAGES = [s for v in BREACH_MAP.values() for s in v]

LD_COLS = ["Call Not Picking Up", "Call Not Connected"]

# ─────────────────────────────────────────────
# 4. CSS  (light-blue → deep-blue theme)
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --accent-primary  : #3B82F6;
    --accent-secondary: #60A5FA;
    --radius-sm: 8px; --radius-md: 12px; --radius-lg: 16px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,.08);
    --shadow-md: 0 4px 16px rgba(0,0,0,.10);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.14);
    --transition: all 0.22s cubic-bezier(.4,0,.2,1);
}

[data-testid="stAppViewContainer"]:not([class*="dark"]) {
    --bg-base: #EFF6FF; --bg-surface: #FFFFFF; --bg-muted: #DBEAFE;
    --border: rgba(59,130,246,.12); --text-primary: #1E3A5F;
    --text-muted: #6B7280; --metric-bg: #FFFFFF;
}
@media (prefers-color-scheme: dark) {
    :root {
        --bg-base: #05080F; --bg-surface: #0A1628; --bg-elevated: #0F1F3D;
        --bg-muted: #0C1830; --border: rgba(59,130,246,.10);
        --text-primary: #EFF6FF; --text-muted: #93C5FD; --metric-bg: #0F1F3D;
    }
}
[data-theme="dark"] {
    --bg-base: #05080F !important; --bg-surface: #0A1628 !important;
    --bg-muted: #0C1830 !important; --border: rgba(59,130,246,.10) !important;
    --text-primary: #EFF6FF !important; --text-muted: #93C5FD !important;
    --metric-bg: #0F1F3D !important;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
footer { visibility: hidden; }
[data-testid="stStatusWidget"] { display: none !important; }
[data-testid="stSidebar"] { border-right: 1px solid var(--border); }

.ld-header {
    background: linear-gradient(135deg, #0c1445 0%, #1e3a8a 45%, #1e40af 100%);
    border-radius: var(--radius-lg); padding: 1.5rem 2rem 1.2rem;
    margin-bottom: 1.2rem; box-shadow: var(--shadow-lg);
    position: relative; overflow: hidden;
}
.ld-header::before {
    content: ""; position: absolute; top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(96,165,250,.2) 0%, transparent 70%);
    border-radius: 50%;
}
.ld-title    { font-size: 1.65rem; font-weight: 700; color: #FFF; letter-spacing: .5px; margin: 0 0 .25rem; }
.ld-subtitle { font-size: .82rem; color: rgba(255,255,255,.6); font-family:'DM Mono',monospace; margin: 0; }
.ld-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18);
    border-radius: 20px; padding: 3px 10px; font-size: .73rem;
    color: rgba(255,255,255,.9); font-family:'DM Mono',monospace;
}
.ld-pulse {
    width: 6px; height: 6px; background: #93C5FD; border-radius: 50%;
    display: inline-block; animation: ld-blink 1.8s ease-in-out infinite;
}
@keyframes ld-blink {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.5; transform:scale(1.4); }
}

.metric-card {
    background: var(--metric-bg,#fff); border: 1px solid var(--border);
    border-radius: var(--radius-md); padding: .9rem 1rem;
    transition: var(--transition); box-shadow: var(--shadow-sm);
    position: relative; overflow: hidden; text-align: center;
}
.metric-card::before {
    content: ""; position: absolute; top: 0; left: 0;
    width: 100%; height: 3px; background: linear-gradient(90deg,#3B82F6,#60A5FA);
    opacity: 0; transition: opacity .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.metric-card:hover::before { opacity: 1; }
.metric-label { font-size:.68rem; font-weight:600; text-transform:uppercase; letter-spacing:.8px; color:var(--text-muted,#6B7280); margin:0 0 .3rem; }
.metric-value { font-size:1.45rem; font-weight:700; color:var(--text-primary,#1E3A5F); line-height:1; font-family:'DM Mono',monospace; }
.metric-delta { font-size:.7rem; color:#3B82F6; margin-top:.2rem; font-weight:500; }

.section-header { display:flex; align-items:center; gap:.6rem; margin:1.5rem 0 .8rem; }
.section-header-line { flex:1; height:1px; background:linear-gradient(90deg,#3B82F6,transparent); opacity:.35; }
.section-title { font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:1.2px; color:#3B82F6; white-space:nowrap; text-align:center; }

.insight-card { background:var(--metric-bg,#fff); border:1px solid var(--border); border-radius:var(--radius-md); padding:1rem 1.1rem; margin-bottom:.6rem; box-shadow:var(--shadow-sm); transition:var(--transition); }
.insight-card:hover { box-shadow:var(--shadow-md); }
.insight-card.good { border-left:3px solid #3B82F6; }
.insight-card.warn { border-left:3px solid #FBBF24; }
.insight-card.bad  { border-left:3px solid #F87171; }
.insight-card.info { border-left:3px solid #60A5FA; }
.insight-icon  { font-size:1.1rem; }
.insight-title { font-size:.82rem; font-weight:700; color:var(--text-primary); margin:.2rem 0; }
.insight-body  { font-size:.76rem; color:var(--text-muted); line-height:1.5; }

div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg,#1e3a8a,#1e40af) !important;
    color:#fff !important; font-family:'DM Sans',sans-serif !important;
    font-size:.72rem !important; font-weight:700 !important; text-transform:uppercase;
    white-space:normal !important; text-align:center !important;
    vertical-align:middle !important; min-width:80px !important; padding:10px !important;
}

[data-testid="stSidebar"] .stButton>button {
    width:100%; font-family:'DM Sans',sans-serif !important;
    font-weight:600 !important; font-size:.82rem !important;
    border-radius:var(--radius-sm); transition:var(--transition);
    background:linear-gradient(135deg,#1e40af,#1e3a8a) !important;
    color:#fff !important; border:none !important;
}
[data-testid="stSidebar"] .stButton>button:hover { opacity:.88 !important; transform:translateY(-1px) !important; }

.stDownloadButton>button {
    background:linear-gradient(135deg,#1e40af,#1e3a8a) !important;
    color:#fff !important; border:none !important;
    border-radius:var(--radius-sm) !important;
    font-family:'DM Sans',sans-serif !important;
    font-weight:600 !important; transition:var(--transition) !important;
}
.stDownloadButton>button:hover { opacity:.88; transform:translateY(-1px); }
hr { border-color:var(--border) !important; margin:1.2rem 0 !important; }
.brand-name    { font-size:.85rem; font-weight:700; color:#3B82F6; }
.brand-tagline { font-size:.58rem; letter-spacing:.8px; font-family:monospace; margin-bottom:.9rem; color:#1D4ED8; }

[data-testid="stTabs"] [role="tablist"] { gap:.3rem; border-bottom:1px solid var(--border); }
[data-testid="stTabs"] button[role="tab"] {
    font-family:'DM Sans',sans-serif !important; font-size:.82rem !important;
    font-weight:600 !important; border-radius:var(--radius-sm) var(--radius-sm) 0 0;
    padding:.55rem 1.1rem !important; transition:var(--transition);
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 5. HELPERS
# ─────────────────────────────────────────────

def section_header(label):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header-line"></div>
        <span class="section-title">{label}</span>
        <div class="section-header-line" style="background:linear-gradient(90deg,transparent,#3B82F6)"></div>
    </div>""", unsafe_allow_html=True)

def style_total_caller(row):
    if str(row.get("CALLER", "")) == "TOTAL":
        return ["font-weight:bold;background-color:#374151;color:#FFFFFF;"] * len(row)
    return [""] * len(row)

def style_total_team(row):
    if str(row.get("TEAM", "")) == "TOTAL":
        return ["font-weight:bold;background-color:#374151;color:#FFFFFF;"] * len(row)
    return [""] * len(row)


# ─────────────────────────────────────────────
# 6. DATA FETCHING
# ─────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_metadata():
    df = pd.read_csv(CSV_URL)
    df.columns = df.columns.str.strip()
    df["merge_key"] = df["Caller Name"].str.strip().str.lower()
    teams     = sorted(df["Team Name"].dropna().unique())
    verticals = sorted(df["Vertical"].dropna().unique())
    return teams, verticals, df

@st.cache_data(ttl=600, show_spinner=False)
def get_last_update():
    try:
        r = client.query(f"SELECT MAX(updated_at_ampm) AS u FROM `{LEADS_TABLE}`").to_dataframe()
        return str(r["u"].iloc[0]) if not r.empty and r["u"].iloc[0] else "N/A"
    except:
        return "N/A"

@st.cache_data(ttl=600, show_spinner=False)
def get_available_dates():
    try:
        r = client.query(f"SELECT MIN(AssignedOn) AS mn, MAX(AssignedOn) AS mx FROM `{LEADS_TABLE}`").to_dataframe()
        if not r.empty and r["mn"].iloc[0]:
            return r["mn"].iloc[0], r["mx"].iloc[0]
    except:
        pass
    return date.today(), date.today()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_leads_data(start_date, end_date):
    query = f"""
        SELECT * FROM `{LEADS_TABLE}`
        WHERE AssignedOn BETWEEN '{start_date}' AND '{end_date}'
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df["Owner"]       = df["Owner"].astype(str).str.strip()
        df["merge_key"]   = df["Owner"].str.lower()
        df["ContactStage"] = df["ContactStage"].astype(str).str.strip()
        df["Assigned_On_Call_Counter"] = (
            pd.to_numeric(df["Assigned_On_Call_Counter"], errors="coerce").fillna(0).astype(int)
        )
        df["Follow_up_date"] = pd.to_datetime(df["Follow_up_date"], errors="coerce")
        df["LastCalledDate"] = pd.to_datetime(df["LastCalledDate"], errors="coerce")
    return df


# ─────────────────────────────────────────────
# 7. TABLE BUILDERS
# ─────────────────────────────────────────────

def _build_pivot(df, group_col, stage_map, stage_cols):
    """Generic groupby → stage count pivot with TOTAL row."""
    if df.empty:
        return pd.DataFrame()
    rows = []
    for name, grp in df.groupby(group_col, sort=False):
        row = {group_col: name}
        for col, stages in stage_map.items():
            row[col] = int(grp["ContactStage"].isin(stages).sum())
        row["TOTAL"] = sum(row[c] for c in stage_cols)
        rows.append(row)
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows).sort_values("TOTAL", ascending=False).reset_index(drop=True)
    tot = {group_col: "TOTAL"}
    for c in stage_cols + ["TOTAL"]:
        tot[c] = int(result[c].sum()) if c in result.columns else 0
    return pd.concat([result, pd.DataFrame([tot])], ignore_index=True)


def build_caller_assigned(df):
    base = _build_pivot(df, "CALLER", STAGE_MAP, ALL_STAGE_COLS)
    if base.empty:
        return base
    team_map = df.drop_duplicates("CALLER").set_index("CALLER")["TEAM"].to_dict()
    base.insert(1, "TEAM", base["CALLER"].map(team_map).fillna("—"))
    base.loc[base["CALLER"] == "TOTAL", "TEAM"] = "—"
    return base

def build_team_assigned(df):
    return _build_pivot(df, "TEAM", STAGE_MAP, ALL_STAGE_COLS)

def _breach_filter(df):
    today  = pd.Timestamp(date.today())
    cutoff = pd.Timestamp(date.today() - timedelta(days=3))
    fup_breach = df["Follow_up_date"].isna() | (df["Follow_up_date"] < today)
    lcd_breach = df["LastCalledDate"].isna()  | (df["LastCalledDate"] < cutoff)
    return df[fup_breach & lcd_breach & df["ContactStage"].isin(BREACH_STAGES)].copy()

def build_caller_breach(df):
    bdf = _breach_filter(df)
    base = _build_pivot(bdf, "CALLER", BREACH_MAP, BREACH_COLS)
    if base.empty:
        return base
    team_map = df.drop_duplicates("CALLER").set_index("CALLER")["TEAM"].to_dict()
    base.insert(1, "TEAM", base["CALLER"].map(team_map).fillna("—"))
    base.loc[base["CALLER"] == "TOTAL", "TEAM"] = "—"
    return base

def build_team_breach(df):
    return _build_pivot(_breach_filter(df), "TEAM", BREACH_MAP, BREACH_COLS)

def _ld_filter(df):
    return df[(df["Assigned_On_Call_Counter"] < 11) & df["ContactStage"].isin(LD_COLS)].copy()

def build_caller_ld(df):
    ldf  = _ld_filter(df)
    ldmap = {c: [c] for c in LD_COLS}
    base  = _build_pivot(ldf, "CALLER", ldmap, LD_COLS)
    if base.empty:
        return base
    team_map = df.drop_duplicates("CALLER").set_index("CALLER")["TEAM"].to_dict()
    base.insert(1, "TEAM", base["CALLER"].map(team_map).fillna("—"))
    base.loc[base["CALLER"] == "TOTAL", "TEAM"] = "—"
    return base

def build_team_ld(df):
    ldmap = {c: [c] for c in LD_COLS}
    return _build_pivot(_ld_filter(df), "TEAM", ldmap, LD_COLS)


# ─────────────────────────────────────────────
# 8. INSIGHTS
# ─────────────────────────────────────────────

def compute_lead_insights(c_asgn, t_asgn, c_breach, t_breach, c_ld, t_ld):
    insights = []

    def ex_tot(df, col):
        return df[df[col] != "TOTAL"] if not df.empty else df

    ca = ex_tot(c_asgn,  "CALLER")
    ta = ex_tot(t_asgn,  "TEAM")
    cb = ex_tot(c_breach, "CALLER")
    tb = ex_tot(t_breach, "TEAM")
    cl = ex_tot(c_ld,    "CALLER")
    tl = ex_tot(t_ld,    "TEAM")

    if not ca.empty:
        top = ca.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"good","icon":"🏆",
            "title":f"Highest Assigned Leads — {top['CALLER']}",
            "body":f"{int(top['TOTAL'])} leads assigned in the selected period. Fresh: {int(top.get('FRESH',0))}, FLW-UP: {int(top.get('FLW-UP',0))}, Counselled: {int(top.get('COUNSELLED',0))}."})

    if not ta.empty:
        top = ta.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"good","icon":"👥",
            "title":f"Highest Leads Team — {top['TEAM']}",
            "body":f"{top['TEAM']} has {int(top['TOTAL'])} total assigned leads. Fresh: {int(top.get('FRESH',0))}, FLW-UP: {int(top.get('FLW-UP',0))}."})

    if not cb.empty:
        top = cb.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"warn","icon":"⚠️",
            "title":f"Most Potential Breached Leads — {top['CALLER']}",
            "body":f"{int(top['TOTAL'])} leads are breach-risk. Follow-up overdue or not called in 3+ days. Stages: CBL {int(top.get('CBL',0))}, FLW-UP {int(top.get('FLW-UP',0))}, COUNSELLED {int(top.get('COUNSELLED',0))}."})
    else:
        insights.append({"type":"good","icon":"✅",
            "title":"No Potential Breached Leads Detected",
            "body":"All leads have recent activity. Follow-up dates are on track. Great work maintaining timely engagement!"})

    if not tb.empty:
        top = tb.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"warn","icon":"🏳️",
            "title":f"Most Breach-Risk Team — {top['TEAM']}",
            "body":f"{top['TEAM']} has {int(top['TOTAL'])} potentially breached leads. Immediate follow-up action required by team leads."})

    if not cl.empty:
        top = cl.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"bad","icon":"📞",
            "title":f"Most Less-Dialled Leads — {top['CALLER']}",
            "body":f"{int(top['TOTAL'])} leads assigned to {top['CALLER']} have < 11 call attempts and remain unconnected. Needs urgent dialling focus."})

    if not tl.empty:
        top = tl.sort_values("TOTAL", ascending=False).iloc[0]
        insights.append({"type":"bad","icon":"🚨",
            "title":f"Most Less-Dialled Team — {top['TEAM']}",
            "body":f"{top['TEAM']} has {int(top['TOTAL'])} under-dialled leads in DNP status. Review dialling discipline and increase call attempts."})

    return insights[:6]


# ─────────────────────────────────────────────
# 9. PDF GUIDE
# ─────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def generate_leads_pdf_bytes() -> bytes:
    buffer    = io.BytesIO()
    BLUE_DARK = colors.HexColor("#1e3a8a")
    BLUE_MID  = colors.HexColor("#1e40af")
    BLUE_PALE = colors.HexColor("#EFF6FF")
    BLUE_ROW  = colors.HexColor("#DBEAFE")
    GREY_MID  = colors.HexColor("#6B7280")
    WHITE     = colors.white
    BLACK     = colors.HexColor("#111827")
    W, H      = A4

    def s(name, **kw):
        d = dict(fontName="Helvetica", fontSize=9, textColor=BLACK, spaceAfter=3, leading=14)
        d.update(kw); return ParagraphStyle(name, **d)

    S = {
        "body"   : s("body"),
        "label"  : s("label",   fontName="Helvetica-Bold", fontSize=8, textColor=BLUE_DARK, spaceAfter=1),
        "formula": s("formula", fontName="Helvetica-Oblique", fontSize=8.5, textColor=BLUE_MID, backColor=BLUE_PALE, leftIndent=8, rightIndent=8),
        "footer" : s("footer",  fontSize=7.5, textColor=GREY_MID, alignment=TA_CENTER),
    }

    class CoverBlock(Flowable):
        def __init__(self, w): Flowable.__init__(self); self.w = w; self.height = 90
        def draw(self):
            c = self.canv
            c.setFillColor(BLUE_DARK);  c.rect(0, 52, self.w, 38, fill=1, stroke=0)
            c.setFillColor(BLUE_MID);   c.rect(0, 22, self.w, 30, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#0c1445")); c.rect(0, 0, self.w, 22, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(self.w/2, 66, "LEAD METRICS DASHBOARD")
            c.setFillColor(colors.HexColor("#BFDBFE")); c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(self.w/2, 34, "Logic & Metric Reference Guide")
            c.setFillColor(colors.HexColor("#DBEAFE")); c.setFont("Helvetica", 8.5)
            c.drawCentredString(self.w/2, 8, "LawSikho & Skill Arbitrage  \u00b7  Sales & Operations Team  \u00b7  Internal Use Only")

    class SectionBanner(Flowable):
        def __init__(self, icon, title, color=None, w=None):
            Flowable.__init__(self); self.icon = icon; self.title = title
            self.color = color or BLUE_DARK; self.w = w or (W - 30*mm); self.height = 22
        def draw(self):
            c = self.canv; c.setFillColor(self.color)
            c.roundRect(0, 0, self.w, self.height, 4, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 11)
            c.drawString(10, 6, f"{self.icon}  {self.title}")

    def btable(rows, cw=None):
        cw   = cw or [44*mm, 116*mm]
        data = [[Paragraph(f"<b>{r[0]}</b>", S["label"]), Paragraph(r[1], S["body"])] for r in rows]
        t    = Table(data, colWidths=cw, hAlign="LEFT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(0,-1), BLUE_PALE), ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("GRID", (0,0),(-1,-1), 0.3, colors.HexColor("#BFDBFE")),
            ("ROWBACKGROUNDS", (0,0),(-1,-1), [WHITE, BLUE_ROW]),
            ("LEFTPADDING", (0,0),(-1,-1), 6), ("RIGHTPADDING", (0,0),(-1,-1), 6),
            ("TOPPADDING",  (0,0),(-1,-1), 4), ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        return t

    def ltable(rows):
        data = [[Paragraph(f"<b>{r[0]}</b>", S["label"]), Paragraph(r[1], S["formula"])] for r in rows]
        t    = Table(data, colWidths=[52*mm, 108*mm], hAlign="LEFT")
        t.setStyle(TableStyle([
            ("VALIGN", (0,0),(-1,-1), "TOP"),
            ("GRID", (0,0),(-1,-1), 0.3, colors.HexColor("#BFDBFE")),
            ("ROWBACKGROUNDS", (0,0),(-1,-1), [WHITE, BLUE_ROW]),
            ("LEFTPADDING", (0,0),(-1,-1), 6), ("RIGHTPADDING", (0,0),(-1,-1), 6),
            ("TOPPADDING",  (0,0),(-1,-1), 4), ("BOTTOMPADDING", (0,0),(-1,-1), 4),
        ]))
        return t

    SP  = Spacer
    HR  = lambda: HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#BFDBFE"), spaceAfter=6, spaceBefore=4)
    BAN = SectionBanner
    cw  = W - 30*mm

    story = [
        SP(1, 18*mm), CoverBlock(cw), SP(1, 10*mm),
        Paragraph("This document explains every metric, table, and column in the Lead Metrics Dashboard — a quick reference for the Sales & Operations team.", S["body"]),
        SP(1, 6*mm),

        BAN("📋", "SECTION 1 — DASHBOARD TABS OVERVIEW"), SP(1, 3*mm),
        btable([
            ("📊 Assigned Leads Report",
             "Callerwise view — three tables: Assigned Leads Distribution (15 stage columns), Potential Breached Leads, Less Dialled Leads. Filtered by AssignedOn date range from the sidebar."),
            ("🧠 Insights & Teamwise",
             "Six auto-generated insights followed by teamwise versions of all three tables. Auto-populates from the last generated report."),
        ]), SP(1, 6*mm),

        BAN("📊", "SECTION 2 — ASSIGNED LEADS DISTRIBUTION"), SP(1, 3*mm),
        Paragraph("One row per active caller, sorted by TOTAL descending. Owner field merged with team sheet via lowercase key.", S["body"]), SP(1, 2*mm),
        ltable([
            ("FRESH",             "New Lead + Re-enquired Lead + Opportunity Created"),
            ("DNP",               "Call Not Picking Up + Call Not Connected"),
            ("CBL",               "Call Back Later"),
            ("FLW-UP",            "Follow Up For Closure"),
            ("COUNSELLED",        "Counselled lead"),
            ("DISCOVERY",         "Discovery Call Done"),
            ("ROADMAP",           "Roadmap Done"),
            ("MBL",               "May buy later"),
            ("ACTUALLY-ENROLLED", "Actually Enrolled"),
            ("INVALID/NTINTRSTD", "Irrelevant lead + Not Interested + Invalid"),
            ("BOOKING-RCVD",      "Booking fees received"),
            ("LOAN-PNDG",         "Loan pending"),
            ("COLL-DNE",          "Collections done"),
            ("PRE-SALES",         "Pre-Sales Registrations"),
            ("COURSE ENROLLED",   "Course Enrolled"),
            ("TOTAL",             "Sum of all 15 stage columns for each row."),
        ]), SP(1, 6*mm),

        BAN("⚠️", "SECTION 3 — POTENTIAL BREACHED LEADS AFTER ASSIGNMENT"), SP(1, 3*mm),
        Paragraph("Leads in active engagement stages (CBL, FLW-UP, COUNSELLED, DISCOVERY, ROADMAP) that satisfy both breach conditions.", S["body"]), SP(1, 2*mm),
        btable([
            ("Breach Condition 1", "Follow_up_date is NULL OR Follow_up_date < today (IST). Overdue or no follow-up scheduled."),
            ("Breach Condition 2", "LastCalledDate is NULL OR LastCalledDate < today − 3 days. Never called or not called in 3+ calendar days."),
            ("Combined Logic",     "BOTH conditions must be true. Only then are the 5 engagement stage counts shown."),
            ("CBL",                "Call Back Later leads meeting both breach conditions."),
            ("FLW-UP",             "Follow Up For Closure leads meeting both breach conditions."),
            ("COUNSELLED",         "Counselled leads meeting both breach conditions."),
            ("DISCOVERY",          "Discovery Call Done leads meeting both breach conditions."),
            ("ROADMAP",            "Roadmap Done leads meeting both breach conditions."),
            ("TOTAL",              "Sum of all 5 breach stage columns for each caller/team."),
        ]), SP(1, 6*mm),

        BAN("📞", "SECTION 4 — LESS DIALLED LEADS AFTER ASSIGNMENT"), SP(1, 3*mm),
        Paragraph("Flags DNP leads (Call Not Picking Up, Call Not Connected) with fewer than 11 call attempts. Under-dialled leads need more outreach.", S["body"]), SP(1, 2*mm),
        btable([
            ("Filter Condition",     "Assigned_On_Call_Counter < 11 AND ContactStage in ('Call Not Picking Up', 'Call Not Connected')."),
            ("Call Not Picking Up",  "Count of DNP-CNPU leads with < 11 call attempts."),
            ("Call Not Connected",   "Count of DNP-CNC leads with < 11 call attempts."),
            ("TOTAL",                "Sum of both DNP columns."),
            ("Why < 11 calls?",      "Industry threshold: a minimum of 11 attempts should be made before a lead is considered unreachable. Below this, the lead is under-dialled."),
        ]), SP(1, 6*mm),

        BAN("📅", "SECTION 5 — DATE & FILTER CONTROLS"), SP(1, 3*mm),
        btable([
            ("AssignedOn Filter",  "Sidebar date range filters leads by the AssignedOn field. Only leads assigned in this window are included in all three tables."),
            ("Team Filter",        "Restricts all tables to selected teams. Applied after team sheet merge."),
            ("Vertical Filter",    "Restricts all tables to selected verticals. Applied after team sheet merge."),
            ("Caller Search",      "Case-insensitive partial match on canonical Caller Name."),
            ("Breach Date",        "Computed from today's date at runtime — not affected by the AssignedOn filter. A lead assigned months ago can still appear as breached."),
        ]), SP(1, 6*mm),

        BAN("🧠", "SECTION 6 — INSIGHTS"), SP(1, 3*mm),
        btable([
            ("Highest Assigned Leads — Caller", "Caller with the highest TOTAL in Assigned Leads Distribution."),
            ("Highest Leads Team",              "Team with the highest TOTAL in Teamwise Assigned Leads Distribution."),
            ("Most Potential Breached — Caller","Caller with the highest TOTAL in Potential Breached Leads table."),
            ("Most Breach-Risk Team",           "Team with the highest TOTAL in Teamwise Potential Breached Leads table."),
            ("Most Less-Dialled — Caller",      "Caller with the highest TOTAL in Less Dialled Leads table."),
            ("Most Less-Dialled Team",          "Team with the highest TOTAL in Teamwise Less Dialled Leads table."),
        ]), SP(1, 6*mm),

        BAN("📖", "KEY TERMS GLOSSARY", color=colors.HexColor("#374151")), SP(1, 3*mm),
        btable([
            ("AssignedOn",              "Date the lead was assigned to the caller. Primary filter date."),
            ("ContactStage",            "Current funnel stage. 15 possible values mapped to abbreviated column names."),
            ("Follow_up_date",          "Scheduled follow-up date. NULL = no follow-up scheduled."),
            ("LastCalledDate",          "Most recent call date. NULL = never called."),
            ("Assigned_On_Call_Counter","Total call attempts since assignment. Used for Less Dialled logic."),
            ("Potential Breached",      "Active-stage leads (CBL/FLW-UP/COUNSELLED/DISCOVERY/ROADMAP) with overdue follow-up AND not called in 3+ days."),
            ("Less Dialled",            "DNP leads (CNPU/CNC) with < 11 call attempts. At risk of going cold."),
            ("Team Sheet Merge",        "Owner field from lsq_leads joined (lowercase) to Caller Name in the team Google Sheet."),
        ], cw=[46*mm, 114*mm]),

        SP(1, 8*mm), HR(),
        Paragraph("Designed by Amit Ray  \u00b7  amitray@lawsikho.com  \u00b7  For Internal Use of Sales and Operations Team Only. All Rights Reserved.", S["footer"]),
    ]

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=14*mm, bottomMargin=14*mm,
        title="Lead Metrics — Logic Reference Guide", author="Amit Ray",
    )
    doc.build(story)
    return buffer.getvalue()


# ─────────────────────────────────────────────
# 10. SIDEBAR
# ─────────────────────────────────────────────

st.sidebar.markdown("""
<div style='padding:.6rem 0 .4rem;text-align:center;'>
    <div style='display:flex;align-items:center;justify-content:center;margin-bottom:.3rem;'>
        <span class='brand-name'>LawSikho</span>
        <div style='width:1px;height:18px;margin:0 .6rem;
                    background:linear-gradient(180deg,transparent,rgba(59,130,246,.9),transparent);
                    box-shadow:0 0 6px rgba(59,130,246,.5);'></div>
        <span class='brand-name'>Skill Arbitrage</span>
    </div>
    <div class='brand-tagline'>India Learning 📖 India Earning</div>
    <div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                color:#6B7280;margin-bottom:.5rem;'>Report Controls</div>
</div>
""", unsafe_allow_html=True)

min_d, max_d = get_available_dates()
min_d = pd.Timestamp(min_d).date()
max_d = pd.Timestamp(max_d).date()

date_range = st.sidebar.date_input(
    "📅 Date Range", value=(max_d, max_d),
    min_value=min_d, max_value=max_d, format="DD-MM-YYYY", key="leads_date_range"
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range if not isinstance(date_range, tuple) else date_range[0]

teams, verticals, df_team_mapping = get_metadata()
selected_team     = st.sidebar.multiselect("👥 Filter by Team",     options=teams,     key="leads_team")
selected_vertical = st.sidebar.multiselect("👑 Filter by Vertical", options=verticals, key="leads_vert")
search_query      = st.sidebar.text_input("👤 Search Caller Name",                     key="leads_search")

gen_report = st.sidebar.button("📊 Generate Leads Report", key="leads_gen_btn")

st.sidebar.download_button(
    label="📖 Metrics Guide (PDF)",
    data=generate_leads_pdf_bytes(),
    file_name="Lead_Metrics_Logic_Guide.pdf",
    mime="application/pdf",
    key="dl_leads_pdf"
)

st.sidebar.markdown("""
<hr style='border:none;border-top:1px solid #3B82F6;opacity:.4;margin:.6rem 0;'>
<div style='font-size:.72rem;color:#6B7280;font-weight:500;'>
    <span style='font-size:.65rem;opacity:.75;display:block;margin-bottom:.5rem;'>For Internal Use of Sales and Operations Team Only.<br>All Rights Reserved.</span>
    DESIGNED BY: <b>AMIT RAY</b><br>
    <a href="mailto:amitray@lawsikho.com" style="color:#3B82F6;text-decoration:none;">amitray@lawsikho.com</a>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 11. HEADER BANNER
# ─────────────────────────────────────────────

last_update_str = get_last_update()
display_start   = start_date.strftime("%d-%m-%Y")
display_end     = end_date.strftime("%d-%m-%Y")

st.markdown(f"""
<div class="ld-header">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:.75rem;">
        <div>
            <div class="ld-title">📊 LEAD METRICS</div>
            <div class="ld-subtitle">ASSIGNED PERIOD&nbsp;·&nbsp;{display_start} to {display_end}</div>
        </div>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-top:.25rem;">
            <span class="ld-badge"><span class="ld-pulse"></span>LEADSQUARED DATA</span>
            <span class="ld-badge">🕐 UPDATED AT: {last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# 12. TABS
# ─────────────────────────────────────────────

tab1, tab2 = st.tabs(["📊 Assigned Leads Report", "🧠 Insights & Teamwise"])


# ══════════════════════════════════════════════
# TAB 1 — ASSIGNED LEADS REPORT
# ══════════════════════════════════════════════

with tab1:
    if gen_report:
        with st.spinner("Fetching lead data…"):
            df_raw = fetch_leads_data(start_date, end_date)

            if df_raw.empty:
                st.warning("No leads found for the selected period.")
            else:
                # Merge team sheet
                df = pd.merge(
                    df_raw,
                    df_team_mapping[["merge_key","Caller Name","Team Name","Vertical"]].drop_duplicates("merge_key"),
                    on="merge_key", how="left"
                )
                df["CALLER"] = df["Caller Name"].fillna(df["Owner"])
                df["TEAM"]   = df["Team Name"].fillna("Others")
                df["Vertical"] = df["Vertical"].fillna("Others")

                # Apply sidebar filters
                if selected_team:     df = df[df["TEAM"].isin(selected_team)]
                if selected_vertical: df = df[df["Vertical"].isin(selected_vertical)]
                if search_query:      df = df[df["CALLER"].str.contains(search_query, case=False, na=False)]
                df = df[df["TEAM"] != "Others"]

                if df.empty:
                    st.error("No leads match the selected filters.")
                else:
                    section_header("📊 LEAD SUMMARY METRICS")

                    # Since you already filtered TEAM != "Others", df is clean
                    df_valid = df.copy()
                    
                    fresh_c = int(df_valid["ContactStage"].isin(STAGE_MAP["FRESH"]).sum())
                    enrolled_c = int(df_valid["ContactStage"].eq("Actually Enrolled").sum())
                    discovery_c = int(df_valid["ContactStage"].eq("Discovery Call Done").sum())
                    roadmap_c = int(df_valid["ContactStage"].eq("Roadmap Done").sum())
                    followup_c = int(df_valid["ContactStage"].isin(["Follow Up For Closure","Counselled lead"]).sum())
                    kpis = [
                        ("Total Assigned Leads", len(df_valid), "📋"),
                        ("Fresh Leads", fresh_c, "🌱"),
                        ("Lead Conversions", enrolled_c, "🎓"),
                        ("Discovery", discovery_c, "🔍"),
                        ("Roadmap", roadmap_c, "🗺️"),
                        ("FLW-UP / CNSLED", followup_c, "📞"),
                        ("Active Callers", df_valid["CALLER"].nunique(), "👤"),
                        ("Active Teams", df_valid["TEAM"].nunique(), "👥"),
                    ]
                    kpi_cols = st.columns(len(kpis))
                    for col, (label, val, icon) in zip(kpi_cols, kpis):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{icon} {label}</div>
                                <div class="metric-value">{val}</div>
                            </div>""", unsafe_allow_html=True)

                    st.divider()

                    # ── TABLE 1: Assigned Leads Distribution ──
                    section_header("📊 ASSIGNED LEADS DISTRIBUTION")
                    c_asgn = build_caller_assigned(df)
                    if not c_asgn.empty:
                        disp = ["CALLER","TEAM"] + ALL_STAGE_COLS + ["TOTAL"]
                        available = [c for c in disp if c in c_asgn.columns]
                        st.dataframe(
                            c_asgn[available].style.apply(style_total_caller, axis=1),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.info("No data available.")

                    st.divider()

                    # ── TABLE 2: Potential Breached Leads ──
                    section_header("⚠️ POTENTIAL BREACHED LEADS AFTER ASSIGNMENT")
                    c_breach = build_caller_breach(df)
                    if not c_breach.empty:
                        disp_b = ["CALLER","TEAM"] + BREACH_COLS + ["TOTAL"]
                        available_b = [c for c in disp_b if c in c_breach.columns]
                        st.dataframe(
                            c_breach[available_b].style.apply(style_total_caller, axis=1),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.success("✅ No potential breached leads detected for the selected filters.")

                    st.divider()

                    # ── TABLE 3: Less Dialled Leads ──
                    section_header("📞 LESS DIALLED LEADS AFTER ASSIGNMENT")
                    c_ld = build_caller_ld(df)
                    if not c_ld.empty:
                        disp_l = ["CALLER","TEAM"] + LD_COLS + ["TOTAL"]
                        available_l = [c for c in disp_l if c in c_ld.columns]
                        st.dataframe(
                            c_ld[available_l].style.apply(style_total_caller, axis=1),
                            use_container_width=True, hide_index=True
                        )
                    else:
                        st.success("✅ No less-dialled leads detected for the selected filters.")

                    # Persist for insights tab
                    st.session_state["ld_df"]       = df.copy()
                    st.session_state["ld_c_asgn"]   = c_asgn.copy() if not c_asgn.empty else pd.DataFrame()
                    st.session_state["ld_c_breach"]  = c_breach.copy() if not c_breach.empty else pd.DataFrame()
                    st.session_state["ld_c_ld"]      = c_ld.copy() if not c_ld.empty else pd.DataFrame()
    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>📊</div>
            <div style='font-size:.9rem;font-weight:600;'>Select a date range and click <b>Generate Leads Report</b></div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — INSIGHTS & TEAMWISE
# ══════════════════════════════════════════════

with tab2:
    if "ld_df" in st.session_state:
        df_ins   = st.session_state["ld_df"]
        c_asgn_s = st.session_state.get("ld_c_asgn",  pd.DataFrame())
        c_brch_s = st.session_state.get("ld_c_breach", pd.DataFrame())
        c_ld_s   = st.session_state.get("ld_c_ld",    pd.DataFrame())

        t_asgn  = build_team_assigned(df_ins)
        t_breach = build_team_breach(df_ins)
        t_ld     = build_team_ld(df_ins)

        # ── Insights ──
        section_header("🧠 LEAD INSIGHTS")
        insights = compute_lead_insights(c_asgn_s, t_asgn, c_brch_s, t_breach, c_ld_s, t_ld)
        if insights:
            cols_ins = st.columns(2)
            for i, ins in enumerate(insights):
                with cols_ins[i % 2]:
                    st.markdown(f"""
                    <div class="insight-card {ins['type']}">
                        <div style='display:flex;align-items:center;gap:.4rem;'>
                            <span class="insight-icon">{ins['icon']}</span>
                            <span class="insight-title">{ins['title']}</span>
                        </div>
                        <div class="insight-body">{ins['body']}</div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.info("Not enough data to generate insights.")

        st.divider()

        # ── Teamwise Assigned ──
        section_header("👥 TEAMWISE ASSIGNED LEADS DISTRIBUTION")
        if not t_asgn.empty:
            st.dataframe(t_asgn.style.apply(style_total_team, axis=1), use_container_width=True, hide_index=True)
        else:
            st.info("No teamwise assigned lead data available.")

        st.divider()

        # ── Teamwise Breached ──
        section_header("⚠️ TEAMWISE POTENTIAL BREACHED LEADS AFTER ASSIGNMENT")
        if not t_breach.empty:
            st.dataframe(t_breach.style.apply(style_total_team, axis=1), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No potential breached leads at team level.")

        st.divider()

        # ── Teamwise Less Dialled ──
        section_header("📞 TEAMWISE LESS DIALLED LEADS AFTER ASSIGNMENT")
        if not t_ld.empty:
            st.dataframe(t_ld.style.apply(style_total_team, axis=1), use_container_width=True, hide_index=True)
        else:
            st.success("✅ No less-dialled leads at team level.")

    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>🧠</div>
            <div style='font-size:.9rem;font-weight:600;'>
                Generate a <b>Leads Report</b> first —<br>Insights will appear here automatically.
            </div>
        </div>""", unsafe_allow_html=True)
