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

# ===================== HEADER WITH LOGO =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"

col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"**📅 Data as of:** {file_date}")

with col2:
    st.markdown(
        "<h1 style='text-align:center; color:#003366;'>Ethekwini WS-7761 Smart Meter Project Status</h1>",
        unsafe_allow_html=True,
    )

with col3:
    st.image(logo_url, width=110)

st.markdown("---")

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

    # Remove "Is Recurring" and "Late" columns
    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

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
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                        "bar": {"color": dial_color, "thickness": 0.3},
                        "bgcolor": "#f9f9f9",
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

        with st.expander("📈 Additional Insights", expanded=True):
            st.markdown("### Expanded Project Insights")
            df_duration = df_main.copy().replace("Null", None)
            df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
            df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
            df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
            avg_duration = df_duration["Duration"].mean()

            st.markdown(f"**⏱️ Average Task Duration:** {avg_duration:.1f} days" if pd.notna(avg_duration) else "**⏱️ Average Task Duration:** N/A")

            priority_counts = df_main["Priority"].value_counts(normalize=True) * 100
            st.markdown("#### 🔰 Priority Distribution")
            cols = st.columns(2)
            priority_colors = ["#ff6600", "#0099cc", "#00cc66", "#cc3366"]
            for i, (priority, pct) in enumerate(priority_counts.items()):
                with cols[i % 2]:
                    st.plotly_chart(
                        create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]),
                        use_container_width=True,
                    )

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

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")

    def df_to_html(df):
        html = "<table style='border-collapse: collapse; width: 100%;'>"
        html += "<tr>"
        for col in df.columns:
            if col in ["Completed Date", "Completed Checklist Items"]:
                col_wrapped = "<br>".join(col.split())
                html += f"<th style='border:1px solid gray; padding:4px; background-color:{bg_color}; color:{text_color}'>{col_wrapped}</th>"
            else:
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
                cell_display = f"<i style='color:gray;'>Null</i>" if str(cell).strip() == "Null" else str(cell)
                html += f"<td style='border:1px solid gray; padding:4px; background-color:{row_color}; color:{text_color}; word-wrap:break-word;'>{cell_display}</td>"
            html += "</tr>"
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

# ===================== EXPORT REPORT TAB =====================
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
