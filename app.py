# app.py - corrected Streamlit dashboard with analog-style gauges
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

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
def load_data(path: str = "Ethekwini WS-7761 07 Oct 2025.xlsx"):
    """
    Load all sheets from an Excel workbook into a dictionary of DataFrames.
    Returns empty dict if file not found or unreadable.
    """
    sheets = {}
    try:
        xls = pd.ExcelFile(path)
        for s in xls.sheet_names:
            try:
                df = pd.read_excel(xls, sheet_name=s)
                sheets[s] = df
            except Exception:
                sheets[s] = pd.DataFrame()
    except Exception:
        # file not found or invalid workbook -> return empty dict
        sheets = {}
    return sheets

# make sure we call load_data BEFORE we reference 'sheets'
sheets = load_data()

# ======================================================
#   SIDEBAR FILTERS
# ======================================================
st.sidebar.header("Data & Filters")
sheet_choice = st.sidebar.selectbox(
    "Main sheet to view",
    options=list(sheets.keys()) if sheets else ["No workbook loaded"],
    index=list(sheets.keys()).index("Tasks") if ("Tasks" in sheets) else 0
)

search_task = st.sidebar.text_input("Search Task name (contains)")
# Provide defaults to avoid Streamlit complaining about None default for date_input
date_from = st.sidebar.date_input("Start date from", value=datetime(2000, 1, 1))
date_to = st.sidebar.date_input("Due date to", value=datetime(2100, 12, 31))
show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

st.sidebar.markdown("**Sheets in workbook:**")
if sheets:
    for s in sheets:
        st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")
else:
    st.sidebar.write("- No workbook loaded or file not found")

df_main = sheets.get(sheet_choice, pd.DataFrame()).copy() if sheets else pd.DataFrame()

# ======================================================
#   MAIN CONTENT
# ======================================================

if df_main.empty:
    st.warning("Selected sheet is empty or workbook not loaded. Confirm the Excel file path and sheet names.")
else:
    # Standardize datetime columns where possible
    date_cols = [c for c in df_main.columns if "date" in c.lower()]
    for c in date_cols:
        try:
            df_main[c] = pd.to_datetime(df_main[c], dayfirst=True, errors='coerce')
        except Exception:
            pass

    # Apply filters safely
    if search_task and not df_main.empty:
        first_col = df_main.columns[0]
        df_main = df_main[df_main[first_col].astype(str).str.contains(search_task, case=False, na=False)]
    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

    # ======================================================
    #   KPIs + ANALOG-STYLE GAUGES (all dials under KPI header)
    # ======================================================
    # Ensure 'sheets' exists and contains the Tasks sheet before referencing
    if isinstance(sheets, dict) and "Tasks" in sheets:
        st.subheader("Key Performance Indicators")

        tasks = sheets["Tasks"].copy()
        # parse dates defensively
        for col in ["Start date", "Due date", "Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

        # Ensure Progress column exists and is string safe
        if 'Progress' not in tasks.columns:
            tasks['Progress'] = ""  # empty strings for safe comparisons
        else:
            tasks['Progress'] = tasks['Progress'].fillna("").astype(str)

        total = len(tasks)
        total_safe = max(total, 1)  # avoid zero-range in gauge axis

        completed = tasks['Progress'].str.lower().eq('completed').sum()
        inprogress = tasks['Progress'].str.lower().eq('in progress').sum()
        notstarted = tasks['Progress'].str.lower().eq('not started').sum()
        overdue = 0
        if 'Due date' in tasks.columns:
            overdue = ((tasks['Due date'] < pd.Timestamp.today()) & (~tasks['Progress'].str.lower().eq('completed'))).sum()

        # Define gauges with analog styling; overdue gets red accent
        gauges = [
            {"label": "Not Started", "value": notstarted, "color": "#5DADE2"},
            {"label": "In Progress", "value": inprogress, "color": "#2874A6"},
            {"label": "Completed", "value": completed, "color": "#1B4F72"},
            {"label": "Overdue", "value": overdue, "color": "#C0392B"},
        ]

        fig_gauges = go.Figure()

        # Build each gauge in a 4-column row
        for i, g in enumerate(gauges):
            # Use threshold line + bar + steps to emulate a needle + colored zones
            fig_gauges.add_trace(go.Indicator(
                mode="gauge+number",
                value=g["value"],
                title={'text': f"<b>{g['label']}</b>", 'font': {'size': 16, 'color': '#003366'}},
                number={'font': {'size': 20, 'color': '#003366'}},
                domain={'x': [i * 0.25, (i + 1) * 0.25], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [0, total_safe], 'tickwidth': 1, 'tickcolor': "#666", 'dtick': max(1, total_safe // 5)},
                    'bar': {'color': g["color"], 'thickness': 0.25},
                    'bgcolor': "white",
                    'borderwidth': 3,
                    'bordercolor': "#B0B0B0",
                    'steps': [
                        {'range': [0, total_safe * 0.6], 'color': '#E6F4FF'},   # safe zone - very light blue
                        {'range': [total_safe * 0.6, total_safe * 0.85], 'color': '#F7DC6F'},  # warning - yellow
                        {'range': [total_safe * 0.85, total_safe], 'color': '#F1948A'}  # critical - light red
                    ],
                    # threshold used to emulate needle tip / marker
                    'threshold': {
                        'line': {'color': "#2E4053", 'width': 4},
                        'thickness': 0.8,
                        'value': g["value"]
                    }
                }
            ))

        fig_gauges.update_layout(
            grid={'rows': 1, 'columns': 4},
            paper_bgcolor="white",
            plot_bgcolor="white",
            height=380,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(fig_gauges, use_container_width=True)

    # ======================================================
    #   SHEET PREVIEW
    # ======================================================
    st.markdown("----")
    st.subheader(f"Sheet: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    st.dataframe(df_main.head(200))

    # ======================================================
    #   ADDITIONAL VISUALS: Tasks per Bucket & Overdue table
    # ======================================================
    if isinstance(sheets, dict) and "Tasks" in sheets:
        tasks = sheets["Tasks"].copy()
        for col in ["Start date", "Due date", "Completed Date"]:
            if col in tasks.columns:
                tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

        if 'Bucket Name' in tasks.columns:
            agg = tasks['Bucket Name'].value_counts().reset_index()
            agg.columns = ['Bucket Name', 'Count']
            fig2 = go.Figure(data=go.Bar(x=agg['Bucket Name'], y=agg['Count'], marker_color='#4682B4'))
            fig2.update_layout(title="Tasks per Bucket", plot_bgcolor='white', paper_bgcolor='white', font_color='#003366')
            st.plotly_chart(fig2, use_container_width=True)

        if 'Due date' in tasks.columns and 'Progress' in tasks.columns:
            overdue_df = tasks[(tasks['Due date'] < pd.Timestamp.today()) & (tasks['Progress'].str.lower() != 'completed')]
            st.markdown("#### Overdue Tasks")
            show_cols = [c for c in ['Task Name', 'Bucket Name', 'Progress', 'Due date', 'Priority'] if c in overdue_df.columns]
            st.dataframe(overdue_df.sort_values('Due date').reset_index(drop=True).loc[:, show_cols].head(200))

    # ======================================================
    #   EXPORT
    # ======================================================
    st.markdown("---")
    st.subheader("Export")
    csv = df_main.to_csv(index=False).encode('utf-8')
    st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime='text/csv')
