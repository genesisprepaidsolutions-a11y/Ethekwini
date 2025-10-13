import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# ======================================================
#   Ethekwini WS-7761 Dashboard
# ======================================================
st.set_page_config(page_title="Ethekwini WS-7761 Dashboard", layout="wide")


@st.cache_data
def load_data(path="Ethekwini WS-7761 07 Oct 2025.xlsx"):
    """Load all sheets from an Excel workbook into a dict of DataFrames."""
    xls = pd.ExcelFile(path)
    sheets = {}
    for s in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=s)
            sheets[s] = df
        except Exception:
            sheets[s] = pd.DataFrame()
    return sheets


# ======================================================
#   Load data and Sidebar filters
# ======================================================
sheets = load_data()

st.sidebar.header("Data & Filters")
sheet_choice = st.sidebar.selectbox(
    "Main sheet to view",
    list(sheets.keys()),
    index=list(sheets.keys()).index("Tasks") if "Tasks" in sheets else 0,
)
search_task = st.sidebar.text_input("Search Task name (contains)")
date_from = st.sidebar.date_input("Start date from", value=None)
date_to = st.sidebar.date_input("Due date to", value=None)
show_logo = st.sidebar.checkbox("Show logo (if file exists)", value=False)

st.sidebar.markdown("**Sheets in workbook:**")
for s in sheets:
    st.sidebar.write(f"- {s} ({sheets[s].shape[0]} rows)")


# ======================================================
#   Utility: convert common date-like columns
# ======================================================
def standardize_dates(df, cols=None):
    """Convert date-like columns to pandas datetime, dayfirst=True."""
    if cols is None:
        cols = [c for c in df.columns if "date" in c.lower()]
    for c in cols:
        if c in df.columns:
            try:
                df[c] = pd.to_datetime(df[c], dayfirst=True, errors="coerce")
            except Exception:
                pass
    return df


# ======================================================
#   Utility: row styling for overdue/completed highlighting
# ======================================================
def highlight_rows(row):
    """
    Return a list of CSS style strings for the given row:
    - Completed tasks -> light green background
    - Overdue (Due date < today and not completed) -> light red background
    - Otherwise -> no style
    """
    styles = [""] * len(row)
    # Quick guards
    if "Progress" not in row.index:
        return styles
    prog = str(row.get("Progress", "")).lower()
    # Completed (green)
    if prog == "completed":
        styles = ["background-color: #d4f4dd;"] * len(row)
        return styles
    # Overdue (red) - must have Due date column and be a real date
    due = row.get("Due date")
    if pd.notna(due):
        try:
            if pd.to_datetime(due) < pd.Timestamp.today():
                styles = ["background-color: #f8d7da;"] * len(row)
                return styles
        except Exception:
            pass
    return styles


# ======================================================
#   Header area with logo (centered above title)
# ======================================================
logo_path = "/mnt/data/deezlo.png"
logo_exists = os.path.exists(logo_path)

if logo_exists or show_logo:
    # Center the logo by placing it in the middle column
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        # width tuned to look good in most layouts; adjust if needed
        st.image(logo_path, use_column_width=False, width=420)

# Title (centered via markdown)
st.markdown("<h1 style='text-align:center'>Ethekwini WS-7761 Dashboard</h1>", unsafe_allow_html=True)


# ======================================================
#   Main: show selected sheet preview and dashboards
# ======================================================
df_main = sheets.get(sheet_choice, pd.DataFrame()).copy()

if df_main.empty:
    st.warning("Selected sheet is empty. Choose another sheet from the sidebar.")
