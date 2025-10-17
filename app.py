import os
import time
from datetime import datetime, date
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
#   LIGHT THEME (WHITE + DARK BLUE ACCENTS)
# ======================================================
st.markdown(
    """
    <style>
    [data-testid="stAppViewContainer"] {
        background: #FFFFFF !important;
        color: #000000 !important;
    }
    [data-testid="stSidebar"] {
        background: #F4F7FB !important;
        border-right: 2px solid #003366;
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: #FFFFFF !important;
        border-bottom: 1px solid #003366;
    }
    h1, h2, h3, h4, h5, h6, label {
        color: #00264d !important;
        font-weight: 600;
    }
    p, span, div, td, th {
        color: #333333 !important;
    }
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #99b3e6;
        box-shadow: 0 2px 10px rgba(0, 38, 77, 0.15);
        text-align: center;
    }
    hr {
        border: none;
        height: 2px;
        background: #003366;
        opacity: 0.25;
    }
    .stDownloadButton > button {
        background: #003366 !important;
        color: #FFFFFF !important;
        border-radius: 8px !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   SIDEBAR CONFIGURATION
# ======================================================
st.sidebar.header("Configuration")
enable_animations = st.sidebar.checkbox("Enable animations", value=True)
st.sidebar.markdown("---")
st.sidebar.header("Data source")

excel_path = st.sidebar.text_input("Excel file path", value="Ethekwini WS-7761 07 Oct 2025.xlsx")

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
    <h1 style='text-align:center; color:#00264d;'>eThekwini Municipality</h1>
    <hr>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   FILTER SECTION
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
    k1.markdown(f"<div class='metric-card'><h4>Total Tasks</h4><h2 style='color:#00264d;'>{total}</h2></div>", unsafe_allow_html=True)
    k2.markdown(f"<div class='metric-card'><h4>Completed</h4><h2 style='color:#004080;'>{completed}</h2></div>", unsafe_allow_html=True)
    k3.markdown(f"<div class='metric-card'><h4>In Progress</h4><h2 style='color:#3366cc;'>{inprogress}</h2></div>", unsafe_allow_html=True)
    k4.markdown(f"<div class='metric-card'><h4>Overdue</h4><h2 style='color:#cc0000;'>{overdue}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   DATA PREVIEW
# ======================================================
st.subheader("📋 Data Preview")
st.dataframe(df_main.head(200))

# ======================================================
#   TASK ANALYTICS - 3 DIALS (WITH NEEDLES)
# ======================================================
if "Tasks" in sheets:
    st.subheader("📊 Task Analytics")
    tasks = standardize_dates(sheets["Tasks"].copy())

    if "Progress" in tasks.columns:
        prog = tasks["Progress"].fillna("").astype(str).str.lower().str.strip()
        completed_count = prog.eq("completed").sum()
        inprogress_count = prog.eq("in progress").sum()
        not_started_count = prog.isin(["to do", "pending", "to-do", "pending ", "not started"]).sum()
        total_count = len(tasks) if len(tasks) > 0 else 1

        # Define function for gauge creation
        def make_needle_gauge(title, value, total, color):
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                number={'suffix': f" / {total}", 'font': {'color': '#00264d'}},
                title={'text': title, 'font': {'size': 18, 'color': '#00264d'}},
                gauge={
                    'axis': {'range': [0, total], 'tickwidth': 1, 'tickcolor': '#00264d'},
                    'bar': {'color': color},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#00264d",
                    'steps': [
                        {'range': [0, total * 0.5], 'color': '#b3c6ff'},
                        {'range': [total * 0.5, total * 0.8], 'color': '#809fff'},
                        {'range': [total * 0.8, total], 'color': '#4d79ff'}
                    ],
                    'threshold': {
                        'line': {'color': '#001a33', 'width': 6},
                        'thickness': 0.8,
                        'value': value
                    }
                }
            ))
            fig.update_layout(margin=dict(l=25, r=25, t=50, b=25), height=300)
            return fig

        c1, c2, c3 = st.columns(3)
        if enable_animations:
            for pct in range(0, total_count + 1, max(1, total_count // 20)):
                c1.plotly_chart(make_needle_gauge("Not Started", min(pct, not_started_count), total_count, "#3366cc"),
                                use_container_width=True, key=f"not_started_{pct}")
                c2.plotly_chart(make_needle_gauge("In Progress", min(pct, inprogress_count), total_count, "#003399"),
                                use_container_width=True, key=f"in_progress_{pct}")
                c3.plotly_chart(make_needle_gauge("Completed", min(pct, completed_count), total_count, "#001a66"),
                                use_container_width=True, key=f"completed_{pct}")
                time.sleep(0.03)
        else:
            c1.plotly_chart(make_needle_gauge("Not Started", not_started_count, total_count, "#3366cc"), use_container_width=True)
            c2.plotly_chart(make_needle_gauge("In Progress", inprogress_count, total_count, "#003399"), use_container_width=True)
            c3.plotly_chart(make_needle_gauge("Completed", completed_count, total_count, "#001a66"), use_container_width=True)

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
