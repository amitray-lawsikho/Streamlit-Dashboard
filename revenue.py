import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account
import pandas as pd
from datetime import datetime, date, timedelta
import os
import pytz
import numpy as np
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.platypus import Flowable
from reportlab.lib.enums import TA_CENTER
import io
# ─────────────────────────────────────────────
# 1. CREDENTIALS & CONFIG
# ─────────────────────────────────────────────

if "gcp_service_account" in st.secrets:
    info = dict(st.secrets["gcp_service_account"])
    credentials = service_account.Credentials.from_service_account_info(info)
    client = bigquery.Client(credentials=credentials, project=info["project_id"])
else:
    SERVICE_ACCOUNT_FILE = "/content/drive/MyDrive/Lawsikho/credentials/bigquery_key.json"
    if os.path.exists(SERVICE_ACCOUNT_FILE):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = SERVICE_ACCOUNT_FILE
        client = bigquery.Client()
    else:
        st.error("Credentials not found!")

CSV_URL      = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRT73ztvPNZSvIu5WLxo-3WQ76JMAnt4P9dITd4EAbjSvuDytfgvdfri1WPXotCjm_Etnb80_Q7S-wf/pub?gid=973926168&single=true&output=csv"
REV_TABLE_ID = "studious-apex-488820-c3.crm_dashboard.revenue_sheet"

# Callers that are not real agents
EXCLUDE_CALLERS = {'direct', 'bootcamp - direct'}

# ─────────────────────────────────────────────
# 2. PAGE CONFIG
# ─────────────────────────────────────────────

st.set_page_config(
    layout="wide",
    page_title="REVENUE METRICS",
    initial_sidebar_state="expanded",
    page_icon="💰"
)

# ─────────────────────────────────────────────
# 3. CSS
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

:root {
    --accent-primary:   #10B981;
    --accent-secondary: #34D399;
    --accent-gold:      #F59E0B;
    --accent-warn:      #FBBF24;
    --accent-danger:    #F87171;
    --accent-info:      #60A5FA;
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

[data-testid="stAppViewContainer"]:not([class*="dark"]) {
    --bg-base:      #F0FDF4;
    --bg-surface:   #FFFFFF;
    --bg-elevated:  #FFFFFF;
    --bg-muted:     #DCFCE7;
    --border:       rgba(0,0,0,.08);
    --text-primary: #111827;
    --text-muted:   #6B7280;
    --metric-bg:    #FFFFFF;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-base:      #0A0F0D;
        --bg-surface:   #111B16;
        --bg-elevated:  #162119;
        --bg-muted:     #0F1A14;
        --border:       rgba(255,255,255,.07);
        --text-primary: #F1F5F9;
        --text-muted:   #94A3B8;
        --metric-bg:    #162119;
    }
}

[data-theme="dark"] {
    --bg-base:      #0A0F0D !important;
    --bg-surface:   #111B16 !important;
    --bg-elevated:  #162119 !important;
    --bg-muted:     #0F1A14 !important;
    --border:       rgba(255,255,255,.07) !important;
    --text-primary: #F1F5F9 !important;
    --text-muted:   #94A3B8 !important;
    --metric-bg:    #162119 !important;
}

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }

footer { visibility: hidden; }
[data-testid="stStatusWidget"], .stStatusWidget { display: none !important; }
[data-testid="stMainViewContainer"] { padding-top: 1.5rem; }
[data-testid="stSidebar"] { border-right: 1px solid var(--border, rgba(0,0,0,.08)); }

.rv-header {
    background: linear-gradient(135deg, #064e3b 0%, #065f46 45%, #1e3a5f 100%);
    border-radius: var(--radius-lg);
    padding: 1.5rem 2rem 1.2rem;
    margin-bottom: 1.2rem;
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-lg);
}
.rv-header::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(16,185,129,.2) 0%, transparent 70%);
    border-radius: 50%;
}
.rv-title   { font-size: 1.65rem; font-weight: 700; color: #FFFFFF; letter-spacing: .5px; margin: 0 0 .25rem; }
.rv-subtitle{ font-size: .82rem; color: rgba(255,255,255,.6); font-weight: 400; margin: 0; font-family: 'DM Mono', monospace; }
.rv-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: rgba(255,255,255,.12); backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,.18); border-radius: 20px;
    padding: 3px 10px; font-size: .73rem;
    color: rgba(255,255,255,.9); font-family: 'DM Mono', monospace;
}
.rv-pulse {
    width: 6px; height: 6px; background: #34D399; border-radius: 50%;
    display: inline-block; animation: pulse-ring 1.8s ease-in-out infinite;
}
@keyframes pulse-ring {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%       { opacity: .5; transform: scale(1.4); }
}

