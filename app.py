\import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="WS7761 Smart Meter Project Status",
    layout="wide",
)

# ======================================================
#   CUSTOM CSS STYLING
# ======================================================
st.markdown("""
    <style>
    /* General background and text colors */
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }

    /* Header layout */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        background: linear-gradient(to right, #1c1f26, #272b33);
        padding: 15px 25px;
        border-radius: 12px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.3);
    }

    .header-container img {
        height: 60px;
        margin-right: 20px;
    }

    .header-container h1 {
        color: #f5f5f5;
        font-size: 28px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    /* KPI styling */
    .kpi-box {
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.2);
        font-size: 18px;
        font-weight: bold;
        color: #ffffff;
    }

    .not-started { background: linear-gradient(45deg, green, yellow, red); }
    .in-progress { background: linear-gradient(45deg, red, yellow, green); }
    .completed { background: linear-gradient(45deg, red, yellow, green); }
    .overdue { background: linear-gradient(45deg, yellow, red, darkred); }

    </style>
""", unsafe_allow_html=True)

# ======================================================
#   HEADER SECTION
# ======================================================
header_html = f"""
    <div class="header-container">
        <img src="data:image/png;base64,{st.image("ethekwini_logo.png", use_column_width=False)}" alt="Logo">
        <h1>WS7761 Smart Meter Project Status</h1>
    </div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ======================================================
#   DATA UPLOAD / LOAD
# ======================================================
st.sidebar.header("Upload Data")
uploaded_file = st.sidebar.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    st.warning("Please upload a data file to continue.")
    st.stop()

# ======================================================
#   KPI SECTION
# ======================================================
st.subheader("Project KPI Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown('<div class="kpi-box not-started">Not Started<br><br>12</div>', unsafe_allow_html=True)
with col2:
    st.markdown('<div class="kpi-box in-progress">In Progress<br><br>25</div>', unsafe_allow_html=True)
with col3:
    st.markdown('<div class="kpi-box completed">Completed<br><br>43</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="kpi-box overdue">Overdue<br><br>5</div>', unsafe_allow_html=True)

# ======================================================
#   DATA VISUALIZATION SECTION
# ======================================================
st.subheader("Performance Analytics")

if "Status" in df.columns:
    status_count = df["Status"].value_counts().reset_index()
    status_count.columns = ["Status", "Count"]

    fig = px.bar(
        status_count,
        x="Status",
        y="Count",
        text="Count",
        color="Status",
        title="Project Task Status Overview",
        color_discrete_sequence=px.colors.qualitative.Dark24,
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No 'Status' column found in the uploaded data.")

# ======================================================
#   FOOTER SECTION
# ======================================================
st.markdown("""
    <hr style="border: 0.5px solid #444;">
    <div style="text-align:center; color:gray;">
        © 2025 Ethekwini Smart Meter Dashboard | Powered by Acucomm Consulting
    </div>
""", unsafe_allow_html=True)
