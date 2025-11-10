import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
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
    # Try to sort by date if possible
    try:
        sorted_sheets = sorted(sheet_names, key=lambda x: datetime.strptime(x, "%Y-%m-%d"), reverse=True)
        latest_sheet = sorted_sheets[0]
    except:
        latest_sheet = sheet_names[-1]
    df = pd.read_excel(path, sheet_name=latest_sheet)
    return df, latest_sheet

df_installations, sheet_name = load_latest_sheet(data_path)

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

    # Clean column names
    df_installations.columns = [c.strip().lower() for c in df_installations.columns]

    # Ensure numeric
    df_installations["total number of installed"] = pd.to_numeric(df_installations["total number of installed"], errors="coerce").fillna(0)
    df_installations["total number of sites"] = pd.to_numeric(df_installations["total number of sites"], errors="coerce").fillna(0)

    def create_installation_gauge(installed, total, contractor, color):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=installed,
                delta={"reference": total, "increasing": {"color": "#ff4d4d"}},
                title={"text": contractor, "font": {"size": 22, "color": color}},
                gauge={
                    "axis": {"range": [0, total], "tickwidth": 1, "tickcolor": "gray"},
                    "bar": {"color": color, "thickness": 0.3},
                    "bgcolor": "#ffffff",
                    "steps": [{"range": [0, total], "color": "#e0e0e0"}],
                    "threshold": {
                        "line": {"color": color, "width": 4},
                        "thickness": 0.8,
                        "value": installed
                    },
                },
                number={"font": {"size": 36, "color": color}},
            )
        )
        fig.update_layout(height=300, margin=dict(l=15, r=15, t=40, b=20))
        return fig

    colors = ["#003366", "#007acc", "#00b386"]

    # Display 3 dials (one per contractor)
    c1, c2, c3 = st.columns(3)
    for i, row in enumerate(df_installations.itertuples(), start=1):
        if i == 1:
            with c1:
                st.plotly_chart(create_installation_gauge(row._2, row._3, row.Contractor, colors[0]), use_container_width=True)
        elif i == 2:
            with c2:
                st.plotly_chart(create_installation_gauge(row._2, row._3, row.Contractor, colors[1]), use_container_width=True)
        elif i == 3:
            with c3:
                st.plotly_chart(create_installation_gauge(row._2, row._3, row.Contractor, colors[2]), use_container_width=True)

    st.markdown("---")
    st.dataframe(df_installations)

# ===================== PLACEHOLDER TABS =====================
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
