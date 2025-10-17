import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="Ethekwini WS-7761 Dashboard",
    layout="wide"
)

# Apply white background styling
st.markdown("""
    <style>
        body, .stApp {
            background-color: white !important;
            color: #002B5B;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #003366;
        }
        .stMetricLabel, .stMarkdown, .stDataFrame {
            color: #003366;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center; color:#003366;'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)

# ======================================================
#   DATA LOADING
# ======================================================
@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=s)
            sheets[s] = df
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()

# ======================================================
#   SIDEBAR FILTERS
# ======================================================
st.sidebar.header("Data & Filters")
sheet_choice = st.sidebar.selectbox("Main sheet to view", list(sheets.keys()), 
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0)
search_task = st.sidebar.text_input("Search Task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)
show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

st.sidebar.markdown("**Sheets in workbook:**")
for s in sheets:
    st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

# ======================================================
#   MAIN CONTENT
# ======================================================
if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    # Parse datetime columns
    date_cols = [c for c in df_main.columns if "date" in c.lower()]
    for c in date_cols:
        try:
            df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors='coerce')
        except:
            pass

    # Apply filters
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]
    
    # ======================================================
    #   KPIs
    # ======================================================
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

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tasks", total)
        k2.metric("Completed", completed)
        k3.metric("In Progress", inprogress)
        k4.metric("Overdue", int(overdue))

    st.markdown("----")
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # ======================================================
    #   SPEEDOMETER DASHBOARD
    # ======================================================
    if sheet_choice == "Tasks" or "Tasks" in sheets:
        st.subheader("Task Progress Overview (Speedometers)")
        fig_gauges = go.Figure()

        # Gauge colors: light to dark blue
        colors = ['#A7C7E7', '#4682B4', '#003366']

        gauges = [
            {"label": "Not Started", "value": notstarted, "color": colors[0]},
            {"label": "In Progress", "value": inprogress, "color": colors[1]},
            {"label": "Completed", "value": completed, "color": colors[2]}
        ]

        for i, g in enumerate(gauges):
            fig_gauges.add_trace(go.Indicator(
                mode="gauge+number",
                value=g["value"],
                domain={'x': [i * 0.33, (i + 1) * 0.33], 'y': [0, 1]},
                title={'text': g["label"], 'font': {'size': 18, 'color': '#003366'}},
                gauge={
                    'axis': {'range': [0, total if total > 0 else 1], 'tickwidth': 1, 'tickcolor': "#003366"},
                    'bar': {'color': g["color"]},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#003366",
                    'steps': [
                        {'range': [0, total/2 if total > 0 else 1], 'color': '#E0ECF8'},
                        {'range': [total/2 if total > 0 else 1, total], 'color': '#C6DBEF'}
                    ],
                }
            ))

        fig_gauges.update_layout(
            grid={'rows': 1, 'columns': 3},
            template=None,
            paper_bgcolor="white",
            plot_bgcolor="white",
            height=400
        )
        st.plotly_chart(fig_gauges, use_container_width=True)

        # ======================================================
        #   OTHER CHARTS
        # ======================================================
        if 'Bucket Name' in tasks.columns:
            agg = tasks['Bucket Name'].value_counts().reset_index()
            agg.columns = ['Bucket Name', 'Count']
            fig2 = go.Figure(data=go.Bar(
                x=agg['Bucket Name'], 
                y=agg['Count'], 
                marker_color='#4682B4'
            ))
            fig2.update_layout(
                title="Tasks per Bucket",
                plot_bgcolor='white',
                paper_bgcolor='white',
                font_color='#003366'
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Overdue Tasks
        if 'Due date' in tasks.columns and 'Progress' in tasks.columns:
            overdue_df = tasks[(tasks['Due date'] < pd.Timestamp.today()) & (tasks['Progress'].str.lower() != 'completed')]
            st.markdown("#### Overdue Tasks")
            st.dataframe(overdue_df.sort_values('Due date').reset_index(drop=True).loc[:, 
                        ['Task Name', 'Bucket Name', 'Progress', 'Due date', 'Priority']].head(200))

    # ======================================================
    #   EXPORT
    # ======================================================
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
