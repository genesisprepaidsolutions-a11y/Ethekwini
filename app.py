import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="eThekwini WS-7761 Smart Meter Project", layout="wide")

# ===================== CUSTOM STYLE =====================
st.markdown(
    """
    <style>
    body {
        background-color: #f7f9fb;
        font-family: 'Segoe UI', sans-serif;
        color: #003366;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #f7f9fb;
        padding: 1rem 2rem;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%);
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    h1, h2, h3 {
        color: #003366 !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #eaf4ff;
        border-radius: 10px;
        padding: 10px 16px;
        color: #003366;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007acc !important;
        color: white !important;
    }
    .metric-card {
        background-color: #eaf4ff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .dial-label {
        text-align: center;
        font-weight: 500;
        color: #003366;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== FILE PATHS =====================
data_path_main = "Ethekwini WS-7761.xlsx"
data_path_install = "Weekly update sheet.xlsx"
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"

# ===================== HEADER WITH LOGO =====================
col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path_main):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path_main)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>", unsafe_allow_html=True)
with col3:
    st.image(logo_url, width=220)
st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_excel_data(path):
    if not os.path.exists(path):
        return {}
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            sheets[s] = pd.read_excel(xls, sheet_name=s)
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets

# Load main project file
sheets_main = load_excel_data(data_path_main)
df_main = sheets_main.get("Tasks", pd.DataFrame()).copy()

# Load installation sheet
sheets_install = load_excel_data(data_path_install)
df_install = sheets_install.get("Installations", pd.DataFrame()).copy()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")
    df_main = df_main.fillna("Null").replace("NaT", "Null")
    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

# ===================== TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Progress by Contractor")

    if not df_install.empty:
        df_install.columns = [c.strip().lower() for c in df_install.columns]

        # Expect columns: Contractor, Installs Done, Total Sites
        contractor_col = [c for c in df_install.columns if "contractor" in c][0]
        installs_col = [c for c in df_install.columns if "done" in c][0]
        total_col = [c for c in df_install.columns if "site" in c or "total" in c][0]

        df_install["percent"] = df_install[installs_col] / df_install[total_col] * 100

        def create_install_gauge(value, total, title, color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 36, "color": color}},
                    title={"text": title, "font": {"size": 18, "color": color}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": color, "thickness": 0.3},
                        "steps": [{"range": [0, 100], "color": "#f0f6fb"}],
                    },
                )
            )
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=0))
            return fig

        colors = ["#007acc", "#00b386", "#ff9933", "#003366", "#cc3366", "#3399ff"]
        cols_per_row = 3
        for i in range(0, len(df_install), cols_per_row):
            row = df_install.iloc[i:i+cols_per_row]
            cols = st.columns(len(row))
            for j, (_, r) in enumerate(row.iterrows()):
                with cols[j]:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.plotly_chart(create_install_gauge(r[installs_col], r[total_col], r[contractor_col], colors[j % len(colors)]), use_container_width=True)
                    st.markdown(f"<div class='dial-label'>{int(r[installs_col])} / {int(r[total_col])} installs</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("No installation data found in 'Weekly update sheet.xlsx'.")

# ===================== KPI TAB =====================
with tabs[1]:
    if not df_main.empty:
        st.subheader("Key Performance Indicators")

        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        def create_colored_gauge(value, total, title, color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 36, "color": color}},
                    title={"text": title, "font": {"size": 20, "color": color}},
                    gauge={"axis": {"range": [0, 100]}, "bar": {"color": color, "thickness": 0.3}, "bgcolor": "#f7f9fb"},
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]

        c1, c2, c3, c4 = st.columns(4)
        for c, (v, t, clr) in zip([c1, c2, c3, c4],
                                  [(notstarted, "Not Started", dial_colors[0]),
                                   (inprogress, "In Progress", dial_colors[1]),
                                   (completed, "Completed", dial_colors[2]),
                                   (overdue, "Overdue", dial_colors[3])]):
            with c:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(create_colored_gauge(v, total, t, clr), use_container_width=True)
                st.markdown(f"<div class='dial-label'>{v} / {total}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("📈 Additional Insights", expanded=True):
            df_duration = df_main.copy().replace("Null", None)
            df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
            df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
            df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
            avg_duration = df_duration["Duration"].mean()
            st.markdown(f"**⏱️ Average Task Duration:** {avg_duration:.1f} days" if pd.notna(avg_duration) else "**⏱️ Average Task Duration:** N/A")

            priority_counts = df_main["Priority"].value_counts(normalize=True) * 100
            st.markdown("#### 🔰 Priority Distribution")
            cols = st.columns(2)
            priority_colors = ["#ff6600", "#0099cc", "#00cc66", "#cc3366"]
            for i, (priority, pct) in enumerate(priority_counts.items()):
                with cols[i % 2]:
                    st.plotly_chart(create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]), use_container_width=True)

            completion_by_bucket = df_main.groupby("Bucket Name")["Progress"].apply(lambda x: (x.str.lower() == "completed").mean() * 100).reset_index()
            st.markdown("#### 🧭 Phase Completion Dials")
            bucket_cols = st.columns(2)
            for i, row in enumerate(completion_by_bucket.itertuples()):
                with bucket_cols[i % 2]:
                    st.plotly_chart(create_colored_gauge(row._2, 100, row._1, "#006666"), use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[2]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")
    st.dataframe(df_main, use_container_width=True)

# ===================== TIMELINE TAB =====================
with tabs[3]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None)
        timeline = df_copy.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0, 60)
            progress_color_map = {"Not Started": "#66b3ff", "In Progress": "#3399ff", "Completed": "#33cc33"}
            fig_tl = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short", color="Progress",
                                 color_discrete_map=progress_color_map, title="Task Timeline")
            fig_tl.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
    st.subheader("📄 Export Smart Meter Project Report")
    st.info("The report now includes installation summary as well as KPIs.")

