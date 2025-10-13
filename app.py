
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
#   CUSTOM STYLING (DARK GLASS THEME + ANIMATIONS)
# ======================================================
st.markdown(
    """
    <style>
    /* Global Dark Background */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #0e0e0e, #121212) !important;
        color: white !important;
    }

    [data-testid="stSidebar"] {
        background: #181818 !important;
        border-right: 1px solid #2a2a2a;
    }

    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: rgba(18,18,18,0.8) !important;
        backdrop-filter: blur(10px);
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6, p, label, span, div, td, th {
        color: #f2f2f2 !important;
    }

    /* KPI Glass Cards */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        backdrop-filter: blur(12px);
        transition: all 0.3s ease-in-out;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.5);
    }

    /* Animations */
    @keyframes fadeIn {
        0% {opacity: 0; transform: translateY(10px);}
        100% {opacity: 1; transform: translateY(0);}
    }

    .fade-in {
        animation: fadeIn 1s ease-in-out;
    }

    /* Divider Styling */
    hr {
        border: 1px solid #333;
        margin-top: 20px;
        margin-bottom: 20px;
    }

    /* Buttons */
    .stDownloadButton > button {
        background-color: #F26522 !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: bold;
        transition: background 0.3s ease;
    }
    .stDownloadButton > button:hover {
        background-color: #ff7f3e !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   COMPANY HEADER (DEEZLO BRANDING)
# ======================================================
logo_path = "/mnt/data/deezlo.png"

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=420)
    st.markdown("""
        <div class="fade-in">
            <h1 style='text-align:center; color:#F26522; margin-bottom:0;'>Deezlo Trading cc</h1>
            <h4 style='text-align:center; margin-top:0; color:white;'>You Dream it, We Build it</h4>
            <h2 style='text-align:center; margin-top:2rem; color:#F26522;'>Ethekwini WS-7761 Dashboard</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

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
        styles = ["background-color:#2e7d32; color:white;"] * len(row)
    elif "Due date" in row.index:
        due = row["Due date"]
        if pd.notna(due) and pd.to_datetime(due) < pd.Timestamp.today():
            styles = ["background-color:#8b0000; color:white;"] * len(row)
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
#   KPI SECTION (Animated Glass Cards)
# ======================================================
if "Tasks" in sheets:
    st.markdown("<div class='fade-in'><h3>📈 Key Performance Indicators</h3></div>", unsafe_allow_html=True)
    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

    total = len(tasks)
    completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
    inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
    overdue = (
        ((tasks["Due date"] < pd.Timestamp.today()) &
         (~tasks["Progress"].str.lower().eq("completed"))).sum()
        if "Due date" in tasks.columns and "Progress" in tasks.columns else 0
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"<div class='metric-card fade-in'><h4>Total Tasks</h4><h2>{total}</h2></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='metric-card fade-in'><h4>Completed</h4><h2 style='color:#77DD77;'>{completed}</h2></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='metric-card fade-in'><h4>In Progress</h4><h2 style='color:#FFFACD;'>{inprogress}</h2></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='metric-card fade-in'><h4>Overdue</h4><h2 style='color:#FFB6C1;'>{overdue}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   DATA PREVIEW
# ======================================================
st.markdown("<div class='fade-in'><h3>📋 Data Preview</h3></div>", unsafe_allow_html=True)
st.dataframe(df_main.head(200))

# ======================================================
#   DASHBOARDS (PASTEL COLOUR PALETTE)
# ======================================================
pastel_colors = ["#AEC6CF", "#77DD77", "#CBAACB", "#FFFACD", "#FFB347", "#FFB6C1"]

if "Tasks" in sheets:
    st.markdown("<div class='fade-in'><h3>📊 Task Analytics</h3></div>", unsafe_allow_html=True)
    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

    if "Progress" in tasks.columns:
        fig = px.pie(tasks, names="Progress", hole=0.3, title="Progress Distribution", color_discrete_sequence=pastel_colors)
        fig.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="white")
        st.plotly_chart(fig, use_container_width=True)

    if "Bucket Name" in tasks.columns:
        agg = tasks["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name", "Count"]
        fig2 = px.bar(agg, x="Bucket Name", y="Count", color="Bucket Name",
                      color_discrete_sequence=pastel_colors, title="Tasks per Bucket")
        fig2.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

    if "Priority" in tasks.columns:
        fig3 = px.pie(tasks, names="Priority", title="Priority Distribution", color_discrete_sequence=pastel_colors)
        fig3.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

    if {"Start date", "Due date", "Task Name"}.issubset(tasks.columns):
        timeline = tasks.dropna(subset=["Start date", "Due date", "Task Name"])
        if not timeline.empty:
            fig4 = px.timeline(timeline, x_start="Start date", x_end="Due date", y="Task Name",
                               color="Bucket Name" if "Bucket Name" in timeline.columns else None,
                               color_discrete_sequence=pastel_colors, title="Task Timeline (Start to Due)")
            fig4.update_yaxes(autorange="reversed")
            fig4.update_layout(paper_bgcolor="#121212", plot_bgcolor="#121212", font_color="white")
            st.plotly_chart(fig4, use_container_width=True)

# ======================================================
#   EXPORT SECTION
# ======================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='fade-in'><h3>📤 Export Data</h3></div>", unsafe_allow_html=True)

csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download current view as CSV",
    csv,
    file_name=f"{sheet_choice}_export.csv",
    mime="text/csv"
)
