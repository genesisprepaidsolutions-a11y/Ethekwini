import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import os

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
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export"])

# ===================== KPI TAB =====================
with tabs[0]:
    if "Tasks" in sheets:
        st.subheader("Key Performance Indicators")
        tasks = sheets["Tasks"].copy()
        for col in ["Start date", "Due date", "Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors="coerce")

        total = len(tasks)
        completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
        inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
        notstarted = tasks["Progress"].str.lower().eq("not started").sum() if "Progress" in tasks.columns else 0
        overdue = ((tasks["Due date"] < pd.Timestamp.today()) &
                   (~tasks["Progress"].str.lower().eq("completed"))).sum() if "Due date" in tasks.columns else 0

        def create_gauge(value, total, title, color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={'suffix': '%', 'font': {'size': 36, 'color': text_color}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 2, 'tickcolor': text_color},
                    'bar': {'color': color, 'thickness': 0.3},
                    'bgcolor': "#e6e6e6",
                    'steps': [{'range': [0, 100], 'color': '#f0f0f0'}]
                },
                title={'text': title, 'font': {'size': 18, 'color': text_color}}
            ))
            fig.update_layout(height=280, margin=dict(l=20, r=20, t=50, b=50), paper_bgcolor=bg_color)
            return fig

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.plotly_chart(create_gauge(notstarted, total, "Not Started", table_colors["Not Started"]), use_container_width=True)
        with c2: st.plotly_chart(create_gauge(inprogress, total, "In Progress", table_colors["In Progress"]), use_container_width=True)
        with c3: st.plotly_chart(create_gauge(completed, total, "Completed", table_colors["Completed"]), use_container_width=True)
        with c4: st.plotly_chart(create_gauge(overdue, total, "Overdue", table_colors["Overdue"]), use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")

    st.dataframe(df_main)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        timeline = df_main.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["Task"] = timeline[df_main.columns[0]].astype(str)
            fig_tl = px.timeline(
                timeline,
                x_start="Start date",
                x_end="Due date",
                y="Task",
                color="Progress",
                title="Task Timeline"
            )
            fig_tl.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT TAB =====================
with tabs[3]:
    st.subheader("📄 Export Dashboard to PDF")

    def generate_pdf(dataframe, filename="Project_Report.pdf"):
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4

        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, 800, "Ethekwini Smart Meter Project Report")

        if os.path.exists(logo_path):
            c.drawImage(logo_path, 40, 760, width=60, preserveAspectRatio=True)

        c.setFont("Helvetica", 10)
        c.drawString(40, 740, f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}")

        # KPIs summary
        c.drawString(40, 710, f"Total Tasks: {len(dataframe)}")
        c.drawString(200, 710, f"Completed: {completed}")
        c.drawString(350, 710, f"In Progress: {inprogress}")
        c.drawString(480, 710, f"Overdue: {overdue}")

        # Create table preview
        preview_df = dataframe.head(15)
        data = [preview_df.columns.tolist()] + preview_df.values.tolist()
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 8),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT')
        ]))
        table.wrapOn(c, width, height)
        table.drawOn(c, 40, 500)

        c.showPage()
        c.save()
        return filename

    if st.button("Generate PDF Report"):
        pdf_file = generate_pdf(df_main)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="⬇️ Download PDF",
                data=f,
                file_name="Ethekwini_SmartMeter_Report.pdf",
                mime="application/pdf"
            )
