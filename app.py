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
    body { background-color: #f7f9fb; font-family: 'Segoe UI', sans-serif; color: #003366; }
    [data-testid="stAppViewContainer"] { background-color: #f7f9fb; padding: 1rem 2rem; }
    [data-testid="stHeader"] { background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%); color: white; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
    h1, h2, h3 { color: #003366 !important; font-weight: 600; }
    .metric-card { background-color: #eaf4ff; border-radius: 16px; padding: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 1rem; }
    .dial-label { text-align: center; font-weight: 500; color: #003366; margin-bottom: 10px; font-size: 1rem; }
    .gauge-center { display:flex; justify-content:center; width:100%; text-align:center; font-size:1.3vw; font-weight:bold; color:#003366; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== FILE PATHS =====================
data_path = "Ethekwini WS-7761.xlsx"
install_path = "Weekly update sheet.xlsx"
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"

# ===================== HEADER WITH LOGO =====================
col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>", unsafe_allow_html=True)

with col3:
    st.image(logo_url, width=220)

st.markdown("---")

# ===================== LOAD DATA & INSTALLATIONS =====================
def file_last_modified(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0

@st.cache_data
def load_data(path, last_modified):
    if not os.path.exists(path):
        return {}
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try: sheets[s] = pd.read_excel(xls, sheet_name=s)
        except: sheets[s] = pd.DataFrame()
    return sheets

@st.cache_data
def load_install_data(path, last_modified):
    if not os.path.exists(path):
        return pd.DataFrame()
    xls = pd.ExcelFile(path)
    df = pd.read_excel(xls, header=0)
    df = df.rename(columns=lambda x: str(x).strip())
    return df

data_last_mod = file_last_modified(data_path)
install_last_mod = file_last_modified(install_path)
sheets = load_data(data_path, data_last_mod)
df_main = sheets.get("Tasks", pd.DataFrame()).copy()
df_install = load_install_data(install_path, install_last_mod).copy()

# ===================== MAIN TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Status")

    if not df_install.empty:
        # Move Deezlo, Nimba and Isandiso to top
        top_names = ["Deezlo", "Nimba", "Isandiso"]
        top_tiles = df_install[df_install[df_install.columns[0]].astype(str).isin(top_names)]

        if not top_tiles.empty:
            st.markdown("### 🔝 Key Contractors")
            c1, c2, c3 = st.columns(3)
            for idx, (_, row) in enumerate(top_tiles.head(3).iterrows()):
                with [c1, c2, c3][idx]:
                    st.markdown(f"<div class='metric-card'><b>{row[df_install.columns[0]]}</b></div>", unsafe_allow_html=True)

        # === Gauges below ===
        contractor_col = df_install.columns[0]
        installed_col = df_install.columns[1]
        sites_col = df_install.columns[2]

        summary = df_install.groupby(contractor_col).agg(
            Completed_Sites=(installed_col, "sum"),
            Total_Sites=(sites_col, "sum")
        ).reset_index()

        def make_contractor_gauge(completed, total, title, dial_color="#007acc"):
            pct = (completed / total * 100) if total > 0 else 0
            return go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%", "font": {"size": 40}},
                title={"text": title, "font": {"size": 18}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": dial_color},
                    "borderwidth": 1,
                    "bgcolor": "#f7f9fb",
                    "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                },
                domain={"x": [0, 1], "y": [0, 1]},
            ))

        st.markdown("### ⚙️ Contractor Installation Progress")

        records = summary.to_dict("records")
        for i in range(0, len(records), 3):
            cols = st.columns(3)
            for j, rec in enumerate(records[i:i+3]):
                completed, total = int(rec["Completed_Sites"]), int(rec["Total_Sites"])
                pct = (completed/total*100) if total>0 else 0
                color = "#00b386" if pct >= 90 else "#007acc" if pct >= 70 else "#e67300"
                with cols[j]:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.plotly_chart(make_contractor_gauge(completed, total, str(rec[contractor_col]), dial_color=color), use_container_width=True)
                    st.markdown(f"<div class='dial-label'>{completed} / {total} installs</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.warning("No data found in Weekly update sheet.xlsx.")
