import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="eThekwini Municipality",
    layout="wide",
    page_icon="📊"
)

# ======================================================
#   LIGHT THEME (PURE WHITE + BLUE ACCENTS)
# ======================================================
st.markdown(
    """
    <style>
    /* Global Background */
    [data-testid="stAppViewContainer"] {
        background: #FFFFFF !important;
        color: #000000 !important;
    }
    [data-testid="stSidebar"] {
        background: #F5F8FF !important;  /* light blue tint */
        border-right: 2px solid #0073e6;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #FFFFFF !important;
        border-bottom: 1px solid #0073e6;
    }
    h1, h2, h3, h4, h5, h6, label {
        color: #003366 !important;
        font-weight: 600;
    }
    p, span, div, td, th {
        color: #333333 !important;
    }
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #cce0ff;
        box-shadow: 0 2px 8px rgba(0, 115, 230, 0.1);
        text-align: center;
    }
    hr {
        border: none;
        height: 2px;
        background: #0073e6;
        opacity: 0.3;
    }
    .stDownloadButton > button {
        background: #0073e6 !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   Sidebar: Options and file path
# ======================================================
st.sidebar.header("Configuration")
enable_animations = st.sidebar.checkbox("Enable animations", value=True)
st.sidebar.markdown("---")
st.sidebar.header("Data source")
excel_path = st.sidebar.text_input("Excel file path", value="Ethekwini WS-7761 07 Oct 2025.xlsx")

# ======================================================
#   LOAD EXCEL DATA
# ======================================================
@st.cache_data
def _read_excel_all_sheets(path):
    xls = pd.ExcelFile(path)
    return {sheet: pd.read_excel(xls, sheet_name=sheet) for sheet in xls.sheet_names}

if not os.path.exists(excel_path):
    st.error(f"Excel file not found: {excel_path}")
    st.stop()

sheets = _read_excel_all_sheets(excel_path)

# ======================================================
#   HEADER (REPLACED WITH MUNICIPAL TITLE)
# ======================================================
st.markdown(
    """
    <h1 style='text-align:center; color:#003366;'>eThekwini Municipality</h1>
    <hr>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   DATA & FILTERS
# ======================================================
sheet_choice = st.sidebar.selectbox(
    "Select main sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)

search_task = st.sidebar.text_input("Search task name (contains)")
# Note: Streamlit date_input requires a default value; using today's date where necessary is reasonable.
# Keeping the original approach but provide sensible defaults if user doesn't set them.
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if df_main.empty:
    st.warning("Selected sheet is empty.")
    st.stop()

def standardize_dates(df):
    for c in df.columns:
        if "date" in c.lower():
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    return df

df_main = standardize_dates(df_main)

# The original file used the first column as task name search; keep that behaviour
if search_task:
    first_col = df_main.columns[0]
    df_main = df_main[df_main[first_col].astype(str).str.contains(search_task, case=False, na=False)]
if date_from and "Start date" in df_main.columns:
    df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
if date_to and "Due date" in df_main.columns:
    df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

# ======================================================
#   KPI SECTION
# ======================================================
if "Tasks" in sheets:
    st.subheader("📈 Key Performance Indicators")
    tasks = standardize_dates(sheets["Tasks"].copy())

    total = len(tasks)
    if "Progress" in tasks.columns:
        prog = tasks["Progress"].fillna("").astype(str).str.lower().str.strip()
        completed = prog.eq("completed").sum()
        inprogress = prog.eq("in progress").sum()
        # Not Started includes "to do" and "pending"
        not_started = prog.isin(["to do", "pending", "to-do", "pending "]).sum()
    else:
        completed = inprogress = not_started = 0

    overdue = 0
    if "Due date" in tasks.columns and "Progress" in tasks.columns:
        overdue = (
            ((tasks["Due date"] < pd.Timestamp.today()) &
             (~tasks["Progress"].astype(str).str.lower().eq("completed"))).sum()
        )

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"<div class='metric-card'><h4>Total Tasks</h4><h2 style='color:#003366;'>{total}</h2></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><h4>Completed</h4><h2 style='color:#0073e6;'>{completed}</h2></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><h4>In Progress</h4><h2 style='color:#4da6ff;'>{inprogress}</h2></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='metric-card'><h4>Overdue</h4><h2 style='color:#ff4d4d;'>{overdue}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   DATA PREVIEW
# ======================================================
st.subheader("📋 Data Preview")
st.dataframe(df_main.head(200))

# ======================================================
#   BLUE VISUALS (REPLACED PIE WITH 3 DIALS)
# ======================================================
blue_palette = px.colors.sequential.Blues

if "Tasks" in sheets:
    st.subheader("📊 Task Analytics")
    tasks = standardize_dates(sheets["Tasks"].copy())

    # Prepare progress counts
    if "Progress" in tasks.columns:
        prog = tasks["Progress"].fillna("").astype(str).str.lower().str.strip()
        completed_count = prog.eq("completed").sum()
        inprogress_count = prog.eq("in progress").sum()
        not_started_count = prog.isin(["to do", "pending", "to-do", "pending "]).sum()
        total_count = len(tasks)
    else:
        completed_count = inprogress_count = not_started_count = total_count = 0

    # Avoid division by zero; gauges will use counts and have axis range set to total_count (or 1 if zero)
    axis_max = total_count if total_count > 0 else 1

    # Colors: Red / Yellow / Green (classic)
    colors = {
        "not_started": "red",
        "inprogress": "yellow",
        "completed": "green"
    }

    # Create three gauge charts (counts shown, axis range 0..total_count)
    gauge_not_started = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=not_started_count,
            number={'suffix': f" / {axis_max}"},
            title={'text': "Not Started (To Do / Pending)", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, axis_max], 'tickmode': 'linear'},
                'bar': {'color': colors["not_started"]},
                'steps': [
                    {'range': [0, axis_max * 0.5], 'color': "#ffe6e6"},
                    {'range': [axis_max * 0.5, axis_max * 0.8], 'color': "#ffcccc"},
                    {'range': [axis_max * 0.8, axis_max], 'color': "#ff9999"},
                ],
                'threshold': {
                    'line': {'color': 'red', 'width': 4},
                    'thickness': 0.75,
                    'value': not_started_count
                }
            }
        )
    )
    gauge_not_started.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)

    gauge_inprogress = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=inprogress_count,
            number={'suffix': f" / {axis_max}"},
            title={'text': "In Progress", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, axis_max], 'tickmode': 'linear'},
                'bar': {'color': colors["inprogress"]},
                'steps': [
                    {'range': [0, axis_max * 0.5], 'color': "#fff9e6"},
                    {'range': [axis_max * 0.5, axis_max * 0.8], 'color': "#fff2cc"},
                    {'range': [axis_max * 0.8, axis_max], 'color': "#ffe699"},
                ],
                'threshold': {
                    'line': {'color': 'orange', 'width': 4},
                    'thickness': 0.75,
                    'value': inprogress_count
                }
            }
        )
    )
    gauge_inprogress.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)

    gauge_completed = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=completed_count,
            number={'suffix': f" / {axis_max}"},
            title={'text': "Completed", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, axis_max], 'tickmode': 'linear'},
                'bar': {'color': colors["completed"]},
                'steps': [
                    {'range': [0, axis_max * 0.5], 'color': "#e6ffe6"},
                    {'range': [axis_max * 0.5, axis_max * 0.8], 'color': "#ccffcc"},
                    {'range': [axis_max * 0.8, axis_max], 'color': "#99ff99"},
                ],
                'threshold': {
                    'line': {'color': 'green', 'width': 4},
                    'thickness': 0.75,
                    'value': completed_count
                }
            }
        )
    )
    gauge_completed.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)

    # Display the three gauges side-by-side (option 1)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(gauge_not_started, use_container_width=True)
    with g2:
        st.plotly_chart(gauge_inprogress, use_container_width=True)
    with g3:
        st.plotly_chart(gauge_completed, use_container_width=True)

    # Retain other blue visuals: tasks per bucket and priority distribution if available
    if "Bucket Name" in tasks.columns:
        agg = tasks["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name", "Count"]
        fig2 = px.bar(agg, x="Bucket Name", y="Count", title="Tasks per Bucket", color="Bucket Name", color_discrete_sequence=blue_palette)
        st.plotly_chart(fig2, use_container_width=True)

    if "Priority" in tasks.columns:
        fig3 = px.pie(tasks, names="Priority", title="Priority Distribution", color_discrete_sequence=blue_palette)
        st.plotly_chart(fig3, use_container_width=True)

# ======================================================
#   EXPORT SECTION
# ======================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.subheader("📤 Export Data")

csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download current view as CSV",
    csv,
    file_name=f"{sheet_choice}_export.csv",
    mime="text/csv"
)

