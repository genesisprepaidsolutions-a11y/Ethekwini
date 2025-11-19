# ⬇️ FULL FILE STARTS HERE ⬇️
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
    st.markdown(
        "<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>",
        unsafe_allow_html=True,
    )

with col3:
    st.image(logo_url, width=220)

st.markdown("---")

# ===================== THEME SETTINGS =====================
bg_color = "#ffffff"
text_color = "#003366"
table_colors = {
    "Not Started": "#cce6ff",
    "In Progress": "#ffeb99",
    "Completed": "#b3ffd9",
    "Overdue": "#ffb3b3",
}

# ===================== LOAD DATA (CACHED) =====================

def file_last_modified(path):
    return os.path.getmtime(path) if os.path.exists(path) else 0

@st.cache_data
def load_data(path, last_modified):
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

@st.cache_data
def load_install_data(path, last_modified, target_sheet_names=None):
    if not os.path.exists(path):
        return pd.DataFrame()
    xls = pd.ExcelFile(path)
    sheet_names = xls.sheet_names
    chosen = None
    if target_sheet_names is None:
        for s in sheet_names:
            if str(s).strip().lower() == "installations":
                chosen = s
                break
        if not chosen:
            for s in sheet_names:
                if "install" in str(s).lower():
                    chosen = s
                    break
    else:
        for s in sheet_names:
            if s in target_sheet_names:
                chosen = s
                break
    if not chosen:
        chosen = sheet_names[0] if len(sheet_names) > 0 else None
    if not chosen:
        return pd.DataFrame()
    raw = pd.read_excel(xls, sheet_name=chosen, header=None, dtype=object)
    header_row_idx = None
    for idx, row in raw.iterrows():
        first_cell = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ""
        if "contractor" in first_cell or "installer" in first_cell or "contractors" in first_cell:
            header_row_idx = idx
            break
        row_text = " ".join([str(x).lower() if pd.notna(x) else "" for x in row.tolist()])
        if "contractor" in row_text or "installer" in row_text:
            header_row_idx = idx
            break
    if header_row_idx is None:
        header_row_idx = 0
    try:
        df = pd.read_excel(xls, sheet_name=chosen, header=header_row_idx, dtype=object)
    except Exception:
        df = pd.DataFrame()
    if not df.empty:
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]
        colmap = {}
        for c in df.columns:
            low = c.lower()
            if "contractor" in low or "installer" in low or "contractors" in low:
                colmap[c] = "Contractor"
            elif "install" in low or "installed" in low or "complete" in low or "status" in low:
                colmap[c] = "Installed"
            elif "site" in low or "sites" in low or "total" in low:
                colmap[c] = "Sites"
        if colmap:
            df = df.rename(columns=colmap)
        if "Contractor" in df.columns:
            df["Contractor"] = df["Contractor"].astype(str).str.strip()
        for numeric_col in ["Sites", "Installed"]:
            if numeric_col in df.columns:
                df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")
    return df

data_last_mod = file_last_modified(data_path)
install_last_mod = file_last_modified(install_path)
sheets = load_data(data_path, data_last_mod)
df_main = sheets.get("Tasks", pd.DataFrame()).copy()
df_install = load_install_data(install_path, install_last_mod).copy()

# ===================== INSTALLATIONS TAB =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

with tabs[0]:
    st.subheader("📦 Installations Status")
    if not df_install.empty:
        st.markdown(f"Total Contractors: **{df_install.shape[0]}**")

        contractor_col = "Contractor" if "Contractor" in df_install.columns else None
        status_col = "Installed" if "Installed" in df_install.columns else None
        sites_col = "Sites" if "Sites" in df_install.columns else None

        if contractor_col and status_col:
            def make_contractor_gauge(completed, total, title, dial_color="#007acc"):
                pct = (completed / total * 100) if total and total > 0 else 0
                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 38, "color": dial_color}},
                    title={"text": "", "font": {"size": 1}},
                    gauge={"axis": {"range": [0, 100]},
                           "bar": {"color": dial_color, "thickness": 0.3},
                           "steps": [{"range": [0, 100], "color": "#e0e0e0"}]}
                ))
                fig.update_layout(height=200, margin=dict(l=5, r=5, t=5, b=5))
                return fig

            summary = df_install.groupby(contractor_col).agg(
                Completed_Sites=(status_col, "sum"),
                Total_Sites=(sites_col, "sum"),
            ).reset_index()

            records = summary.to_dict("records")
            for i in range(0, len(records), 3):
                cols = st.columns(3)
                for j, rec in enumerate(records[i : i + 3]):
                    completed = int(rec["Completed_Sites"])
                    total = int(rec["Total_Sites"])
                    pct = (completed / total * 100) if total else 0
                    color = "#00b386" if pct >= 90 else "#007acc" if pct >= 70 else "#e67300"

                    with cols[j]:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)

                        # Contractor Title Above Gauge
                        st.markdown(
                            f"<h4 style='text-align:center; color:#003366; margin-bottom:-5px;'>{rec[contractor_col]}</h4>",
                            unsafe_allow_html=True)

                        # Gauge
                        st.plotly_chart(make_contractor_gauge(completed, total, "", color),
                                        use_container_width=True, config={'displayModeBar': False})

                        # Percentage
                        st.markdown(
                            f"<p style='text-align:center; font-size:24px; font-weight:600; color:#e67300; margin-top:-10px;'>{pct:.1f}%</p>",
                            unsafe_allow_html=True)

                        # Install Numbers
                        st.markdown(
                            f"<p style='text-align:center; color:#003366; font-size:14px; margin-top:-5px;'>{completed} / {total} installs</p>",
                            unsafe_allow_html=True)

                        st.markdown("</div>", unsafe_allow_html=True)

# ===================== KPI, TASK, TIMELINE & EXPORT (UNCHANGED) =====================
# *** The rest of your code stays exactly the same ***
