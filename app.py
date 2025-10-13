# ======================================================
#   Deezlo Trading cc Dashboard – Streamlit App
# ======================================================

import streamlit as st
import pandas as pd
import os

# ======================================================
#   Page Config
# ======================================================
st.set_page_config(
    page_title="Ethekwini WS-7761 Dashboard",
    page_icon="📊",
    layout="wide",
)

# ======================================================
#   Header with Logo and Titles
# ======================================================
logo_path = "deezlo.png"  # Make sure this file is in the same folder or update the path

col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=160)
with col2:
    st.markdown("""
        <h1 style='margin-bottom:0; color:#F26522;'>Deezlo Trading cc</h1>
        <h4 style='margin-top:0; color:#FFFFFF; text-shadow:1px 1px 3px #000;'>You Dream it, We Build it</h4>
        <h2 style='margin-top:1em; text-align:left;'>Ethekwini WS-7761 Dashboard</h2>
    """, unsafe_allow_html=True)

st.markdown("---")

# ======================================================
#   Data Input Section
# ======================================================
st.header("📋 Project Overview")

with st.expander("Upload Project Data", expanded=True):
    uploaded_file = st.file_uploader("Upload your data file (Excel or CSV)", type=["xlsx", "csv"])
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.success("✅ File uploaded successfully!")
        st.dataframe(df)
    else:
        st.info("Please upload a project file to view data.")

st.markdown("---")

# ======================================================
#   Task Management Section
# ======================================================
st.header("✅ Tasks")

with st.expander("Add / Manage Tasks", expanded=True):
    st.text_input("Task Name", placeholder="Enter a new task")
    st.text_area("Task Description", placeholder="Add task details here...")
    st.selectbox("Task Status", ["Pending", "In Progress", "Completed"])
    st.date_input("Due Date")
    st.button("Add Task")

# Placeholder Task DataFrame
task_data = {
    "Task": ["Meter Installation", "Site Survey", "Quality Check"],
    "Status": ["Completed", "In Progress", "Pending"],
    "Due Date": ["2025-10-01", "2025-10-15", "2025-10-20"],
}
tasks_df = pd.DataFrame(task_data)

st.dataframe(tasks_df, use_container_width=True)

st.markdown("---")

# ======================================================
#   Reports / Charts
# ======================================================
st.header("📈 Progress Overview")

colA, colB = st.columns(2)

with colA:
    st.subheader("Project Summary")
    st.metric(label="Total Tasks", value=len(tasks_df))
    st.metric(label="Completed", value=(tasks_df['Status'] == "Completed").sum())
    st.metric(label="In Progress", value=(tasks_df['Status'] == "In Progress").sum())
    st.metric(label="Pending", value=(tasks_df['Status'] == "Pending").sum())

with colB:
    st.subheader("Completion Rate")
    completed = (tasks_df['Status'] == "Completed").sum()
    total = len(tasks_df)
    completion_rate = int((completed / total) * 100)
    st.progress(completion_rate / 100)
    st.write(f"{completion_rate}% Complete")

st.markdown("---")

# ======================================================
#   Footer
# ======================================================
st.markdown("""
    <div style='text-align:center; color:gray; font-size:13px; margin-top:40px;'>
        © 2025 Deezlo Trading cc | Ethekwini WS-7761 | All Rights Reserved
    </div>
""", unsafe_allow_html=True)
