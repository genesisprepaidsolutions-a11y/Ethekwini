# ======================================================
#   WS7761 - Smart Meter Project Status Dashboard
# ======================================================

import os
from datetime import datetime
from io import BytesIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import streamlit as st

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="WS7761-Smart Meter Project Status",
    page_icon="⚡",
    layout="wide",
)

# ======================================================
#   LOAD DATA
# ======================================================
@st.cache_data
def load_data():
    excel_file = "Ethekwini WS-7761 07 Oct 2025.xlsx"
    df = pd.read_excel(excel_file, sheet_name="Sheet1")
    df["Due Date"] = pd.to_datetime(df["Due Date"], errors="coerce")
    df["Start Date"] = pd.to_datetime(df["Start Date"], errors="coerce")
    return df

df = load_data()

# ======================================================
#   STYLING
# ======================================================
PRIMARY_COLOR = "#004b8d"
SECONDARY_COLOR = "#007acc"
ACCENT_COLOR = "#66b2ff"
LIGHT_COLOR = "#d9e6f2"

st.markdown(
    f"""
    <style>
        .block-container {{
            padding-top: 1rem;
            padding-bottom: 1rem;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: {PRIMARY_COLOR};
        }}
        .stApp {{
            background-color: #f7f9fb;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================
#   SAFE PLOT EXPORT FUNCTION (No Kaleido Crash)
# ======================================================
def save_plot_as_image(fig):
    """Safely convert Plotly figure to image or fallback placeholder."""
    try:
        import plotly.io as pio
        # Try exporting with kaleido
        img_bytes = fig.to_image(format="png", width=800, height=500, scale=2)
        return ImageReader(BytesIO(img_bytes))
    except Exception as e:
        # Fallback placeholder if Kaleido or Chrome is missing
        print("⚠️ Kaleido export failed:", e)
        fallback = BytesIO()
        c = canvas.Canvas(fallback, pagesize=(800, 500))
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(400, 250, "Chart preview unavailable")
        c.setFont("Helvetica", 12)
        c.drawCentredString(400, 230, "(Kaleido/Chrome missing in environment)")
        c.save()
        fallback.seek(0)
        return ImageReader(fallback)

# ======================================================
#   DASHBOARD HEADER
# ======================================================
st.title("⚡ WS7761 – Smart Meter Project Status")

# ======================================================
#   SUMMARY METRICS
# ======================================================
total_tasks = len(df)
completed = len(df[df["Status"].str.lower() == "completed"])
in_progress = len(df[df["Status"].str.lower() == "in progress"])
not_started = len(df[df["Status"].str.lower() == "not started"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tasks", total_tasks)
col2.metric("Completed", completed)
col3.metric("In Progress", in_progress)
col4.metric("Not Started", not_started)

# ======================================================
#   STATUS DISTRIBUTION (BAR CHART)
# ======================================================
status_counts = df["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]

fig_status = px.bar(
    status_counts,
    x="Status",
    y="Count",
    color="Status",
    title="Task Distribution by Status",
    color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR],
)
st.plotly_chart(fig_status, use_container_width=True)

# ======================================================
#   GANTT CHART
# ======================================================
if "Task" in df.columns and "Start Date" in df.columns and "Due Date" in df.columns:
    gantt_df = df.copy()
    gantt_df = gantt_df.dropna(subset=["Start Date", "Due Date"])
    fig_gantt = px.timeline(
        gantt_df,
        x_start="Start Date",
        x_end="Due Date",
        y="Task",
        color="Status",
        title="Project Timeline (Gantt Chart)",
        color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR],
    )
    fig_gantt.update_yaxes(autorange="reversed")
    st.plotly_chart(fig_gantt, use_container_width=True)
else:
    st.warning("Task, Start Date, and Due Date columns are required for the Gantt chart.")

# ======================================================
#   PROGRESS PIE
# ======================================================
fig_pie = px.pie(
    status_counts,
    names="Status",
    values="Count",
    title="Overall Task Progress",
    color="Status",
    color_discrete_sequence=[PRIMARY_COLOR, SECONDARY_COLOR, ACCENT_COLOR],
)
st.plotly_chart(fig_pie, use_container_width=True)

# ======================================================
#   EXPORT TO PDF SECTION
# ======================================================
st.subheader("📄 Export Dashboard as PDF")

if st.button("Generate PDF"):
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet

    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>WS7761 – Smart Meter Project Status Report</b>", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 24))

    # Insert summary charts
    for fig in [fig_status, fig_pie, fig_gantt]:
        img = save_plot_as_image(fig)
        pdf_canvas = canvas.Canvas(buffer, pagesize=A4)
        pdf_canvas.drawImage(img, 50, 200, width=500, height=300, preserveAspectRatio=True)
        pdf_canvas.showPage()

    pdf.build(elements)
    buffer.seek(0)
    st.download_button("Download PDF Report", data=buffer, file_name="WS7761_Project_Status.pdf", mime="application/pdf")

