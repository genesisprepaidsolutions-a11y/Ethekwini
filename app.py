import streamlit as st
import pandas as pd
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

# show available sheets
cols = st.columns([1,3])
with cols[0]:
    st.sidebar.header("Data & Filters")
    sheet_choice = st.sidebar.selectbox("Main sheet to view", list(sheets.keys()), index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0)
    search_task = st.sidebar.text_input("Search Task name (contains)")
    date_from = st.sidebar.date_input("Start date from", value=None)
    date_to = st.sidebar.date_input("Due date to", value=None)
    show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

# show raw sheet data
st.sidebar.markdown("**Sheets in workbook:**")
for s in sheets:
    st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    # try to standardize datetime columns
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
        # try to apply to 'Start date' if exists
        if "Start date" in df_main.columns:
            df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to:
        if "Due date" in df_main.columns:
            df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]
    
    # Top KPIs (if Tasks sheet)
    if "Tasks" in sheets:
        st.subheader("Key Performance Indicators")
        tasks = sheets["Tasks"].copy()
        # parse dates
        for col in ["Start date","Due date","Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')
        total = len(tasks)
        completed = tasks['Progress'].str.lower().eq('completed').sum() if 'Progress' in tasks.columns else 0
        inprogress = tasks['Progress'].str.lower().eq('in progress').sum() if 'Progress' in tasks.columns else 0
        notstarted = tasks['Progress'].str.lower().eq('not started').sum() if 'Progress' in tasks.columns else 0
        overdue = ((tasks['Due date'] < pd.Timestamp.today()) & (~tasks['Progress'].str.lower().eq('completed'))).sum() if 'Due date' in tasks.columns and 'Progress' in tasks.columns else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tasks", total)
        k2.metric("Completed", completed)
        k3.metric("In Progress", inprogress)
        k4.metric("Overdue", int(overdue))

    st.markdown("----")
    st.subheader(f"List: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # If Tasks sheet selected, build the main dashboards
    if sheet_choice == "Tasks" or "Tasks" in sheets:
        tasks = sheets["Tasks"].copy()
        # standardize dates
        for col in ["Start date","Due date","Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

        st.subheader("Task Breakdown & Visuals")
        # Progress Distribution
        if 'Progress' in tasks.columns:
            fig1 = px.pie(tasks, names='Progress', title="Progress distribution", hole=0.3)
            st.plotly_chart(fig1, use_container_width=True)
        # Tasks per Bucket
        if 'Bucket Name' in tasks.columns:
            agg = tasks['Bucket Name'].value_counts().reset_index()
            agg.columns = ['Bucket Name','Count']
            fig2 = px.bar(agg, x='Bucket Name', y='Count', title="Tasks per Bucket")
            st.plotly_chart(fig2, use_container_width=True)
        # Priority distribution
        if 'Priority' in tasks.columns:
            fig3 = px.pie(tasks, names='Priority', title="Priority distribution")
            st.plotly_chart(fig3, use_container_width=True)

        # Overdue table
        if 'Due date' in tasks.columns and 'Progress' in tasks.columns:
            overdue_df = tasks[(tasks['Due date'] < pd.Timestamp.today()) & (tasks['Progress'].str.lower() != 'completed')]
            st.markdown("#### Overdue tasks")
            st.dataframe(overdue_df.sort_values('Due date').reset_index(drop=True).loc[:, ['Task Name','Bucket Name','Progress','Due date','Priority']].head(200))

        # Checklist completion parsing (if exists)
        if 'Completed Checklist Items' in tasks.columns:
    def to_pct(x):
        if pd.isna(x):
            return None
        parts = str(x).split('/')
        if len(parts) == 2:
            try:
                num, den = float(parts[0]), float(parts[1])
               return (num / den * 100) if den != 0 else None
            except:
                return None
        return None

    tasks['check_pct'] = tasks['Completed Checklist Items'].apply(to_pct)

        
        # Timeline chart (start -> due)
        if 'Start date' in tasks.columns and 'Due date' in tasks.columns:
            timeline = tasks.dropna(subset=['Start date','Due date']).copy()
            if not timeline.empty:
                # shorten task name for display
                timeline['task_short'] = timeline['Task Name'].astype(str).str.slice(0,60)
                fig4 = px.timeline(timeline, x_start="Start date", x_end="Due date", y="task_short", color="Bucket Name", title="Task timeline (Start -> Due)")
                fig4.update_yaxes(autorange="reversed")
                st.plotly_chart(fig4, use_container_width=True)

    # Offer download of the current sheet as CSV
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
