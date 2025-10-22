import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="WS7761 - Smart Meter Project Status", layout="wide")

# ===================== HEADER WITH LOGO =====================
logo_path = "ethekwini_logo.png"
col1, col2 = st.columns([8, 1])
with col1:
    st.markdown("<h1 style='text-align:center'>WS7761 - Smart Meter Project Status</h1>", unsafe_allow_html=True)
with col2:
    if os.path.exists(logo_path):
        st.image(logo_path, width=90)

# ===================== THEME TOGGLE =====================
theme = st.sidebar.radio("Select Theme", ["Light", "Dark"])
if theme == "Dark":
    bg_color = "#0e1117"
    text_color = "white"
    table_colors = {"Not Started": "#006400", "In Progress": "#cccc00", "Completed": "#3399ff", "Overdue": "#ff3333"}
else:
    bg_color = "white"
    text_color = "black"
    table_colors = {"Not Started": "#80ff80", "In Progress": "#ffff80", "Completed": "#80ccff", "Overdue": "#ff8080"}

# ===================== DATA LOADING =====================
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

# ===================== SIDEBAR FILTERS =====================
st.sidebar.header("Data & Filters")
sheet_choice = st.sidebar.selectbox(
    "Main sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)
search_task = st.sidebar.text_input("Search Task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)
bucket_filter = st.sidebar.multiselect("Bucket Name", [])
priority_filter = st.sidebar.multiselect("Priority", [])
progress_filter = st.sidebar.multiselect("Progress", [])
show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

# ===================== MAIN DATAFRAME =====================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]
    if bucket_filter and "Bucket Name" in df_main.columns:
        df_main = df_main[df_main["Bucket Name"].isin(bucket_filter)]
    if priority_filter and "Priority" in df_main.columns:
        df_main = df_main[df_main["Priority"].isin(priority_filter)]
    if progress_filter and "Progress" in df_main.columns:
        df_main = df_main[df_main["Progress"].isin(progress_filter)]

# ===================== TABS =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== KPI TAB =====================
with tabs[0]:
    st.subheader("Key Performance Indicators")
    if "Tasks" in sheets:
        tasks = sheets["Tasks"].copy()
        for col in ["Start date", "Due date", "Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors="coerce")

        total = len(tasks)
        completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
        inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
        notstarted = tasks["Progress"].str.lower().eq("not started").sum() if "Progress" in tasks.columns else 0
        overdue = ((tasks["Due date"] < pd.Timestamp.today()) & (~tasks["Progress"].str.lower().eq("completed"))).sum() \
            if "Due date" in tasks.columns and "Progress" in tasks.columns else 0

        def create_simple_gauge(value, total, title, color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={'suffix':'%', 'font':{'size':36, 'color': text_color}},
                gauge={
                    'axis': {'range':[0,100], 'tickwidth':2, 'tickcolor': text_color},
                    'bar': {'color': color, 'thickness':0.3},
                    'bgcolor': "#e6e6e6",
                    'steps': [{'range':[0,100], 'color':'#f0f0f0'}]
                },
                title={'text': title, 'font':{'size':18, 'color': text_color}}
            ))
            fig.update_layout(
                height=280,
                margin=dict(l=20,r=20,t=50,b=50),
                paper_bgcolor=bg_color
            )
            return fig

        c1, c2, c3, c4 = st.columns(4)
        with c1: fig_ns = create_simple_gauge(notstarted, total, "Not Started", table_colors["Not Started"]); st.plotly_chart(fig_ns, use_container_width=True)
        with c2: fig_ip = create_simple_gauge(inprogress, total, "In Progress", table_colors["In Progress"]); st.plotly_chart(fig_ip, use_container_width=True)
        with c3: fig_c = create_simple_gauge(completed, total, "Completed", table_colors["Completed"]); st.plotly_chart(fig_c, use_container_width=True)
        with c4: fig_o = create_simple_gauge(overdue, total, "Overdue", table_colors["Overdue"]); st.plotly_chart(fig_o, use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")

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
                html += f"<td style='border:1px solid gray; padding:4px; background-color:{row_color}; color:{text_color}'>{cell}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    st.markdown(df_to_html(df_main), unsafe_allow_html=True)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        timeline = df_main.dropna(subset=["Start date","Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0,60)
            progress_color_map = {
                "Not Started": "#66b3ff",
                "In Progress": "#3399ff",
                "Completed": "#33cc33"
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
                color_discrete_map=progress_color_map
            )
            fig_tl.update_yaxes(autorange="reversed")
            fig_tl.update_xaxes(dtick="M1", tickformat="%b %Y", tickangle=-30, showgrid=True, gridcolor="lightgray")
            fig_tl.update_layout(
                legend_title_text="Progress Status",
                paper_bgcolor=bg_color,
                plot_bgcolor=bg_color,
                font_color=text_color
            )
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT REPORT TAB =====================
with tabs[3]:
    st.subheader("Export KPI Report to PDF")

    if "Tasks" in sheets:
        buf = BytesIO()

        def save_plot_as_image(fig):
            img_bytes = fig.to_image(format="png", width=600, height=400, scale=2)
            return ImageReader(BytesIO(img_bytes))

        # Create PDF
        doc = SimpleDocTemplate(buf, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        story.append(Paragraph("<b>WS7761 - Smart Meter Project Status Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        if os.path.exists(logo_path):
            story.append(Image(logo_path, width=100, height=60))
            story.append(Spacer(1, 12))

        # KPI table
        kpi_data = [
            ["KPI", "Count"],
            ["Not Started", notstarted],
            ["In Progress", inprogress],
            ["Completed", completed],
            ["Overdue", overdue]
        ]
        table = Table(kpi_data, colWidths=[150, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        # Add KPI charts
        story.append(Paragraph("<b>KPI Visuals</b>", styles["Heading2"]))
        for fig in [fig_ns, fig_ip, fig_c, fig_o]:
            story.append(Image(save_plot_as_image(fig), width=400, height=250))
            story.append(Spacer(1, 12))

        doc.build(story)

        st.download_button(
            label="📄 Download PDF Report",
            data=buf.getvalue(),
            file_name="WS7761_Project_Status_Report.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("No task data found to export.")
