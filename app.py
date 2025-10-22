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

# Ensure avg_duration exists for export even if KPI block doesn't set it
avg_duration = None

# ===================== ASSETS & PATHS =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"

# ===================== STYLES (LOOK ONLY) =====================
st.markdown(
    f"""
    <style>
    /* Page background color */
    .stApp {{
        background-color: #f7f9fb;
    }}

    /* Container & header */
    .top-header {{
        background: linear-gradient(90deg, rgba(222,236,255,1) 0%, rgba(235,225,255,1) 100%);
        border-radius: 12px;
        padding: 22px 26px;
        margin-bottom: 18px;
        box-shadow: 0 8px 24px rgba(32, 45, 75, 0.06);
    }}

    .top-title {{
        color: #0b4a78;
        font-size: 30px;
        font-weight:700;
        margin: 0;
    }}

    .top-sub {{
        color:#6b7a88;
        margin-top:6px;
        font-size:13px;
    }}

    /* Filter bar */
    .filter-bar {{
        background: transparent;
        padding: 10px 0 24px 0;
        margin-bottom: 6px;
    }}

    /* KPI cards */
    .kpi-card {{
        background: #ffffff;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 6px 18px rgba(20,20,50,0.05);
        min-height: 120px;
    }}
    .kpi-title {{ color:#7a8a98; font-size:13px; margin-bottom:6px; }}
    .kpi-value {{ font-weight:700; font-size:26px; color:#052e56; }}
    .kpi-sub {{ color:#9eaec0; font-size:12px; margin-top:6px; }}

    /* Card containers */
    .card {{
        background: #fff;
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 6px 18px rgba(20,20,50,0.04);
    }}

    /* Small muted text */
    .muted {{ color:#9aa6b3; font-size:13px; }}

    /* Table styling */
    .styled-table {{
        border-collapse: collapse;
        font-size:13px;
        width: 100%;
    }}
    .styled-table thead tr {{
        background: #fbfdff;
        color: #495057;
        text-align: left;
    }}
    .styled-table tbody tr {{
        border-bottom: 1px solid #f1f3f5;
    }}
    .styled-table tbody tr:nth-child(even) {{
        background: #ffffff;
    }}
    .styled-table tbody tr:nth-child(odd) {{
        background: #fcfeff;
    }}
    .badge {{
        display:inline-block;
        padding:4px 8px;
        border-radius:999px;
        background:#eef6ff;
        color:#05507a;
        font-size:12px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER WITH LOGO (LOOK ONLY) =====================
col1, col2, col3 = st.columns([2, 7, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")

with col2:
    st.markdown("<div class='top-header'>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; align-items:center; gap:18px;'>", unsafe_allow_html=True)
    # Title and subtitle centered-left
    st.markdown(
        f"<div><div class='top-title'>Water Management Dashboard</div><div class='top-sub'>Operational view of meter health, consumption, and revenue.</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with col3:
    # small data date on the right
    st.markdown(f"<div style='text-align:right;'><span class='muted'>Data as of</span><br><strong>{file_date}</strong></div>", unsafe_allow_html=True)

st.markdown("")  # spacing

# ===================== THEME SETTINGS (no logic change) =====================
bg_color = "white"
text_color = "black"
table_colors = {
    "Not Started": "#e8f7e9",  # soft green
    "In Progress": "#eef6ff",  # soft blue
    "Completed": "#f2fbf7",    # soft teal
    "Overdue": "#fff2f2",      # soft red
}

# ===================== LOAD DATA =====================
@st.cache_data
def load_data(path=data_path):
    # preserve original behavior - attempt to read Excel with multiple sheets
    if not os.path.exists(path):
        # If file not present, return empty dict to preserve logic
        return {}
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            sheets[s] = pd.read_excel(xls, sheet_name=s)
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame()).copy() if sheets else pd.DataFrame().copy()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    df_main = df_main.fillna("Null")
    df_main = df_main.replace("NaT", "Null")

    # Remove "Is Recurring" and "Late" columns if present
    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

# ===================== MAIN TABS =====================
tabs = st.tabs(["KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== KPI TAB (layout/look only) =====================
with tabs[0]:
    if not df_main.empty:
        # keep original computations
        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        # compute avg_duration used by export (preserve behavior)
        df_duration = df_main.copy().replace("Null", None)
        df_duration["Start date"] = pd.to_datetime(df_duration.get("Start date", pd.NaT), errors="coerce")
        df_duration["Due date"] = pd.to_datetime(df_duration.get("Due date", pd.NaT), errors="coerce")
        df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
        try:
            avg_duration = df_duration["Duration"].mean()
        except Exception:
            avg_duration = None

        # KPI cards displayed like the screenshot (rounded cards)
        st.markdown("<div style='display:flex; gap:18px; margin-bottom:12px;'>", unsafe_allow_html=True)
        # Card 1 - Tamper Alerts (static value preserved from previous design)
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-title'>Tamper Alerts</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-value'>65</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-sub'>out of 1,200 meters</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 2 - Leak Alerts
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-title'>Leak Alerts</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-value'>48</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-sub'>out of 1,200 meters</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 3 - Avg Consumption L/day
        avg_cons_text = f"{int(df_main['Consumption'].mean()):,}" if ("Consumption" in df_main.columns and pd.to_numeric(df_main['Consumption'], errors='coerce').notna().any()) else "N/A"
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-title'>Avg Consumption (L/day)</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-value'>{avg_cons_text}</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-sub'>per meter</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # Card 4 - Avg Consumption R/day
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-title'>Avg Consumption (R/day)</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-value'>R 23.16</div>", unsafe_allow_html=True)
        st.markdown("<div class='kpi-sub'>per meter</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Keep the original gauge creation function and dials (no logic change)
        def create_colored_gauge(value, total, title, dial_color):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={"suffix": "%", "font": {"size": 36, "color": dial_color}},
                    title={"text": title, "font": {"size": 18, "color": dial_color}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                        "bar": {"color": dial_color, "thickness": 0.3},
                        "bgcolor": "#f9f9f9",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=260, margin=dict(l=10, r=10, t=20, b=20), paper_bgcolor="white")
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]

        # Place dials in a row with card look
        dcol1, dcol2, dcol3, dcol4 = st.columns(4)
        with dcol1:
            st.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", dial_colors[0]), use_container_width=True)
        with dcol2:
            st.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", dial_colors[1]), use_container_width=True)
        with dcol3:
            st.plotly_chart(create_colored_gauge(completed, total, "Completed", dial_colors[2]), use_container_width=True)
        with dcol4:
            st.plotly_chart(create_colored_gauge(overdue, total, "Overdue", dial_colors[3]), use_container_width=True)

        # Preserve Additional Insights section unchanged
        with st.expander("📈 Additional Insights", expanded=True):
            st.markdown("### Expanded Project Insights")
            st.markdown(f"**⏱️ Average Task Duration:** {avg_duration:.1f} days" if (avg_duration is not None and not pd.isna(avg_duration)) else "**⏱️ Average Task Duration:** N/A")

            priority_counts = df_main["Priority"].value_counts(normalize=True) * 100 if "Priority" in df_main.columns else pd.Series()
            st.markdown("#### 🔰 Priority Distribution")
            cols = st.columns(2)
            priority_colors = ["#ff6600", "#0099cc", "#00cc66", "#cc3366"]
            for i, (priority, pct) in enumerate(priority_counts.items()):
                with cols[i % 2]:
                    st.plotly_chart(
                        create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]),
                        use_container_width=True,
                    )

            if "Bucket Name" in df_main.columns:
                completion_by_bucket = (
                    df_main.groupby("Bucket Name")["Progress"]
                    .apply(lambda x: (x.str.lower() == "completed").mean() * 100)
                    .reset_index()
                    .rename(columns={"Progress": "Completion %"})
                )

                st.markdown("#### 🧭 Phase Completion Dials")
                bucket_cols = st.columns(2)
                for i, row in enumerate(completion_by_bucket.itertuples()):
                    with bucket_cols[i % 2]:
                        st.plotly_chart(
                            create_colored_gauge(row._2, 100, row._1, "#006666"),
                            use_container_width=True,
                        )
    else:
        st.info("No data available to display KPIs.")

# ===================== TASK BREAKDOWN TAB (same data, restyled table look only) =====================
with tabs[1]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")

    def df_to_html(df):
        html = "<table class='styled-table' style='border-collapse: collapse; width: 100%;'>"
        html += "<thead><tr>"
        for col in df.columns:
            # wrap long headers like original
            header = col
            if col in ["Completed Date", "Completed Checklist Items"]:
                header = "<br>".join(col.split())
            html += f"<th style='padding:10px; text-align:left'>{header}</th>"
        html += "</tr></thead><tbody>"
        for _, row in df.iterrows():
            # determine row color based on Progress and Due date (keep original logic but only change appearance)
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

            html += f"<tr style='background:{row_color}'>"
            for cell in row:
                cell_display = f"<i style='color:gray;'>Null</i>" if str(cell).strip() == "Null" else str(cell)
                html += f"<td style='padding:10px; border-bottom:1px solid #f1f3f5; vertical-align:top'>{cell_display}</td>"
            html += "</tr>"
        html += "</tbody></table>"
        return html

    # Render the styled html table (same data as before)
    if not df_main.empty:
        st.markdown(df_to_html(df_main), unsafe_allow_html=True)
    else:
        st.info("No task data to show.")

# ===================== TIMELINE TAB (no logic change, restyled container) =====================
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
            fig_tl.update_layout(height=520, margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="white")
            st.plotly_chart(fig_tl, use_container_width=True)
        else:
            st.info("Timeline data not available.")
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT REPORT TAB (same logic, look only) =====================
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
        story.append(Image(logo_url, width=120, height=70))
        story.append(Spacer(1, 12))

        # Preserve original KPI table content & style
        total = len(df_main)
        completed = df_main["Progress"].str.lower().eq("completed").sum()
        inprogress = df_main["Progress"].str.lower().eq("in progress").sum()
        notstarted = df_main["Progress"].str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
            & (~df_main["Progress"].str.lower().eq("completed"))
        ).sum()

        kpi_data = [
            ["Metric", "Count"],
            ["Total Tasks", total],
            ["Completed", completed],
            ["In Progress", inprogress],
            ["Not Started", notstarted],
            ["Overdue", overdue],
            ["Average Duration (days)", f"{avg_duration:.1f}" if (avg_duration is not None and not pd.isna(avg_duration)) else "N/A"],
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

# ===================== Footer (visual only) =====================
st.markdown("<div style='margin-top:18px; color:#98a2b3; font-size:12px'>Ethekwini Municipality | Automated Project Dashboard</div>", unsafe_allow_html=True)