else:
    df_main = standardize_dates(df_main)

    # ----------------------
    # Filters
    # ----------------------
    if search_task:
        # assume first column is the task name column if no explicit Task Name provided
        df_main = df_main[df_main[df_main.columns[0]].astype(str).str.contains(search_task, case=False, na=False)]

    if date_from and "Start date" in df_main.columns:
        df_main = df_main[df_main["Start date"] >= pd.to_datetime(date_from)]

    if date_to and "Due date" in df_main.columns:
        df_main = df_main[df_main["Due date"] <= pd.to_datetime(date_to)]

    # ----------------------
    # KPIs (if Tasks sheet exists)
    # ----------------------
    if "Tasks" in sheets:
        st.subheader("Key Performance Indicators")
        tasks = sheets["Tasks"].copy()
        tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

        total = len(tasks)
        completed = tasks["Progress"].str.lower().eq("completed").sum() if "Progress" in tasks.columns else 0
        inprogress = tasks["Progress"].str.lower().eq("in progress").sum() if "Progress" in tasks.columns else 0
        notstarted = tasks["Progress"].str.lower().eq("not started").sum() if "Progress" in tasks.columns else 0
        overdue = (
            ((tasks["Due date"] < pd.Timestamp.today()) & (~tasks["Progress"].str.lower().eq("completed")))
            .sum()
            if "Due date" in tasks.columns and "Progress" in tasks.columns
            else 0
        )

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Tasks", total)
        k2.metric("Completed", int(completed))
        k3.metric("In Progress", int(inprogress))
        k4.metric("Overdue", int(overdue))

    st.markdown("----")
    st.subheader(f"List: {sheet_choice} — Preview ({df_main.shape[0]} rows)")
    # show a basic preview (first 200 rows)
    st.dataframe(df_main.head(200))


    # ======================================================
    #   If Tasks sheet selected, build the Task Dashboards
    # ======================================================
    if sheet_choice == "Tasks" or "Tasks" in sheets:
        tasks = sheets["Tasks"].copy()
        tasks = standardize_dates(tasks, ["Start date", "Due date", "Completed Date"])

        # ----------------------
        # Task Breakdown & Visuals
        # ----------------------
        st.markdown(
            "############################################################\n"
            "#   TASK BREAKDOWN & VISUALS\n"
            "############################################################"
        )

        # Progress distribution
        if "Progress" in tasks.columns:
            fig1 = px.pie(tasks, names="Progress", title="Progress distribution", hole=0.3)
            st.plotly_chart(fig1, use_container_width=True)

        # Tasks per Bucket
        if "Bucket Name" in tasks.columns:
            agg = tasks["Bucket Name"].value_counts().reset_index()
            agg.columns = ["Bucket Name", "Count"]
            fig2 = px.bar(agg, x="Bucket Name", y="Count", title="Tasks per Bucket")
            st.plotly_chart(fig2, use_container_width=True)

        # Priority distribution
        if "Priority" in tasks.columns:
            fig3 = px.pie(tasks, names="Priority", title="Priority distribution")
            st.plotly_chart(fig3, use_container_width=True)

        # Overdue table (styled)
        if "Due date" in tasks.columns and "Progress" in tasks.columns:
            overdue_df = tasks[
                (tasks["Due date"] < pd.Timestamp.today()) & (tasks["Progress"].str.lower() != "completed")
            ].copy()
            st.markdown("#### Overdue tasks")
            if not overdue_df.empty:
                # apply row styling (red background intended)
                styled_overdue = overdue_df.style.apply(highlight_rows, axis=1)
                # Display with data_editor and styling (Streamlit may accept Styler)
                try:
                    st.data_editor(styled_overdue, use_container_width=True)
                except Exception:
                    # fallback to table if data_editor can't render styler objects
                    st.table(styled_overdue.to_html(), unsafe_allow_html=True)

        # Checklist percentage calculation (simple numeric conversion)
        st.markdown(
            "############################################################\n"
            "#   CHECKLIST PARSING\n"
            "############################################################"
        )
        if "Completed Checklist Items" in tasks.columns:
            def to_pct(x):
                if pd.isna(x):
                    return None
                parts = str(x).split("/")
                if len(parts) == 2:
                    try:
                        num, den = float(parts[0]), float(parts[1])
                        return num / den if den != 0 else None
                    except Exception:
                        return None
                return None

            tasks["check_pct"] = tasks["Completed Checklist Items"].apply(to_pct)

            # if you want to preview checklist completion with styling
            if tasks["check_pct"].notna().any():
                st.markdown("#### Checklist completion (task-level) — preview")
                try:
                    styled_check = tasks.loc[
                        :, ["Task Name", "Completed Checklist Items", "check_pct"]
                    ].style.apply(highlight_rows, axis=1)
                    st.data_editor(styled_check, use_container_width=True)
                except Exception:
                    st.dataframe(tasks.loc[:, ["Task Name", "Completed Checklist Items", "check_pct"]].head(200))

        # Timeline chart (start -> due)
        st.markdown(
            "############################################################\n"
            "#   TIMELINE\n"
            "############################################################"
        )
        if "Start date" in tasks.columns and "Due date" in tasks.columns:
            timeline = tasks.dropna(subset=["Start date", "Due date"]).copy()
            if not timeline.empty:
                timeline["task_short"] = timeline["Task Name"].astype(str).str.slice(0, 60)
                fig4 = px.timeline(
                    timeline,
                    x_start="Start date",
                    x_end="Due date",
                    y="task_short",
                    color="Bucket Name" if "Bucket Name" in timeline.columns else None,
                    title="Task timeline (Start -> Due)",
                )
                fig4.update_yaxes(autorange="reversed")
                st.plotly_chart(fig4, use_container_width=True)

        # Full Tasks view with highlighting (data_editor with row styling)
        st.markdown(
            "############################################################\n"
            "#   FULL TASKS VIEW\n"
            "############################################################"
        )
        full_tasks = tasks.copy().reset_index(drop=True)
        if not full_tasks.empty:
            try:
                styled_full = full_tasks.style.apply(highlight_rows, axis=1)
                st.data_editor(styled_full, use_container_width=True)
            except Exception:
                # fallback: show dataframe (without styling) if data_editor can't accept Styler
                st.dataframe(full_tasks.head(500))


# ======================================================
#   Export Section
# ======================================================
st.markdown("---")
st.subheader("Export")
csv = df_main.to_csv(index=False).encode("utf-8")
st.download_button("Download current view as CSV", csv, file_name=f"{sheet_choice}_export.csv", mime="text/csv")

