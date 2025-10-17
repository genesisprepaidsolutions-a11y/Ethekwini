import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

st.markdown("<h1 style='text-align:center'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)

@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=s)
            sheets[s] = df
        except Exception as e:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()

# Sidebar
cols = st.columns([1,3])
with cols[0]:
    st.sidebar.header("Data & Filters")
    sheet_choice = st.sidebar.selectbox("Main sheet to view", list(sheets.keys()), index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0)
    search_task = st.sidebar.text_input("Search Task name (contains)")
    date_from = st.sidebar.date_input("Start date from", value=None)
    date_to = st.sidebar.date_input("Due date to", value=None)
    show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

# Sidebar Sheets
st.sidebar.markdown("**Sheets in workbook:**")
for s in sheets:
    st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    # Convert date columns
    date_cols = [c for c in df_main.columns if "date" in c.lower()]
    for c in date_cols:
        try:
            df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors='coerce')
        except:
            pass

    # Filters
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]
    if date_from:
        if "Start date" in df_main.columns:
            df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to:
        if "Due date" in df_main.columns:
            df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]
    
    # ===================== KPI SECTION =====================
    if "Tasks" in sheets:
        st.subheader("Key Performance Indicators")
        tasks = sheets["Tasks"].copy()
        for col in ["Start date", "Due date", "Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

        total = len(tasks)
        completed = tasks['Progress'].str.lower().eq('completed').sum() if 'Progress' in tasks.columns else 0
        inprogress = tasks['Progress'].str.lower().eq('in progress').sum() if 'Progress' in tasks.columns else 0
        notstarted = tasks['Progress'].str.lower().eq('not started').sum() if 'Progress' in tasks.columns else 0
        overdue = ((tasks['Due date'] < pd.Timestamp.today()) & (~tasks['Progress'].str.lower().eq('completed'))).sum() if 'Due date' in tasks.columns and 'Progress' in tasks.columns else 0

        # ===== Custom Gauge Function (Dark blue needle + % center) =====
        def create_gauge(value, total, title, colors):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=pct,
                number={'suffix': "%", 'font': {'size': 36}},
                title={'text': title, 'font': {'size': 20}},
                gauge={
                    'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                    'bar': {'color': "darkblue", 'thickness': 0.35},  # dark blue needle
                    'steps': [
                        {'range': [0, 33], 'color': colors[0]},
                        {'range': [33, 66], 'color': colors[1]},
                        {'range': [66, 100], 'color': colors[2]},
                    ],
                }
            ))
            fig.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                height=250,
                paper_bgcolor="rgba(0,0,0,0)",
                font={'color': "white"}
            )
            return fig

        # Gauges
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(create_gauge(notstarted, total, "Not Started", ["green", "yellow", "red"]), use_container_width=True)
        with c2:
            st.plotly_chart(create_gauge(inprogress, total, "In Progress", ["red", "yellow", "green"]), use_container_width=True)
        with c3:
            st.plotly_chart(create_gauge(completed, total, "Completed", ["red", "yellow", "green"]), use_container_width=True)
        with c4:
            st.plotly_chart(create_gauge(overdue, total, "Overdue", ["yellow", "red", "darkred"]), use_container_width=True)

    # ========================================================
    st.markdown("----")
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # ===================== DASHBOARD VISUALS =====================
    if sheet_choice == "Tasks" or "Tasks" in sheets:
        tasks = sheets["Tasks"].copy()
        for col in ["Start date","Due date","Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

        st.subheader("Task Breakdown & Visuals")

        # Tasks per Bucket (with value labels)
        if 'Bucket Name' in tasks.columns:
            agg = tasks['Bucket Name'].value_counts().reset_index()
            agg.columns = ['Bucket Name', 'Count']
            fig2 = px.bar(agg, x='Bucket Name', y='Count', title="Tasks per Bucket", text='Count')
            fig2.update_traces(texttemplate='%{text}', textposition='outside')
            fig2.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
            st.plotly_chart(fig2, use_container_width=True)

        # Priority distribution
        if 'Priority' in tasks.columns:
            fig3 = px.pie(tasks, names='Priority', title="Priority distribution")
            st.plotly_chart(fig3, use_container_width=True)

        # Overdue table
        if 'Due date' in tasks.columns and 'Progress' in tasks.columns:
            overdue_df = tasks[(tasks['Due date'] < pd.Timestamp.today()) & (tasks['Progress'].str.lower() != 'completed')]
            st.markdown("#### Overdue tasks")
            st.dataframe(overdue_df.sort_values('Due date').reset_index(drop=True).loc[:, ['Task Name', 'Bucket Name', 'Progress', 'Due date', 'Priority']].head(200))

        # Checklist completion parsing
        if 'Completed Checklist Items' in tasks.columns:
            def parse_checklist(x):
                try:
                    if pd.isna(x): return None
                    if isinstance(x, (int, float)): return float(x)
                    parts = str(x).split('/')
                    if len(parts) == 2:
                        return float(parts[0]) / float(parts[1]) if float(parts[1]) != 0 else None
                    return None
                except:
                    return None
            tasks['check_pct'] = tasks['Completed Checklist Items'].apply(parse_checklist)
            if tasks['check_pct'].notna().any():
                st.markdown("#### Checklist completion (task-level)")
                st.dataframe(tasks[['Task Name','Completed Checklist Items','check_pct']].sort_values('check_pct', ascending=False).head(200))
        
        # Timeline chart (start -> due)
        if 'Start date' in tasks.columns and 'Due date' in tasks.columns:
            timeline = tasks.dropna(subset=['Start date', 'Due date']).copy()
            if not timeline.empty:
                timeline['task_short'] = timeline['Task Name'].astype(str).str.slice(0, 60)
                fig4 = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short", color="Bucket Name", title="Task timeline (Start -> Due)")
                fig4.update_yaxes(autorange="reversed")
                st.plotly_chart(fig4, use_container_width=True)

    # Export
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
