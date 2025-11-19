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

# Small mobile viewport hint
st.markdown('<meta name="viewport" content="width=device-width, initial-scale=1.0">', unsafe_allow_html=True)

# ===================== CUSTOM STYLE (RESPONSIVE UPDATES) =====================
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
        padding: 1rem 1rem; /* slightly smaller side padding for small screens */
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
    /* allow tabs to wrap on narrow screens */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        flex-wrap: wrap !important;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #eaf4ff;
        border-radius: 10px;
        padding: 8px 12px;
        color: #003366;
        font-weight: 500;
        margin-bottom:6px;
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
        border-radius: 12px;
        padding: 0.75rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 0.75rem;
        width: 100% !important; /* ensure full width inside columns */
        box-sizing: border-box;
    }
    .dial-label {
        text-align: center;
        font-weight: 500;
        color: #003366;
        margin-top: 6px;
        margin-bottom: 12px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
        table-layout: auto;
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

    /* prevent overflow on very narrow screens */
    * { max-width: 100% !important; }
    /* small tweaks for very small viewports */
    @media (max-width: 600px) {
        .stApp .block-container { padding-left: 8px; padding-right: 8px; }
        .metric-card { padding: 0.5rem; }
        .stTabs [data-baseweb="tab"] { padding: 6px 8px; font-size: 14px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== FILE PATHS =====================
data_path = "Ethekwini WS-7761.xlsx"
install_path = "Weekly update sheet.xlsx"
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"

# ===================== HEADER WITH LOGO (RESPONSIVE) =====================
# Use balanced column ratios that behave better on small screens
col1, col2, col3 = st.columns([1, 3, 1])
with col1:
    if os.path.exists(data_path):
        file_date = datetime.fromtimestamp(os.path.getmtime(data_path)).strftime("%d %B %Y")
    else:
        file_date = datetime.now().strftime("%d %B %Y")
    st.markdown(f"<div class='metric-card'><b>📅 Data as of:</b> {file_date}</div>", unsafe_allow_html=True)

with col2:
    st.markdown(
        "<h1 style='text-align:center; color:#003366; margin:6px 0;'>eThekwini WS-7761 Smart Meter Project </h1>",
        unsafe_allow_html=True,
    )

with col3:
    # use responsive image sizing
    try:
        st.image(logo_url, use_column_width=True)
    except Exception:
        # fallback to a small placeholder text
        st.markdown("<div style='text-align:center;'><b>eThekwini</b></div>", unsafe_allow_html=True)

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

# ===================== LOAD DATA (AUTO-REFRESH ENABLED) =====================

def file_last_modified(path):
    """Return last modified timestamp of a file (used to detect changes)."""
    return os.path.getmtime(path) if os.path.exists(path) else 0


@st.cache_data
def load_data(path, last_modified):
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


@st.cache_data
def load_install_data(path, last_modified, target_sheet_names=None):
    if not os.path.exists(path):
        return pd.DataFrame()

    xls = pd.ExcelFile(path)
    sheet_names = xls.sheet_names
    chosen = None
    if target_sheet_names is None:
        for s in sheet_names:
            if str(s).strip().lower() == "installations":
                chosen = s
                break
        if not chosen:
            for s in sheet_names:
                if "install" in str(s).lower():
                    chosen = s
                    break
    else:
        for s in sheet_names:
            if s in target_sheet_names:
                chosen = s
                break

    if not chosen:
        chosen = sheet_names[0] if len(sheet_names) > 0 else None
    if not chosen:
        return pd.DataFrame()

    raw = pd.read_excel(xls, sheet_name=chosen, header=None, dtype=object)
    header_row_idx = None
    for idx, row in raw.iterrows():
        first_cell = str(row.iloc[0]).strip().lower() if pd.notna(row.iloc[0]) else ""
        if "contractor" in first_cell or "installer" in first_cell or "contractors" in first_cell:
            header_row_idx = idx
            break
        row_text = " ".join([str(x).lower() if pd.notna(x) else "" for x in row.tolist()])
        if "contractor" in row_text or "installer" in row_text:
            header_row_idx = idx
            break

    if header_row_idx is None:
        header_row_idx = 0

    try:
        df = pd.read_excel(xls, sheet_name=chosen, header=header_row_idx, dtype=object)
    except Exception:
        df = pd.DataFrame()

    if not df.empty:
        df = df.dropna(axis=0, how="all").dropna(axis=1, how="all")
        df.columns = [str(c).strip() for c in df.columns]
        colmap = {}
        for c in df.columns:
            low = c.lower()
            if "contractor" in low or "installer" in low or "contractors" in low:
                colmap[c] = "Contractor"
            elif "install" in low or "installed" in low or "complete" in low or "status" in low:
                colmap[c] = "Installed"
            elif "site" in low or "sites" in low or "total" in low:
                colmap[c] = "Sites"
        if colmap:
            df = df.rename(columns=colmap)
        if "Contractor" in df.columns:
            df["Contractor"] = df["Contractor"].astype(str).str.strip()
        for numeric_col in ["Sites", "Installed"]:
            if numeric_col in df.columns:
                df[numeric_col] = pd.to_numeric(df[numeric_col], errors="coerce")

    return df


# Detect file changes by timestamp
data_last_mod = file_last_modified(data_path)
install_last_mod = file_last_modified(install_path)

# Load (and auto-reload when files change)
sheets = load_data(data_path, data_last_mod)
df_main = sheets.get("Tasks", pd.DataFrame()).copy()
df_install = load_install_data(install_path, install_last_mod).copy()

# ===================== CLEAN DATA =====================
if not df_main.empty:
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    df_main = df_main.fillna("Null")
    df_main = df_main.replace("NaT", "Null")

    df_main = df_main.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_main.columns])

# compute avg_duration globally (so Export tab can use it)
avg_duration = None
if not df_main.empty and "Start date" in df_main.columns and "Due date" in df_main.columns:
    df_duration = df_main.copy().replace("Null", None)
    try:
        df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
        df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
        df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
        avg_duration = df_duration["Duration"].mean()
    except Exception:
        avg_duration = None

if not df_install.empty:
    for c in [col for col in df_install.columns if "date" in col.lower()]:
        df_install[c] = pd.to_datetime(df_install[c], dayfirst=True, errors="coerce")
    df_install = df_install.fillna("Null").replace("NaT", "Null")
    df_install = df_install.drop(columns=[col for col in ["Is Recurring", "Late"] if col in df_install.columns], errors="ignore")

# ===================== MAIN TABS =====================
tabs = st.tabs(["Installations", "KPIs", "Task Breakdown", "Timeline", "Export Report"])

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Status")

    if not df_install.empty:
        st.markdown(f"Total Contractors: **{df_install.shape[0]}**")

        contractor_col = None
        status_col = None
        sites_col = None

        if "Contractor" in df_install.columns:
            contractor_col = "Contractor"
        if "Installed" in df_install.columns:
            status_col = "Installed"
        if "Sites" in df_install.columns:
            sites_col = "Sites"

        for c in df_install.columns:
            low = str(c).lower()
            if not contractor_col and ("contractor" in low or "installer" in low or "contractors" in low):
                contractor_col = c
            if not status_col and ("status" in low or "install" in low or "installed" in low or "complete" in low):
                status_col = c
            if not sites_col and ("site" in low or "sites" in low or "total" in low):
                sites_col = c

        if not status_col:
            for c in df_install.columns:
                low = str(c).lower()
                if "progress" in low or "state" in low:
                    status_col = c
                    break

        if not contractor_col:
            for c in df_install.columns:
                if df_install[c].dtype == object and not any(k in str(c).lower() for k in ["date"]):
                    contractor_col = c
                    break

        if contractor_col and status_col:
            st.markdown("### ⚙️ Contractor Installation Progress")

            def is_completed(value):
                try:
                    s = str(value).strip().lower()
                    return s in ("completed", "complete", "installed", "yes", "done") or pd.notna(pd.to_numeric(value, errors="coerce"))
                except Exception:
                    return False

            if pd.api.types.is_numeric_dtype(df_install[status_col]) or df_install[status_col].dropna().apply(lambda x: str(x).replace('.','',1).isdigit()).all():
                if sites_col:
                    summary = df_install.groupby(contractor_col).agg(
                        Installed_Sites=(status_col, "sum"),
                        Total_Sites=(sites_col, "sum"),
                    ).reset_index()
                else:
                    summary = df_install.groupby(contractor_col).agg(
                        Installed_Sites=(status_col, "sum"),
                    ).reset_index()
                    summary["Total_Sites"] = summary["Installed_Sites"]
                summary = summary.rename(columns={"Installed_Sites": "Completed_Sites", "Total_Sites": "Total_Sites"})
            else:
                summary = (
                    df_install.assign(_is_completed=df_install[status_col].apply(lambda v: str(v).strip().lower() in ("completed","installed","complete","yes","done")))
                    .groupby(contractor_col)
                    .agg(Total_Sites=(status_col, "count"), Completed_Sites=("_is_completed", "sum"))
                    .reset_index()
                )

            def make_contractor_gauge(completed, total, title, dial_color="#007acc"):
                pct = (completed / total * 100) if total and total > 0 else 0
                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=pct,
                        number={"suffix": "%", "font": {"size": 30, "color": dial_color}},
                        title={"text": title, "font": {"size": 16, "color": dial_color}},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                            "bar": {"color": dial_color, "thickness": 0.3},
                            "bgcolor": "#f7f9fb",
                            "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                        },
                    )
                )
                fig.update_layout(autosize=True, margin=dict(l=10, r=10, t=40, b=10))
                return fig

            records = summary.to_dict("records")
            # render gauges in rows of up to 3; handle rows with fewer items gracefully
            for i in range(0, len(records), 3):
                row_items = records[i : i + 3]
                cols = st.columns(len(row_items))
                for j, rec in enumerate(row_items):
                    completed = int(rec.get("Completed_Sites", 0) if rec.get("Completed_Sites", 0) is not None else 0)
                    total = int(rec.get("Total_Sites", 0) if rec.get("Total_Sites", 0) is not None else 0)
                    pct = (completed / total * 100) if total > 0 else 0
                    if pct >= 90:
                        color = "#00b386"
                    elif pct >= 70:
                        color = "#007acc"
                    else:
                        color = "#e67300"
                    with cols[j]:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                        st.plotly_chart(make_contractor_gauge(completed, total, str(rec[contractor_col]), dial_color=color), use_container_width=True)
                        st.markdown(f"<div class='dial-label'>{completed} / {total} installs</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Could not auto-detect Contractor or Status columns. Showing raw installation data below.")

        st.markdown("### 🧾 Installation Data")

        def df_to_html_install(df):
            html = "<div style='overflow-x:auto;'>"
            html += "<table>"
            html += "<tr>"
            for col in df.columns:
                html += f"<th>{col}</th>"
            html += "</tr>"
            for _, row in df.iterrows():
                html += "<tr>"
                for cell in row:
                    cell_display = f"<i style='color:gray;'>Null</i>" if str(cell).strip() == "Null" else str(cell)
                    html += f"<td>{cell_display}</td>"
                html += "</tr>"
            html += "</table>"
            html += "</div>"
            return html

        st.markdown(df_to_html_install(df_install), unsafe_allow_html=True)
    else:
        st.warning("No data found in Weekly update sheet.xlsx.")

