import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

st.markdown("<h1 style='text-align:center'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)

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
cols = st.columns([1, 3])
with cols[0]:
    st.sidebar.header("Data & Filters")
    sheet_choice = st.sidebar.selectbox("Main sheet to view", list(sheets.keys()), index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0)
    search_task = st.sidebar.text_input("Search Task name (contains)")
    date_from = st.sidebar.date_input("Start date from", value=None)
    date_to = st.sidebar.date_input("Due date to", value=None)
    show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

st.sidebar.markdown("**Sheets in workbook:**")
for s in sheets:
    st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

# ======================================================
#   KPI GAUGE FUNCTION
# ======================================================
def create_gauge(title, value, max_value, colorscale, needle_color="#003366"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18, 'color': '#003366'}},
        number={'font': {'color': '#003366', 'size': 24}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': '#003366'},
            'bar': {'color': needle_color, 'thickness': 0.25},
            'bgcolor': 'white',
            'steps': [
                {'range': [0, max_value * 0.5], 'color': colorscale[0]},
                {'range': [max_value * 0.75, max_value], 'color': colorscale[1]},
            ],
        }
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=10),
        height=260,
        paper_bgcolor="white"
    )
    return fig

# ======================================================
#   KPI SECTION
# ======================================================
if not df_main.empty and "Tasks" in sheets:
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.plotly_chart(create_gauge("Not Started", notstarted, total, ["#00CC66", "#FF0000"]), use_container_width=True)
    with col2:
        st.plotly_chart(create_gauge("In Progress", inprogress, total, ["#FF0000", "#00CC66"]), use_container_width=True)
    with col3:
        st.plotly_chart(create_gauge("Completed", completed, total, ["#FF0000", "#00CC66"]), use_container_width=True)
    with col4:
        st.plotly_chart(create_gauge("Overdue", overdue, total, ["#FFFF00", "#FF0000"]), use_container_width=True)

# ======================================================
#   SHEET DISPLAY
# ======================================================
if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    st.markdown("----")
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # Export current sheet
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
