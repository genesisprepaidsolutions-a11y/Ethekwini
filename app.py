# app_ethekwini.py

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
st.markdown("""
<style>
body {background-color: #f7f9fb; font-family: 'Segoe UI', sans-serif; color: #003366;}
[data-testid="stAppViewContainer"] {background-color: #f7f9fb; padding: 1rem 2rem;}
[data-testid="stHeader"] {background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%); color: white; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.15);}
h1, h2, h3 {color: #003366 !important; font-weight: 600;}
.stTabs [data-baseweb="tab-list"] {gap: 10px;}
.stTabs [data-baseweb="tab"] {background-color: #eaf4ff; border-radius: 10px; padding: 10px 16px; color: #003366; font-weight: 500;}
.stTabs [aria-selected="true"] {background-color: #007acc !important; color: white !important;}
.metric-card {background-color: #eaf4ff; border-radius: 16px; padding: 1rem; box-shadow: 0 2px 10px rgba(0,0,0,0.05); margin-bottom: 1rem;}
.dial-label {text-align: center; font-weight: 500; color: #003366; margin-top: -10px; margin-bottom: 20px;}
table {border-collapse: collapse; width: 100%; border-radius: 10px; overflow: hidden;}
th {background-color: #007acc; color: white !important; text-align: center; padding: 8px;}
td {padding: 6px; text-align: center;}
tr:nth-child(even) {background-color: #f0f6fb;}
tr:hover {background-color: #d6ecff;}
</style>
""", unsafe_allow_html=True)

# ===================== FILE PATHS =====================
data_path = "Ethekwini WS-7761.xlsx"
install_path = os.path.join(os.path.dirname(__file__), "Weekly update sheet.xlsx")
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"

# ===================== HEADER WITH LOGO =====================
col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    file_date = datetime.now().strftime("%d %B %Y")
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)
with col2:
    st.markdown("<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>", unsafe_allow_html=True)
with col3:
    st.image(logo_url, width=220)
st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path=data_path):
    if not os.path.exists(path):
        return {}
    xls = pd.ExcelFile(path)
    return {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}

@st.cache_data
def load_install_data():
    """Read the 'Weekly update sheet.xlsx' (Installations sheet only)."""
    if not os.path.exists(install_path):
        return pd.DataFrame()
    xls = pd.ExcelFile(install_path)
    sheet = None
    for s in xls.sheet_names:
        if "install" in s.lower():
            sheet = s
            break
    if not sheet:
        sheet = xls.sheet_names[0]
    raw = pd.read_excel(xls, sheet_name=sheet, header=None)
    header_row = None
    for i, row in raw.iterrows():
        if "contractor" in " ".join([str(x).lower() for x in row.tolist()]):
            header_row = i
            break
    if header_row is None:
        header_row = 0
    df = pd.read_excel(xls, sheet_name=sheet, header=header_row)
    df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
    df.columns = [str(c).strip() for c in df.columns]
    if "Contractor" not in df.columns:
        for c in df.columns:
            if "contractor" in c.lower():
                df.rename(columns={c: "Contractor"}, inplace=True)
    if "Installed" not in df.columns:
        for c in df.columns:
            if "install" in c.lower():
                df.rename(columns={c: "Installed"}, inplace=True)
    if "Sites" not in df.columns:
        for c in df.columns:
            if "site" in c.lower():
                df.rename(columns={c: "Sites"}, inplace=True)
    for col in ["Sites", "Installed"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

# Load main tasks and installation data
sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame())
df_install = load_install_data()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in df_main.columns:
        if "date" in c.lower():
            df_main[c] = pd.to_datetime(df_main[c], errors="coerce")
    df_main = df_main.fillna("Null")

# ===================== MAIN TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Status")
    if df_install.empty:
        st.warning("No installation data found in 'Weekly update sheet.xlsx'.")
    else:
        st.markdown(f"Total Contractors: **{df_install.shape[0]}**")
        summary = df_install.groupby("Contractor").agg(
            Completed_Sites=("Installed", "sum"),
            Total_Sites=("Sites", "sum")
        ).reset_index()

        def make_gauge(completed, total, title, color):
            pct = (completed / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%"},
                title={"text": title},
                gauge={"axis": {"range": [0, 100]},
                        "bar": {"color": color},
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}]}
            ))
            fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))
            return fig

        for i in range(0, len(summary), 3):
            cols = st.columns(3)
            for j, row in enumerate(summary.iloc[i:i+3].itertuples()):
                pct = (row.Completed_Sites / row.Total_Sites * 100) if row.Total_Sites > 0 else 0
                color = "#00b386" if pct >= 90 else "#007acc" if pct >= 70 else "#e67300"
                with cols[j]:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.plotly_chart(make_gauge(row.Completed_Sites, row.Total_Sites, row.Contractor, color), use_container_width=True)
                    st.markdown(f"<div class='dial-label'>{int(row.Completed_Sites)} / {int(row.Total_Sites)} installs</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### 🧾 Installation Data")
        st.dataframe(df_install)

# ===================== KPI TAB =====================
with tabs[1]:
    if df_main.empty:
        st.warning("No main task data found.")
    else:
        st.subheader("Key Performance Indicators")
        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = ((pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
                   & (~df_main["Progress"].str.lower().eq("completed"))).sum()

        def gauge(v, total, title, color):
            pct = (v / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%"},
                title={"text": title},
                gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}]}
            ))
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=10))
            return fig

        cols = st.columns(4)
        colors = ["#003366", "#007acc", "#00b386", "#e67300"]
        vals = [notstarted, inprogress, completed, overdue]
        labels = ["Not Started", "In Progress", "Completed", "Overdue"]
        for i in range(4):
            with cols[i]:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(gauge(vals[i], total, labels[i], colors[i]), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[2]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")
    if not df_main.empty:
        st.dataframe(df_main)

# ===================== TIMELINE TAB =====================
with tabs[3]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None).dropna(subset=["Start date", "Due date"])
        if not df_copy.empty:
            fig = px.timeline(df_copy, x_start="Start date", x_end="Due date", y=df_copy.columns[0],
                              color="Progress", title="Task Timeline")
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data found.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
    st.subheader("📄 Export Smart Meter Project Report")
    if df_main.empty:
        st.warning("No data found to export.")
    else:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        story = [Paragraph("<b>Ethekwini WS-7761 Smart Meter Project Report</b>", styles["Title"]),
                 Spacer(1, 12),
                 Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]),
                 Spacer(1, 12),
                 Image(logo_url, width=120, height=70),
                 Spacer(1, 12)]

        table_data = [["Metric", "Count"],
                      ["Total Tasks", len(df_main)],
                      ["Completed", completed],
                      ["In Progress", inprogress],
                      ["Not Started", notstarted],
                      ["Overdue", overdue]]
        table = Table(table_data)
        table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.lightgray),
                                   ("GRID", (0, 0), (-1, -1), 1, colors.gray)]))
        story.append(table)
        story.append(Spacer(1, 20))
        doc.build(story)
        st.download_button("📥 Download PDF Report", data=buf.getvalue(),
                           file_name="Ethekwini_WS7761_Report.pdf", mime="application/pdf")