# ===================== KPI TAB =====================
with tabs[1]:
    if not df_main.empty:
        st.subheader("Key Performance Indicators")

        total = len(df_main)
        # make progress-safe
        progress_series = df_main.get("Progress", pd.Series([""] * len(df_main)))
        completed = progress_series.str.lower().eq("completed").sum()
        inprogress = progress_series.str.lower().eq("in progress").sum()
        notstarted = progress_series.str.lower().eq("not started").sum()
        overdue = (
            (pd.to_datetime(df_main.get("Due date", pd.Series([])), errors="coerce") < pd.Timestamp.today())
            & (~progress_series.str.lower().eq("completed"))
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
            fig.update_layout(autosize=True, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]

        with st.container():
            # use dynamic columns so they can wrap on narrow screens
            cols = st.columns(4)
            widgets = [notstarted, inprogress, completed, overdue]
            titles = ["Not Started", "In Progress", "Completed", "Overdue"]
            for c, val, t, col in zip(cols, widgets, titles, dial_colors):
                with c:
                    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
                    st.plotly_chart(create_colored_gauge(val, total, t, col), use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("📈 Additional Insights", expanded=True):
            st.markdown("### Expanded Project Insights")
            df_duration2 = df_main.copy().replace("Null", None)
            df_duration2["Start date"] = pd.to_datetime(df_duration2.get("Start date", pd.Series([])), errors="coerce")
            df_duration2["Due date"] = pd.to_datetime(df_duration2.get("Due date", pd.Series([])), errors="coerce")
            df_duration2["Duration"] = (df_duration2["Due date"] - df_duration2["Start date"]).dt.days
            avg_duration_local = df_duration2["Duration"].mean()

            st.markdown(f"**⏱️ Average Task Duration:** {avg_duration_local:.1f} days" if pd.notna(avg_duration_local) else "**⏱️ Average Task Duration:** N/A")

            priority_counts = df_main.get("Priority", pd.Series([])).value_counts(normalize=True) * 100
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
                bucket_cols = st.columns(1)
                for i, row in enumerate(completion_by_bucket.itertuples(index=False)):
                    bucket_name = row[0]
                    bucket_pct = row[1]
                    with bucket_cols[i % 1]:
                        st.plotly_chart(
                            create_colored_gauge(bucket_pct, 50, bucket_name, "#006666"),
                            use_container_width=True,
                        )

# ===================== TASK BREAKDOWN TAB =====================
with tabs[2]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")

    def df_to_html(df):
        html = "<div style='overflow-x:auto;'>"
        html += "<table>"
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
        html += "</div>"
        return html

    st.markdown(df_to_html(df_main), unsafe_allow_html=True)

# ===================== TIMELINE TAB =====================
with tabs[3]:
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
            fig_tl.update_layout(autosize=True, margin=dict(l=20, r=20, t=40, b=20))
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
            ["Total Tasks", len(df_main)],
            ["Completed", df_main["Progress"].str.lower().eq("completed").sum()],
            ["In Progress", df_main["Progress"].str.lower().eq("in progress").sum()],
            ["Not Started", df_main["Progress"].str.lower().eq("not started").sum()],
            ["Overdue", (
                (pd.to_datetime(df_main["Due date"], errors="coerce") < pd.Timestamp.today())
                & (~df_main["Progress"].str.lower().eq("completed"))
            ).sum()],
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

        if not df_install.empty:
            story.append(Paragraph("<b>Installations Summary</b>", styles["Heading2"]))
            story.append(Spacer(1, 6))
            install_head = df_install.head(10).fillna("Null")
            data_i = [list(install_head.columns)]
            for _, r in install_head.iterrows():
                row_vals = []
                for v in r:
                    if str(v).strip() == "Null":
                        row_vals.append(Paragraph("<i>Null</i>", null_style))
                    else:
                        row_vals.append(Paragraph(str(v), cell_style))
                data_i.append(row_vals)
            col_count_i = len(install_head.columns) if len(install_head.columns) > 0 else 1
            table_i = Table(data_i, colWidths=[(A4[1] - 80) / col_count_i] * col_count_i, repeatRows=1)
            table_i.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(table_i)
            story.append(Spacer(1, 12))

        story.append(Paragraph("<b>Task Summary</b>", styles["Heading2"]))
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

        col_count = len(limited.columns) if len(limited.columns) > 0 else 1
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
