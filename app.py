# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

# ==========================================
# PAGE CONFIG
# ==========================================
st.set_page_config(
    page_title="eThekwini WS-7761 Smart Meter Project Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# CUSTOM STYLING
# ==========================================
st.markdown("""
    <style>
        .main {
            background-color: #f9fafc;
            padding: 1rem;
        }
        .title-text {
            font-size: 32px;
            font-weight: 700;
            color: #003366;
            margin-bottom: -5px;
        }
        .sub-text {
            font-size: 18px;
            color: #444;
            margin-bottom: 25px;
        }
        .metric-label {
            font-size: 18px;
            font-weight: 600;
            color: #003366;
        }
        .footer {
            font-size: 13px;
            text-align: center;
            color: #888;
            margin-top: 40px;
        }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# LOAD DATA
# ==========================================
def load_data(file):
    try:
        df = pd.read_excel(file)
        return df
    except Exception as e:
        st.error(f"❌ Failed to read Excel file: {e}")
        return pd.DataFrame()

uploaded_file = st.file_uploader("📤 Upload Weekly Update Sheet (.xlsx)", type=["xlsx"])
if uploaded_file is None:
    st.warning("Please upload the latest 'Weekly update sheet.xlsx' to view the dashboard.")
    st.stop()

df = load_data(uploaded_file)
if df.empty:
    st.stop()

# ==========================================
# TITLE + DATE
# ==========================================
st.markdown(f"""
<div class="title-text">📅 Data as of: {datetime.today().strftime('%d %B %Y')}</div>
<div class="sub-text">eThekwini WS-7761 Smart Meter Project</div>
""", unsafe_allow_html=True)

# ==========================================
# VALIDATE CONTRACTOR COLUMNS
# ==========================================
expected_contractors = ["Deezlo", "Nimba", "Isandiso"]
for col in expected_contractors:
    if col not in df.columns:
        st.error(f"Missing column in Excel: **{col}** — please verify your file headers.")
        st.stop()

# ==========================================
# KPI CARD HELPER
# ==========================================
def kpi_card(label, value, icon):
    st.markdown(f"""
        <div style="
            background: white;
            padding: 1rem;
            border-radius: 15px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            text-align: center;
        ">
            <div style="font-size: 28px; font-weight: bold; color: #003366;">{value}</div>
            <div style="font-size: 16px; color: #666;">{icon} {label}</div>
        </div>
    """, unsafe_allow_html=True)

# ==========================================
# INSTALLATION DIAL HELPER
# ==========================================
def create_installation_gauge(value, title, color):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': 18}},
        gauge={
            'axis': {'range': [0, max(1, df[expected_contractors].max().max())]},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 1,
            'bordercolor': "#ccc",
        }
    ))
    fig.update_layout(height=250, margin=dict(t=30, b=0, l=0, r=0))
    return fig

# ==========================================
# MAIN DASHBOARD
# ==========================================
st.markdown("## 🧰 Installations Overview")
st.caption("Below are the installation dials for each contractor based on the latest weekly update sheet.")

installed = df[expected_contractors].sum()

colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
cols = st.columns(3)

for i, col in enumerate(expected_contractors):
    with cols[i]:
        st.plotly_chart(create_installation_gauge(installed[col], f"{col} Installed", colors[i]), use_container_width=True)

# ==========================================
# KPI SECTION
# ==========================================
st.markdown("## 📊 Project KPIs")
total_installs = installed.sum()
avg_per_contractor = int(total_installs / len(expected_contractors))
remaining_target = max(0, 10000 - total_installs)

col1, col2, col3 = st.columns(3)
with col1:
    kpi_card("Total Installations", total_installs, "✅")
with col2:
    kpi_card("Avg per Contractor", avg_per_contractor, "📦")
with col3:
    kpi_card("Remaining Target", remaining_target, "🎯")

# ==========================================
# DOWNLOAD REPORT
# ==========================================
st.markdown("### 📥 Export Report")
output = BytesIO()
with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
    df.to_excel(writer, index=False, sheet_name="Installations")
st.download_button(
    label="⬇️ Download Excel Report",
    data=output.getvalue(),
    file_name="Installation_Report.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.markdown('<div class="footer">© 2025 Accucom Dashboard | Smart Meter Installations</div>', unsafe_allow_html=True)
