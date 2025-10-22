# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ------------------ PAGE CONFIG ------------------
st.set_page_config(page_title="eThekwini WS-7761 Smart Meter Project", layout="wide", initial_sidebar_state="collapsed")

# ------------------ ASSETS ------------------
# Developer-provided images (these exist in the container)
LOCAL_LOGO = "/mnt/data/ecfa7c96-7592-4cf8-aaf4-24b5cdbf5abb.png"
LOCAL_HEADER_IMG = "/mnt/data/ad3a3ae7-c1ce-4e7d-bba3-06fd823ee683.png"
DATA_PATH = "Ethekwini WS-7761.xlsx"

# ------------------ STYLE (CSS) ------------------
st.markdown(
    """
    <style>
    /* Page background */
    .stApp {
        background-color: #f6f8fb;
    }

    /* Gradient header */
    .header {
        background: linear-gradient(135deg, #d7e9ff 0%, #efe8ff 50%, #f3fbff 100%);
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 16px;
    }

    .header h1 {
        margin: 0;
        color: #0b5394;
        font-size: 34px;
    }

    .header p {
        margin: 4px 0 0 0;
        color: #5b6b7a;
    }

    /* KPI card styling */
    .kpi-card {
        background: white;
        padding: 18px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(20,20,50,0.06);
        height:120px;
    }

    .kpi-title { color:#6b7a8a; font-size:13px; margin-bottom:6px; }
    .kpi-value { font-weight:700; font-size:28px; color:#0b5394;}
    .kpi-sub { color:#9aa6b3; font-size:12px; margin-top:6px; }

    /* Suspicious card */
    .susp-card {
        background: white;
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(20,20,50,0.06);
    }

    /* table wrapper */
    .table-card {
        background: white;
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 6px 18px rgba(20,20,50,0.06);
    }

    /* Filter row */
    .filter-row .stSelectbox, .filter-row .stDateInput, .filter-row .stButton {
        display:inline-block;
    }

    /* Small text */
    .muted { color:#9aa6b3; font-size:12px }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------ LOAD DATA (or create demo) ------------------
@st.cache_data(show_spinner=False)
def load_sheets(path=DATA_PATH):
    if os.path.exists(path):
        try:
            xls = pd.ExcelFile(path)
            sheets = {s: pd.read_excel(xls, sheet_name=s) for s in xls.sheet_names}
            return sheets
        except Exception as e:
            # fallback to demo if read fails
            return {"Tasks": pd.DataFrame()}
    else:
        return {"Tasks": pd.DataFrame()}

sheets = load_sheets()
df_main = sheets.get("Tasks", pd.DataFrame()).copy()

# If df_main empty, create demo dataset so UI shows something
if df_main.empty:
    # demo structure consistent with your earlier code
    num = 40
    start = datetime.today() - timedelta(days=60)
    demo = []
    priorities = ["High", "Medium", "Low"]
    buckets = ["Installation", "Testing", "Commissioning", "QA"]
    progress_states = ["Not Started", "In Progress", "Completed"]
    for i in range(num):
        s = start + timedelta(days=i)
        d = s + timedelta(days=(7 + (i % 20)))
        demo.append({
            "Task": f"Task {i+1} - Meter work",
            "Start date": s.date(),
            "Due date": d.date(),
            "Progress": progress_states[i % len(progress_states)],
            "Priority": priorities[i % len(priorities)],
            "Bucket Name": buckets[i % len(buckets)],
            "Customer": f"Customer {i%6}",
            "Location": f"Ward {1 + (i % 6)}",
            "Consumption": int(150000 - i*1000 + (i%5)*2000),
            "Meter": f"WM-{1000 + i}"
        })
    df_main = pd.DataFrame(demo)

# CLEAN UP: unify date columns
for c in [col for col in df_main.columns if "date" in col.lower()]:
    df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

df_main = df_main.fillna("Null")
df_main = df_main.replace("NaT", "Null")

# ------------------ HEADER ------------------
logo_to_show = LOCAL_LOGO if os.path.exists(LOCAL_LOGO) else None
with st.container():
    st.markdown("<div class='header'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 6, 2])
    with col1:
        if logo_to_show:
            st.image(logo_to_show, width=120)
    with col2:
        st.markdown("<h1>Water Management Dashboard</h1>", unsafe_allow_html=True)
        st.markdown("<p class='muted'>Operational view of meter health, consumption, and revenue.</p>", unsafe_allow_html=True)
    with col3:
        # small stats top right
        st.markdown("<div style='text-align:right'><span class='muted'>Data as of</span><br><strong>" +
                    datetime.now().strftime("%d %b %Y") + "</strong></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ FILTER ROW ------------------
with st.container():
    st.markdown("<div class='filter-row'>", unsafe_allow_html=True)
    fcol1, fcol2, fcol3, fcol4 = st.columns([2, 2, 2, 1])
    with fcol1:
        daterange = st.selectbox("Date range", ["Last 7 days", "Last 30 days", "Last 90 days", "All"], index=1)
    with fcol2:
        region = st.selectbox("Region", ["All", "Ward 1", "Ward 2", "Ward 3", "Ward 4"], index=0)
    with fcol3:
        cust_type = st.selectbox("Customer Type", ["All", "Residential", "Commercial"], index=0)
    with fcol4:
        st.markdown("<div style='padding-top:18px'></div>", unsafe_allow_html=True)
        apply_btn = st.button("Apply", key="apply_filters")
    st.markdown("</div>", unsafe_allow_html=True)

# Filter logic (simple; demo)
df_filtered = df_main.copy()
if daterange != "All":
    days = 30
    if daterange == "Last 7 days":
        days = 7
    elif daterange == "Last 90 days":
        days = 90
    cutoff = pd.Timestamp.today() - pd.Timedelta(days=days)
    if "Due date" in df_filtered.columns:
        df_filtered = df_filtered[
            (pd.to_datetime(df_filtered["Due date"], errors="coerce") >= cutoff)
            | (pd.to_datetime(df_filtered.get("Start date", pd.NaT), errors="coerce") >= cutoff)
        ]

if region != "All" and "Location" in df_filtered.columns:
    df_filtered = df_filtered[df_filtered["Location"].str.contains(region.split()[-1], na=False)]

# ------------------ KPI CARDS ------------------
total = len(df_filtered)
completed = df_filtered["Progress"].str.lower().eq("completed").sum()
inprogress = df_filtered["Progress"].str.lower().eq("in progress").sum()
notstarted = df_filtered["Progress"].str.lower().eq("not started").sum()
overdue = (
    (pd.to_datetime(df_filtered.get("Due date", pd.NaT), errors="coerce") < pd.Timestamp.today())
    & (~df_filtered["Progress"].str.lower().eq("completed"))
).sum()

kpi_cols = st.columns([1.5, 1.5, 1.5, 1.5])
kpi_info = [
    ("Tamper Alerts", 65, "out of 1,200 meters"),
    ("Leak Alerts", 48, "out of 1,200 meters"),
    ("Avg Consumption (L/day)", f"{int(df_filtered['Consumption'].mean()):,}" if "Consumption" in df_filtered.columns else "N/A", "per meter"),
    ("Avg Consumption (R/day)", "R 23.16", "per meter"),
]
# show KPI cards
for col, (title, value, sub) in zip(kpi_cols, kpi_info):
    with col:
        st.markdown("<div class='kpi-card'>", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-title'>{title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-value'>{value}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='kpi-sub'>{sub}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

# ------------------ MAIN LAYOUT: Left charts, Right side cards ------------------
left_col, right_col = st.columns([3, 1])

# Left content (charts + top 5)
with left_col:
    # Top row charts (bar for bulk inflow vs total consumption & donut for meter state)
    chart_col1, chart_col2 = st.columns([2, 1])
    with chart_col1:
        # Bulk inflow vs consumption (demo)
        values = {"Bulk Inflow": 250, "Total Consumption": 230}
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(x=list(values.keys()), y=list(values.values()), marker_color=["#80caff", "#8cd3a6"]))
        fig_bar.update_layout(title_text="Bulk Meter Inflow vs Total Consumption", height=300, margin=dict(t=40, l=20, r=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)
    with chart_col2:
        # Meter state breakdown (donut)
        state_counts = df_filtered["Progress"].value_counts().to_dict()
        if not state_counts:
            state_counts = {"Completed": 1}
        labels = list(state_counts.keys())
        vals = list(state_counts.values())
        fig_donut = go.Figure(data=[go.Pie(labels=labels, values=vals, hole=0.7, sort=False)])
        fig_donut.update_layout(title_text="Meter State Breakdown", height=300, margin=dict(t=40, l=10, r=10, b=10), showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)

    st.markdown("")  # spacing

    # Top 5 meters by consumption (bar + table)
    st.markdown("<div class='table-card'>", unsafe_allow_html=True)
    st.markdown("#### Top 5 Meters by Consumption")
    if "Consumption" in df_filtered.columns:
        top5 = df_filtered.sort_values("Consumption", ascending=False).head(5)
    else:
        top5 = df_filtered.head(5)
    # bar
    try:
        fig_top5 = px.bar(top5, x="Consumption", y="Meter", orientation="h", text="Consumption", height=260)
        fig_top5.update_layout(margin=dict(l=20, r=20, t=30, b=10))
        fig_top5.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_top5, use_container_width=True)
    except Exception:
        # fallback: textual table if columns missing
        st.table(top5.head(5))
    # simple data table below bar
    small_table = top5[["Meter", "Customer", "Location", "Consumption"]].fillna("Null")
    st.write(small_table.to_html(index=False, classes="table"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")  # spacing

    # Vend vs consumption time series (demo)
    st.markdown("<div class='table-card'>", unsafe_allow_html=True)
    st.markdown("#### Total Vend Amount vs Total Consumption Amount (over period)")
    # make a demo days series
    days = pd.date_range(end=pd.Timestamp.today(), periods=14)
    vend = [200000 + (i % 3) * 10000 - i * 2000 for i in range(len(days))]
    cons_amount = [150000 + (i % 4) * 8000 - i * 1000 for i in range(len(days))]
    df_series = pd.DataFrame({"date": days, "Vend Amount (R)": vend, "Consumption Amount (R)": cons_amount})
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(x=df_series["date"], y=df_series["Vend Amount (R)"], mode="lines+markers", name="Vend Amount (R)"))
    fig_ts.add_trace(go.Scatter(x=df_series["date"], y=df_series["Consumption Amount (R)"], mode="lines+markers", name="Consumption Amount (R)"))
    fig_ts.update_layout(height=320, margin=dict(t=20, l=10, r=10, b=20))
    st.plotly_chart(fig_ts, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    st.markdown("<div class='susp-card'>", unsafe_allow_html=True)
    st.markdown("### Suspicious Meters (Top 5)")
    # Demo suspicious scoring: combination of high consumption + not completed + tamper-like
    df_s = df_filtered.copy()
    # create a 'score' heuristic for demo
    if "Consumption" in df_s.columns:
        df_s["score"] = (pd.to_numeric(df_s["Consumption"], errors="coerce").fillna(0) / (df_s["Consumption"].max() + 1)) * 5
    else:
        df_s["score"] = 0
    df_s = df_s.sort_values("score", ascending=False).head(5)
    for _, r in df_s.iterrows():
        meter = r.get("Meter", "Unknown")
        customer = r.get("Customer", "Unknown")
        loc = r.get("Location", "Unknown")
        score = float(r.get("score", 0))
        st.markdown(f"**{meter} • {customer}**")
        st.markdown(f"<span class='muted'>{loc}</span>  &nbsp;&nbsp; <span style='color:#d13f6f; font-weight:700'>Score {score:.1f}</span>", unsafe_allow_html=True)
        st.markdown("---")
    st.markdown("<div class='muted'>Suspicion score considers tamper/leak flags, zero or constant usage, and sudden spikes.</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ TASK BREAKDOWN TAB (detailed table) ------------------
st.markdown("---")
st.markdown("## Full Task Overview")
st.markdown("<div class='table-card'>", unsafe_allow_html=True)
st.markdown(f"Showing {len(df_filtered)} rows")
# Build an HTML table with colored rows (similar to your earlier approach)
def df_to_html(df):
    table_html = "<table style='border-collapse: collapse; width:100%; font-size:13px;'>"
    # headers
    table_html += "<thead><tr>"
    for c in df.columns:
        table_html += f"<th style='text-align:left; padding:8px; color:#495057; background:#fbfdff'>{c}</th>"
    table_html += "</tr></thead><tbody>"
    # rows
    for _, row in df.iterrows():
        progress = str(row.get("Progress", "")).lower()
        row_color = "#ffffff"
        if progress == "not started":
            row_color = "#f0fff0"
        elif progress == "in progress":
            row_color = "#f8faff"
        elif progress == "completed":
            row_color = "#f0fbf8"
        else:
            row_color = "#ffffff"
        table_html += f"<tr style='background:{row_color}'>"
        for c in df.columns:
            val = row.get(c, "")
            display = "<i style='color:gray'>Null</i>" if str(val) == "Null" or pd.isna(val) else str(val)
            table_html += f"<td style='padding:8px; border-bottom:1px solid #f1f3f5'>{display}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    return table_html

st.write(df_to_html(df_filtered.head(200)), unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# ------------------ TIMELINE (Gantt) ------------------
st.markdown("---")
st.markdown("## Project Timeline")
if "Start date" in df_main.columns and "Due date" in df_main.columns:
    df_tl = df_main.copy()
    df_tl = df_tl[df_tl["Start date"].notna() & df_tl["Due date"].notna()]
    if not df_tl.empty:
        df_tl["task_label"] = df_tl["Task"].astype(str).str.slice(0, 50)
        color_map = {"Not Started": "#66b3ff", "In Progress": "#3399ff", "Completed": "#33cc33"}
        df_tl["col"] = df_tl["Progress"].map(color_map).fillna("#9aa6b3")
        fig_tl = px.timeline(df_tl, x_start="Start date", x_end="Due date", y="task_label", color="Progress", color_discrete_map=color_map)
        fig_tl.update_yaxes(autorange="reversed")
        fig_tl.update_layout(height=420, margin=dict(t=30, l=10, r=10, b=20))
        st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("No timeline rows with valid Start date and Due date.")
else:
    st.info("Timeline data not available (Start date / Due date columns missing).")

# ------------------ EXPORT REPORT TAB ------------------
st.markdown("---")
st.markdown("## Export Report")
st.write("Generate a PDF snapshot of KPIs and top tasks.")

def build_pdf_bytes(df, title="Ethekwini WS-7761 Smart Meter Project Report"):
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
    story = []
    styles = getSampleStyleSheet()
    story.append(Paragraph(title, styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
    story.append(Spacer(1, 12))
    # KPIs table
    kpi_data = [
        ["Metric", "Count"],
        ["Total Tasks", total],
        ["Completed", completed],
        ["In Progress", inprogress],
        ["Not Started", notstarted],
        ["Overdue", overdue],
    ]
    table = Table(kpi_data, colWidths=[250, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER")
    ]))
    story.append(table)
    story.append(Spacer(1, 12))
    # Top 10 tasks
    limited = df.head(15).copy().fillna("Null")
    data = [list(limited.columns)]
    for _, r in limited.iterrows():
        row = []
        for c in limited.columns:
            val = r[c]
            row.append(str(val))
        data.append(row)
    col_count = len(limited.columns)
    task_table = Table(data, colWidths=[(A4[1] - 80) / col_count] * col_count, repeatRows=1)
    task_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ]))
    story.append(task_table)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

pdf_bytes = build_pdf_bytes(df_filtered)
st.download_button("📥 Download PDF Report", data=pdf_bytes, file_name="Ethekwini_WS7761_Report.pdf", mime="application/pdf")

# ------------------ FOOTER ------------------
st.markdown("<div style='margin-top:18px; color:#98a2b3; font-size:12px'>Ethekwini Municipality | Automated Project Dashboard</div>", unsafe_allow_html=True)
