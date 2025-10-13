import os
import time
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
#   PAGE CONFIGURATION
# ======================================================
st.set_page_config(
    page_title="Ethekwini WS-7761 Dashboard",
    layout="wide",
    page_icon="📊"
)

# ======================================================
#   CSS / STYLING (BRAND + ANIMATIONS + LOADING OVERLAY)
# ======================================================
st.markdown(
    """
    <style>
    /* Global Background - Brightened Glass Look */
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #1a1a1a, #232323, #1b1b1b) !important;
        color: #f5f5f5 !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #202020, #181818) !important;
        border-right: 2px solid #F26522;
        box-shadow: 2px 0 15px rgba(242,101,34,0.3);
    }
    [data-testid="stHeader"], [data-testid="stToolbar"] {
        background: rgba(25,25,25,0.9) !important;
        backdrop-filter: blur(12px);
        border-bottom: 1px solid #F26522;
    }
    /* Typography Enhancements */
    h1, h2, h3, h4, h5, h6, label {
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }
    p, span, div, td, th {
        color: #e6e6e6 !important;
    }
    /* Metric Glass Cards (Enhanced Glow + Color Pop) */
    .metric-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02));
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 6px 25px rgba(242,101,34,0.25);
        border: 1px solid rgba(242,101,34,0.3);
        backdrop-filter: blur(14px);
        transition: all 0.35s ease-in-out;
    }
    .metric-card.glow {
        animation: pulseGlow 2s infinite;
    }
    @keyframes pulseGlow {
        0% { box-shadow: 0 6px 18px rgba(242,101,34,0.12); transform: translateY(0); }
        50% { box-shadow: 0 14px 40px rgba(242,101,34,0.25); transform: translateY(-4px); }
        100% { box-shadow: 0 6px 18px rgba(242,101,34,0.12); transform: translateY(0); }
    }
    /* Divider Styling */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(to right, transparent, #F26522, transparent);
        margin-top: 30px;
        margin-bottom: 30px;
    }
    /* Fade Animations */
    @keyframes fadeIn {
        0% {opacity: 0; transform: translateY(10px);}
        100% {opacity: 1; transform: translateY(0);}
    }
    .fade-in {
        animation: fadeIn 0.9s ease-in-out;
    }
    /* Buttons */
    .stDownloadButton > button {
        background: linear-gradient(90deg, #F26522, #ff944d) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(242,101,34,0.3);
        transition: all 0.3s ease-in-out;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(90deg, #ff944d, #F26522) !important;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(242,101,34,0.5);
    }
    /* DataFrame Styling */
    .stDataFrame {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 20px rgba(255,255,255,0.05);
    }
    /* Loading overlay */
    .deezlo-loading {
        position: fixed;
        z-index: 9999;
        left: 0; top: 0; right: 0; bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(180deg, rgba(10,10,10,0.8), rgba(10,10,10,0.95));
        backdrop-filter: blur(6px);
    }
    .loading-box {
        text-align: center;
        padding: 30px 40px;
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
    }
    .deezlo-logo {
        font-weight: 800;
        color: #F26522;
        font-size: 36px;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .deezlo-tag {
        color: #ffffff;
        margin-bottom: 12px;
        font-size: 14px;
    }
    .loading-dots span {
        display: inline-block;
        width: 10px;
        height: 10px;
        margin: 0 6px;
        background: #F26522;
        border-radius: 50%;
        animation: dots 1s infinite;
    }
    .loading-dots span:nth-child(2){ animation-delay: 0.15s;}
    .loading-dots span:nth-child(3){ animation-delay: 0.30s;}
    @keyframes dots {
        0% { transform: translateY(0); opacity: 0.6;}
        50% { transform: translateY(-8px); opacity: 1;}
        100% { transform: translateY(0); opacity: 0.6;}
    }
    /* Sidebar Headers */
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
        color: #F26522 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ======================================================
#   Helper: Show & hide loading overlay (HTML placed in a placeholder)
# ======================================================
def show_loading_overlay(placeholder, message="Loading data..."):
    html = f"""
    <div class="deezlo-loading">
      <div class="loading-box">
        <div class="deezlo-logo">DEEZLO</div>
        <div class="deezlo-tag">You Dream It, We Build It</div>
        <div style="margin-top:8px; margin-bottom:8px; color:#e6e6e6;">{message}</div>
        <div class="loading-dots"><span></span><span></span><span></span></div>
      </div>
    </div>
    """
    placeholder.markdown(html, unsafe_allow_html=True)

# ======================================================
#   Sidebar: Options (animations on/off) and file path
# ======================================================
st.sidebar.header("Configuration")
enable_animations = st.sidebar.checkbox("Enable animations & loading screens", value=True)
st.sidebar.markdown("---")
st.sidebar.header("Data source")
excel_path = st.sidebar.text_input("Excel file path", value="Ethekwini WS-7761 07 Oct 2025.xlsx")

# ======================================================
#   LOAD EXCEL DATA (with overlay/spinner)
# ======================================================
@st.cache_data
def _read_excel_all_sheets(path):
    """Load all sheets from Excel file into dictionary of DataFrames."""
    xls = pd.ExcelFile(path)
    data = {}
    for sheet in xls.sheet_names:
        try:
            data[sheet] = pd.read_excel(xls, sheet_name=sheet)
        except Exception:
            data[sheet] = pd.DataFrame()
    return data

sheets = {}
loading_placeholder = st.empty()
try:
    if enable_animations:
        show_loading_overlay(loading_placeholder, message="Importing Excel — building visuals...")
        # small pause to allow overlay to render (non-blocking UI update)
        time.sleep(0.35)

    # attempt to load
    if not os.path.exists(excel_path):
        # if file not found, show message but don't crash
        loading_placeholder.empty()
        st.error(f"Excel file not found at: {excel_path}")
        st.stop()

    sheets = _read_excel_all_sheets(excel_path)

except Exception as e:
    loading_placeholder.empty()
    st.error(f"Failed to load file: {e}")
    st.stop()
finally:
    # remove overlay after load
    loading_placeholder.empty()

# ======================================================
#   SIDEBAR: Data & Filters
# ======================================================
st.sidebar.header("📁 Data & Filters")
if not sheets:
    st.warning("No data loaded. Ensure the Excel file is available.")
    st.stop()

sheet_choice = st.sidebar.selectbox(
    "Select main sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0
)
search_task = st.sidebar.text_input("Search task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)

st.sidebar.markdown("### Sheets Loaded:")
for name, df in sheets.items():
    st.sidebar.write(f"- {name} ({df.shape[0]} rows)")

# ======================================================
#   HELPER FUNCTIONS
# ======================================================
def standardize_dates(df, cols=None):
    if cols is None:
        cols = [c for c in df.columns if "date" in c.lower()]
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    return df

def safe_str(x):
    return "" if pd.isna(x) else str(x)

# ======================================================
#   COMPANY HEADER (DEEZLO BRANDING)
# ======================================================
logo_path_local = "/mnt/data/deezlo.png"
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    if os.path.exists(logo_path_local):
        st.image(logo_path_local, width=420)
    st.markdown("""
        <div class="fade-in">
            <h1 style='text-align:center; color:#F26522; margin-bottom:0;'>DEEZLO TRADING CC</h1>
            <h4 style='text-align:center; margin-top:0; color:#FFFFFF; letter-spacing:1px;'>You Dream It, We Build It</h4>
            <h2 style='text-align:center; margin-top:2rem; color:#F26522; text-shadow:0 0 10px rgba(242,101,34,0.6);'>
                Ethekwini WS-7761 Dashboard
            </h2>
        </div>
    """, unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   MAIN DATA LOAD & FILTERS
# ======================================================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()
if df_main.empty:
    st.warning("Selected sheet is empty.")
    st.stop()

df_main = standardize_dates(df_main)

# Apply filters
if search_task:
    first_col = df_main.columns[0]
    df_main = df_main[df_main[first_col].astype(str).str.contains(search_task, case=False, na=False)]
if date_from and "Start date" in df_main.columns:
    df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]
if date_to and "Due date" in df_main.columns:
    df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

# ======================================================
#   KPI SECTION (Brighter + Animated conditional on toggle)
# ======================================================
if "Tasks" in sheets:
    st.markdown("<div class='fade-in'><h3>📈 Key Performance Indicators</h3></div>", unsafe_allow_html=True)
    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

    total = len(tasks)
    completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
    inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
    overdue = (
        ((tasks["Due date"] < pd.Timestamp.today()) &
         (~tasks["Progress"].str.lower().eq("completed"))).sum()
        if "Due date" in tasks.columns and "Progress" in tasks.columns else 0
    )

    glow_class = "glow" if enable_animations else ""
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"<div class='metric-card {glow_class} fade-in'><h4>Total Tasks</h4><h2 style='color:#F26522;'>{total}</h2></div>", unsafe_allow_html=True)
    with k2:
        st.markdown(f"<div class='metric-card {glow_class} fade-in'><h4>Completed</h4><h2 style='color:#00FF99;'>{completed}</h2></div>", unsafe_allow_html=True)
    with k3:
        st.markdown(f"<div class='metric-card {glow_class} fade-in'><h4>In Progress</h4><h2 style='color:#FFD700;'>{inprogress}</h2></div>", unsafe_allow_html=True)
    with k4:
        st.markdown(f"<div class='metric-card {glow_class} fade-in'><h4>Overdue</h4><h2 style='color:#FF6347;'>{overdue}</h2></div>", unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# ======================================================
#   DATA PREVIEW
# ======================================================
st.markdown("<div class='fade-in'><h3>📋 Data Preview</h3></div>", unsafe_allow_html=True)
st.dataframe(df_main.head(200))

# ======================================================
#   DASHBOARDS (Vibrant Colour Palette + hover templates + transitions)
# ======================================================
bright_colors = ["#FFA500", "#00FF99", "#FFD700", "#00BFFF", "#FF69B4", "#FF4500"]

if "Tasks" in sheets:
    # show small overlay while building charts if animations enabled
    chart_placeholder = st.empty()
    if enable_animations:
        show_loading_overlay(chart_placeholder, message="Rendering charts...")
        time.sleep(0.25)

    st.markdown("<div class='fade-in'><h3>📊 Task Analytics</h3></div>", unsafe_allow_html=True)
    tasks = sheets["Tasks"].copy()
    tasks = standardize_dates(tasks)

    # Progress pie with hover template
    if "Progress" in tasks.columns:
        try:
            fig = px.pie(tasks, names="Progress", hole=0.35,
                         title="Progress Distribution", color_discrete_sequence=bright_colors)
            # hover and trace aesthetics
            fig.update_traces(textinfo="percent+label",
                              hovertemplate="%{label}<br>Count: %{value}<extra></extra>",
                              marker=dict(line=dict(color="rgba(255,255,255,0.85)", width=1.5)))
            fig.update_layout(paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
                              font_color="white", transition=dict(duration=700, easing="cubic-in-out"))
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.error("Failed to render Progress chart")

    # Tasks per Bucket (bar) with hover details
    if "Bucket Name" in tasks.columns:
        agg = tasks["Bucket Name"].value_counts().reset_index()
        agg.columns = ["Bucket Name", "Count"]
        try:
            fig2 = px.bar(agg, x="Bucket Name", y="Count", color="Bucket Name",
                          color_discrete_sequence=bright_colors, title="Tasks per Bucket")
            fig2.update_traces(marker_line_width=1.5,
                               hovertemplate="Bucket: %{x}<br>Count: %{y}<extra></extra>")
            fig2.update_layout(paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
                               font_color="white", transition=dict(duration=700, easing="cubic-in-out"))
            st.plotly_chart(fig2, use_container_width=True)
        except Exception:
            st.error("Failed to render Bucket chart")

    # Priority distribution with hover
    if "Priority" in tasks.columns:
        try:
            fig3 = px.pie(tasks, names="Priority", title="Priority Distribution", color_discrete_sequence=bright_colors)
            fig3.update_traces(textinfo="label+percent",
                               hovertemplate="%{label}<br>Count: %{value}<extra></extra>",
                               marker=dict(line=dict(color="rgba(255,255,255,0.85)", width=1.2)))
            fig3.update_layout(paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
                               font_color="white", transition=dict(duration=700, easing="cubic-in-out"))
            st.plotly_chart(fig3, use_container_width=True)
        except Exception:
            st.error("Failed to render Priority chart")

    # Timeline (Gantt-like) with hover detail
    if {"Start date", "Due date", "Task Name"}.issubset(tasks.columns):
        timeline = tasks.dropna(subset=["Start date", "Due date", "Task Name"]).copy()
        if not timeline.empty:
            try:
                # plotly timeline
                fig4 = px.timeline(timeline, x_start="Start date", x_end="Due date", y="Task Name",
                                   color="Bucket Name" if "Bucket Name" in timeline.columns else None,
                                   color_discrete_sequence=bright_colors, title="Task Timeline (Start to Due)")
                fig4.update_yaxes(autorange="reversed")
                # craft hovertemplate to show task + dates + progress
                hover_texts = []
                for _, r in timeline.iterrows():
                    progress = safe_str(r.get("Progress", ""))
                    bucket = safe_str(r.get("Bucket Name", ""))
                    hover_texts.append(f"{safe_str(r.get('Task Name',''))}<br>Bucket: {bucket}<br>Progress: {progress}<br>Start: {safe_str(r.get('Start date',''))}<br>Due: {safe_str(r.get('Due date',''))}")
                fig4.update_traces(hovertemplate="%{customdata}<extra></extra>",
                                   customdata=hover_texts,
                                   selector=dict(type="bar"))
                fig4.update_layout(paper_bgcolor="#1b1b1b", plot_bgcolor="#1b1b1b",
                                   font_color="white", transition=dict(duration=800, easing="cubic-in-out"))
                st.plotly_chart(fig4, use_container_width=True)
            except Exception:
                st.error("Failed to render Timeline chart")

    # remove small chart overlay
    if enable_animations:
        time.sleep(0.12)
        chart_placeholder.empty()

# ======================================================
#   EXPORT SECTION
# ======================================================
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("<div class='fade-in'><h3>📤 Export Data</h3></div>", unsafe_allow_html=True)

csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download current view as CSV",
    csv,
    file_name=f"{sheet_choice}_export.csv",
    mime="text/csv"
)
