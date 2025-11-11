# app.py
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
    div[data-testid="stMarkdownContainer"] {
        color: #003366;
    }
    .metric-card {
        background-color: #eaf4ff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
    }
    th {
        background-color: #007acc;
        color: white !important;
        text-align: center;
        padding: 8px;
    }
    td {
        padding: 6px;
        text-align: center;
    }
    tr:nth-child(even) {background-color: #f0f6fb;}
    tr:hover {background-color: #d6ecff;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"
installations_path = "Weekly update sheet.xlsx"

col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)

with col2:
    st.markdown(
        "<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>",
        unsafe_allow_html=True,
    )

with col3:
    st.image(logo_url, width=220)

st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path):
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

sheets_main = load_data(data_path)
sheets_install = load_data(installations_path)

df_main = sheets_main.get("Tasks", pd.DataFrame()).copy()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")
    df_main = df_main.fillna("Null").replace("NaT", "Null")
    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

# ===================== INSTALLATIONS DATA =====================
df_inst = pd.DataFrame()
if sheets_install:
    first_sheet = list(sheets_install.keys())[0]
    df_inst = sheets_install[first_sheet].copy()
    df_inst.columns = [str(c).strip() for c in df_inst.columns]
    for col in ["Installed", "Total Sites"]:
        if col in df_inst.columns:
            df_inst[col] = pd.to_numeric(df_inst[col], errors="coerce").fillna(0)

# ===================== MAIN TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("⚙️ Installations Progress by Contractor")

    if not df_inst.empty and "Installed" in df_inst.columns and "Total Sites" in df_inst.columns:
        df_inst["Completion %"] = (df_inst["Installed"] / df_inst["Total Sites"]) * 100

        def create_install_gauge(installed, total, contractor, color="#007acc"):
            pct = (installed / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 32, "color": color}},
                    title={"text": contractor, "font": {"size": 18, "color": color}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": color, "thickness": 0.3},
                        "bgcolor": "#f7f9fb",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=260, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        # Display gauges: 3 per row
        num_contractors = len(df_inst)
        cols_per_row = 3
        for i in range(0, num_contractors, cols_per_row):
            row = df_inst.iloc[i:i + cols_per_row]
            cols = st.columns(len(row))
            for j, r in enumerate(row.itertuples()):
                with cols[j]:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.plotly_chart(
                        create_install_gauge(r.Installed, r._asdict().get("Total Sites", 0), r.Contractor),
                        use_container_width=True,
                    )
                    st.markdown(f"<p style='text-align:center; color:#003366; font-size:14px;'>"
                                f"<b>{int(r.Installed)}</b> / {int(r._asdict().get('Total Sites', 0))} installed</p>",
                                unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Installations data not found or missing required columns (Installed / Total Sites).")

# ===================== KPI TAB =====================
with tabs[1]:
    if not df_main.empty:
        st.subheader("📊 Key Performance Indicators")

        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        def create_colored_gauge(value, total, title, dial_color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 36, "color": dial_color}},
                    title={"text": title, "font": {"size": 20, "color": dial_color}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": dial_color, "thickness": 0.3},
                        "bgcolor": "#f7f9fb",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]
        c1, c2, c3, c4 = st.columns(4)
        c1.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", dial_colors[0]), use_container_width=True)
        c2.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", dial_colors[1]), use_container_width=True)
        c3.plotly_chart(create_colored_gauge(completed, total, "Completed", dial_colors[2]), use_container_width=True)
        c4.plotly_chart(create_colored_gauge(overdue, total, "Overdue", dial_colors[3]), use_container_width=True)

        # Insights
        with st.expander("📈 Additional Insights", expanded=True):
            st.markdown("### Expanded Project Insights")
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
                    st.plotly_chart(
                        create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]),
                        use_container_width=True,
                    )

# ===================== TASK BREAKDOWN, TIMELINE & EXPORT (unchanged) =====================
# (Keeping the rest identical to your working version)
