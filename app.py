import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from PIL import Image

st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

st.markdown("<h1 style='text-align:center'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)

# ===================== DATA LOADING =====================
@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            sheets[s] = pd.read_excel(xls, sheet_name=s)
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()

# ===================== SIDEBAR FILTERS =====================
st.sidebar.header("Filters & Settings")

sheet_choice = st.sidebar.selectbox(
    "Sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)

search_task = st.sidebar.text_input("Search Task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)

show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

# ===================== MAIN DATAFRAME =====================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if not df_main.empty:
    # Convert date columns
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    # Search filter
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]

    # Date filters
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

    # Sidebar dynamic filters
    bucket_filter = st.sidebar.multiselect("Bucket Name", options=df_main["Bucket Name"].unique() if "Bucket Name" in df_main.columns else [])
    priority_filter = st.sidebar.multiselect("Priority", options=df_main["Priority"].unique() if "Priority" in df_main.columns else [])
    progress_filter = st.sidebar.multiselect("Progress", options=df_main["Progress"].unique() if "Progress" in df_main.columns else [])

    if bucket_filter and "Bucket Name" in df_main.columns:
        df_main = df_main[df_main["Bucket Name"].isin(bucket_filter)]
    if priority_filter and "Priority" in df_main.columns:
        df_main = df_main[df_main["Priority"].isin(priority_filter)]
    if progress_filter and "Progress" in df_main.columns:
        df_main = df_main[df_main["Progress"].isin(progress_filter)]

# ===================== KPI CARDS =====================
st.subheader("Key Performance Indicators")

if "Tasks" in sheets:
    tasks = sheets["Tasks"].copy()
    for col in ["Start date", "Due date", "Completed Date"]:
        if col in tasks.columns:
            tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors="coerce")

    total = len(tasks)
    completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
    inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
    notstarted = tasks["Progress"].str.lower().eq("not started").sum() if "Progress" in tasks.columns else 0
    overdue = ((tasks["Due date"] < pd.Timestamp.today()) & (~tasks["Progress"].str.lower().eq("completed"))).sum() if "Due date" in tasks.columns and "Progress" in tasks.columns else 0

    # Trend calculation example
    prev_week = pd.Timestamp.today() - timedelta(days=7)
    completed_prev = ((tasks["Progress"].str.lower().eq("completed")) & (tasks["Completed Date"] < prev_week)).sum() if "Completed Date" in tasks.columns else 0
    trend = (completed - completed_prev)/completed_prev*100 if completed_prev else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Not Started", f"{notstarted}", delta=f"{notstarted/total*100:.1f}%" if total else None, delta_color="inverse")
    with c2:
        st.metric("In Progress", f"{inprogress}", delta=f"{inprogress/total*100:.1f}%" if total else None)
    with c3:
        st.metric("Completed", f"{completed}", delta=f"{trend:.1f}%" if total else None)
    with c4:
        st.metric("Overdue", f"{overdue}", delta=f"{overdue/total*100:.1f}%" if total else None, delta_color="inverse")

# ===================== TASK BREAKDOWN =====================
st.subheader(f"Task Table: {sheet_choice} ({df_main.shape[0]} rows)")

if "Due date" in df_main.columns and "Progress" in df_main.columns:
    def highlight_status(row):
        if pd.notna(row["Due date"]) and row["Due date"] < pd.Timestamp.today() and row["Progress"].lower() != "completed":
            color = "background-color: #ffcccc"  # overdue red
        elif row["Progress"].lower() == "in progress":
            color = "background-color: #fff0b3"  # yellow
        elif row["Progress"].lower() == "completed":
            color = "background-color: #a3f7a3"  # green
        else:
            color = ""
        return [color]*len(row)

    st.dataframe(df_main.style.apply(highlight_status, axis=1))
else:
    st.dataframe(df_main)

# ===================== TASKS PER BUCKET =====================
if "Bucket Name" in df_main.columns:
    agg = df_main["Bucket Name"].value_counts().reset_index()
    agg.columns = ["Bucket Name","Count"]
    fig_bucket = px.bar(agg, x="Bucket Name", y="Count", text="Count", title="Tasks per Bucket", color="Count",
                        color_continuous_scale=px.colors.sequential.Blues)
    fig_bucket.update_traces(texttemplate="%{text}", textposition="outside")
    st.plotly_chart(fig_bucket, use_container_width=True)

# ===================== PRIORITY PIE =====================
if "Priority" in df_main.columns:
    fig_pie = px.pie(df_main, names="Priority", title="Priority Distribution",
                     color="Priority", color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# ===================== TIMELINE =====================
st.subheader("Task Timeline")
if "Start date" in df_main.columns and "Due date" in df_main.columns:
    timeline = df_main.dropna(subset=["Start date","Due date"]).copy()
    if not timeline.empty:
        timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0,60)
        progress_color = {"not started":"red","in progress":"yellow","completed":"green"}
        timeline["color"] = timeline["Progress"].str.lower().map(progress_color)
        fig_tl = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short",
                             color="color", title="Timeline by Progress", color_discrete_map=progress_color)
        fig_tl.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("Timeline data not available.")

# ===================== EXPORT =====================
st.subheader("Export Filtered Data")
csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime="text/csv")
