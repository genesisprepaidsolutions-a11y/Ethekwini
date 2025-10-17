import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

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
st.sidebar.header("Filters & Settings")

sheet_choice = st.sidebar.selectbox(
    "Sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)

search_task = st.sidebar.text_input("Search Task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)

# Progress filter toggle buttons
show_notstarted = st.sidebar.checkbox("Show Not Started", value=True)
show_inprogress = st.sidebar.checkbox("Show In Progress", value=True)
show_completed = st.sidebar.checkbox("Show Completed", value=True)

show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

# ===================== MAIN DATAFRAME =====================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if not df_main.empty:
    # Convert date columns
    for c in [col for col in df_main.columns if "date" in col.lower()]:
        df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors="coerce")

    # Search filter
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]

    # Date filters
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

    # Filter by progress toggle buttons
    progress_map = []
    if show_notstarted:
        progress_map.append("Not Started")
    if show_inprogress:
        progress_map.append("In Progress")
    if show_completed:
        progress_map.append("Completed")

    if progress_map and "Progress" in df_main.columns:
        df_main = df_main[df_main["Progress"].isin(progress_map)]

# ===================== KPI GAUGES =====================
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

# ===================== TASK TABLE =====================
st.subheader(f"Task Table: {sheet_choice} ({df_main.shape[0]} rows)")

if not df_main.empty and "Progress" in df_main.columns:
    def highlight_status(row):
        if pd.notna(row["Due date"]) and row["Due date"] < pd.Timestamp.today() and row["Progress"].lower() != "completed":
            color = "background-color: #ffcccc"  # overdue red
        elif row["Progress"].lower() == "in progress":
            color = "background-color: #fff0b3"  # yellow
        elif row["Progress"].lower() == "completed":
            color = "background-color: #a3f7a3"  # green
        else:
            color = ""
        return [color]*len(row)
    st.dataframe(df_main.style.apply(highlight_status, axis=1))
else:
    st.dataframe(df_main)

# ===================== TASKS PER BUCKET =====================
if "Bucket Name" in df_main.columns:
    agg = df_main["Bucket Name"].value_counts().reset_index()
    agg.columns = ["Bucket Name","Count"]
    fig_bucket = px.bar(agg, x="Bucket Name", y="Count", text="Count", title="Tasks per Bucket",
                        color="Count", color_continuous_scale=px.colors.sequential.Blues)
    fig_bucket.update_traces(texttemplate="%{text}", textposition="outside")
    st.plotly_chart(fig_bucket, use_container_width=True)

# ===================== PRIORITY PIE =====================
if "Priority" in df_main.columns:
    fig_pie = px.pie(df_main, names="Priority", title="Priority Distribution",
                     color="Priority", color_discrete_sequence=px.colors.sequential.Blues_r)
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie.update_layout(showlegend=True)
    st.plotly_chart(fig_pie, use_container_width=True)

# ===================== TIMELINE =====================
st.subheader("Task Timeline")
if "Start date" in df_main.columns and "Due date" in df_main.columns:
    timeline = df_main.dropna(subset=["Start date","Due date"]).copy()
    if not timeline.empty:
        timeline["task_short"] = timeline[df_main.columns[0]].astype(str).str.slice(0,60)
        progress_color = {"not started":"green","in progress":"yellow","completed":"red"}
        timeline["color"] = timeline["Progress"].str.lower().map(progress_color)
        fig_tl = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short",
                             color="color", title="Timeline by Progress", color_discrete_map=progress_color)
        fig_tl.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_tl, use_container_width=True)
else:
    st.info("Timeline data not available.")

# ===================== EXPORT =====================
st.subheader("Export Filtered Data")
csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime="text/csv")
