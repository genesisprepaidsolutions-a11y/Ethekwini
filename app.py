
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Ethekwini — Dashboard (Excel replica)", layout="wide")

# --- Styling (clean corporate) ---
st.markdown(
    """
    <style>
    .stApp { font-family: "Segoe UI", Roboto, Arial; }
    .kpi { background: #ffffff; border-radius: 8px; padding: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
    .phase-bar { background: linear-gradient(90deg,#0d6efd,#60a5fa); height:18px; border-radius:6px; }
    </style>
    """, unsafe_allow_html=True
)

@st.cache_data
def load_workbook(path):
    xls = pd.ExcelFile(path)
    sheets = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
    return sheets

# Load default workbook (allow uploader to override)
uploaded = st.file_uploader("Upload an Excel workbook (.xlsx) to replicate", type=["xlsx"])
if uploaded is not None:
    sheets = load_workbook(uploaded)
    src_label = "Uploaded"
else:
    default_path = Path(__file__).parent / "Ethekwini WS-7761 07 Oct 2025.xlsx"
    if default_path.exists():
        sheets = load_workbook(default_path)
        src_label = "Default workbook"
    else:
        st.error("Default workbook not found. Please upload the Excel file.")
        st.stop()

st.sidebar.header("Filters (applied to TASKS-based KPIs)")
# We'll read TASKS sheet if available
tasks_sheet = None
for candidate in ["TASKS","Tasks","tasks","Task list","Task List"]:
    if candidate in sheets:
        tasks_sheet = candidate
        break
# fallback to first sheet
if tasks_sheet is None:
    tasks_sheet = list(sheets.keys())[0]

# Detect phase summary sheets like "Total vs Complete *"
phase_summaries = {}
for name, df in sheets.items():
    low = name.lower().strip()
    if low.startswith("total") and "complete" in low:
        # attempt to extract two numeric values (total, complete)
        # find first two numeric-like cells in sheet
        flat = df.replace(r'^\s*$', np.nan, regex=True).stack().reset_index(drop=True)
        nums = flat[flat.apply(lambda x: pd.to_numeric(x, errors="coerce")).notna()].apply(pd.to_numeric, errors="coerce")
        vals = nums.tolist()
        if len(vals) >= 2:
            phase_summaries[name] = {"total": float(vals[0]), "complete": float(vals[1])}
        elif len(vals) == 1:
            phase_summaries[name] = {"total": float(vals[0]), "complete": 0.0}
        else:
            # try named columns with totals
            try:
                colnums = df.select_dtypes(include=[np.number]).iloc[0].tolist()
                if len(colnums) >= 2:
                    phase_summaries[name] = {"total": float(colnums[0]), "complete": float(colnums[1])}
            except Exception:
                pass

# Load TASKS sheet dataframe for overall KPIs if present
df_tasks = sheets.get(tasks_sheet).copy() if tasks_sheet in sheets else pd.DataFrame()

# normalize column names
df_tasks.columns = [str(c).strip() for c in df_tasks.columns]

# Detect key columns
def detect_column(df, keywords):
    for c in df.columns:
        low = str(c).lower()
        for k in keywords:
            if k in low:
                return c
    return None

col_task = detect_column(df_tasks, ["task","description","work"])
col_bucket = detect_column(df_tasks, ["bucket","ward","zone","area","phase"])
col_progress = detect_column(df_tasks, ["progress","status"])
col_due = detect_column(df_tasks, ["due"])
col_completed = detect_column(df_tasks, ["completed","completion"])
col_priority = detect_column(df_tasks, ["priority"])

# Parse dates
for c in [col_due, col_completed]:
    if c and c in df_tasks.columns:
        try:
            df_tasks[c] = pd.to_datetime(df_tasks[c], errors="coerce")
        except Exception:
            pass

# Define completed flag logic
def completed_flag(row):
    prog = str(row.get(col_progress, "")).lower() if col_progress else ""
    comp = row.get(col_completed) if col_completed else None
    if pd.notna(comp):
        return True
    if "complete" in prog or prog in ["done","closed","finished"]:
        return True
    return False

if not df_tasks.empty:
    df_tasks["_completed"] = df_tasks.apply(completed_flag, axis=1)
