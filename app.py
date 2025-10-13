import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="Ethekwini WS-7761 Dashboard",
    layout="wide",
    page_icon="📊"
)

# ======================================================
#   COMPANY HEADER (DEEZLO BRANDING)
# ======================================================
logo_path = "/mnt/data/deezlo.png"

# Top layout: centered logo and titles
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=420)
    st.markdown("""
        <h1 style='text-align:center; color:#F26522; margin-bottom:0;'>Deezlo Trading cc</h1>
        <h4 style='text-align:center; margin-top:0; color:#000;'>You Dream it, We Build it</h4>
        <h2 style='text-align:center; margin-top:2rem;'>Ethekwini WS-7761 Dashboard</h2>
    """, unsafe_allow_html=True)

st.markdown("---")

# ======================================================
#   LOAD EXCEL DATA
# ======================================================
@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
    """Load all sheets from Excel file into dictionary of DataFrames."""
    try:
        xls = pd.ExcelFile(path)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return {}
    data = {}
    for sheet in xls.sheet_names:
        try:
            data[sheet] = pd.read_excel(xls, sheet_name=sheet)
        except Exception:
            data[sheet] = pd.DataFrame()
    return data

sheets = load_data()

# ======================================================
#   SIDEBAR FILTERS
# ======================================================
st.sidebar.header("📁 Data & Filters")

if not sheets:
    st.warning("No data loaded. Ensure the Excel file is available.")
    st.stop()

sheet_choice = st.sidebar.selectbox(
    "Select main sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)
search_task = st.sidebar.text_input("Search task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)

st.sidebar.markdown("### Sheets loaded:")
for name, df in sheets.items():
    st.sidebar.write(f"- {name} ({df.shape[0]} rows)")

# ======================================================
#   HELPER FUNCTIONS
# ======================================================
def standardize_dates(df, cols=None):
    """Convert likely date columns to datetime."""
    if cols is None:
        cols = [c for c in df.columns if "date" in c.lower()]
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    return df

def highlight_rows(row):
    """Highlight overdue (red) and completed (green) tasks."""
    styles = [""] * len(row)
    if "Progress" not in row.index:
        return styles
    status = str(row["Progress"]).lower()
    if status == "completed":
        styles = ["background-color:#d4f4dd;"] * len(row)
    elif "Due date" in row.index:
        due = row["Due date"]
        if pd.notna(due) and pd.to_datetime(due) < pd.Timestamp.today():
            styles = ["background-color:#f8d7da;"] * len(row)
    return styles

# ======================================================
#   MAIN SECTION
# ======================================================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if df_main.empty:
    st.warning("Selected sheet is empty.")
    st.stop()

df_main = standardize_dates(df_main)

# Apply filters
if search_task:
    df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]

if date_from and "Start date" in df_main.columns:
    df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]

if date_to and "Due date" in df_main.columns:
    df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

# ======================================================
#   KPI SECTION
# ======================================================
if "Tasks" in sheets:
    st.subheader("📈 Key Performance Indicators")
    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

    total = len(tasks)
    completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
    inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
    notstarted = tasks["Progress"].str.lower().eq("not started").sum() if "Progress" in tasks.columns else 0
    overdue = (
        ((tasks["Due date"] < pd.Timestamp.today()) &
         (~tasks["Progress"].str.lower().eq("completed"))).sum()
        if "Due date" in tasks.columns and "Progress" in tasks.columns else 0
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Tasks", total)
    k2.metric("Completed", int(completed))
    k3.metric("In Progress", int(inprogress))
    k4.metric("Overdue", int(overdue))

st.markdown("---")

# ======================================================
#   DATA PREVIEW
# ======================================================
st.subheader(f"📋 {sheet_choice} — Preview ({df_main.shape[0]} rows)")
st.dataframe(df_main.head(200))

# ======================================================
#   DASHBOARDS (if Tasks sheet exists)
# ======================================================
if "Tasks" in sheets:
    st.markdown("## 📊 Task Analytics")

    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

    # Pie chart - Progress distribution
    if "Progress" in tasks.columns:
        fig = px.pie(tasks, names="Progress", title="Progress Distribution", hole=0.3)
        st.plotly_chart(fig, use_container_width=True)

    # Tasks per Bucket
    if "Bucket Name" in tasks.columns:
        agg = tasks["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name", "Count"]
        fig2 = px.bar(agg, x="Bucket Name", y="Count", title="Tasks per Bucket")
        st.plotly_chart(fig2, use_container_width=True)

    # Priority distribution
    if "Priority" in tasks.columns:
        fig3 = px.pie(tasks, names="Priority", title="Priority Distribution")
        st.plotly_chart(fig3, use_container_width=True)

    # Overdue tasks table
    if "Due date" in tasks.columns and "Progress" in tasks.columns:
        overdue_df = tasks[
            (tasks["Due date"] < pd.Timestamp.today()) &
            (tasks["Progress"].str.lower() != "completed")
        ].copy()
        st.subheader("⚠️ Overdue Tasks")
        if not overdue_df.empty:
            styled = overdue_df.style.apply(highlight_rows, axis=1)
            st.data_editor(styled, use_container_width=True)
        else:
            st.info("No overdue tasks found.")

    # Timeline (Gantt)
    if {"Start date", "Due date"}.issubset(tasks.columns):
        timeline = tasks.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline["Task Name"].astype(str).str.slice(0, 50)
            fig4 = px.timeline(
                timeline,
                x_start="Start date",
                x_end="Due date",
                y="task_short",
                color="Bucket Name" if "Bucket Name" in timeline.columns else None,
                title="Task Timeline"
            )
            fig4.update_yaxes(autorange="reversed")
            st.plotly_chart(fig4, use_container_width=True)

# ======================================================
#   EXPORT SECTION
# ======================================================
st.markdown("---")
st.subheader("📤 Export Data")
csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download current view as CSV",
    csv,
    file_name=f"{sheet_choice}_export.csv",
    mime="text/csv"
)
