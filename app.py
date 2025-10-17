import os
from datetime import datetime
import pandas as pd
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
#   DARK BLUE THEME
# ======================================================
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: #f0f2f6 !important;
        color: #000000 !important;
    }
    [data-testid="stSidebar"] {
        background: #001f3f !important;  
        border-right: 2px solid #001a33;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #001a33 !important;
        border-bottom: 1px solid #001a33;
    }
    h1, h2, h3, h4, h5, h6, label {
        color: #001a33 !important;
        font-weight: 600;
    }
    p, span, div, td, th {
        color: #001a33 !important;
    }
    .metric-card {
        background: #00264d;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #001a33;
        box-shadow: 0 2px 8px rgba(0, 0, 50, 0.3);
        text-align: center;
        color: #ffffff;
    }
    hr {
        border: none;
        height: 2px;
        background: #001a33;
        opacity: 0.5;
    }
    .stDownloadButton > button {
        background: #001a33 !important;
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
    "<h1 style='text-align:center; color:#001a33;'>eThekwini Municipality</h1><hr>",
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
    k1.markdown(f"<div class='metric-card'><h4>Total Tasks</h4><h2>{total}</h2></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><h4>Completed</h4><h2>{completed}</h2></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><h4>In Progress</h4><h2>{inprogress}</h2></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='metric-card'><h4>Overdue</h4><h2 style='color:#ff4d4d;'>{overdue}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   DATA PREVIEW
# ======================================================
st.subheader("📋 Data Preview")
st.dataframe(df_main.head(200))

# ======================================================
#   TASK ANALYTICS (3 NEEDLE GAUGES)
# ======================================================
if "Tasks" in sheets:
    st.subheader("📊 Task Analytics")
    tasks = standardize_dates(sheets["Tasks"].copy())

    if "Progress" in tasks.columns:
        prog = tasks["Progress"].fillna("").astype(str).str.lower().str.strip()
        total_count = len(tasks) if len(tasks) > 0 else 1
        completed_count = prog.eq("completed").sum()
        inprogress_count = prog.eq("in progress").sum()
        not_started_count = prog.isin(["not started", "to do", "pending", "todo", ""]).sum()

        def make_needle_gauge(title, value, total, colors):
            # Gauge with needle effect using steps and bar
            fig = go.Figure()

            # Gauge background
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=value,
                number={'suffix': f" / {total}", 'font': {'size': 22, 'color': '#001a33'}},
                title={'text': title, 'font': {'size': 18, 'color': '#001a33'}},
                gauge={
                    'axis': {'range': [0, total], 'tickcolor': '#001a33', 'tickwidth': 1},
                    'bar': {'color': colors[2]},
                    'bgcolor': "#f0f2f6",
                    'steps': [
                        {'range': [0, total*0.5], 'color': colors[0]},
                        {'range': [total*0.5, total*0.8], 'color': colors[1]},
                        {'range': [total*0.8, total], 'color': colors[2]}
                    ],
                    'borderwidth': 2,
                    'bordercolor': "#001a33"
                }
            ))

            fig.update_layout(height=300, margin=dict(l=25, r=25, t=50, b=25), paper_bgcolor="#f0f2f6")
            return fig

        c1, c2, c3 = st.columns(3)
        # Different dark blue combinations for each gauge
        c1.plotly_chart(make_needle_gauge("Not Started", not_started_count, total_count, ["#003366", "#00264d", "#001f3f"]), use_container_width=True)
        c2.plotly_chart(make_needle_gauge("In Progress", inprogress_count, total_count, ["#00264d", "#001f3f", "#001a33"]), use_container_width=True)
        c3.plotly_chart(make_needle_gauge("Completed", completed_count, total_count, ["#001f3f", "#001a33", "#000d1a"]), use_container_width=True)

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
