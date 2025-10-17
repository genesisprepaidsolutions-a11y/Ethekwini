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
        except Exception as e:
            sheets[s] = pd.DataFrame()
    return sheets

sheets = load_data()

# ======================================================
#   SIDEBAR
# ======================================================
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
def create_gauge(title, value, max_value, gradient_colors, needle_color="#002B5B"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18, 'color': '#002B5B'}},
        number={'font': {'color': '#002B5B', 'size': 22}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1, 'tickcolor': '#002B5B'},
            'bar': {'color': needle_color, 'thickness': 0.25},
            'bgcolor': 'white',
            'steps': [
                {'range': [0, max_value * 0.33], 'color': gradient_colors[0]},
                {'range': [max_value * 0.33, max_value * 0.66], 'color': gradient_colors[1]},
                {'range': [max_value * 0.66, max_value], 'color': gradient_colors[2]},
            ],
        }
    ))
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        height=250,
        paper_bgcolor="white"
    )
    return fig

# ======================================================
#   MAIN SECTION
# ======================================================
if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from sidebar.")
else:
    # Date normalization
    date_cols = [c for c in df_main.columns if "date" in c.lower()]
    for c in date_cols:
        try:
            df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors='coerce')
        except:
            pass

    # Filters
    if search_task:
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

    # ======================================================
    #   KPI SECTION
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
        with k1:
            st.plotly_chart(create_gauge("Not Started", notstarted, total, ["#00FF00", "#FFFF00", "#FF0000"]), use_container_width=True)
        with k2:
            st.plotly_chart(create_gauge("In Progress", inprogress, total, ["#FF0000", "#FFFF00", "#00FF00"]), use_container_width=True)
        with k3:
            st.plotly_chart(create_gauge("Completed", completed, total, ["#FF0000", "#FFFF00", "#00FF00"]), use_container_width=True)
        with k4:
            st.plotly_chart(create_gauge("Overdue", overdue, total, ["#FFFF00", "#FF0000", "#8B0000"]), use_container_width=True)

    # ======================================================
    #   MAIN SHEET PREVIEW
    # ======================================================
    st.markdown("----")
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # ======================================================
    #   EXPORT SECTION
    # ======================================================
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