else:
    df_tasks["_completed"] = pd.Series(dtype=bool)

# Overall KPIs
total_tasks = int(len(df_tasks)) if not df_tasks.empty else 0
completed_tasks = int(df_tasks["_completed"].sum()) if not df_tasks.empty else 0
today = pd.to_datetime(pd.Timestamp.now().date())
if col_due and not df_tasks.empty:
    overdue_mask = (pd.to_datetime(df_tasks[col_due], errors="coerce").notna()) & (pd.to_datetime(df_tasks[col_due], errors="coerce").dt.date < today.date()) & (~df_tasks["_completed"])
    overdue_tasks = int(overdue_mask.sum())
else:
    overdue_tasks = 0

pct_complete = (completed_tasks / total_tasks * 100) if total_tasks>0 else 0.0

# Sidebar filters for TASKS (if available)
if not df_tasks.empty and col_bucket:
    buckets = sorted(df_tasks[col_bucket].dropna().unique().tolist())
    sel_bucket = st.sidebar.selectbox("Bucket / Zone (All)", options=["All"] + buckets)
    if sel_bucket != "All":
        df_display = df_tasks[df_tasks[col_bucket]==sel_bucket]
    else:
        df_display = df_tasks.copy()
else:
    df_display = df_tasks.copy()

# Top row KPIs in layout similar to Excel dashboard
k1,k2,k3,k4 = st.columns([1.2,1.2,1.2,1])
st.markdown("<div class='kpi'>", unsafe_allow_html=True)
k1.metric("Total tasks", f"{total_tasks:,}")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='kpi'>", unsafe_allow_html=True)
k2.metric("Completed tasks", f"{completed_tasks:,}", delta=f"{pct_complete:.1f}%")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='kpi'>", unsafe_allow_html=True)
k3.metric("Overdue tasks", f"{overdue_tasks:,}")
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("<div class='kpi'>", unsafe_allow_html=True)
k4.metric("% Complete", f"{pct_complete:.1f}%")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# Middle section: progress bars per phase. Use phase_summaries if available; else derive from TASKS by Bucket/Phase
st.subheader("Progress by Phase")

phases = []
if phase_summaries:
    for name, vals in phase_summaries.items():
        # Normalize name to a short label
        label = name.replace("Total vs Complete","").strip() or name
        total = int(vals.get("total",0))
        complete = int(vals.get("complete",0))
        percent = (complete/total*100) if total>0 else 0
        phases.append({"phase": label, "total": total, "complete": complete, "pct": percent})
else:
    # attempt to use bucket/phase column in tasks
    if col_bucket and not df_tasks.empty:
        grp = df_tasks.groupby(col_bucket).agg(total=("index","size"), complete=("_completed","sum")).reset_index()
        for _, r in grp.iterrows():
            pct = (r["complete"]/r["total"]*100) if r["total"]>0 else 0
            phases.append({"phase": r[col_bucket], "total": int(r["total"]), "complete": int(r["complete"]), "pct": pct})

# Render progress bars similar to Excel dashboard
for p in phases:
    st.markdown(f"**{p['phase']}** — {p['complete']} / {p['total']} completed ({p['pct']:.1f}%)")
    # simple progress bar
    st.progress(int(p['pct']) if p['pct']<=100 else 100)

st.markdown("---")

# Bottom charts: Completed vs Total by Phase, and Task distribution
st.subheader("Phase Completion — Chart")
if phases:
    phases_df = pd.DataFrame(phases)
    fig = px.bar(phases_df, x="phase", y=["complete","total"], barmode="group", title="Completed vs Total by Phase")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No phase summary data detected in workbook and no bucket/phase column found in TASKS sheet.")

st.markdown("### Task distribution by Progress status")
if not df_tasks.empty and col_progress:
    dist = df_display.groupby(col_progress).size().reset_index(name="count")
    fig2 = px.pie(dist, names=col_progress, values="count", title="Tasks by Progress")
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.info("No TASKS or Progress column available to show distribution.")

st.markdown("---")
st.caption(f"Dashboard built from: {src_label}. Sheets used: " + ", ".join(list(sheets.keys())))
