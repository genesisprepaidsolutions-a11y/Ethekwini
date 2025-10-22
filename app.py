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

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="Ethekwini WS-7761 Smart Meter Project", layout="wide")

# ===================== CONSTANTS / BRANDING =====================
LOGO_URL = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"
logo_path_local = "ethekwini_logo.png"  # preserved for PDF export if you have local copy

# Theme / colors
bg_color = "white"
text_color = "black"
table_colors = {
    "Not Started": "#80ff80",
    "In Progress": "#ffff80",
    "Completed": "#80ccff",
    "Overdue": "#ff8080",
}
# Gradient mapping for visual dials:
GRADIENT_RANGES = [
    {"range": [0, 50], "color": "#ff4d4d"},     # red
    {"range": [50, 80], "color": "#ffd24d"},    # yellow
    {"range": [80, 100], "color": "#b3ff66"},   # light green
]
# For final top range use strong green color visually
FINAL_GREEN = "#33cc33"

# ===================== STYLES (sticky header + theme) =====================
st.markdown(
    f"""
    <style>
    /* Make header area sticky and style it */
    .stApp > div:first-child {{
        background-color: {bg_color};
    }}
    .header-row {{
        position: sticky;
        top: 0;
        z-index: 999;
        padding: 8px 4px;
        background-color: {bg_color};
        border-bottom: 1px solid #e6e6e6;
    }}
    .main-title {{
        margin: 0;
        font-size: 28px;
        font-weight: 700;
        color: {text_color};
        text-align: center;
    }}
    .data-as-of {{
        font-size: 14px;
        color: {text_color};
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER WITH LOGO (date left, title centered, logo right) =====================
file_date = (
    datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    if os.path.exists(data_path)
    else datetime.now().strftime("%d %B %Y")
)

st.markdown("<div class='header-row'>", unsafe_allow_html=True)
left_col, center_col, right_col = st.columns([1, 6, 1])
with left_col:
    st.markdown(f"<div class='data-as-of'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)
with center_col:
    st.markdown(f"<h1 class='main-title'>Ethekwini WS-7761 Smart Meter Project Status</h1>", unsafe_allow_html=True)
with right_col:
    # Display the logo from the provided GitHub raw URL (Streamlit accepts remote images)
    st.image(LOGO_URL, width=120)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path=data_path):
    if os.path.exists(path):
        xls = pd.ExcelFile(path)
        sheets = {}
        for s in xls.sheet_names:
            try:
                sheets[s] = pd.read_excel(xls, sheet_name=s)
            except Exception:
                sheets[s] = pd.DataFrame()
        return sheets
    else:
        # if file doesn't exist return empty dict
        return {}

sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame()).copy()

# ===================== CLEAN DATA (unchanged behavior) =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    df_main = df_main.fillna("Null")
    df_main = df_main.replace("NaT", "Null")

# ===================== TABS (unchanged) =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== HELPER: choose color by percent (for indicator bar color) =====================
def color_for_percent(pct: float) -> str:
    try:
        pct = float(pct)
    except Exception:
        return GRADIENT_RANGES[0]["color"]
    if pct <= 50:
        return GRADIENT_RANGES[0]["color"]
    elif pct <= 80:
        return GRADIENT_RANGES[1]["color"]
    elif pct <= 100:
        return GRADIENT_RANGES[2]["color"]
    else:
        return FINAL_GREEN

# ===================== HELPER: create gauge with gradient background steps =====================
def create_gradient_gauge(value, title, suffix="%", max_range=100, height=280, show_number=True):
    # steps for visuals (show the ranges)
    steps = []
    # ensure steps cover 0..max_range
    for r in GRADIENT_RANGES:
        start = max(0, r["range"][0])
        end = min(max_range, r["range"][1])
        steps.append({"range": [start, end], "color": r["color"]})
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number" if show_number else "gauge",
            value=value if value is not None else 0,
            number={"suffix": suffix, "font": {"size": 30, "color": text_color}},
            gauge={
                "axis": {"range": [0, max_range]},
                "bar": {"color": color_for_percent(value), "thickness": 0.35},
                "bgcolor": "#f6f6f6",
                "steps": steps,
            },
            title={"text": title, "font": {"size": 14, "color": text_color}},
        )
    )
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=45, b=20), paper_bgcolor=bg_color)
    return fig

# ===================== KPI TAB =====================
with tabs[0]:
    if not df_main.empty:
        st.subheader("Key Performance Indicators")

        # Basic counts (preserve original logic)
        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        # Simple existing gauges (unchanged look but reuse helper for consistent style)
        def create_simple_gauge(value, total, title):
            pct = (value / total * 100) if total > 0 else 0
            return create_gradient_gauge(pct, title, suffix="%", max_range=100, height=260)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(create_simple_gauge(notstarted, total, "Not Started"), use_container_width=True)
        with c2:
            st.plotly_chart(create_simple_gauge(inprogress, total, "In Progress"), use_container_width=True)
        with c3:
            st.plotly_chart(create_simple_gauge(completed, total, "Completed"), use_container_width=True)
        with c4:
            st.plotly_chart(create_simple_gauge(overdue, total, "Overdue"), use_container_width=True)

        # ===================== ADDITIONAL INSIGHTS (expanded by default) =====================
        with st.expander("📈 Additional Insights", expanded=True):
            # Average Task Duration
            df_duration = df_main.copy()
            df_duration = df_duration.replace("Null", pd.NA)
            df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
            df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
            df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
            avg_duration = df_duration["Duration"].mean()

            # Tasks by Priority
            # We'll show KPI dials for Important and Medium as requested.
            priorities_of_interest = ["Important", "Medium"]
            priority_counts = df_main["Priority"].replace("Null", pd.NA).value_counts(dropna=True)
            # compute percent of tasks that are each priority
            def pct_of_total_for_priority(p):
                if total <= 0:
                    return 0
                return (priority_counts.get(p, 0) / total) * 100

            # Completion by Bucket Name (as percentage)
            completion_by_bucket = (
                df_main.groupby("Bucket Name")["Progress"]
                .apply(lambda x: (x.str.lower() == "completed").mean() * 100)
                .reset_index()
                .rename(columns={"Progress": "Completion %"})
            )
            # Ensure NaNs handled
            completion_by_bucket["Completion %"] = completion_by_bucket["Completion %"].fillna(0)

            # Layout: 2 dials per row (responsive)
            # Row 1: Average Task Duration (numeric KPI dial) + Priority Distribution (Important, Medium) preview
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                # Numeric KPI dial for Average Duration (days)
                # We'll set a max_range for the gauge as either 30 or double the average (rounded), so the dial is sensible.
                if pd.isna(avg_duration):
                    avg_val = 0
                else:
                    avg_val = float(avg_duration)
                max_for_duration = max(30, int((avg_val or 0) * 2) + 5)
                fig_avg_duration = create_gradient_gauge(avg_val, "Average Task Duration (days)", suffix=" days", max_range=max_for_duration, height=300)
                st.plotly_chart(fig_avg_duration, use_container_width=True)

            with row1_col2:
                # Priority Distribution: show KPI dials for 'Important' and 'Medium'
                st.markdown("#### Priority Distribution")
                # Collect priorities to show: ensure Important and Medium present even if zero
                pri_to_show = priorities_of_interest.copy()
                # if dataset contains other priorities but user asked Important & Medium specifically we limit to those two.
                # Create two dials, stacked 2 per row logic below will handle layout
                for p in pri_to_show:
                    pct = pct_of_total_for_priority(p)
                    fig_pri = create_gradient_gauge(pct, f"{p} ({int(priority_counts.get(p,0))} tasks)", suffix="%", max_range=100, height=220)
                    st.plotly_chart(fig_pri, use_container_width=True)

            st.markdown("---")
            # Row: Phase Completion Dials (replace previous bar chart)
            st.markdown("#### Phase Completion Dials (by Bucket Name)")

            # Create a list of (bucket, completion%) and render two per row
            buckets = completion_by_bucket.sort_values("Completion %", ascending=False).to_dict(orient="records")
            # If no buckets, show message
            if len(buckets) == 0:
                st.info("No Bucket Name / Phase data available.")
            else:
                # Render 2 per row
                for i in range(0, len(buckets), 2):
                    cols = st.columns(2)
                    for j in range(2):
                        idx = i + j
                        if idx < len(buckets):
                            b = buckets[idx]
                            bucket_name = str(b.get("Bucket Name", "Unnamed Phase"))
                            completion_pct = float(b.get("Completion %", 0) or 0)
                            fig_bucket_gauge = create_gradient_gauge(completion_pct, f"{bucket_name}", suffix="%", max_range=100, height=260)
                            cols[j].plotly_chart(fig_bucket_gauge, use_container_width=True)

            # Keep older priority chart removed (we replaced with KPI dials above)
            st.markdown("---")
            st.caption("Phase completion dials replace the previous bar chart. Gradient ranges: 0–50% Red→Yellow, 51–80% Yellow→Light Green, 81–100% Green.")

    else:
        st.warning("No data found in the 'Tasks' sheet. Please provide the Excel file with a 'Tasks' sheet containing the expected columns.")

# ===================== TASK BREAKDOWN TAB (unchanged) =====================
with tabs[1]:
    # Preserve original HTML table rendering
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)" if not df_main.empty else "Task Overview")

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
                try:
                    due_date = pd.to_datetime(row["Due date"], errors="coerce")
                except Exception:
                    due_date = None
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
                cell_display = (
                    f"<i style='color:gray;'>Null</i>" if str(cell).strip() == "Null" else str(cell)
                )
                html += f"<td style='border:1px solid gray; padding:4px; background-color:{row_color}; color:{text_color}; word-wrap:break-word;'>{cell_display}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    if not df_main.empty:
        st.markdown(df_to_html(df_main), unsafe_allow_html=True)
    else:
        st.info("No task data to display.")

# ===================== TIMELINE TAB (unchanged) =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None)
        timeline = df_copy.dropna(subset=["Start date", "Due date"]).copy()
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
            fig_tl.update_xaxes(dtick="M1", tickformat="%b %Y", showgrid=True, gridcolor="lightgray", tickangle=-30)
            st.plotly_chart(fig_tl, use_container_width=True)
        else:
            st.info("Timeline data not available.")
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT REPORT TAB (unchanged behavior, uses local logo if available) =====================
with tabs[3]:
    st.subheader("📄 Export Smart Meter Project Report")

    if not df_main.empty:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()

        cell_style = ParagraphStyle(name="CellStyle", fontSize=8, leading=10, alignment=1)
        null_style = ParagraphStyle(name="NullStyle", fontSize=8, textColor=colors.grey,
                                    leading=10, alignment=1, fontName="Helvetica-Oblique")

        story.append(Paragraph("<b>Ethekwini WS-7761 Smart Meter Project Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Attach logo if a local copy exists (preserve original behavior)
        if os.path.exists(logo_path_local):
            try:
                story.append(Image(logo_path_local, width=120, height=70))
                story.append(Spacer(1, 12))
            except Exception:
                pass

        kpi_data = [
            ["Metric", "Count"],
            ["Total Tasks", total],
            ["Completed", completed],
            ["In Progress", inprogress],
            ["Not Started", notstarted],
            ["Overdue", overdue],
            ["Average Duration (days)", f"{avg_duration:.1f}" if pd.notna(avg_duration) else "N/A"],
        ]
        table = Table(kpi_data, colWidths=[200, 100])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 1, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        story.append(Spacer(1, 20))

        limited = df_main.head(15).copy()
        limited = limited.fillna("Null").replace("NaT", "Null")

        data = [list(limited.columns)]
        for _, row in limited.iterrows():
            wrapped_row = []
            for cell in row:
                if str(cell).strip() == "Null":
                    wrapped_row.append(Paragraph("<i>Null</i>", null_style))
                else:
                    wrapped_row.append(Paragraph(str(cell), cell_style))
            data.append(wrapped_row)

        col_count = len(limited.columns)
        task_table = Table(data, colWidths=[(A4[1] - 80) / col_count] * col_count, repeatRows=1)
        task_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        story.append(task_table)
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
