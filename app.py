import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

st.markdown("<h1 style='text-align:center'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)

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
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0,
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

if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    # Convert date columns
    date_cols = [c for c in df_main.columns if "date" in c.lower()]
    for c in date_cols:
        try:
            df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")
        except Exception:
            pass

    # Filters
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
        overdue = ((tasks["Due date"] < pd.Timestamp.today()) & (~tasks["Progress"].str.lower().eq("completed"))).sum() if "Due date" in tasks.columns and "Progress" in tasks.columns else 0

        # Custom gauge function
        def create_gauge(value, total, title, colors):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=pct,
                number={"suffix":"%", "font":{"size":40,"color":"darkblue"}, "valueformat":".1f"},
                gauge={
                    "axis":{"range":[0,100], "tickwidth":1,"tickcolor":"darkgray"},
                    "bar":{"color":"darkblue","thickness":0.35},
                    "steps":[{"range":[0,33],"color":colors[0]},{"range":[33,66],"color":colors[1]},{"range":[66,100],"color":colors[2]}]
                }
            ))

            fig.add_annotation(text=f"<b>{title}</b>", x=0.5, y=1.25, showarrow=False, font=dict(size=18,color="darkblue"), xanchor="center")
            fig.add_annotation(text=f"{value} of {total} tasks", x=0.5, y=-0.25, showarrow=False, font=dict(size=14,color="darkblue"), xanchor="center")
            fig.update_layout(margin=dict(l=10,r=10,t=70,b=50), height=270, paper_bgcolor="rgba(0,0,0,0)", font={"color":"white"})
            return fig

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(create_gauge(notstarted, total, "Not Started", ["green","yellow","red"]), use_container_width=True)
        with c2:
            st.plotly_chart(create_gauge(inprogress, total, "In Progress", ["red","yellow","green"]), use_container_width=True)
        with c3:
            st.plotly_chart(create_gauge(completed, total, "Completed", ["red","yellow","green"]), use_container_width=True)
        with c4:
            st.plotly_chart(create_gauge(overdue, total, "Overdue", ["yellow","red","darkred"]), use_container_width=True)

# ===================== TASK BREAKDOWN TAB =====================
with tabs[1]:
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    
    # Conditional formatting
    if "Due date" in df_main.columns and "Progress" in df_main.columns:
        def highlight_status(row):
            color = ""
            if pd.notna(row["Due date"]) and row["Due date"] < pd.Timestamp.today() and row["Progress"].lower() != "completed":
                color = "background-color: #ffcccc"  # red for overdue
            elif row["Progress"].lower() == "in progress":
                color = "background-color: #fff0b3"  # yellow
            elif row["Progress"].lower() == "completed":
                color = "background-color: #ccffcc"  # green
            return [color]*len(row)
        st.dataframe(df_main.style.apply(highlight_status, axis=1))
    else:
        st.dataframe(df_main)

    # Tasks per Bucket
    if "Bucket Name" in df_main.columns:
        agg = df_main["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name","Count"]
        fig_bucket = px.bar(agg, x="Bucket Name", y="Count", text="Count", title="Tasks per Bucket")
        fig_bucket.update_traces(texttemplate="%{text}", textposition="outside")
        st.plotly_chart(fig_bucket, use_container_width=True)

    # Priority Pie
    if "Priority" in df_main.columns:
        fig_pie = px.pie(df_main, names="Priority", title="Priority Distribution")
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        fig_pie.update_layout(showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

# ===================== TIMELINE TAB =====================
with tabs[2]:
    if "Start date" in df_main.columns and "Due date" in df_main.columns:
        timeline = df_main.dropna(subset=["Start date","Due date"]).copy()
        if not timeline.empty:
            timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0,60)
            fig_tl = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short", color="Bucket Name", title="Task Timeline")
            fig_tl.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_tl, use_container_width=True)
    else:
        st.info("Timeline data not available.")

# ===================== EXPORT TAB =====================
with tabs[3]:
    st.subheader("Export Filtered Data")
    csv = df_main.to_csv(index=False).encode("utf-8")
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime="text/csv")
