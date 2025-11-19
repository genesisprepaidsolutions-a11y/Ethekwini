import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Image, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# ===================== PAGE CONFIGURATION =====================
st.set_page_config(page_title="eThekwini WS-7761 Smart Meter Project", layout="wide")

# ===================== CUSTOM STYLE =====================
st.markdown(
    """
    <style>
    body {
        background-color: #f7f9fb;
        font-family: 'Segoe UI', sans-serif;
        color: #003366;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #f7f9fb;
        padding: 1rem 2rem;
    }
    [data-testid="stHeader"] {
        background: linear-gradient(90deg, #007acc 0%, #00b4d8 100%);
        color: white;
        font-weight: bold;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    }
    h1, h2, h3 {
        color: #003366 !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #eaf4ff;
        border-radius: 10px;
        padding: 10px 16px;
        color: #003366;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #007acc !important;
        color: white !important;
    }
    div[data-testid="stMarkdownContainer"] {
        color: #003366;
    }
    .metric-card {
        background-color: #eaf4ff;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
    }
    .dial-label {
        text-align: center;
        font-weight: 500;
        color: #003366;
        margin-top: -10px;
        margin-bottom: 20px;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
    }
    th {
        background-color: #007acc;
        color: white !important;
        text-align: center;
        padding: 8px;
    }
    td {
        padding: 6px;
        text-align: center;
    }
    tr:nth-child(even) {background-color: #f0f6fb;}
    tr:hover {background-color: #d6ecff;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ===================== INSTALLATIONS TAB =====================
with tabs[0]:
    st.subheader("📦 Installations Status")

    if not df_install.empty:
        st.markdown(f"Total Contractors: **{df_install.shape[0]}**")

        contractor_col = None
        status_col = None
        sites_col = None

        if "Contractor" in df_install.columns:
            contractor_col = "Contractor"
        if "Installed" in df_install.columns:
            status_col = "Installed"
        if "Sites" in df_install.columns:
            sites_col = "Sites"

        for c in df_install.columns:
            low = str(c).lower()
            if not contractor_col and ("contractor" in low or "installer" in low or "contractors" in low):
                contractor_col = c
            if not status_col and ("status" in low or "install" in low or "installed" in low or "complete" in low):
                status_col = c
            if not sites_col and ("site" in low or "sites" in low or "total" in low):
                sites_col = c

        if not status_col:
            for c in df_install.columns:
                low = str(c).lower()
                if "progress" in low or "state" in low:
                    status_col = c
                    break

        if not contractor_col:
            for c in df_install.columns:
                if df_install[c].dtype == object and not any(k in str(c).lower() for k in ["date"]):
                    contractor_col = c
                    break

        if contractor_col and status_col:
            st.markdown("### ⚙️ Contractor Installation Progress")

            if pd.api.types.is_numeric_dtype(df_install[status_col]) or df_install[status_col].dropna().apply(lambda x: str(x).replace('.','',1).isdigit()).all():
                if sites_col:
                    summary = df_install.groupby(contractor_col).agg(
                        Installed_Sites=(status_col, "sum"),
                        Total_Sites=(sites_col, "sum"),
                    ).reset_index()
                else:
                    summary = df_install.groupby(contractor_col).agg(
                        Installed_Sites=(status_col, "sum"),
                    ).reset_index()
                    summary["Total_Sites"] = summary["Installed_Sites"]
                summary = summary.rename(columns={"Installed_Sites": "Completed_Sites", "Total_Sites": "Total_Sites"})
            else:
                summary = (
                    df_install.assign(_is_completed=df_install[status_col].apply(lambda v: str(v).strip().lower() in ("completed","installed","complete","yes","done")))
                    .groupby(contractor_col)
                    .agg(Total_Sites=(status_col, "count"), Completed_Sites=("_is_completed", "sum"))
                    .reset_index()
                )

            def make_contractor_gauge(completed, total, title, dial_color="#007acc"):
                pct = (completed / total * 100) if total and total > 0 else 0
                fig = go.Figure(
                    go.Indicator(
                        mode="gauge+number",
                        value=pct,
                        number={"suffix": "%", "font": {"size": 8, "color": dial_color}},
                        title={"text": "", "font": {"size": 1, "color": dial_color}},
                        gauge={
                            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "gray"},
                            "bar": {"color": dial_color, "thickness": 0.3},
                            "bgcolor": "#f7f9fb",
                            "steps": [{"range": [0, 100], "color": "#e0e0e0"}],
                        },
                    )
                )
                fig.update_layout(height=200, margin=dict(l=5, r=5, t=5, b=5))
                return fig

            records = summary.to_dict("records")

            # 🚫 REMOVED TOP TILE BLOCK HERE 🚫

            for i in range(0, len(records), 3):
                cols = st.columns(3)
                for j, rec in enumerate(records[i : i + 3]):
                    completed = int(rec.get("Completed_Sites", 0) or 0)
                    total = int(rec.get("Total_Sites", 0) or 0)
                    pct = (completed / total * 100) if total > 0 else 0
                    if pct >= 90:
                        color = "#00b386"
                    elif pct >= 70:
                        color = "#007acc"
                    else:
                        color = "#e67300"
                    with cols[j]:
                        st.markdown("<div class='metric-card'>", unsafe_allow_html=True)

                        contractor_name_display = str(rec.get(contractor_col, "")).upper()
                        st.markdown(f"<div style='text-align:center; font-weight:700; color:#003366; margin-bottom:6px;'>{contractor_name_display}</div>", unsafe_allow_html=True)

                        st.plotly_chart(make_contractor_gauge(completed, total, "", dial_color=color), use_container_width=True)

                        st.markdown(
                            f"<div style='text-align:center; font-size:calc(14px + 1.4vw); font-weight:600; color:{color}; margin-top:-12px;'>{pct:.1f}%</div>",
                            unsafe_allow_html=True,
                        )

                        st.markdown(f"<div class='dial-label'>{completed} / {total} installs</div>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
