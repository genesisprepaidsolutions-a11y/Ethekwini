import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="Ethekwini WS-7761 Smart Meter Project", layout="wide")

# ===================== CONSTANTS / BRANDING =====================
LOGO_URL = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"
logo_path_local = "ethekwini_logo.png"  # preserved for PDF export if you have local copy

# Theme / colors
bg_color = "white"
text_color = "black"
table_colors = {
    "Not Started": "#80ff80",
    "In Progress": "#ffff80",
    "Completed": "#80ccff",
    "Overdue": "#ff8080",
}
# Gradient mapping for visual dials:
GRADIENT_RANGES = [
    {"range": [0, 50], "color": "#ff4d4d"},     # red
    {"range": [50, 80], "color": "#ffd24d"},    # yellow
    {"range": [80, 100], "color": "#b3ff66"},   # light green
]
# For final top range use strong green color visually
FINAL_GREEN = "#33cc33"

# ===================== STYLES (sticky header + theme) =====================
st.markdown(
    f"""
    <style>
    /* Make header area sticky and style it */
    .stApp > div:first-child {{
        background-color: {bg_color};
    }}
    .header-row {{
        position: sticky;
        top: 0;
        z-index: 999;
        padding: 8px 4px;
        background-color: {bg_color};
        border-bottom: 1px solid #e6e6e6;
    }}
    .main-title {{
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: {text_color};
        text-align: center;
    }}
    .data-as-of {{
        font-size: 14px;
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER WITH LOGO (date left, title centered, logo right) =====================
file_date = (
    datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    if os.path.exists(data_path)
    else datetime.now().strftime("%d %B %Y")
)

st.markdown("<div class='header-row'>", unsafe_allow_html=True)
left_col, center_col, right_col = st.columns([1, 6, 1])
with left_col:
    st.markdown(f"<div class='data-as-of'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)
with center_col:
    st.markdown(f"<h1 class='main-title'>Ethekwini WS-7761 Smart Meter Project Status</h1>", unsafe_allow_html=True)
with right_col:
    # Display the logo from the provided GitHub raw URL (Streamlit accepts remote images)
    st.image(LOGO_URL, width=120)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path=data_path):
    if os.path.exists(path):
        xls = pd.ExcelFile(path)
        sheets = {}
        for s in xls.sheet_names:
            try:
                sheets[s] = pd.read_excel(xls, sheet_name=s)
            except Exception:
                sheets[s] = pd.DataFrame()
        return sheets
    else:
        # if file doesn't exist return empty dict
        return {}

sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame()).copy()

# ===================== CLEAN DATA (unchanged behavior) =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    df_main = df_main.fillna("Null")
    df_main = df_main.replace("NaT", "Null")

# ===================== TABS (unchanged) =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== HELPER: choose color by percent (for indicator bar color) =====================
def color_for_percent(pct: float) -> str:
    try:
        pct = float(pct)
    except Exception:
        return GRADIENT_RANGES[0]["color"]
    if pct <= 50:
        return GRADIENT_RANGES[0]["color"]
    elif pct <= 80:
        return GRADIENT_RANGES[1]["color"]
    elif pct <= 100:
        return GRADIENT_RANGES[2]["color"]
    else:
        return FINAL_GREEN

# ===================== HELPER: create gauge with gradient background steps =====================
def create_gradient_gauge(value, title, suffix="%", max_range=100, height=280, show_number=True):
    # steps for visuals (show the ranges)
    steps = []
    # ensure steps cover 0..max_range
    for r in GRADIENT_RANGES:
        start = max(0, r["range"][0])
        end = min(max_range, r["range"][1])
        steps.append({"range": [start, end], "color": r["color"]})
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number" if show_number else "gauge",
            value=value if value is not None else 0,
            number={"suffix": suffix, "font": {"size": 30, "color": text_color}},
            gauge={
                "axis": {"range": [0, max_range]},
                "bar": {"color": color_for_percent(value), "thickness": 0.35},
                "bgcolor": "#f6f6f6",
                "steps": steps,
            },
            title={"text": title, "font": {"size": 14, "color": text_color}},
        )
    )
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=45, b=20), paper_bgcolor=bg_color)
    return fig

# ===================== KPI TAB =====================
with tabs[0]:
    if not df_main.empty:
        st.subheader("Key Performance Indicators")
