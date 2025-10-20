import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")

# ======================================================
#   LOAD & DISPLAY LOGO IN TOP-RIGHT
# ======================================================
LOGO_PATH = "ethekwini_logo.png"

# Use absolute positioning with HTML to float top-right
if os.path.exists(LOGO_PATH):
    st.markdown(
        f"""
        <style>
            .top-right-logo {{
                position: absolute;
                top: 10px;
                right: 10px;
            }}
        </style>
        <div class="top-right-logo">
            <img src="data:image/png;base64,{open(LOGO_PATH, "rb").read().encode('base64').decode()}" width="120">
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("⚠️ Logo not found: 'ethekwini_logo.png'. Place it in the same folder as this script.")

# ======================================================
#   TITLE
# ======================================================
st.markdown("<h1 style='text-align: center; color: #0A3D91;'>Ethekwini WS-7761</h1>", unsafe_allow_html=True)

# ======================================================
#   SAMPLE CONTENT BELOW (REPLACE WITH YOUR VISUALS)
# ======================================================

st.write("")

# Example DataFrame Display (Placeholder)
data = {
    "Task": ["Plumbing Fix", "Electrical Check", "Inspection"],
    "Status": ["Completed", "In Progress", "Pending"],
    "Due Date": ["2025-10-20", "2025-10-22", "2025-10-25"]
}
df = pd.DataFrame(data)

st.subheader("Task Overview")
st.dataframe(df, use_container_width=True)

# Example Chart (Blue Theme)
fig = px.bar(df, x="Task", y=[1, 2, 3], title="Sample Progress", color_discrete_sequence=["#1E88E5"])
st.plotly_chart(fig, use_container_width=True)
