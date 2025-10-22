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
import plotly.io as pio

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="WS7761 - Smart Meter Project Status", layout="wide")

# ===================== HEADER WITH LOGO =====================
logo_path = "ethekwini_logo.png"
col1, col2 = st.columns([8, 1])
with col1:
    st.markdown(
        "<h1 style='text-align:center'>WS7761 - Smart Meter Project Status</h1>",
        unsafe_allow_html=True,
    )
with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=90)

# ===================== THEME SETTINGS =====================
bg_color = "white"
text_color = "black"
table_colors = {
    "Not Started": "#80ff80",
    "In Progress": "#ffff80",
    "Completed": "#80ccff",
    "Overdue": "#ff8080",
}

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
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

if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

# ===================== MAIN TABS =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== KPI TAB =====================
with tabs[0]:
    if not df_main.empty:
        st.subheader("Key Performance Indicators")

        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (df_main["Due date"] < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        def create_simple_gauge(value, total, title, color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 36, "color": text_color}},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": color, "thickness": 0.3},
                        "bgcolor": "#e6e6e6",
                        "steps": [{"range": [0, 100], "color": "#f0f0f0"}],
                    },
                    title={"text": title, "font": {"size": 18, "color": text_color}},
                )
            )
            fig.update_layout(
                height=280, margin=dict(l=20, r=20, t=50, b=50), paper_bgcolor=bg_color
            )
            return fig

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            fig_ns = create_simple_gauge(notstarted, total, "Not Started", table_colors["Not Started"])
            st.plotly_chart(fig_ns, use_container_width=True)
        with c2:
            fig_ip = create_simple_gauge(inprogress, total, "In Progress", table_colors["In Progress"])
            st.plotly_chart(fig_ip, use_container_width=True)
        with c3:
            fig_c = create_simple_gauge(completed, total, "Completed", table_colors["Completed"])
            st.plotly_chart(fig_c, use_container_width=True)
        with c4:
            fig_o = create_simple_gauge(overdue, total, "Overdue", table_colors["Overdue"])
            st.plotly_chart(fig_o, use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")

    def df_to_html(df):
        html = "<table style='border-collapse: collapse; width: 100%;'>"
        html += "<tr>"
        for col in df.columns:
            html += f"<th style='border:1px solid gray; padding:4px; background-color:{bg_color}; color:{text_color}'>{col}</th>"
        html += "</tr>"
        for _, row in df.iterrows():
            row_color = bg_color
            if "Progress" in df.columns and "Due date" in df.columns:
                progress = str(row["Progress"]).lower()
                due_date = row["Due date"]
                if pd.notna(due_date) and due_date < pd.Timestamp.today() and progress != "completed":
                    row_color = table_colors["Overdue"]
                elif progress == "in progress":
                    row_color = table_colors["In Progress"]
                elif progress == "not started":
                    row_color = table_colors["Not Started"]
                elif progress == "completed":
                    row_color = table_colors["Completed"]
            html += "<tr>"
            for cell in row:
                html += f"<td style='border:1px solid gray; padding:4px; background-color:{row_color}; color:{text_color}; word-wrap:break-word;'>{cell}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    st.markdown(df_to_html(df_main), unsafe_allow_html=True)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        timeline = df_main.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0, 60)
            progress_color_map = {
                "Not Started": "#66b3ff",
                "In Progress": "#3399ff",
                "Completed": "#33cc33",
            }
            timeline["Progress"] = timeline["Progress"].fillna("Not Specified")
            timeline["color_label"] = timeline["Progress"].map(lambda x: x if x in progress_color_map else "Other")
            fig_tl = px.timeline(
                timeline,
                x_start="Start date",
                x_end="Due date",
                y="task_short",
                color="color_label",
                title="Task Timeline",
                color_discrete_map=progress_color_map,
            )
            fig_tl.update_yaxes(autorange="reversed")
            fig_tl.update_xaxes(
                dtick="M1", tickformat="%b %Y", showgrid=True, gridcolor="lightgray", tickangle=-30
            )
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT REPORT TAB =====================
with tabs[3]:
    st.subheader("📄 Export Smart Meter Project Report")

    if not df_main.empty:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()

        # custom style for wrapping cells
        cell_style = ParagraphStyle(
            name="CellStyle",
            fontSize=8,
            leading=10,
            alignment=1,  # center
        )

        story.append(Paragraph("<b>Ethekwini Smart Meter Project Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        if os.path.exists(logo_path):
            story.append(Image(logo_path, width=120, height=70))
            story.append(Spacer(1, 12))

        # KPI summary
        kpi_data = [
            ["Metric", "Count"],
            ["Total Tasks", total],
            ["Completed", completed],
            ["In Progress", inprogress],
            ["Not Started", notstarted],
            ["Overdue", overdue],
        ]
        table = Table(kpi_data, colWidths=[200, 100])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(table)
        story.append(Spacer(1, 20))

        # Task Summary
        story.append(Paragraph("<b>Task Summary (Top 15)</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))
        limited = df_main.head(15).fillna("")
        data = [list(limited.columns)]

        # wrap every cell content in Paragraph for text wrapping
        for _, row in limited.iterrows():
            wrapped_row = [Paragraph(str(cell), cell_style) for cell in row]
            data.append(wrapped_row)

        col_count = len(limited.columns)
        task_table = Table(
            data,
            colWidths=[(A4[1] - 80) / col_count] * col_count,
            repeatRows=1,
        )
        task_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ]
            )
        )
        story.append(task_table)
        story.append(Spacer(1, 20))
        story.append(Paragraph("Ethekwini Municipality | Automated Project Report", styles["Normal"]))

        doc.build(story)

        st.download_button(
            "📥 Download PDF Report",
            data=buf.getvalue(),
            file_name="Ethekwini_SmartMeter_Report.pdf",
            mime="application/pdf",
        )
    else:
        st.warning("No data found to export.")
