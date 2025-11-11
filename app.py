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

# ===================== FILE PATHS =====================
data_path_main = "Ethekwini WS-7761.xlsx"
data_path_install = "Weekly update sheet.xlsx"

# ===================== HEADER WITH LOGO =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"

col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path_main):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path_main)).strftime("%d %B %Y")
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

# ===================== THEME SETTINGS =====================
bg_color = "#ffffff"
text_color = "#003366"
table_colors = {
    "Not Started": "#cce6ff",
    "In Progress": "#ffeb99",
    "Completed": "#b3ffd9",
    "Overdue": "#ffb3b3",
}

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

sheets_main = load_excel_data(data_path_main)
sheets_install = load_excel_data(data_path_install)

df_main = sheets_main.get("Tasks", pd.DataFrame()).copy()
df_install = next(iter(sheets_install.values()), pd.DataFrame()).copy()  # Auto-load first sheet

# ===================== CLEAN DATA =====================
def clean_dataframe(df):
    if not df.empty:
        for c in [col for col in df.columns if "date" in col.lower()]:
            df[c] = pd.to_datetime(df[c], dayfirst=True, errors="coerce")
        df = df.fillna("Null").replace("NaT", "Null")
        drop_cols = [col for col in ["Is Recurring", "Late"] if col in df.columns]
        df = df.drop(columns=drop_cols, errors="ignore")
    return df

df_main = clean_dataframe(df_main)
df_install = clean_dataframe(df_install)

# ===================== MAIN TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Summary")

    if not df_install.empty:
        st.markdown(f"Total records: **{df_install.shape[0]}**")

        # Display first few rows
        st.dataframe(df_install.head(20), use_container_width=True)

        # Optional: Dial summaries if numeric columns exist
        numeric_cols = df_install.select_dtypes(include="number").columns
        if len(numeric_cols) >= 1:
            st.markdown("### Installation Metrics")
            cols = st.columns(min(3, len(numeric_cols)))
            for i, col in enumerate(numeric_cols[:3]):
                val = df_install[col].sum()
                fig = go.Figure(
                    go.Indicator(
                        mode="number",
                        value=val,
                        title={"text": col},
                        number={"font": {"size": 36, "color": "#007acc"}},
                    )
                )
                fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=10))
                with cols[i]:
                    st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No data found in Weekly update sheet.xlsx.")

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

# ===================== TASK BREAKDOWN TAB =====================
with tabs[2]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")

    def df_to_html(df):
        html = "<table><tr>" + "".join([f"<th>{c}</th>" for c in df.columns]) + "</tr>"
        for _, row in df.iterrows():
            html += "<tr>" + "".join([f"<td>{'' if v=='Null' else v}</td>" for v in row]) + "</tr>"
        html += "</table>"
        return html

    st.markdown(df_to_html(df_main), unsafe_allow_html=True)

# ===================== TIMELINE TAB =====================
with tabs[3]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None)
        timeline = df_copy.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["Task Short"] = timeline[df_main.columns[0]].astype(str).str.slice(0, 60)
            fig_tl = px.timeline(
                timeline,
                x_start="Start date",
                x_end="Due date",
                y="Task Short",
                color="Progress",
                title="Task Timeline",
            )
            fig_tl.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

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

        # Include Installations
        if not df_install.empty:
            story.append(Paragraph("<b>Installations Summary</b>", styles["Heading2"]))
            story.append(Spacer(1, 6))
            install_head = df_install.head(10).fillna("Null")
            data_i = [list(install_head.columns)] + install_head.values.tolist()
            table_i = Table(data_i, colWidths=[(A4[1] - 80) / len(install_head.columns)] * len(install_head.columns))
            table_i.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ]))
            story.append(table_i)
            story.append(Spacer(1, 12))

        # Include Task Summary
        story.append(Paragraph("<b>Task Summary</b>", styles["Heading2"]))
        limited = df_main.head(15).fillna("Null")
        data = [list(limited.columns)] + limited.values.tolist()
        table = Table(data, colWidths=[(A4[1] - 80) / len(limited.columns)] * len(limited.columns))
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("Ethekwini Municipality | Automated Project Report", styles["Normal"]))

        doc.build(story)
        st.download_button(
            "📥 Download PDF Report",
            data=buf.getvalue(),
            file_name="Ethekwini_WS7761_SmartMeter_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("No data found to export.")
