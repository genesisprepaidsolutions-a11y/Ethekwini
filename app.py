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
st.set_page_config(
    page_title="eThekwini WS-7761 Smart Meter Project",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== FORCE WHITE THEME =====================
st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        color: #003366 !important;
    }
    body {
        font-family: 'Segoe UI', sans-serif;
        color: #003366 !important;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%);
        color: white !important;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    .metric-card {
        background-color: #f5f9ff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    [data-testid="stToolbar"], button[data-testid="baseButton-secondary"], [data-testid="stThemeToggle"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== HEADER =====================
logo_url = "https://github.com/genesisprepaidsolutions-a11y/Ethekwini/blob/main/ethekwini_logo.png?raw=true"
data_path = "Ethekwini WS-7761.xlsx"

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
                        "bgcolor": "#ffffff",
                        "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        dial_colors = ["#003366", "#007acc", "#00b386", "#e67300"]

        with st.container():
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.plotly_chart(create_colored_gauge(notstarted, total, "Not Started", dial_colors[0]), use_container_width=True)
            with c2: st.plotly_chart(create_colored_gauge(inprogress, total, "In Progress", dial_colors[1]), use_container_width=True)
            with c3: st.plotly_chart(create_colored_gauge(completed, total, "Completed", dial_colors[2]), use_container_width=True)
            with c4: st.plotly_chart(create_colored_gauge(overdue, total, "Overdue", dial_colors[3]), use_container_width=True)

        # ===================== ADDITIONAL INSIGHTS =====================
        with st.expander("📈 Additional Insights", expanded=True):
            st.markdown("### Expanded Project Insights")

            df_duration = df_main.copy().replace("Null", None)
            df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
            df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
            df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
            avg_duration = df_duration["Duration"].mean()
            st.markdown(f"**⏱️ Average Task Duration:** {avg_duration:.1f} days" if pd.notna(avg_duration) else "**⏱️ Average Task Duration:** N/A")

            # Contractor Completion Dials
            if "Contractor" in df_main.columns:
                st.markdown("#### 🧰 Installations by Contractor")
                contractors = df_main["Contractor"].unique()
                contractor_cols = st.columns(2)
                for i, contractor in enumerate(contractors):
                    df_contractor = df_main[df_main["Contractor"] == contractor]
                    total_con = len(df_contractor)
                    completed_con = df_contractor["Progress"].str.lower().eq("completed").sum()
                    pct = (completed_con / total_con * 100) if total_con > 0 else 0
                    with contractor_cols[i % 2]:
                        st.plotly_chart(
                            create_colored_gauge(pct, 100, contractor, "#004d66"),
                            use_container_width=True,
                        )

            # Priority Dials
            st.markdown("#### 🔰 Priority Distribution")
            priority_counts = df_main["Priority"].value_counts(normalize=True) * 100
            cols = st.columns(2)
            priority_colors = ["#ff6600", "#0099cc", "#00cc66", "#cc3366"]
            for i, (priority, pct) in enumerate(priority_counts.items()):
                with cols[i % 2]:
                    st.plotly_chart(create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]), use_container_width=True)

            # Phase Completion Dials
            st.markdown("#### 🧭 Phase Completion Dials")
            completion_by_bucket = (
                df_main.groupby("Bucket Name")["Progress"]
                .apply(lambda x: (x.str.lower() == "completed").mean() * 100)
                .reset_index()
                .rename(columns={"Progress": "Completion %"})
            )
            bucket_cols = st.columns(2)
            for i, row in enumerate(completion_by_bucket.itertuples()):
                with bucket_cols[i % 2]:
                    st.plotly_chart(create_colored_gauge(row._2, 100, row._1, "#006666"), use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Task Overview ({df_main.shape[0]} rows)")
    st.dataframe(df_main)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        df_copy = df_main.replace("Null", None)
        timeline = df_copy.dropna(subset=["Start date", "Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0, 60)
            progress_color_map = {"Not Started": "#66b3ff", "In Progress": "#3399ff", "Completed": "#33cc33"}
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

# ===================== EXPORT REPORT TAB =====================
with tabs[3]:
    st.subheader("📄 Export Smart Meter Project Report")
    if not df_main.empty:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4))
        story = []
        styles = getSampleStyleSheet()
        story.append(Paragraph("<b>Ethekwini WS-7761 Smart Meter Project Report</b>", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles["Normal"]))
        story.append(Spacer(1, 12))
        story.append(Image(logo_url, width=120, height=70))
        story.append(Spacer(1, 12))
        story.append(Paragraph("Ethekwini Municipality | Automated Project Report", styles["Normal"]))
        doc.build(story)
        st.download_button("📥 Download PDF Report", data=buf.getvalue(), file_name="Ethekwini_WS7761_SmartMeter_Report.pdf", mime="application/pdf")
