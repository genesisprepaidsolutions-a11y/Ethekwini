import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(
    page_title="eThekwini WS-7761 Smart Meter Project",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== THEME =====================
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #003366 !important;
    }
    body {
        font-family: 'Segoe UI', sans-serif;
        color: #003366 !important;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%);
        color: white !important;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .metric-card {
        background-color: #f5f9ff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    [data-testid="stToolbar"], button[data-testid="baseButton-secondary"], [data-testid="stThemeToggle"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Weekly update sheet.xlsx"

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
def load_latest_sheet(path):
    """Load the latest (most recent date-named) sheet from Excel"""
    xls = pd.ExcelFile(path)
    sheet_names = xls.sheet_names
    try:
        sorted_sheets = sorted(sheet_names, key=lambda x: datetime.strptime(x, "%Y-%m-%d"), reverse=True)
        latest_sheet = sorted_sheets[0]
    except:
        latest_sheet = sheet_names[-1]
    df = pd.read_excel(path, sheet_name=latest_sheet)
    return df, latest_sheet

df_installations, sheet_name = load_latest_sheet(data_path)

# ===================== NORMALIZE COLUMNS =====================
# Clean and standardize column names
df_installations.columns = (
    df_installations.columns.str.strip()
    .str.lower()
    .str.replace(r"\s+", " ", regex=True)
)

# Show available columns for debugging
st.write("🔍 Detected columns:", list(df_installations.columns))

# Try to match flexible names
def find_col(possible_names):
    for name in df_installations.columns:
        for target in possible_names:
            if target in name:
                return name
    return None

col_contractor = find_col(["contractor"])
col_installed = find_col(["installed"])
col_sites = find_col(["site"])

if not all([col_contractor, col_installed, col_sites]):
    st.error("❌ Could not find expected columns. Please check your Excel headers.")
    st.stop()

# Convert to numeric safely
df_installations[col_installed] = pd.to_numeric(df_installations[col_installed], errors="coerce").fillna(0)
df_installations[col_sites] = pd.to_numeric(df_installations[col_sites], errors="coerce").fillna(0)

# ===================== TABS =====================
tabs = st.tabs(["KPIs", "Installations", "Task Breakdown", "Timeline", "Export Report"])

# ===================== KPI TAB =====================
with tabs[0]:
    st.subheader("Key Performance Indicators")
    st.markdown("This tab contains existing KPI dials and insights.")

# ===================== INSTALLATIONS TAB =====================
with tabs[1]:
    st.subheader(f"🧰 Installations Overview — Sheet: {sheet_name}")
    st.markdown("Below are the installation dials for each contractor based on the latest weekly update sheet.")

    def create_installation_gauge(installed, total, contractor, color):
        completion = (installed / total * 100) if total > 0 else 0
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=completion,
                title={"text": f"{contractor}<br><span style='font-size:14px'>({installed}/{int(total)})</span>",
                       "font": {"size": 22, "color": color}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                    "bar": {"color": color, "thickness": 0.3},
                    "bgcolor": "#ffffff",
                    "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    "threshold": {
                        "line": {"color": color, "width": 4},
                        "thickness": 0.8,
                        "value": completion
                    },
                },
                number={"font": {"size": 36, "color": color}, "suffix": "%"},
            )
        )
        fig.update_layout(height=300, margin=dict(l=15, r=15, t=40, b=20))
        return fig

    colors = ["#003366", "#007acc", "#00b386"]

    c1, c2, c3 = st.columns(3)
    contractors = df_installations.to_dict("records")
    for i, row in enumerate(contractors):
        contractor = row[col_contractor]
        installed = row[col_installed]
        total = row[col_sites]
        color = colors[i % len(colors)]
        if i == 0:
            with c1:
                st.plotly_chart(create_installation_gauge(installed, total, contractor, color), use_container_width=True)
        elif i == 1:
            with c2:
                st.plotly_chart(create_installation_gauge(installed, total, contractor, color), use_container_width=True)
        elif i == 2:
            with c3:
                st.plotly_chart(create_installation_gauge(installed, total, contractor, color), use_container_width=True)

    st.markdown("---")
    st.dataframe(df_installations)

# ===================== OTHER TABS =====================
with tabs[2]:
    st.subheader("Task Breakdown")
    st.markdown("Placeholder for task breakdown data.")

with tabs[3]:
    st.subheader("Timeline")
    st.markdown("Placeholder for timeline visualization.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
    st.subheader("📄 Export Smart Meter Project Report")
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph("<b>Ethekwini WS-7761 Smart Meter Project Report</b>", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Image(logo_url, width=120, height=70))
    story.append(Spacer(1, 12))
    story.append(Paragraph("Ethekwini Municipality | Automated Project Report", styles["Normal"]))
    doc.build(story)
    st.download_button("📥 Download PDF Report", data=buf.getvalue(),
                       file_name="Ethekwini_WS7761_SmartMeter_Report.pdf", mime="application/pdf")
