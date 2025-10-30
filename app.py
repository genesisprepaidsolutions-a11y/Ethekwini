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
st.set_page_config(
    page_title="eThekwini WS-7761 Smart Meter Project",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== FORCE WHITE THEME =====================
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #003366 !important;
    }
    body {
        font-family: 'Segoe UI', sans-serif;
        background-color: #ffffff !important;
        color: #003366 !important;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%);
        color: white !important;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        padding: 1rem 2rem;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
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
    h1, h2, h3 { color: #003366 !important; font-weight: 600; }
    div[data-testid="stMarkdownContainer"] { color: #003366 !important; }
    .metric-card {
        background-color: #f5f9ff;
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
        background-color: #ffffff !important;
    }
    th {
        background-color: #007acc !important;
        color: white !important;
        text-align: center;
        padding: 8px;
    }
    td {
        padding: 6px;
        text-align: center;
        color: #003366 !important;
    }
    tr:nth-child(even) { background-color: #f0f6fb; }
    tr:hover { background-color: #d6ecff; }
    [data-testid="stToolbar"], button[data-testid="baseButton-secondary"], [data-testid="stThemeToggle"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER WITH LOGO =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"

col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project</h1>", unsafe_allow_html=True)

with col3:
    st.image(logo_url, width=220)

st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path=data_path):
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            sheets[s] = pd.read_excel(xls, sheet_name=s)
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame()).copy()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    df_main = df_main.fillna("Null")
    df_main = df_main.replace("NaT", "Null")
    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

# ===================== MAIN TABS =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Installations", "Export Report"])

# ===================== KPI TAB =====================
with tabs[0]:
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
                        "bgcolor": "#ffffff",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        st.markdown("#### 📊 KPI Overview")
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            st.plotly_chart(create_colored_gauge(completed, total, "Completed", "#00b386"), use_container_width=True)
        with kpi_cols[1]:
            st.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", "#007acc"), use_container_width=True)
        with kpi_cols[2]:
            st.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", "#e67300"), use_container_width=True)
        with kpi_cols[3]:
            st.plotly_chart(create_colored_gauge(overdue, total, "Overdue", "#cc0000"), use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")
    def df_to_html(df):
        html = "<table><tr>" + "".join(f"<th>{c}</th>" for c in df.columns) + "</tr>"
        for _, row in df.iterrows():
            html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
        html += "</table>"
        return html
    st.markdown(df_to_html(df_main), unsafe_allow_html=True)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None)
        timeline = df_copy.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0, 60)
            progress_color_map = {"Not Started": "#66b3ff", "In Progress": "#3399ff", "Completed": "#33cc33"}
            timeline["Progress"] = timeline["Progress"].fillna("Not Specified")
            fig_tl = px.timeline(
                timeline,
                x_start="Start date",
                x_end="Due date",
                y="task_short",
                color="Progress",
                title="Task Timeline",
                color_discrete_map=progress_color_map,
            )
            fig_tl.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== INSTALLATION TAB =====================
with tabs[3]:
    st.subheader("🧰 Contractor Installation Insights")
    if "Installation" in sheets:
        df_inst = sheets["Installation"].copy()
        df_inst.columns = [c.lower().strip() for c in df_inst.columns]
        if "contractor" in df_inst.columns and "count of installations" in df_inst.columns:
            contractors = df_inst[["contractor", "count of installations"]].dropna()
            contractors["count of installations"] = pd.to_numeric(contractors["count of installations"], errors="coerce").fillna(0)

            def create_count_gauge(value, title, dial_color="#007acc"):
                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=value,
                        title={"text": title, "font": {"size": 18, "color": "#003366"}},
                        number={"font": {"size": 28, "color": dial_color}},
                        gauge={
                            "axis": {"range": [0, max(contractors["count of installations"]) * 1.2]},
                            "bar": {"color": dial_color, "thickness": 0.3},
                            "bgcolor": "#f5f9ff",
                            "steps": [{"range": [0, value], "color": "#d9ecff"}],
                        },
                    )
                )
                fig.update_layout(height=260, margin=dict(l=15, r=15, t=40, b=20))
                return fig

            dial_colors = ["#007acc", "#009999", "#00b386", "#e67300", "#3399ff", "#3366cc"]

            for i in range(0, len(contractors), 3):
                cols = st.columns(3)
                for j, col in enumerate(cols):
                    if i + j < len(contractors):
                        row = contractors.iloc[i + j]
                        with col:
                            st.plotly_chart(
                                create_count_gauge(
                                    row["count of installations"],
                                    row["contractor"],
                                    dial_colors[(i + j) % len(dial_colors)],
                                ),
                                use_container_width=True,
                            )
        else:
            st.warning("⚠️ 'Contractor' or 'Count of Installations' column missing in Installation tab.")
    else:
        st.warning("⚠️ Installation tab not found in the Excel file.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
    st.subheader("📄 Export Smart Meter Project Report")
    if not df_main.empty:
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
        doc.build(story)
        st.download_button(
            "📥 Download PDF Report",
            data=buf.getvalue(),
            file_name="Ethekwini_WS7761_SmartMeter_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("No data found to export.")