.metric-card {
    background: var(--metric-bg, #fff);
    border: 1px solid var(--border, rgba(0,0,0,.08));
    border-radius: var(--radius-md);
    padding: .9rem 1rem;
    transition: var(--transition);
    box-shadow: var(--shadow-sm);
    position: relative; overflow: hidden; text-align: center;
}
.metric-card::before {
    content: ""; position: absolute; top: 0; left: 0;
    width: 100%; height: 3px;
    background: linear-gradient(90deg, #10B981, #34D399);
    opacity: 0; transition: opacity .2s;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.metric-card:hover::before { opacity: 1; }
.metric-label  { font-size: .68rem; font-weight: 600; text-transform: uppercase; letter-spacing: .8px; color: var(--text-muted, #6B7280); margin: 0 0 .3rem; }
.metric-value  { font-size: 1.45rem; font-weight: 700; color: var(--text-primary, #111827); line-height: 1; font-family: 'DM Mono', monospace; }
.metric-delta  { font-size: .7rem; color: #10B981; margin-top: .2rem; font-weight: 500; }

.section-header { display: flex; align-items: center; gap: .6rem; margin: 1.5rem 0 .8rem; }
.section-header-line { flex: 1; height: 1px; background: linear-gradient(90deg, #10B981, transparent); opacity: .35; }
.section-title { font-size: .78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; color: #10B981; white-space: nowrap; text-align: center; }

.insight-card { background: var(--metric-bg, #fff); border: 1px solid var(--border, rgba(0,0,0,.08)); border-radius: var(--radius-md); padding: 1rem 1.1rem; margin-bottom: .6rem; box-shadow: var(--shadow-sm); transition: var(--transition); }
.insight-card:hover { box-shadow: var(--shadow-md); }
.insight-card.good { border-left: 3px solid #10B981; }
.insight-card.warn { border-left: 3px solid #FBBF24; }
.insight-card.bad  { border-left: 3px solid #F87171; }
.insight-card.info { border-left: 3px solid #60A5FA; }
.insight-icon  { font-size: 1.1rem; }
.insight-title { font-size: .82rem; font-weight: 700; color: var(--text-primary, #111827); margin: .2rem 0; }
.insight-body  { font-size: .76rem; color: var(--text-muted, #6B7280); line-height: 1.5; }

[data-testid="stTabs"] [role="tablist"] { gap: .3rem; border-bottom: 1px solid var(--border, rgba(0,0,0,.08)); }
[data-testid="stTabs"] button[role="tab"] {
    font-family: 'DM Sans', sans-serif !important; font-size: .82rem !important;
    font-weight: 600 !important; letter-spacing: .3px;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
    padding: .55rem 1.1rem !important; transition: var(--transition);
}

div[data-testid="stDataFrame"] thead tr th {
    background: linear-gradient(135deg, #064e3b, #065f46) !important;
    color: #fff !important; font-family: 'DM Sans', sans-serif !important;
    font-size: .72rem !important; font-weight: 700 !important; letter-spacing: .6px;
    text-transform: uppercase; white-space: normal !important; word-wrap: break-word !important;
    text-align: center !important; vertical-align: middle !important;
    min-width: 100px !important; padding: 10px !important;
}

[data-testid="stSidebar"] .stButton>button {
    width: 100%; font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important; font-size: .82rem !important;
    border-radius: var(--radius-sm); transition: var(--transition);
}
[data-testid="stSidebar"] .stButton>button:first-child {
    background: linear-gradient(135deg, #059669, #065f46) !important;
    color: #fff !important; border: none !important;
}
[data-testid="stSidebar"] .stButton>button:last-child {
    background: linear-gradient(135deg, #0F766E, #064e3b) !important;
    color: #fff !important; border: none !important;
}

hr { border-color: var(--border, rgba(0,0,0,.08)) !important; margin: 1.2rem 0 !important; }

.achieve-bar-wrap { background: var(--bg-muted, #DCFCE7); border-radius: 999px; height: 6px; margin-top: .4rem; overflow: hidden; }
.achieve-bar-fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #10B981, #34D399); transition: width .6s ease; }
/* ── Download Buttons — match Generate Revenue Report style ── */
.stDownloadButton > button {
    width: 100% !important;
    background: linear-gradient(135deg, #059669, #065f46) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: .82rem !important;
    transition: var(--transition) !important;
}
.stDownloadButton > button:hover {
    opacity: .88 !important;
    transform: translateY(-1px) !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def fmt_inr(value):
    if pd.isna(value) or value == 0: return "₹0"
    if value >= 1_00_00_000: return f"₹{value/1_00_00_000:.2f}Cr"
    if value >= 1_00_000:    return f"₹{value/1_00_000:.2f}L"
    if value >= 1_000:       return f"₹{value/1_000:.2f}K"
    return f"₹{int(value)}"

def section_header(label):
    st.markdown(f"""
    <div class="section-header">
        <div class="section-header-line"></div>
        <span class="section-title">{label}</span>
        <div class="section-header-line" style="background:linear-gradient(90deg,transparent,#10B981)"></div>
    </div>""", unsafe_allow_html=True)

def style_total_rev(row):
    if row.get("CALLER NAME") == "TOTAL":
        return ['font-weight: bold; background-color: #374151; color: #FFFFFF;'] * len(row)
    return [''] * len(row)

def get_months_in_range(start_date, end_date):
    months, cur = [], date(start_date.year, start_date.month, 1)
    end_month   = date(end_date.year, end_date.month, 1)
    while cur <= end_month:
        months.append(cur)
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months

def count_working_days(start_date, end_date):
    """Count Mon–Fri days between start_date and end_date inclusive."""
    count = 0
    cur   = start_date
    while cur <= end_date:
        if cur.weekday() < 5:   # 0=Mon … 4=Fri
            count += 1
        cur += timedelta(days=1)
    return count


# ─────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────

@st.cache_data(ttl=120, show_spinner=False)
def get_metadata():
    df_meta = pd.read_csv(CSV_URL)
    df_meta.columns = df_meta.columns.str.strip().str.replace('\xa0', '', regex=False)

    month_col = next((c for c in df_meta.columns if c.strip().lower() == 'month'), None)
    if month_col and month_col != 'Month':
        df_meta.rename(columns={month_col: 'Month'}, inplace=True)

    if 'Month' in df_meta.columns:
        df_meta['Month'] = pd.to_datetime(df_meta['Month'], dayfirst=True, errors='coerce').dt.date
    else:
        df_meta['Month'] = None

    teams     = sorted(df_meta['Team Name'].dropna().unique()) if 'Team Name' in df_meta.columns else []
    verticals = sorted(df_meta['Vertical'].dropna().unique())  if 'Vertical'  in df_meta.columns else []
    df_meta['merge_key'] = df_meta['Caller Name'].str.strip().str.lower()
    return teams, verticals, df_meta

@st.cache_data(ttl=120, show_spinner=False)
def get_last_update():
    query = f"""
        SELECT updated_at_ampm FROM `{REV_TABLE_ID}`
        WHERE updated_at IS NOT NULL
        ORDER BY updated_at DESC LIMIT 1
    """
    try:
        res = client.query(query).to_dataframe()
        return str(res['updated_at_ampm'].iloc[0]) if not res.empty else "N/A"
    except:
        return "N/A"

@st.cache_data(ttl=120, show_spinner=False)
def get_available_dates():
    query = f"SELECT MIN(Date) as min_date, MAX(Date) as max_date FROM `{REV_TABLE_ID}`"
    try:
        df = client.query(query).to_dataframe()
        if not df.empty and not pd.isna(df['min_date'].iloc[0]):
            return df['min_date'].iloc[0], df['max_date'].iloc[0]
    except:
        pass
    return date.today(), date.today()

@st.cache_data(ttl=120, show_spinner=False)
def fetch_revenue_data(start_date, end_date):
    query = f"""
        SELECT * FROM `{REV_TABLE_ID}`
        WHERE Date BETWEEN '{start_date}' AND '{end_date}'
        AND Fee_paid > 0
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['Caller_name']  = df['Caller_name'].astype(str).str.strip()
        df['merge_key']    = df['Caller_name'].str.lower()
        df['Fee_paid']     = pd.to_numeric(df['Fee_paid'],     errors='coerce').fillna(0)
        df['Course_Price'] = pd.to_numeric(df['Course_Price'], errors='coerce').fillna(0)

        enr       = df['Enrollment'].astype(str).str.strip()
        enr_lower = enr.str.lower()
        src_lower = df['Source'].astype(str).str.lower()

        df['is_new_enrollment']       = enr_lower == 'new enrollment'
        df['is_balance_payment']      = enr_lower == 'new enrollment - balance payment'
        df['is_bootcamp_collection']  = enr_lower == 'bootcamp collections - balance payments'
        df['is_community_collection'] = enr_lower == 'community collections - balance payments'
        df['is_other_revenue']        = enr_lower == 'other revenue'
        df['is_empty_enrollment']     = enr == ''
        df['source_has_community']    = src_lower.str.contains('community', na=False)

        # Legacy compat
        df['is_new'] = df['is_new_enrollment']
    return df


# ─────────────────────────────────────────────
# TARGET / DESIGNATION RESOLUTION
# ─────────────────────────────────────────────

def _col(df, name):
    name_clean = name.strip().lower()
    match = next((c for c in df.columns if c.strip().lower() == name_clean), None)
    if match is None:
        raise KeyError(f"Column '{name}' not found. Available: {list(df.columns)}")
    return match

def resolve_targets(df_meta, start_date, end_date):
    months_needed = get_months_in_range(start_date, end_date)
    caller_col    = _col(df_meta, 'Caller Name')
    month_col     = _col(df_meta, 'Month')

    target_col = None
    for candidate in ['Target', 'target', 'TARGET', 'Monthly Target', 'Monthly target', 'Sales Target']:
        try:
            target_col = _col(df_meta, candidate)
            break
        except KeyError:
            continue

    if target_col is None:
        st.warning(f"⚠️ Target column not found. Sheet columns: `{list(df_meta.columns)}`")
        return {}

    months_ym = {(m.year, m.month) for m in months_needed}

    def _ym(val):
        try:
            if pd.isna(val):
                return None
            d = pd.to_datetime(val, dayfirst=True, errors='coerce')
            if pd.isna(d):
                return None
            return (d.year, d.month)
        except:
            return None

    relevant = df_meta[df_meta[month_col].apply(_ym).isin(months_ym)].copy()
    if relevant.empty:
        return {}

    dedup = relevant.drop_duplicates(subset=[caller_col, month_col])
    dedup[target_col] = pd.to_numeric(
        dedup[target_col].astype(str).str.replace(',', '', regex=False),
        errors='coerce'
    ).fillna(0)
    return dedup.groupby(caller_col)[target_col].sum().to_dict()

def resolve_designations(df_meta, start_date, end_date):
    months_needed = get_months_in_range(start_date, end_date)
    caller_col    = _col(df_meta, 'Caller Name')
    month_col     = _col(df_meta, 'Month')

    def safe_col(name):
        try:    return _col(df_meta, name)
        except: return None

    desig_col   = safe_col('Academic Counselor/TL/ATL')
    team_col    = safe_col('Team Name')
    vert_col    = safe_col('Vertical')
    analyst_col = safe_col('Analyst')

    months_ym = {(m.year, m.month) for m in months_needed}

    def _ym(val):
        try:
            if pd.isna(val):
                return None
            d = pd.to_datetime(val, dayfirst=True, errors='coerce')
            if pd.isna(d):
                return None
            return (d.year, d.month)
        except:
            return None

    relevant = df_meta[df_meta[month_col].apply(_ym).isin(months_ym)].copy()
    if relevant.empty:
        return {}

    relevant = relevant.sort_values(month_col, ascending=False)
    dedup    = relevant.drop_duplicates(subset=[caller_col], keep='first').set_index(caller_col)

    result = {}
    for caller in dedup.index:
        result[caller] = {
            'Academic Counselor/TL/ATL': dedup.at[caller, desig_col]   if desig_col   else '—',
            'Team Name':                 dedup.at[caller, team_col]     if team_col    else '—',
            'Vertical':                  dedup.at[caller, vert_col]     if vert_col    else '—',
            'Analyst':                   dedup.at[caller, analyst_col]  if analyst_col else '—',
        }
    return result


# ─────────────────────────────────────────────
# CALLER CLASSIFICATION + METRICS PROCESSING
# ─────────────────────────────────────────────

def classify_and_process(df, df_meta, start_date, end_date):
    target_map       = resolve_targets(df_meta, start_date, end_date)
    desig_map        = resolve_designations(df_meta, start_date, end_date)
    target_map_norm  = {str(k).strip().lower(): v for k, v in target_map.items()}
    desig_map_norm   = {str(k).strip().lower(): v for k, v in desig_map.items()}

    # Pre-compute working days ratio once for all callers
    months_count    = max(len(get_months_in_range(start_date, end_date)), 1)
    working_days    = count_working_days(start_date, end_date)
    till_day_ratio  = min(working_days / (20 * months_count), 1.0)

    calling_rows, collection_rows, both_rows = [], [], []

    for caller, grp in df.groupby('Caller_name'):
        if caller.strip().lower() in EXCLUDE_CALLERS:
            continue

        caller_key = caller.strip().lower()
        info       = desig_map_norm.get(caller_key, {})
        team       = str(info.get('Team Name', '—')).strip()
        target     = float(target_map_norm.get(caller_key, 0) or 0)

        till_day_target = round(target * till_day_ratio)

        enr_rev      = grp[grp['is_new_enrollment']]['Fee_paid'].sum()
        bal_rev      = grp[grp['is_balance_payment']]['Fee_paid'].sum()
        boot_coll    = grp[grp['is_bootcamp_collection']]['Fee_paid'].sum()
        comm_coll    = grp[grp['is_community_collection']]['Fee_paid'].sum()
        enrollments  = int(grp['is_new_enrollment'].sum())

        calling_rev    = enr_rev + bal_rev
        collection_rev = boot_coll + comm_coll
        total_rev      = calling_rev + collection_rev

        is_changemakers = team.lower() == 'changemakers'
        has_calling     = calling_rev > 0
        has_collection  = collection_rev > 0

        row = {
            'DESIGNATION'         : info.get('Academic Counselor/TL/ATL', '—'),
            'CALLER NAME'         : caller,
            'TEAM'                : team,
            'VERTICAL'            : info.get('Vertical', '—'),
            'TOTAL TARGET (₹)'    : target,
            'TILL DAY TARGET (₹)' : till_day_target,
            'ENROLLMENTS'         : enrollments,
            'ENROLLMENT REV'      : enr_rev,
            'BALANCE REV'         : bal_rev,
            'COMMUNITY COLLECTION': comm_coll,
            'BOOTCAMP COLLECTION' : boot_coll,
            'CALLING REVENUE'     : calling_rev,
            'COLLECTION REVENUE'  : collection_rev,
            'TOTAL REVENUE'       : total_rev,
            'raw_revenue'         : total_rev,
            'raw_target'          : target,
            'raw_enrollments'     : enrollments,
            'raw_calling_rev'     : calling_rev,
            'raw_collection_rev'  : collection_rev,
        }

        if is_changemakers:
            row['ACHIEVEMENT %'] = round(collection_rev / target * 100, 1) if target > 0 else 0.0
            collection_rows.append(row)
        elif has_calling and has_collection:
            row['ACHIEVEMENT %'] = round(total_rev / target * 100, 1) if target > 0 else 0.0
            both_rows.append(row)
        elif has_collection:
            row['ACHIEVEMENT %'] = round(collection_rev / target * 100, 1) if target > 0 else 0.0
            collection_rows.append(row)
        else:
            row['ACHIEVEMENT %'] = round(calling_rev / target * 100, 1) if target > 0 else 0.0
            calling_rows.append(row)

    def _to_df(rows, sort_col):
        if not rows:
            return pd.DataFrame()
        d = pd.DataFrame(rows).sort_values(sort_col, ascending=False).reset_index(drop=True)
        return d

    calling_df    = _to_df(calling_rows,    'raw_calling_rev')
    collection_df = _to_df(collection_rows, 'raw_collection_rev')
    both_df       = _to_df(both_rows,       'raw_revenue')

    return calling_df, collection_df, both_df


# ─────────────────────────────────────────────
# SUMMARY METRICS COMPUTATION
# ─────────────────────────────────────────────

def compute_summary_metrics(df):
    excl_mask = df['Caller_name'].str.strip().str.lower().isin(EXCLUDE_CALLERS)

    calling_rev = (
        df[~excl_mask & df['is_new_enrollment']]['Fee_paid'].sum() +
        df[~excl_mask & df['is_balance_payment']]['Fee_paid'].sum()
    )

    collection_rev = df[df['is_bootcamp_collection']]['Fee_paid'].sum()

    community_rev = (
        df[df['is_community_collection']]['Fee_paid'].sum() +
        df[df['is_other_revenue'] & df['source_has_community']]['Fee_paid'].sum() +
        df[
            df['is_new_enrollment'] &
            df['source_has_community'] &
            (df['Caller_name'].str.strip().str.lower() == 'direct')
        ]['Fee_paid'].sum()
    )

    direct_rev = df[
        (df['Caller_name'].str.strip().str.lower() == 'direct') &
        (~df['source_has_community']) &
        (df['is_other_revenue'] | df['is_new_enrollment'] | df['is_balance_payment'])
    ]['Fee_paid'].sum()

    dna_rev = df[df['is_empty_enrollment']]['Fee_paid'].sum()

    bootcamp_direct_rev = df[
        df['is_new_enrollment'] &
        (df['Caller_name'].str.strip().str.lower() == 'bootcamp - direct')
    ]['Fee_paid'].sum()

    total_rev = calling_rev + bootcamp_direct_rev + collection_rev + community_rev + direct_rev + dna_rev

    return {
        'total_rev'          : total_rev,
        'calling_rev'        : calling_rev,
        'bootcamp_direct_rev': bootcamp_direct_rev,
        'collection_rev'     : collection_rev,
        'community_rev'      : community_rev,
        'direct_rev'         : direct_rev,
        'dna_rev'            : dna_rev,
    }

# ─────────────────────────────────────────────
# ENROLLMENT SUMMARY COMPUTATION
# ─────────────────────────────────────────────

def compute_enrollment_metrics(df):
    caller_lower = df['Caller_name'].str.strip().str.lower()

    direct_enr    = int(df[
        df['is_new_enrollment'] &
        (caller_lower == 'direct') &
        (~df['source_has_community'])
    ].shape[0])

    bootcamp_enr  = int(df[
        df['is_new_enrollment'] &
        (caller_lower == 'bootcamp - direct')
    ].shape[0])

    caller_enr    = int(df[
        df['is_new_enrollment'] &
        (~caller_lower.isin(['direct', 'bootcamp - direct']))
    ].shape[0])

    community_enr = int(df[
        df['is_new_enrollment'] &
        (caller_lower == 'direct') &
        df['source_has_community']
    ].shape[0])

    total_enr = direct_enr + bootcamp_enr + caller_enr + community_enr

    return {
        'total_enr'    : total_enr,
        'direct_enr'   : direct_enr,
        'bootcamp_enr' : bootcamp_enr,
        'caller_enr'   : caller_enr,
        'community_enr': community_enr,
    }

# ─────────────────────────────────────────────
# TABLE RENDERING HELPER
# ─────────────────────────────────────────────

def render_perf_table(df, display_cols, total_overrides, sort_col, table_key):
    """Renders a styled performance table with medals and a TOTAL row."""
    if df.empty:
        st.info("No data available for this category in the selected period.")
        return

    d = df.copy().reset_index(drop=True)

    # Medals
    d.insert(0, 'Rank', '')
    for i, medal in enumerate(['🥇', '🥈', '🥉']):
        if i < len(d):
            d.at[i, 'Rank'] = medal

    # Format currency cols
    for col in ['ENROLLMENT REV', 'BALANCE REV', 'COMMUNITY COLLECTION',
                'BOOTCAMP COLLECTION', 'CALLING REVENUE', 'COLLECTION REVENUE',
                'TOTAL REVENUE', 'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)']:
        if col in d.columns:
            d[col] = d[col].apply(fmt_inr)

    if 'ACHIEVEMENT %' in d.columns:
        d['ACHIEVEMENT %'] = d['ACHIEVEMENT %'].apply(lambda x: f"{x}%")

    # Build total row
    total_dict = {c: '—' for c in ['Rank'] + display_cols}
    total_dict['Rank']        = ''
    total_dict['CALLER NAME'] = 'TOTAL'
    for k, v in total_overrides.items():
        total_dict[k] = v

    all_cols   = ['Rank'] + [c for c in display_cols if c in d.columns]
    total_row  = pd.DataFrame([{c: total_dict.get(c, '—') for c in all_cols}])
    final      = pd.concat([d[all_cols], total_row], ignore_index=True)

    st.dataframe(
        final.style.apply(style_total_rev, axis=1),
        column_order=all_cols,
        use_container_width=True,
        hide_index=True
    )


# ─────────────────────────────────────────────
# INSIGHTS
# ─────────────────────────────────────────────

def compute_revenue_insights(df, calling_df, collection_df, both_df, start_date, end_date):
    insights = []
    if df.empty:
        return insights

    month_label = start_date.strftime("%B %Y")

    _all_list = [d for d in [calling_df, collection_df, both_df] if not d.empty]
    all_agents = pd.concat(_all_list, ignore_index=True) if _all_list else pd.DataFrame()

    # ── 1. Top Calling Revenue Achiever ──
    _calling_pool_list = [d for d in [calling_df, both_df] if not d.empty]
    _calling_pool = pd.concat(_calling_pool_list, ignore_index=True) if _calling_pool_list else pd.DataFrame()
    if not _calling_pool.empty:
        top_c = _calling_pool.sort_values('raw_calling_rev', ascending=False).iloc[0]
        insights.append({
            "type": "good", "icon": "🏆",
            "title": f"Top Calling Revenue — {top_c['CALLER NAME']}",
            "body": (f"Achieved {fmt_inr(top_c['raw_calling_rev'])} in calling revenue with "
                     f"{top_c['ENROLLMENTS']} new enrollment(s) in {month_label}. "
                     f"Target achievement: {top_c['ACHIEVEMENT %']}%.")
        })

    # ── 2. Top Collection Revenue Achiever ──
    _coll_pool_list = [d for d in [collection_df, both_df] if not d.empty]
    _coll_pool = pd.concat(_coll_pool_list, ignore_index=True) if _coll_pool_list else pd.DataFrame()
    if not _coll_pool.empty:
        top_col = _coll_pool.sort_values('raw_collection_rev', ascending=False).iloc[0]
        insights.append({
            "type": "good", "icon": "🏦",
            "title": f"Top Collection Revenue — {top_col['CALLER NAME']}",
            "body": (f"Collected {fmt_inr(top_col['raw_collection_rev'])} in {month_label} "
                     f"across community and bootcamp collections. "
                     f"Team: {top_col['TEAM']}.")
        })

    # ── 3. Most Enrollments ──
    if not all_agents.empty and all_agents['raw_enrollments'].max() > 0:
        top_enr = all_agents.sort_values('raw_enrollments', ascending=False).iloc[0]
        insights.append({
            "type": "good", "icon": "🎓",
            "title": f"Most Enrollments — {top_enr['CALLER NAME']}",
            "body": (f"Closed {top_enr['raw_enrollments']} new enrollment(s) in {month_label}, "
                     f"highest among all callers. "
                     f"Calling revenue generated: {fmt_inr(top_enr['raw_calling_rev'])}.")
        })

    # ── 4. Best Target Achievement ──
    if not all_agents.empty:
        _with_target = all_agents[all_agents['raw_target'] > 0]
        if not _with_target.empty:
            top_ach = _with_target.sort_values('ACHIEVEMENT %', ascending=False).iloc[0]
            insights.append({
                "type": "good" if top_ach['ACHIEVEMENT %'] >= 80 else "warn", "icon": "🎯",
                "title": f"Best Target Achievement — {top_ach['CALLER NAME']}",
                "body": (f"Achieved {top_ach['ACHIEVEMENT %']}% of their "
                         f"{fmt_inr(top_ach['raw_target'])} target in {month_label}. "
                         f"Revenue: {fmt_inr(top_ach['raw_revenue'])}. Team: {top_ach['TEAM']}.")
            })

    # ── 5. Focus Required — worst target achievement ──
    if not all_agents.empty:
        _with_target = all_agents[
            (all_agents['raw_target'] > 0) &
            (all_agents['raw_revenue'] > 0)
        ]
        if len(_with_target) > 1:
            worst = _with_target.sort_values('ACHIEVEMENT %').iloc[0]
            if worst['ACHIEVEMENT %'] < 60:
                insights.append({
                    "type": "bad", "icon": "⚠️",
                    "title": f"Focus Required — {worst['CALLER NAME']}",
                    "body": (f"Only {worst['ACHIEVEMENT %']}% of "
                             f"{fmt_inr(worst['raw_target'])} target achieved in {month_label}. "
                             f"Revenue so far: {fmt_inr(worst['raw_revenue'])}. "
                             f"Team: {worst['TEAM']}. Needs immediate attention.")
                })

     # ── 6. Callers with target but zero revenue (calling agents only) ──
    _calling_only_list = [d for d in [calling_df, both_df] if not d.empty]
    _calling_only = pd.concat(_calling_only_list, ignore_index=True) if _calling_only_list else pd.DataFrame()

    if not _calling_only.empty:
        _with_target   = _calling_only[_calling_only['raw_target'] > 0]
        _zero_rev      = _with_target[_with_target['raw_calling_rev'] == 0]
        _zero_count    = len(_zero_rev)
        _total_callers = len(_with_target)

        if _zero_count > 0:
            _zero_names = ', '.join(_zero_rev['CALLER NAME'].head(3).tolist())
            _more       = f" and {_zero_count - 3} more" if _zero_count > 3 else ""
            insights.append({
                "type": "bad", "icon": "🚨",
                "title": f"{_zero_count} of {_total_callers} Callers Have Zero Revenue in {month_label}",
                "body": (f"{_zero_names}{_more} have an assigned target but no enrollment "
                         f"or balance revenue recorded in the selected period. "
                         f"Immediate follow-up recommended to unblock closures.")
            })
        else:
            _below_50  = _with_target[_with_target['raw_calling_rev'] / _with_target['raw_target'] * 100 < 50]
            _b50_count = len(_below_50)
            if _b50_count > 0:
                _top_team = (
                    _calling_only.groupby('TEAM')['raw_calling_rev']
                    .sum().sort_values(ascending=False).index[0]
                )
                insights.append({
                    "type": "warn", "icon": "📊",
                    "title": f"{_b50_count} Caller(s) Below 50% Achievement in {month_label}",
                    "body": (f"All callers have some revenue but {_b50_count} are below 50% of their "
                             f"calling target. Best performing team is {_top_team}. "
                             f"Focus support on underperforming callers to improve month-end numbers.")
                })
            else:
                _top_team = (
                    _calling_only.groupby('TEAM')['raw_calling_rev']
                    .sum().sort_values(ascending=False).index[0]
                )
                _top_team_rev = _calling_only.groupby('TEAM')['raw_calling_rev'].sum().max()
                insights.append({
                    "type": "good", "icon": "🌟",
                    "title": f"Strong Month — All Callers On Track in {month_label}",
                    "body": (f"Every caller with a target has recorded enrollment revenue in the selected period. "
                             f"Leading team is {_top_team} with {fmt_inr(_top_team_rev)} in calling revenue. "
                             f"Keep monitoring till-day targets to sustain momentum through month-end.")
                })

    return insights[:6]

def generate_helper_pdf_bytes() -> bytes:
    buffer = io.BytesIO()

    GREEN_DARK  = colors.HexColor("#064e3b")
    GREEN_MID   = colors.HexColor("#065f46")
    GREEN_LIGHT = colors.HexColor("#10B981")
    GREEN_PALE  = colors.HexColor("#DCFCE7")
    GREEN_ROW   = colors.HexColor("#F0FDF4")
    GREY_DARK   = colors.HexColor("#374151")
    GREY_MID    = colors.HexColor("#6B7280")
    WHITE       = colors.white
    BLACK       = colors.HexColor("#111827")
    W, H        = A4

    def s(name, **kw):
        defaults = dict(fontName='Helvetica', fontSize=9,
                        textColor=BLACK, spaceAfter=3, leading=14)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    S = {
        'body'      : s('body'),
        'label'     : s('label',   fontName='Helvetica-Bold', fontSize=8,
                         textColor=GREEN_DARK, spaceAfter=1),
        'formula'   : s('formula', fontName='Helvetica-Oblique', fontSize=8.5,
                         textColor=colors.HexColor("#065f46"),
                         backColor=GREEN_PALE, leftIndent=8, rightIndent=8),
        'footer'    : s('footer',  fontSize=7.5, textColor=GREY_MID,
                         alignment=TA_CENTER),
    }

    class CoverBlock(Flowable):
        def __init__(self, w):
            Flowable.__init__(self)
            self.w = w
            self.height = 90
        def draw(self):
            c = self.canv
            c.setFillColor(GREEN_DARK);  c.rect(0, 52, self.w, 38, fill=1, stroke=0)
            c.setFillColor(GREEN_MID);   c.rect(0, 22, self.w, 30, fill=1, stroke=0)
            c.setFillColor(colors.HexColor("#065f46")); c.rect(0, 0, self.w, 22, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 22)
            c.drawCentredString(self.w/2, 66, "REVENUE METRICS DASHBOARD")
            c.setFillColor(colors.HexColor("#A7F3D0")); c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(self.w/2, 34, "Logic & Metric Reference Guide")
            c.setFillColor(colors.HexColor("#D1FAE5")); c.setFont("Helvetica", 8.5)
            c.drawCentredString(self.w/2, 8,
                "LawSikho & Skill Arbitrage  \u00b7  Sales & Operations Team  \u00b7  Internal Use Only")

    class SectionBanner(Flowable):
        def __init__(self, icon, title, color=None, w=None):
            Flowable.__init__(self)
            self.icon = icon; self.title = title
            self.color = color or GREEN_DARK
            self.w = w or (W - 30*mm); self.height = 22
        def draw(self):
            c = self.canv
            c.setFillColor(self.color)
            c.roundRect(0, 0, self.w, self.height, 4, fill=1, stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold", 11)
            c.drawString(10, 6, f"{self.icon}  {self.title}")

    def btable(rows, cw=None):
        cw = cw or [42*mm, 118*mm]
        data = [[Paragraph(f"<b>{r[0]}</b>", S['label']),
                 Paragraph(r[1], S['body'])] for r in rows]
        t = Table(data, colWidths=cw, hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(0,-1), GREEN_PALE),
            ('VALIGN',        (0,0),(-1,-1),'TOP'),
            ('GRID',          (0,0),(-1,-1),0.3, colors.HexColor("#D1FAE5")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE, GREEN_ROW]),
            ('LEFTPADDING',   (0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',    (0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        return t

    def ltable(rows):
        data = [[Paragraph(f"<b>{r[0]}</b>", S['label']),
                 Paragraph(r[1], S['formula'])] for r in rows]
        t = Table(data, colWidths=[50*mm, 110*mm], hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN',        (0,0),(-1,-1),'TOP'),
            ('GRID',          (0,0),(-1,-1),0.3, colors.HexColor("#A7F3D0")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE, GREEN_ROW]),
            ('LEFTPADDING',   (0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',    (0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        return t

    SP  = Spacer
    HR  = lambda: HRFlowable(width="100%", thickness=0.6,
                              color=colors.HexColor("#A7F3D0"),
                              spaceAfter=6, spaceBefore=4)
    BAN = SectionBanner
    cw  = W - 30*mm

    story = [
        SP(1,18*mm), CoverBlock(cw), SP(1,10*mm),
        Paragraph("This document explains every metric, table, and highlight card in the "
                  "Revenue Metrics Dashboard — a quick reference for the Sales & Operations team.", S['body']),
        SP(1,4*mm),

        # ── Section 1 ──
        BAN("🏆","SECTION 1 — TOP 3 REVENUE HIGHLIGHTS"), SP(1,3*mm),
        Paragraph("Three cards at the top of the dashboard — each shows the single best performer "
                  "in one dimension for the selected date range.", S['body']), SP(1,2*mm),
        btable([
            ("🥇 Top Revenue — Caller",    "Caller with highest Calling Revenue (Enrollment Rev + Balance Rev). Excludes 'direct' and 'bootcamp-direct'."),
            ("🎓 Most Enrollments",         "Caller with most rows where Enrollment = 'New Enrollment'. Covers all agent types."),
            ("🥇 Top Revenue — Collection", "Caller with highest Collection Revenue (Community Collections + Bootcamp Collections). From Collection table only."),
        ]), SP(1,4*mm),

        # ── Section 2 ──
        BAN("💵","SECTION 2 — REVENUE SUMMARY METRICS"), SP(1,3*mm),
        Paragraph("Full-picture revenue breakdown. Filter: Fee Paid > 0 applied globally.", S['body']), SP(1,2*mm),
        ltable([
            ("Total Revenue\n(EXCL. Services)",    "Calling + Bootcamp-Direct + Bootcamp-Collection + Community + Direct/Other + DNA revenue."),
            ("Calling Revenue\n(INCL. Funnel)",    "Fee Paid where Enrollment = 'New Enrollment' OR 'New Enrollment - Balance Payment', caller NOT in {direct, bootcamp-direct}."),
            ("Bootcamp-Direct\nRevenue",            "Fee Paid where Enrollment = 'New Enrollment' AND Caller = 'bootcamp-direct'."),
            ("Bootcamp-Collection\nRevenue",        "Fee Paid where Enrollment = 'Bootcamp Collections - Balance Payments'."),
            ("Community Revenue\n(Direct+Collection)", "Fee Paid from: (a) Community Collections rows, (b) Other Revenue with community Source, (c) New Enrollment by 'direct' with community Source."),
            ("Direct/Other Revenue\n(INCL. Funnel)","Fee Paid where Caller='direct', Source has no 'community', Enrollment in {Other Revenue, New Enrollment, Balance Payment}."),
            ("DNA / Not Updated Yet",               "Fee Paid where Enrollment column is blank. Not yet categorised in BigQuery."),
        ]), SP(1,4*mm),

        # ── Section 3 ──
        BAN("🎓","SECTION 3 — ENROLLMENT SUMMARY METRICS"), SP(1,3*mm),
        Paragraph("Counts ONLY rows where Enrollment = 'New Enrollment'. Balance payments and collections are excluded.", S['body']), SP(1,2*mm),
        ltable([
            ("Total Enrollments",            "All New Enrollment rows across all callers."),
            ("Caller Enrollments",           "New Enrollment rows where Caller is NOT 'direct' or 'bootcamp-direct'."),
            ("Direct Enrollments",           "New Enrollment by 'direct' caller AND Source has no 'community'."),
            ("Bootcamp-Direct Enrollments",  "New Enrollment where Caller = 'bootcamp-direct'."),
            ("Community-Direct Enrollments", "New Enrollment by 'direct' caller AND Source contains 'community'."),
        ]), SP(1,4*mm),

        # ── Section 4 ──
        BAN("📞","SECTION 4 — CALLER REVENUE PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Calling agents with Calling Revenue > 0, no collection revenue, not Changemakers team. Sorted by Calling Revenue descending.", S['body']), SP(1,2*mm),
        btable([
            ("DESIGNATION",         "Role from team sheet: Academic Counselor, TL, ATL, etc."),
            ("TOTAL TARGET (₹)",    "Sum of monthly targets from team sheet for all months in selected range."),
            ("TILL DAY TARGET (₹)", "Total Target × (Mon-Fri days elapsed ÷ (20 × months in range)). Capped at 1.0."),
            ("ENROLLMENTS",         "Count of New Enrollment rows for this caller."),
            ("ENROLLMENT REV",      "Fee Paid where Enrollment = 'New Enrollment' for this caller."),
            ("BALANCE REV",         "Fee Paid where Enrollment = 'New Enrollment - Balance Payment' for this caller."),
            ("CALLING REVENUE",     "Enrollment Rev + Balance Rev."),
            ("ACHIEVEMENT %",       "Calling Revenue ÷ Total Target × 100."),
        ]), SP(1,4*mm),

        # ── Section 5 ──
        BAN("🏦","SECTION 5 — COLLECTION CALLER REVENUE PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Callers with Collection Revenue > 0 and no calling revenue. Changemakers team always here. Sorted by Collection Revenue descending.", S['body']), SP(1,2*mm),
        btable([
            ("COMMUNITY COLLECTION", "Fee Paid where Enrollment = 'Community Collections - Balance Payments'."),
            ("BOOTCAMP COLLECTION",  "Fee Paid where Enrollment = 'Bootcamp Collections - Balance Payments'."),
            ("COLLECTION REVENUE",   "Community Collection + Bootcamp Collection."),
            ("ACHIEVEMENT %",        "Collection Revenue ÷ Total Target × 100."),
        ]), SP(1,4*mm),

        # ── Section 6 ──
        BAN("📞🏦","SECTION 6 — CALLING + COLLECTION CALLER REVENUE PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Callers with BOTH Calling Revenue > 0 AND Collection Revenue > 0, not Changemakers. Sorted by Total Revenue descending.", S['body']), SP(1,2*mm),
        btable([
            ("TOTAL REVENUE",  "Calling Revenue + Collection Revenue."),
            ("ACHIEVEMENT %",  "Total Revenue ÷ Total Target × 100."),
            ("Other columns",  "Same definitions as Sections 4 and 5."),
        ]), SP(1,4*mm),

        # ── Section 7 ──
        BAN("📞","SECTION 7 — CALLER REVENUE TEAM PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Section 4 callers grouped by team. Insights & Leaderboard tab only. Sorted by Calling Revenue descending.", S['body']), SP(1,2*mm),
        ltable([
            ("Callers",         "Count of agents from this team in the Caller table."),
            ("Total Target",    "Sum of all agent targets for this team."),
            ("Till Day Target", "Sum of all agent till-day targets for this team."),
            ("Calling Revenue", "Sum of Calling Revenue across all agents in this team."),
            ("Achievement %",   "Team Calling Revenue ÷ Team Total Target × 100."),
        ]), SP(1,4*mm),

        # ── Section 8 ──
        BAN("🏦","SECTION 8 — COLLECTION CALLER TEAM REVENUE PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Section 5 callers grouped by team. Sorted by Collection Revenue descending.", S['body']), SP(1,2*mm),
        ltable([
            ("Community Collection", "Sum of Community Collection revenue for this team."),
            ("Bootcamp Collection",  "Sum of Bootcamp Collection revenue for this team."),
            ("Collection Revenue",   "Community + Bootcamp Collection total for this team."),
            ("Achievement %",        "Team Collection Revenue ÷ Team Total Target × 100."),
        ]), SP(1,4*mm),

        # ── Section 9 ──
        BAN("📞🏦","SECTION 9 — CALLING + COLLECTION CALLER TEAM REVENUE PERFORMANCE TABLE"), SP(1,3*mm),
        Paragraph("Section 6 callers grouped by team. Sorted by Total Revenue descending.", S['body']), SP(1,2*mm),
        ltable([
            ("Calling Revenue",      "Sum of Calling Revenue for dual-stream agents in this team."),
            ("Community Collection", "Sum of Community Collection revenue."),
            ("Bootcamp Collection",  "Sum of Bootcamp Collection revenue."),
            ("Total Revenue",        "Calling + Community + Bootcamp Collection for this team."),
            ("Achievement %",        "Team Total Revenue ÷ Team Total Target × 100."),
        ]), SP(1,4*mm),

        # ── Glossary ──
        BAN("📖","KEY TERMS GLOSSARY", color=GREY_DARK), SP(1,3*mm),
        btable([
            ("New Enrollment",       "A fresh admission. Counts toward enrollment metrics and Calling Revenue."),
            ("Balance Payment",      "Remaining fee from a prior enrollment. NOT a new enrollment."),
            ("Bootcamp Collections", "Balance payments from bootcamp-enrolled students."),
            ("Community Collections","Balance payments from community-channel students."),
            ("DNA / Not Updated",    "Rows with blank Enrollment. Tracked separately in summary."),
            ("direct",               "Pseudo-caller for organic closures. Excluded from agent tables."),
            ("bootcamp-direct",      "Pseudo-caller for bootcamp direct admissions. Tracked separately."),
            ("Till Day Target",      "Daily-prorated target: Total Target x (Working Days / (20 x Months)). Working Days = Mon-Fri in selected range."),
            ("Changemakers",         "Special team always routed to Collection table regardless of calling revenue."),
        ], cw=[44*mm, 116*mm]),

        SP(1,8*mm), HR(),
        Paragraph("Designed by Amit Ray  \u00b7  amitray@lawsikho.com  \u00b7  "
                  "For Internal Use of Sales and Operations Team Only. All Rights Reserved.", S['footer']),
    ]

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=14*mm,  bottomMargin=14*mm,
        title="Revenue Metrics — Logic Reference Guide",
        author="Amit Ray",
    )
    doc.build(story)
    return buffer.getvalue()

def generate_calling_helper_pdf_bytes() -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.platypus import Flowable
    from reportlab.lib.enums import TA_CENTER
    import io

    buffer = io.BytesIO()
    ORANGE_DARK=colors.HexColor("#7c2d12"); ORANGE_MID=colors.HexColor("#431407")
    ORANGE_PALE=colors.HexColor("#FEF3E8"); ORANGE_ROW=colors.HexColor("#FFF8F3")
    GREY_DARK=colors.HexColor("#374151"); GREY_MID=colors.HexColor("#6B7280")
    WHITE=colors.white; BLACK=colors.HexColor("#111827"); W,H=A4

    def s(name,**kw):
        d=dict(fontName='Helvetica',fontSize=9,textColor=BLACK,spaceAfter=3,leading=14)
        d.update(kw); return ParagraphStyle(name,**d)

    S={'body':s('body'),
       'label':s('label',fontName='Helvetica-Bold',fontSize=8,textColor=ORANGE_DARK,spaceAfter=1),
       'formula':s('formula',fontName='Helvetica-Oblique',fontSize=8.5,textColor=colors.HexColor("#7c2d12"),backColor=ORANGE_PALE,leftIndent=8,rightIndent=8),
       'footer':s('footer',fontSize=7.5,textColor=GREY_MID,alignment=TA_CENTER)}

    class CoverBlock(Flowable):
        def __init__(self,w): Flowable.__init__(self); self.w=w; self.height=90
        def draw(self):
            c=self.canv
            c.setFillColor(ORANGE_DARK); c.rect(0,52,self.w,38,fill=1,stroke=0)
            c.setFillColor(ORANGE_MID);  c.rect(0,22,self.w,30,fill=1,stroke=0)
            c.setFillColor(colors.HexColor("#1c0700")); c.rect(0,0,self.w,22,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold",22)
            c.drawCentredString(self.w/2,66,"CALLING METRICS DASHBOARD")
            c.setFillColor(colors.HexColor("#FBBF24")); c.setFont("Helvetica-Bold",11)
            c.drawCentredString(self.w/2,34,"Logic & Metric Reference Guide")
            c.setFillColor(colors.HexColor("#FDE68A")); c.setFont("Helvetica",8.5)
            c.drawCentredString(self.w/2,8,"LawSikho & Skill Arbitrage  \u00b7  Sales & Operations Team  \u00b7  Internal Use Only")

    class SectionBanner(Flowable):
        def __init__(self,icon,title,color=None,w=None):
            Flowable.__init__(self); self.icon=icon; self.title=title
            self.color=color or ORANGE_DARK; self.w=w or (W-30*mm); self.height=22
        def draw(self):
            c=self.canv; c.setFillColor(self.color)
            c.roundRect(0,0,self.w,self.height,4,fill=1,stroke=0)
            c.setFillColor(WHITE); c.setFont("Helvetica-Bold",11)
            c.drawString(10,6,f"{self.icon}  {self.title}")

    def btable(rows,cw=None):
        cw=cw or [44*mm,116*mm]
        data=[[Paragraph(f"<b>{r[0]}</b>",S['label']),Paragraph(r[1],S['body'])] for r in rows]
        t=Table(data,colWidths=cw,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,-1),ORANGE_PALE),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#FDE68A")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,ORANGE_ROW]),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        return t

    def ltable(rows):
        data=[[Paragraph(f"<b>{r[0]}</b>",S['label']),Paragraph(r[1],S['formula'])] for r in rows]
        t=Table(data,colWidths=[52*mm,108*mm],hAlign='LEFT')
        t.setStyle(TableStyle([
            ('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),0.3,colors.HexColor("#FDE68A")),
            ('ROWBACKGROUNDS',(0,0),(-1,-1),[WHITE,ORANGE_ROW]),
            ('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
        return t

    SP=Spacer; BAN=SectionBanner; cw=W-30*mm
    HR=lambda: HRFlowable(width="100%",thickness=0.6,color=colors.HexColor("#FBBF24"),spaceAfter=6,spaceBefore=4)

    story=[
        SP(1,18*mm),CoverBlock(cw),SP(1,10*mm),
        Paragraph("This document explains every metric, table, tab, and column in the Calling Metrics Dashboard. Use it as a quick reference to understand how each number is calculated and what each section means.",S['body']),
        SP(1,6*mm),
        BAN("📋","SECTION 1 — DASHBOARD TABS OVERVIEW"),SP(1,3*mm),
        Paragraph("The dashboard has three tabs. Each serves a different purpose.",S['body']),SP(1,2*mm),
        btable([
            ("🚀 Dynamic Dashboard","The main report tab. Shows agent-level performance for the selected date range — Top 3 highlights, Summary KPIs, and the full Agent Performance Table. Click 'Generate Dynamic Report' in the sidebar to load it."),
            ("📅 Duration Report","A team-by-team breakdown showing call duration metrics only. Each team gets its own table sorted by call duration. TLs and ATLs are grouped separately at the bottom. Useful for sharing per-team performance without exposing cross-team data. Click 'Generate Duration Report' in the sidebar."),
            ("🧠 Insights & Leaderboard","Auto-populated from whichever report was generated last. Shows 5-6 auto-generated team insights and a Team Leaderboard table. No separate button needed — switch to this tab after generating any report."),
        ]),SP(1,6*mm),
        BAN("🏆","SECTION 2 — TOP 3 PERFORMANCE HIGHLIGHTS"),SP(1,3*mm),
        Paragraph("Three highlight cards at the top of the Dynamic Dashboard. Each picks the single best agent in one dimension.",S['body']),SP(1,2*mm),
        btable([
            ("🥇 Top Performer","Agent with the highest total Call Duration for calls above 3 minutes (raw_dur_sec). Agents are sorted by qualifying call duration descending — the top row wins this card."),
            ("✆ Highest Calls","Agent with the highest Total Calls count across all statuses (answered + missed). Sorted separately — a different agent may win this card."),
            ("🗣️ Deep Engagement","Agent with the most calls lasting 20 minutes or more (duration >= 1200 seconds). Signals high-quality prospect conversations."),
        ]),SP(1,6*mm),
        BAN("📊","SECTION 3 — SUMMARY METRICS (KPI CARDS)"),SP(1,3*mm),
        Paragraph("Eight KPI cards shown below the Top 3 highlights. Aggregate numbers across ALL agents and sources for the selected date range.",S['body']),SP(1,2*mm),
        ltable([
            ("Total Calls","Count of all call rows across Acefone + Ozonetel + Manual after filters applied."),
            ("Acefone Calls","Count of rows where source = 'Acefone'."),
            ("Ozonetel Calls","Count of rows where source = 'Ozonetel'."),
            ("Manual Calls","Count of rows where source = 'Manual'. Calls logged manually by agents and approved — not system-generated CDR."),
            ("Unique Leads","Count of distinct phone numbers across all sources. One lead dialled multiple times still counts as 1 unique lead."),
            ("Pick-Up Ratio","Answered Calls / Total Calls x 100, rounded to nearest whole percent. Answered = rows where status = 'answered'."),
            ("Active Callers","Count of distinct agents in the report after all filters. Only agents with at least one call in the date range are counted."),
            ("Avg Prod Hrs","Average Productive Hours across all active agents. Productive Hours = (10 hrs x active days) - total break time >= 15 mins. Shown as Xh Ym."),
        ]),SP(1,6*mm),
        BAN("📋","SECTION 4 — AGENT PERFORMANCE TABLE"),SP(1,3*mm),
        Paragraph("Main data table in the Dynamic Dashboard. One row per active agent, sorted by Call Duration > 3 Mins descending. Top 3 rows get medal emojis. A bold TOTAL row is appended at the bottom.",S['body']),SP(1,2*mm),
        btable([
            ("Rank","Medal emoji for top 3 agents by call duration: Gold, Silver, Bronze."),
            ("IN/OUT TIME","First call start (In) and last call end (Out) per day. Format: DD/MM: In HH:MM AM/PM . Out HH:MM AM/PM. Derived from call_starttime and call_endtime after IST conversion."),
            ("CALLER","Agent name from the team sheet, normalised via lowercase merge key. Falls back to raw system name if not matched."),
            ("TEAM","Team name from the team sheet. Shows 'Others' if the agent is unmatched."),
            ("TOTAL CALLS","All calls for this agent in the date range — all statuses combined."),
            ("CALL STATUS","'X Ans / Y Unans' — count of answered and missed/unanswered calls for this agent."),
            ("PICK UP RATIO %","Answered / Total Calls x 100 for this agent, rounded to nearest whole percent."),
            ("CALLS > 3 MINS","Count of calls where duration >= 180 seconds. Qualifying threshold for duration metrics."),
            ("CALLS 15-20 MINS","Count of calls where duration >= 900 seconds AND < 1200 seconds. Mid-range engagement."),
            ("20+ MIN CALLS","Count of calls where duration >= 1200 seconds. Deep engagement indicator."),
            ("CALL DURATION > 3 MINS","Sum of duration for calls >= 3 minutes, shown as Xh Ym."),
            ("PRODUCTIVE HOURS","(10 hrs x active days) - total break time >= 15 mins. Shown as Xh Ym."),
            ("BREAKS (>=15 MINS)","Gaps between calls of 15+ minutes shown per day with time ranges. Gaps < 15 mins are ignored."),
            ("REMARKS","Auto-flagged issues: Late Check-In (first call after 10:15 AM), Early Check-Out (last call before 8 PM), Low Calls (<40 qualifying/day), Low Duration (<3h 15m/day), Excessive Breaks (>2 breaks >= 15 mins/day), Less Productive (<5 hrs productive/day)."),
        ],cw=[46*mm,114*mm]),SP(1,6*mm),
        BAN("📅","SECTION 5 — DURATION REPORT TAB"),SP(1,3*mm),
        Paragraph("Generates a simplified shareable table per team showing duration columns only — no break details or remarks.",S['body']),SP(1,2*mm),
        btable([
            ("Team separation","Each team gets its own section and table. Teams with zero qualifying duration are skipped entirely."),
            ("TL / ATL separation","Agents flagged as TL, ATL, AD, Team Lead, or Team Leader in the team sheet are shown in a single 'TL Duration Report' section at the bottom. Only TLs with > 5 mins qualifying duration are included."),
            ("Columns shown","CALLER, TOTAL CALLS, CALL STATUS, PICK UP RATIO %, CALLS > 3 MINS, CALLS 15-20 MINS, 20+ MIN CALLS, CALL DURATION > 3 MINS. Same definitions as Section 4."),
            ("Sorting","Within each team table, agents are sorted by Call Duration > 3 Mins descending."),
            ("TOTAL row","Each team table has a TOTAL row summing calls and duration."),
            ("CDR per team","Each team section has its own Download CDR button exporting only that team's raw records."),
        ]),SP(1,6*mm),
        BAN("🏅","SECTION 6 — TEAM LEADERBOARD (INSIGHTS TAB)"),SP(1,3*mm),
        Paragraph("Appears in the Insights tab. Aggregates all agents by team, ranked by total call duration descending. Only shown when no Team or Name filter is active.",S['body']),SP(1,2*mm),
        ltable([
            ("Team","Team name from the team sheet."),
            ("Agents","Count of distinct agents from this team in the report."),
            ("Total Calls","Sum of all calls across all agents in this team."),
            ("Total Dur (h)","Sum of qualifying call duration (>3 min) in hours, 1 decimal place."),
            ("Avg Dur/Agent (h)","Total Duration divided by agent count for this team, in hours."),
            ("Avg Prod Hrs (h)","Average productive hours per agent in this team, in hours."),
            ("20+ Min Calls","Sum of 20+ minute calls across all agents in this team."),
            ("Medal","Gold, Silver, Bronze for the top 3 teams by Total Duration."),
        ]),SP(1,6*mm),
        BAN("📥","SECTION 7 — CDR DOWNLOAD COLUMNS"),SP(1,3*mm),
        Paragraph("The Download CDR button exports a CSV of raw call detail records. Each row is one call.",S['body']),SP(1,2*mm),
        btable([
            ("client_number","Lead phone number. Unique lead identifier."),
            ("call_datetime","Original timestamp from the source system (UTC). For Ozonetel: call start. For Acefone: call end."),
            ("call_starttime_clean","Call start time in IST, timezone stripped. Used for break and productive hours calculations."),
            ("call_endtime_clean","Call end time in IST, timezone stripped. For Acefone: call_datetime. For Ozonetel: start + duration."),
            ("call_duration","Call duration in seconds. Zero-duration answered calls from Ozonetel are excluded before ingestion."),
            ("status","Call outcome: 'answered' or 'missed'. Ozonetel 'unanswered' mapped to 'missed'."),
            ("direction","Call direction: 'outbound' or 'inbound'. Ozonetel 'manual' mapped to 'outbound'."),
            ("service","Service or campaign name (Acefone only)."),
            ("reason","Disposition or reason code. For Manual calls this is the Approver name."),
            ("call_owner","Agent name after team sheet normalisation. Raw system name replaced by canonical Caller Name."),
            ("Call Date","Date of the call only. Used for day-level grouping."),
            ("updated_at_ampm","Timestamp when the record was last written to BigQuery, in AM/PM format."),
            ("Team Name","Team name from the team sheet, merged on lowercase agent name."),
            ("Vertical","Business vertical from the team sheet (e.g. Lawsikho, Skill Arbitrage)."),
            ("Analyst","Analyst name from the team sheet, if populated."),
            ("source","Data source: 'Acefone', 'Ozonetel', or 'Manual'."),
        ],cw=[46*mm,114*mm]),SP(1,6*mm),
        BAN("📖","KEY TERMS GLOSSARY",color=GREY_DARK),SP(1,3*mm),
        btable([
            ("Qualifying Call","Any call with duration >= 180 seconds (3 minutes). Used for all duration metrics and performance flags."),
            ("Office Hours","10:00 AM to 8:00 PM IST (10 hours = 36,000 seconds). Reference window for breaks and productive hours."),
            ("Break","A gap between consecutive calls >= 900 seconds (15 minutes). Shorter gaps are ignored."),
            ("Productive Hours","(10 hrs x active days) - total break seconds. Expressed as Xh Ym."),
            ("Late Check-In","First call of the day starts after 10:15 AM IST."),
            ("Early Check-Out","Last call of the day ends before 8:00 PM IST."),
            ("Low Calls","Fewer than 40 qualifying calls (>3 min) in a single day."),
            ("Low Duration","Total qualifying duration < 3h 15m (11,700 seconds) in a single day."),
            ("Excessive Breaks","More than 2 breaks >= 15 minutes in a single day."),
            ("Less Productive","Productive seconds < 5 hours (18,000 seconds) in a single day."),
            ("Merge Key","Lowercase-stripped agent name used to join call data with the team sheet."),
            ("IST","Indian Standard Time (UTC+5:30). All timestamps are converted to IST for display and calculations."),
        ],cw=[46*mm,114*mm]),
        SP(1,8*mm),HR(),
        Paragraph("Designed by Amit Ray  \u00b7  amitray@lawsikho.com  \u00b7  For Internal Use of Sales and Operations Team Only. All Rights Reserved.",S['footer']),
    ]

    doc=SimpleDocTemplate(buffer,pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=14*mm,title="Calling Metrics — Logic Reference Guide",author="Amit Ray")
    doc.build(story)
    return buffer.getvalue()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────

min_d, max_d = get_available_dates()

def build_month_options(min_date, max_date):
    options, cur = {}, date(min_date.year, min_date.month, 1)
    end = date(max_date.year, max_date.month, 1)
    while cur <= end:
        options[cur.strftime("%B %Y")] = cur
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return options

month_options        = build_month_options(min_d, max_d)
st.sidebar.markdown("""
<div style='padding:.6rem 0 .4rem; text-align:center;'>
    <div style='display:flex; align-items:center; justify-content:center; gap:0; margin-bottom:.3rem;'>
        <span style='font-size:.85rem; font-weight:700; color:#FFFFFF; letter-spacing:-.3px;'>LawSikho</span>
        <div style='width:1px; height:18px; margin:0 .6rem;
                    background:linear-gradient(180deg,transparent,rgba(16,185,129,.9),transparent);
                    box-shadow:0 0 6px rgba(16,185,129,.5);'></div>
        <span style='font-size:.85rem; font-weight:700; color:#FFFFFF; letter-spacing:-.3px;'>Skill Arbitrage</span>
    </div>
    <div style='font-size:.58rem; color:rgba(255,255,255,.3); letter-spacing:.8px;
                font-family:monospace; margin-bottom:.9rem;'>India Learning 📖 India Earning</div>
    <div style='font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;
                color:var(--text-muted,#6B7280);margin-bottom:.5rem;'>Report Controls</div>
</div>
""", unsafe_allow_html=True)

selected_month_label = st.sidebar.selectbox("🗓️ Month", options=list(reversed(list(month_options.keys()))))
selected_month_date  = month_options[selected_month_label]

min_d = pd.Timestamp(min_d).date()
max_d = pd.Timestamp(max_d).date()

if selected_month_date is not None:
    s           = pd.Timestamp(selected_month_date).date()
    next_month  = (s.replace(day=28) + timedelta(days=4)).replace(day=1)
    month_end   = next_month - timedelta(days=1)
    default_start = max(s, min_d)
    default_end   = min(month_end, max_d)
    if default_start > default_end:
        default_start = default_end
else:
    default_start = default_end = max_d

selected_dates = st.sidebar.date_input(
    "📅 Date Range",
    value=(default_start, default_end),
    min_value=min_d, max_value=max_d, format="DD-MM-YYYY"
)

if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_date, end_date = selected_dates
else:
    start_date = end_date = selected_dates if not isinstance(selected_dates, tuple) else selected_dates[0]

teams, verticals, df_team_mapping = get_metadata()
selected_vertical = st.sidebar.multiselect("👑 Filter by Vertical", options=verticals)
selected_team     = st.sidebar.multiselect("👥 Filter by Team",     options=teams)
search_query      = st.sidebar.text_input("👤 Search Caller Name")

st.sidebar.markdown("<div style='margin:.5rem 0'></div>", unsafe_allow_html=True)
gen_report   = st.sidebar.button("💰 Generate Revenue Report")
st.sidebar.markdown("<div style='margin:.3rem 0'></div>", unsafe_allow_html=True)

st.sidebar.markdown("""
<hr style='border:none; border-top:1px solid #F97316; opacity:.4; margin:.6rem 0;'>
<div style='font-size:.72rem; color:var(--text-muted,#6B7280); font-weight:500; letter-spacing:0.3px;'>
    <span style='font-size:.65rem; opacity:.75; display:block; margin-bottom:.5rem;'>For Internal Use of Sales and Operations Team Only.<br>All Rights Reserved.</span>
    DESIGNED BY: <b>AMIT RAY</b><br>
    <a href="mailto:amitray@lawsikho.com" style="color:#F97316; text-decoration:none;">amitray@lawsikho.com</a>
</div>
""", unsafe_allow_html=True)

st.sidebar.download_button(
    label="📖 Metrics Guide (PDF)",
    data=generate_calling_helper_pdf_bytes(),
    file_name="Calling_Metrics_Logic_Guide.pdf",
    mime="application/pdf",
    key="dl_calling_helper_pdf"
)
st.sidebar.download_button(
    label="📖 Metrics Guide (PDF)",
    data=generate_helper_pdf_bytes(),
    file_name="Revenue_Metrics_Logic_Guide.pdf",
    mime="application/pdf",
    key="dl_helper_pdf"
)

# ─────────────────────────────────────────────
# HEADER BANNER
# ─────────────────────────────────────────────

last_update_str = get_last_update()
display_start   = start_date.strftime('%d-%m-%Y')
display_end     = end_date.strftime('%d-%m-%Y')

st.markdown(f"""
<div class="rv-header">
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:.75rem;">
        <div>
            <div class="rv-title">💰 REVENUE METRICS</div>
            <div class="rv-subtitle">REVENUE PERIOD&nbsp;·&nbsp; {display_start} to {display_end}</div>
        </div>
        <div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin-top:.25rem;">
            <span class="rv-badge"><span class="rv-pulse"></span>LIVE REVENUE DATA</span>
            <span class="rv-badge">🕐 UPDATED AT: {last_update_str}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────

tab1, tab2 = st.tabs(["💰 Revenue Dashboard", "🧠 Insights & Leaderboard"])


# ══════════════════════════════════════════════
# TAB 1 — REVENUE DASHBOARD
# ══════════════════════════════════════════════

with tab1:
    if gen_report:
        with st.spinner("Fetching revenue data…"):
            df_raw = fetch_revenue_data(start_date, end_date)

            if df_raw.empty:
                st.warning("No revenue records found for the selected period (Fee Paid > 0).")
            else:
                # Merge team info
                df = pd.merge(
                    df_raw,
                    df_team_mapping[['merge_key','Caller Name','Team Name','Vertical']].drop_duplicates('merge_key'),
                    on='merge_key', how='left'
                )
                df['Caller_name'] = df['Caller Name'].fillna(df['Caller_name'])

                # Apply filters
                if selected_team:
                    df = df[df['Team Name'].isin(selected_team)]
                if selected_vertical:
                    df = df[df['Vertical'].isin(selected_vertical)]
                if search_query:
                    df = df[df['Caller_name'].str.contains(search_query, case=False, na=False)]

                if df.empty:
                    st.error("No records match the selected filters.")
                else:
                    # ── Classify callers ──
                    calling_df, collection_df, both_df = classify_and_process(
                        df, df_team_mapping, start_date, end_date
                    )

                    # ── Summary metrics ──
                    metrics = compute_summary_metrics(df)

                    # ── TOP 3 HIGHLIGHTS ──
                    section_header("🏆 TOP 3 REVENUE HIGHLIGHTS")
                    top_cols = st.columns(3)

                    # Top Revenue Caller — from calling_df
                    with top_cols[0]:
                        if not calling_df.empty:
                            top_c = calling_df.iloc[0]
                            st.markdown(f"""
                            <div class="metric-card" style="border-top:3px solid var(--accent-primary);">
                                <div class="metric-label">🥇 TOP REVENUE — CALLER</div>
                                <div class="metric-value" style="font-size:1.1rem;">{top_c['CALLER NAME']}</div>
                                <div class="metric-delta">{fmt_inr(top_c['raw_calling_rev'])} Calling Revenue</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""<div class="metric-card" style="border-top:3px solid var(--gold);">
                                <div class="metric-label">🥇 TOP REVENUE — CALLER</div>
                                <div class="metric-value" style="font-size:1rem;">No Data</div>
                            </div>""", unsafe_allow_html=True)

                    # Most Enrollments — from all agent types combined
                    with top_cols[1]:
                        _agent_list = [d for d in [calling_df, collection_df, both_df] if not d.empty]
                        all_agents = pd.concat(_agent_list, ignore_index=True) if _agent_list else pd.DataFrame()
                        if not all_agents.empty and all_agents['raw_enrollments'].max() > 0:
                            top_enr = all_agents.sort_values('raw_enrollments', ascending=False).iloc[0]
                            st.markdown(f"""
                            <div class="metric-card" style="border-top:3px solid var(--accent-primary);">
                                <div class="metric-label">🎓 MOST ENROLLMENTS</div>
                                <div class="metric-value" style="font-size:1.1rem;">{top_enr['CALLER NAME']}</div>
                                <div class="metric-delta">{top_enr['raw_enrollments']} New Enrollments</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""<div class="metric-card" style="border-top:3px solid var(--silver);">
                                <div class="metric-label">🎓 MOST ENROLLMENTS</div>
                                <div class="metric-value" style="font-size:1rem;">No Data</div>
                            </div>""", unsafe_allow_html=True)

                    # Top Revenue Collection Caller — from collection_df
                    with top_cols[2]:
                        _coll_list = [d for d in [collection_df] if not d.empty]
                        coll_combined = pd.concat(_coll_list, ignore_index=True) if _coll_list else pd.DataFrame()
                        if not coll_combined.empty:
                            top_coll = coll_combined.sort_values('raw_collection_rev', ascending=False).iloc[0]
                            st.markdown(f"""
                            <div class="metric-card" style="border-top:3px solid var(--accent-primary);">
                                <div class="metric-label">🥇 TOP REVENUE — COLLECTION</div>
                                <div class="metric-value" style="font-size:1.1rem;">{top_coll['CALLER NAME']}</div>
                                <div class="metric-delta">{fmt_inr(top_coll['raw_collection_rev'])} Collection Revenue</div>
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""<div class="metric-card" style="border-top:3px solid var(--bronze);">
                                <div class="metric-label">🥇 TOP REVENUE — COLLECTION</div>
                                <div class="metric-value" style="font-size:1rem;">No Data</div>
                            </div>""", unsafe_allow_html=True)

                    # ── SUMMARY KPI CARDS ──
                    section_header("💵 REVENUE SUMMARY METRICS")

                    kpis = [
                        ("Total Revenue (EXCL. Services)",                   fmt_inr(metrics['total_rev']),      "💰"),
                        ("Calling Revenue (INCL. Funnel)",                  fmt_inr(metrics['calling_rev']),    "📞"),
                        ("Bootcamp-Direct Revenue",         fmt_inr(metrics['bootcamp_direct_rev']),     "🎓"),
                        ("Bootcamp-Collection Revenue",              fmt_inr(metrics['collection_rev']), "🏦"),
                        ("Community Revenue (Direct + Collection)",               fmt_inr(metrics['community_rev']),  "🌐"),
                        ("Direct/Other Revenue (INCL. Funnel)",                  fmt_inr(metrics['direct_rev']),     "🎯"),
                        ("Details Not Available/ Not Updated Yet",           fmt_inr(metrics['dna_rev']),        "❓"),
                    ]

                    cols = st.columns(len(kpis))
                    for col, (label, val, icon) in zip(cols, kpis):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{icon} {label}</div>
                                <div class="metric-value">{val}</div>
                            </div>""", unsafe_allow_html=True)

                    st.divider()

                    # ══════════════════════════════════════
                    # ENROLLMENT SUMMARY METRICS
                    # ══════════════════════════════════════
                    section_header("🎓 ENROLLMENT SUMMARY METRICS")

                    enr_metrics = compute_enrollment_metrics(df)

                    enr_kpis = [
                        ("Total Enrollments",             enr_metrics['total_enr'],     "🎯"),
                        ("Caller Enrollments",            enr_metrics['caller_enr'],    "📞"),
                        ("Direct Enrollments",            enr_metrics['direct_enr'],    "🎯"),
                        ("Bootcamp-Direct Enrollments",   enr_metrics['bootcamp_enr'],  "🎓"),
                        ("Community-Direct Enrollments",  enr_metrics['community_enr'], "🌐"),
                    ]

                    enr_cols = st.columns(len(enr_kpis))
                    for col, (label, val, icon) in zip(enr_cols, enr_kpis):
                        with col:
                            st.markdown(f"""
                            <div class="metric-card">
                                <div class="metric-label">{icon} {label}</div>
                                <div class="metric-value">{val}</div>
                            </div>""", unsafe_allow_html=True)

                    st.divider()

                    # ── Download Summary Cards ──
                    _rev_summary = pd.DataFrame([{
                        'Metric'  : label,
                        'Amount'  : val
                    } for label, val, _ in [
                        ("Total Revenue (EXCL. Services)",          metrics['total_rev'],           ""),
                        ("Calling Revenue (INCL. Funnel)",          metrics['calling_rev'],         ""),
                        ("Bootcamp-Direct Revenue",                 metrics['bootcamp_direct_rev'], ""),
                        ("Bootcamp-Collection Revenue",             metrics['collection_rev'],      ""),
                        ("Community Revenue (Direct+Collection)",   metrics['community_rev'],       ""),
                        ("Direct/Other Revenue (INCL. Funnel)",     metrics['direct_rev'],          ""),
                        ("Details Not Available / Not Updated Yet", metrics['dna_rev'],             ""),
                    ]])

                    _enr_summary = pd.DataFrame([{
                        'Metric': label,
                        'Count' : val
                    } for label, val, _ in [
                        ("Total Enrollments",            enr_metrics['total_enr'],     ""),
                        ("Caller Enrollments",           enr_metrics['caller_enr'],    ""),
                        ("Direct Enrollments",           enr_metrics['direct_enr'],    ""),
                        ("Bootcamp-Direct Enrollments",  enr_metrics['bootcamp_enr'],  ""),
                        ("Community-Direct Enrollments", enr_metrics['community_enr'], ""),
                    ]])

                    _combined = pd.concat([
                        _rev_summary.rename(columns={'Amount': 'Value'}),
                        _enr_summary.rename(columns={'Count': 'Value'})
                    ], ignore_index=True)

                    st.download_button(
                        label="📥 Download Revenue & Enrollment Summary",
                        data=_combined.to_csv(index=False).encode('utf-8'),
                        file_name=f"Summary_{display_start}_to_{display_end}.csv",
                        mime='text/csv',
                        key='dl_summary'
                    )

                    st.divider()

                    # ══════════════════════════════════════
                    # TABLE 1 — CALLER REVENUE PERFORMANCE
                    # ══════════════════════════════════════
                    section_header("📞 CALLER REVENUE PERFORMANCE TABLE")

                    calling_display_cols = [
                        'DESIGNATION', 'CALLER NAME', 'TEAM', 'VERTICAL',
                        'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)', 'ENROLLMENTS',
                        'ENROLLMENT REV', 'BALANCE REV',
                        'CALLING REVENUE', 'ACHIEVEMENT %'
                    ]

                    if not calling_df.empty:
                        calling_totals = {
                            'TOTAL TARGET (₹)'    : fmt_inr(calling_df['raw_target'].sum()),
                            'TILL DAY TARGET (₹)' : fmt_inr(calling_df['TILL DAY TARGET (₹)'].sum()),
                            'ENROLLMENTS'         : int(calling_df['raw_enrollments'].sum()),
                            'ENROLLMENT REV'      : fmt_inr(calling_df['ENROLLMENT REV'].sum()),
                            'BALANCE REV'         : fmt_inr(calling_df['BALANCE REV'].sum()),
                            'CALLING REVENUE'     : fmt_inr(calling_df['CALLING REVENUE'].sum()),
                            'ACHIEVEMENT %'       : f"{round(calling_df['CALLING REVENUE'].sum() / calling_df['raw_target'].sum() * 100, 1) if calling_df['raw_target'].sum() > 0 else 0}%",
                        }
                    else:
                        calling_totals = {}

                    render_perf_table(
                        calling_df, calling_display_cols,
                        calling_totals, 'raw_calling_rev', 'calling'
                    )
                    if not calling_df.empty:
                        st.download_button(
                            label="📥 Download Caller Revenue CSV",
                            data=calling_df[calling_display_cols].to_csv(index=False).encode('utf-8'),
                            file_name=f"Caller_Revenue_{display_start}_to_{display_end}.csv",
                            mime='text/csv', key='dl_calling'
                        )

                    st.divider()

                    # ══════════════════════════════════════════════
                    # TABLE 2
                    # ══════════════════════════════════════════════
                    section_header("🏦 COLLECTION CALLER REVENUE PERFORMANCE TABLE")

                    collection_display_cols = [
                        'DESIGNATION', 'CALLER NAME', 'TEAM', 'VERTICAL',
                        'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)', 'ENROLLMENTS',
                        'CALLING REVENUE',
                        'COMMUNITY COLLECTION', 'BOOTCAMP COLLECTION',
                        'COLLECTION REVENUE'
                    ]

                    if not collection_df.empty:
                        collection_totals = {
                            'TOTAL TARGET (₹)'    : fmt_inr(collection_df['raw_target'].sum()),
                            'TILL DAY TARGET (₹)' : fmt_inr(collection_df['TILL DAY TARGET (₹)'].sum()),
                            'ENROLLMENTS'         : int(collection_df['raw_enrollments'].sum()),
                            'CALLING REVENUE'     : fmt_inr(collection_df['CALLING REVENUE'].sum()),
                            'COMMUNITY COLLECTION': fmt_inr(collection_df['COMMUNITY COLLECTION'].sum()),
                            'BOOTCAMP COLLECTION' : fmt_inr(collection_df['BOOTCAMP COLLECTION'].sum()),
                            'COLLECTION REVENUE'  : fmt_inr(collection_df['COLLECTION REVENUE'].sum()),
                        }
                    else:
                        collection_totals = {}

                    render_perf_table(
                        collection_df, collection_display_cols,
                        collection_totals, 'raw_collection_rev', 'collection'
                    )
                    if not collection_df.empty:
                        st.download_button(
                            label="📥 Download Collection Revenue CSV",
                            data=collection_df[collection_display_cols].to_csv(index=False).encode('utf-8'),
                            file_name=f"Collection_Revenue_{display_start}_to_{display_end}.csv",
                            mime='text/csv', key='dl_collection'
                        )

                    st.divider()

                    # ══════════════════════════════════════════════════════════
                    # TABLE 3
                    # ══════════════════════════════════════════════════════════
                    section_header("📞🏦 CALLING + COLLECTION CALLER REVENUE PERFORMANCE TABLE")

                    both_display_cols = [
                        'DESIGNATION', 'CALLER NAME', 'TEAM', 'VERTICAL',
                        'TOTAL TARGET (₹)', 'TILL DAY TARGET (₹)', 'ENROLLMENTS',
                        'CALLING REVENUE', 'COMMUNITY COLLECTION', 'BOOTCAMP COLLECTION',
                        'TOTAL REVENUE', 'ACHIEVEMENT %'
                    ]

                    if not both_df.empty:
                        _both_target     = both_df['raw_target'].sum()
                        _both_till       = both_df['TILL DAY TARGET (₹)'].sum()
                        _both_enr        = int(both_df['raw_enrollments'].sum())
                        _both_comm       = both_df['COMMUNITY COLLECTION'].sum()
                        _both_boot       = both_df['BOOTCAMP COLLECTION'].sum()
                        _both_calling    = both_df['CALLING REVENUE'].sum()
                        _both_collection = both_df['COLLECTION REVENUE'].sum()
                        _both_total      = both_df['raw_revenue'].sum()
                        _both_ach        = round(_both_total / _both_target * 100, 1) if _both_target > 0 else 0
                        both_totals = {
                            'TOTAL TARGET (₹)'    : fmt_inr(_both_target),
                            'TILL DAY TARGET (₹)' : fmt_inr(_both_till),
                            'ENROLLMENTS'         : _both_enr,
                            'COMMUNITY COLLECTION': fmt_inr(_both_comm),
                            'BOOTCAMP COLLECTION' : fmt_inr(_both_boot),
                            'CALLING REVENUE'     : fmt_inr(_both_calling),
                            'COLLECTION REVENUE'  : fmt_inr(_both_collection),
                            'TOTAL REVENUE'       : fmt_inr(_both_total),
                            'ACHIEVEMENT %'       : f"{_both_ach}%",
                        }
                    else:
                        both_totals = {}
                    render_perf_table(
                        both_df, both_display_cols,
                        both_totals, 'raw_revenue', 'both'
                    )
                    if not both_df.empty:
                        st.download_button(
                            label="📥 Download Calling+Collection Revenue CSV",
                            data=both_df[both_display_cols].to_csv(index=False).encode('utf-8'),
                            file_name=f"Both_Revenue_{display_start}_to_{display_end}.csv",
                            mime='text/csv', key='dl_both'
                        )

    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>💰</div>
            <div style='font-size:.9rem;font-weight:600;'>Select a date range and click <b>Generate Revenue Report</b></div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# TAB 2 — INSIGHTS & LEADERBOARD
# ══════════════════════════════════════════════

with tab2:
    if gen_report:
        with st.spinner("Analysing revenue patterns…"):
            df_raw = fetch_revenue_data(start_date, end_date)
            if df_raw.empty:
                st.warning("No revenue data found for the selected period.")
            else:
                df_ins = pd.merge(
                    df_raw,
                    df_team_mapping[['merge_key','Caller Name','Team Name','Vertical']].drop_duplicates('merge_key'),
                    on='merge_key', how='left'
                )
                df_ins['Caller_name'] = df_ins['Caller Name'].fillna(df_ins['Caller_name'])

                if selected_team:
                    df_ins = df_ins[df_ins['Team Name'].isin(selected_team)]
                if selected_vertical:
                    df_ins = df_ins[df_ins['Vertical'].isin(selected_vertical)]
                if search_query:
                    df_ins = df_ins[df_ins['Caller_name'].str.contains(search_query, case=False, na=False)]

                calling_ins, collection_ins, both_ins = classify_and_process(
                    df_ins, df_team_mapping, start_date, end_date
                )

                _ins_list = [d for d in [calling_ins, collection_ins, both_ins] if not d.empty]
                all_agents_ins = pd.concat(_ins_list, ignore_index=True) if _ins_list else pd.DataFrame()

                if all_agents_ins.empty:
                    st.warning("Not enough data for insights with current filters.")
                else:
                    # ── 6 INSIGHTS ──
                    section_header("🧠 REVENUE INSIGHTS")
                    insights = compute_revenue_insights(
                        df_ins, calling_ins, collection_ins, both_ins,
                        start_date, end_date
                    )

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
                        st.info("Not enough variation in data to generate insights.")

                    st.divider()

                    # ══════════════════════════════════════════════
                    # TABLE A — CALLER TEAM LEADERBOARD
                    # ══════════════════════════════════════════════
                    section_header("📞 CALLER REVENUE TEAM PERFORMANCE TABLE")

                    if not calling_ins.empty:
                        lb_calling = (
                            calling_ins.groupby('TEAM')
                            .agg(
                                Callers   = ('CALLER NAME',       'count'),
                                Enrollments=('raw_enrollments',   'sum'),
                                Target    = ('raw_target',        'sum'),
                                Till_Day  = ('TILL DAY TARGET (₹)','sum'),
                                Enr_Rev   = ('ENROLLMENT REV',    'sum'),
                                Bal_Rev   = ('BALANCE REV',       'sum'),
                                Revenue   = ('raw_calling_rev',   'sum'),
                            )
                            .reset_index()
                            .sort_values('Revenue', ascending=False)
                        )
                        lb_calling['Achievement %'] = lb_calling.apply(
                            lambda r: f"{round(r['Revenue']/r['Target']*100,1)}%" if r['Target'] > 0 else "—", axis=1
                        )
                        lb_calling['Target']   = lb_calling['Target'].apply(fmt_inr)
                        lb_calling['Till_Day'] = lb_calling['Till_Day'].apply(fmt_inr)
                        lb_calling['Enr_Rev']  = lb_calling['Enr_Rev'].apply(fmt_inr)
                        lb_calling['Bal_Rev']  = lb_calling['Bal_Rev'].apply(fmt_inr)
                        lb_calling['Revenue']  = lb_calling['Revenue'].apply(fmt_inr)
                        medals = (["🥇", "🥈", "🥉"] + [""] * len(lb_calling))[:len(lb_calling)]
                        lb_calling.insert(0, "🏅", medals)
                        lb_calling.columns = ['🏅', 'Team', 'Callers', 'Enrollments',
                                              'Total Target', 'Till Day Target',
                                              'Enrollment Rev', 'Balance Rev',
                                              'Calling Revenue', 'Achievement %']
                        st.dataframe(lb_calling.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("No calling agent data available.")

                    st.divider()

                    # ══════════════════════════════════════════════
                    # TABLE B — COLLECTION TEAM LEADERBOARD
                    # ══════════════════════════════════════════════
                    section_header("🏦 COLLECTION CALLER TEAM REVENUE PERFORMANCE TABLE")

                    if not collection_ins.empty:
                        lb_coll = (
                            collection_ins.groupby('TEAM')
                            .agg(
                                Callers     = ('CALLER NAME',          'count'),
                                Enrollments = ('raw_enrollments',      'sum'),
                                Target      = ('raw_target',           'sum'),
                                Till_Day    = ('TILL DAY TARGET (₹)',  'sum'),
                                Calling_Rev = ('CALLING REVENUE',      'sum'),
                                Comm_Coll   = ('COMMUNITY COLLECTION', 'sum'),
                                Boot_Coll   = ('BOOTCAMP COLLECTION',  'sum'),
                                Revenue     = ('raw_collection_rev',   'sum'),
                            )
                            .reset_index()
                            .sort_values('Revenue', ascending=False)
                        )
                        lb_coll['Achievement %'] = lb_coll.apply(
                            lambda r: f"{round(r['Revenue']/r['Target']*100,1)}%" if r['Target'] > 0 else "—", axis=1
                        )
                        lb_coll['Target']      = lb_coll['Target'].apply(fmt_inr)
                        lb_coll['Till_Day']    = lb_coll['Till_Day'].apply(fmt_inr)
                        lb_coll['Calling_Rev'] = lb_coll['Calling_Rev'].apply(fmt_inr)
                        lb_coll['Comm_Coll']   = lb_coll['Comm_Coll'].apply(fmt_inr)
                        lb_coll['Boot_Coll']   = lb_coll['Boot_Coll'].apply(fmt_inr)
                        lb_coll['Revenue']     = lb_coll['Revenue'].apply(fmt_inr)
                        medals = (["🥇", "🥈", "🥉"] + [""] * len(lb_coll))[:len(lb_coll)]
                        lb_coll.insert(0, "🏅", medals)
                        lb_coll.columns = ['🏅', 'Team', 'Callers', 'Enrollments',
                                           'Total Target', 'Till Day Target',
                                           'Calling Revenue', 'Community Collection',
                                           'Bootcamp Collection', 'Collection Revenue', 'Achievement %']
                        st.dataframe(lb_coll.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("No collection agent data available.")

                    st.divider()

                    # ══════════════════════════════════════════════
                    # TABLE C — BOTH TEAM LEADERBOARD
                    # ══════════════════════════════════════════════
                    section_header("📞🏦 CALLING + COLLECTION CALLER TEAM REVENUE PERFORMANCE TABLE")

                    if not both_ins.empty:
                        lb_both = (
                            both_ins.groupby('TEAM')
                            .agg(
                                Callers     = ('CALLER NAME',          'count'),
                                Enrollments = ('raw_enrollments',      'sum'),
                                Target      = ('raw_target',           'sum'),
                                Till_Day    = ('TILL DAY TARGET (₹)',  'sum'),
                                Calling_Rev = ('CALLING REVENUE',      'sum'),
                                Comm_Coll   = ('COMMUNITY COLLECTION', 'sum'),
                                Boot_Coll   = ('BOOTCAMP COLLECTION',  'sum'),
                                Total_Rev   = ('raw_revenue',          'sum'),
                            )
                            .reset_index()
                            .sort_values('Total_Rev', ascending=False)
                        )
                        lb_both['Achievement %'] = lb_both.apply(
                            lambda r: f"{round(r['Total_Rev']/r['Target']*100,1)}%" if r['Target'] > 0 else "—", axis=1
                        )
                        lb_both['Target']      = lb_both['Target'].apply(fmt_inr)
                        lb_both['Till_Day']    = lb_both['Till_Day'].apply(fmt_inr)
                        lb_both['Calling_Rev'] = lb_both['Calling_Rev'].apply(fmt_inr)
                        lb_both['Comm_Coll']   = lb_both['Comm_Coll'].apply(fmt_inr)
                        lb_both['Boot_Coll']   = lb_both['Boot_Coll'].apply(fmt_inr)
                        lb_both['Total_Rev']   = lb_both['Total_Rev'].apply(fmt_inr)
                        medals = (["🥇", "🥈", "🥉"] + [""] * len(lb_both))[:len(lb_both)]
                        lb_both.insert(0, "🏅", medals)
                        lb_both.columns = ['🏅', 'Team', 'Callers', 'Enrollments',
                                           'Total Target', 'Till Day Target',
                                           'Calling Revenue', 'Community Collection',
                                           'Bootcamp Collection', 'Total Revenue', 'Achievement %']
                        st.dataframe(lb_both.reset_index(drop=True), use_container_width=True, hide_index=True)
                    else:
                        st.info("No calling+collection agent data available.")

    else:
        st.markdown("""
        <div style='text-align:center;padding:6rem 1rem;opacity:.6;'>
            <div style='font-size:4rem;margin-bottom:1rem;'>🧠</div>
            <div style='font-size:.95rem;font-weight:600;'>Click <b>Generate Revenue Report</b> to load insights</div>
        </div>""", unsafe_allow_html=True)
