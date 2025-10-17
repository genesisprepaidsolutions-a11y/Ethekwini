import os
import time
from datetime import datetime, date
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
    [data-testid="stAppViewContainer"] {
        background: #FFFFFF !important;
        color: #000000 !important;
    }
    [data-testid="stSidebar"] {
        background: #F5F8FF !important;
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
#   HEADER
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

today = date.today()
date_from = st.sidebar.date_input("Start date from", value=today.replace(year=today.year - 1))
date_to = st.sidebar.date_input("Due date to", value=today)

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
    tasks = standardize_dates(sheets["Tasks"].copy())
    
    total = len(tasks)
    completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
    inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
    overdue = (
        ((tasks["Due date"] < pd.Timestamp.today()) &
         (~tasks["Progress"].str.lower().eq("completed"))).sum()
        if "Due date" in tasks.columns and "Progress" in tasks.columns else 0
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
#   TASK ANALYTICS WITH AUTO-ANIMATED DIALS
# ======================================================
if "Tasks" in sheets:
    st.subheader("📊 Task Analytics")

    tasks = standardize_dates(sheets["Tasks"].copy())
    if "Progress" in tasks.columns:
        total = len(tasks)
        not_started = tasks["Progress"].str.lower().eq("not started").sum()
        in_progress = tasks["Progress"].str.lower().eq("in progress").sum()
        completed = tasks["Progress"].str.lower().eq("completed").sum()

        not_started_pct = round((not_started / total) * 100, 1) if total > 0 else 0
        in_progress_pct = round((in_progress / total) * 100, 1) if total > 0 else 0
        completed_pct = round((completed / total) * 100, 1) if total > 0 else 0

        c1, c2, c3 = st.columns(3)

        def make_auto_gauge(title, value, color):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                title={'text': title},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 50], 'color': "#e6f0ff"},
                        {'range': [50, 100], 'color': "#cce6ff"}
                    ],
                }
            ))
            fig.update_layout(height=300, margin=dict(t=20, b=10, l=20, r=20))
            return fig

        # simple auto animation
        if enable_animations:
            for pct in range(0, 101, 5):
                with c1:
                    st.plotly_chart(make_auto_gauge("Not Started (%)", min(pct, not_started_pct), "#99c2ff"), use_container_width=True)
                with c2:
                    st.plotly_chart(make_auto_gauge("In Progress (%)", min(pct, in_progress_pct), "#4da6ff"), use_container_width=True)
                with c3:
                    st.plotly_chart(make_auto_gauge("Completed (%)", min(pct, completed_pct), "#0073e6"), use_container_width=True)
                time.sleep(0.03)
        else:
            with c1:
                st.plotly_chart(make_auto_gauge("Not Started (%)", not_started_pct, "#99c2ff"), use_container_width=True)
            with c2:
                st.plotly_chart(make_auto_gauge("In Progress (%)", in_progress_pct, "#4da6ff"), use_container_width=True)
            with c3:
                st.plotly_chart(make_auto_gauge("Completed (%)", completed_pct, "#0073e6"), use_container_width=True)

    if "Bucket Name" in tasks.columns:
        agg = tasks["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name", "Count"]
        fig2 = px.bar(agg, x="Bucket Name", y="Count", title="Tasks per Bucket", color="Bucket Name", color_discrete_sequence=px.colors.sequential.Blues)
        st.plotly_chart(fig2, use_container_width=True)

    if "Priority" in tasks.columns:
        fig3 = px.pie(tasks, names="Priority", title="Priority Distribution", color_discrete_sequence=px.colors.sequential.Blues)
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
