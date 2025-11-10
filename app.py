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

# ===================== HEADER WITH LOGO =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"
installations_path = "Weekly update sheet.xlsx"  # file to be read automatically for installations

col1, col2, col3 = st.columns([2, 6, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)

with col2:
    st.markdown(
        "<h1 style='text-align:center; color:#003366;'>eThekwini WS-7761 Smart Meter Project </h1>",
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

# ===================== LOAD DATA (MAIN) =====================
@st.cache_data
def load_data(path=data_path):
    if not os.path.exists(path):
        return {}
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

sheets = load_data()
df_main = sheets.get("Tasks", pd.DataFrame()).copy()

# ===================== LOAD INSTALLATIONS DATA =====================
@st.cache_data
def load_installations(path=installations_path):
    """
    Attempt to read the Weekly update sheet.xlsx and extract installations information.
    The function will try to find columns matching 'contractor', 'installed', and 'sites'
    (case-insensitive). If not found, it will attempt to take the first sheet and look
    for plausible columns. Returns a cleaned DataFrame with columns:
    ['Contractor', 'total number of installed', 'total number of sites']
    """
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Contractor", "total number of installed", "total number of sites"])

    try:
        xls = pd.ExcelFile(path)
        # read first sheet by default (user provided file expected to have installations in first sheet)
        raw = pd.read_excel(xls, sheet_name=0)
    except Exception:
        try:
            raw = pd.read_excel(path)
        except Exception:
            return pd.DataFrame(columns=["Contractor", "total number of installed", "total number of sites"])

    if raw is None or raw.empty:
        return pd.DataFrame(columns=["Contractor", "total number of installed", "total number of sites"])

    # Normalize column names
    cols_lower = {c: c.lower().strip() for c in raw.columns}
    # Find contractor column
    contractor_col = None
    installed_col = None
    sites_col = None

    for orig, low in cols_lower.items():
        if "contractor" in low:
            contractor_col = orig
        if ("install" in low and "site" not in low) or "installed" in low or "total number of installed" in low:
            installed_col = orig
        if "site" in low and "installed" not in low:
            sites_col = orig
        # handle possible variations
        if low.replace(" ", "").startswith("contractor"):
            contractor_col = orig

    # fallback heuristics
    if contractor_col is None:
        # try first text column
        for c in raw.columns:
            if raw[c].dtype == object:
                contractor_col = c
                break

    if installed_col is None:
        # try numeric columns - pick the numeric column with name or first numeric col
        for c in raw.columns:
            if pd.api.types.is_numeric_dtype(raw[c]):
                installed_col = c
                break

    if sites_col is None:
        # pick next numeric column different from installed_col
        for c in raw.columns:
            if c != installed_col and pd.api.types.is_numeric_dtype(raw[c]):
                sites_col = c
                break

    # Build installations DataFrame robustly
    try:
        df_inst = pd.DataFrame()
        df_inst["Contractor"] = raw[contractor_col].astype(str).str.strip() if contractor_col in raw.columns else raw.iloc[:, 0].astype(str).str.strip()
        if installed_col in raw.columns:
            df_inst["total number of installed"] = pd.to_numeric(raw[installed_col], errors="coerce").fillna(0).astype(int)
        else:
            # if no installed column found, set zeros
            df_inst["total number of installed"] = 0
        if sites_col in raw.columns:
            df_inst["total number of sites"] = pd.to_numeric(raw[sites_col], errors="coerce").fillna(0).astype(int)
        else:
            df_inst["total number of sites"] = 0

        # Drop rows where contractor is blank or equals 'nan'
        df_inst = df_inst[df_inst["Contractor"].str.strip().replace("nan", "").replace("None", "") != ""]
        df_inst = df_inst.reset_index(drop=True)
        return df_inst
    except Exception:
        # On any failure, return an empty standardized DF
        return pd.DataFrame(columns=["Contractor", "total number of installed", "total number of sites"])

df_installations = load_installations()

# ===================== CLEAN DATA (MAIN) =====================
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
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                        "bar": {"color": dial_color, "thickness": 0.3},
                        "bgcolor": "#f7f9fb",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]

        with st.container():
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", dial_colors[0]), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", dial_colors[1]), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c3:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(create_colored_gauge(completed, total, "Completed", dial_colors[2]), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c4:
                st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                st.plotly_chart(create_colored_gauge(overdue, total, "Overdue", dial_colors[3]), use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

        # Additional Insights section (kept unchanged)
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
        html = "<table>"
        html += "<tr>"
        for col in df.columns:
            html += f"<th>{col}</th>"
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
            html += f"<tr style='background-color:{row_color};'>"
            for cell in row:
                cell_display = f"<i style='color:gray;'>Null</i>" if str(cell).strip() == "Null" else str(cell)
                html += f"<td>{cell_display}</td>"
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

# ===================== INSTALLATIONS TAB =====================
with tabs[3]:
    st.subheader("Installations Summary (from Weekly update sheet.xlsx)")
    if df_installations is not None and not df_installations.empty:
        # Display a neat styled table
        st.table(df_installations.rename(columns={
            "Contractor": "Contractor",
            "total number of installed": "Total Number Installed",
            "total number of sites": "Total Number of Sites"
        }))
    else:
        st.warning(f"No installations data found in '{installations_path}'.")

# ===================== EXPORT REPORT TAB =====================
with tabs[4]:
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

        # ===== Add Installations table (all contractors) to the PDF export =====
        if df_installations is not None and not df_installations.empty:
            story.append(Paragraph("<b>Installations Summary</b>", styles["Heading3"]))
            story.append(Spacer(1, 8))
            # Prepare data for PDF table
            inst_df = df_installations.fillna("Null").replace("NaT", "Null")
            inst_data = [list(inst_df.columns)]
            for _, row in inst_df.iterrows():
                wrapped_row = []
                for cell in row:
                    if str(cell).strip() == "Null":
                        wrapped_row.append(Paragraph("<i>Null</i>", null_style))
                    else:
                        wrapped_row.append(Paragraph(str(cell), cell_style))
                inst_data.append(wrapped_row)

            col_count_inst = len(inst_df.columns)
            inst_table = Table(inst_data, colWidths=[(A4[1] - 80) / col_count_inst] * col_count_inst, repeatRows=1)
            inst_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(inst_table)
            story.append(Spacer(1, 20))
        else:
            story.append(Paragraph("<b>Installations Summary</b>", styles["Heading3"]))
            story.append(Spacer(1, 8))
            story.append(Paragraph("No installations data available from the Weekly update sheet.", styles["Normal"]))
            story.append(Spacer(1, 12))

        # ===== Add limited tasks table (existing behavior) =====
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
