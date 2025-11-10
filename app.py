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

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="eThekwini WS-7761 Smart Meter Project", layout="wide")

# ===================== CUSTOM STYLES =====================
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
        "<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project</h1>",
        unsafe_allow_html=True,
    )

with col3:
    st.image(logo_url, width=220)

st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path):
    try:
        xls = pd.ExcelFile(path)
        sheets = {}
        for s in xls.sheet_names:
            try:
                sheets[s] = pd.read_excel(xls, sheet_name=s)
            except Exception:
                sheets[s] = pd.DataFrame()
        return sheets
    except Exception:
        return {}

sheets = load_data(data_path)
df_main = sheets.get("Tasks", pd.DataFrame())
if df_main.empty:
    df_main = pd.DataFrame(columns=["Task Name", "Start date", "Due date", "Progress", "Priority", "Bucket Name"])

# ===================== INSTALLATION DATA =====================
install_data = {
    "Contractor": ["Deezlo", "Nimba", "Isandiso"],
    "Installed": [60, 48, 26],
    "Sites": [155, 156, 156],
}
df_install = pd.DataFrame(install_data)

# ===================== TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("🧰 Installations Overview")
    st.markdown("Below are the installation dials for each contractor based on the latest weekly update sheet.")

    def create_installation_gauge(installed, total, title, color):
        pct = (installed / total) * 100 if total > 0 else 0
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix": "%", "font": {"size": 36, "color": color}},
                title={"text": title, "font": {"size": 20, "color": color}},
                gauge={
                    "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                    "bar": {"color": color, "thickness": 0.3},
                    "bgcolor": "#f7f9fb",
                    "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                },
            )
        )
        fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
        return fig

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(create_installation_gauge(60, 155, "Deezlo Installed", "#003366"), use_container_width=True)
    with c2:
        st.plotly_chart(create_installation_gauge(48, 156, "Nimba Installed", "#007acc"), use_container_width=True)
    with c3:
        st.plotly_chart(create_installation_gauge(26, 156, "Isandiso Installed", "#00b386"), use_container_width=True)

# ===================== KPIs TAB =====================
with tabs[1]:
    st.subheader("📊 Key Performance Indicators")
    if not df_main.empty:
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
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", dial_colors[0]), use_container_width=True)
        with c2:
            st.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", dial_colors[1]), use_container_width=True)
        with c3:
            st.plotly_chart(create_colored_gauge(completed, total, "Completed", dial_colors[2]), use_container_width=True)
        with c4:
            st.plotly_chart(create_colored_gauge(overdue, total, "Overdue", dial_colors[3]), use_container_width=True)
    else:
        st.info("No task data found in workbook.")

# ===================== TASK BREAKDOWN TAB =====================
with tabs[2]:
    st.subheader("📋 Task Breakdown")
    if df_main.empty:
        st.warning("No task data available.")
    else:
        st.dataframe(df_main, use_container_width=True)

# ===================== TIMELINE TAB =====================
with tabs[3]:
    st.subheader("📅 Project Timeline")
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.dropna(subset=["Start date", "Due date"]).copy()
        if not df_copy.empty:
            df_copy["Start date"] = pd.to_datetime(df_copy["Start date"], errors="coerce")
            df_copy["Due date"] = pd.to_datetime(df_copy["Due date"], errors="coerce")
            df_copy["Task"] = df_copy[df_main.columns[0]].astype(str)
            progress_colors = {"Not Started": "#66b3ff", "In Progress": "#3399ff", "Completed": "#33cc33"}
            fig = px.timeline(
                df_copy,
                x_start="Start date",
                x_end="Due date",
                y="Task",
                color="Progress",
                color_discrete_map=progress_colors,
                title="Task Timeline",
            )
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No timeline data available.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
    st.subheader("📄 Export Smart Meter Project Report")

    if not df_main.empty:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()

        cell_style = ParagraphStyle(name="CellStyle", fontSize=8, leading=10, alignment=1)
        null_style = ParagraphStyle(name="NullStyle", fontSize=8, textColor=colors.grey, leading=10, alignment=1)

        story.append(Paragraph("<b>Ethekwini WS-7761 Smart Meter Project Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Image(logo_url, width=120, height=70))
        story.append(Spacer(1, 12))

        kpi_data = [
            ["Metric", "Count"],
            ["Total Tasks", len(df_main)],
            ["Completed", df_main["Progress"].str.lower().eq("completed").sum()],
            ["In Progress", df_main["Progress"].str.lower().eq("in progress").sum()],
            ["Not Started", df_main["Progress"].str.lower().eq("not started").sum()],
        ]
        table = Table(kpi_data, colWidths=[200, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9d9d9")),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        doc.build(story)
        st.download_button("📥 Download PDF Report", data=buf.getvalue(),
                           file_name="Ethekwini_WS7761_SmartMeter_Report.pdf", mime="application/pdf")
    else:
        st.warning("No data found to export.")
