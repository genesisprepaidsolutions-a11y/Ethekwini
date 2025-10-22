import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title="Task Dashboard", layout="wide")

# ===================== FILE UPLOAD =====================
st.title("📊 Project Task Dashboard")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])
if uploaded_file:
    df_main = pd.read_excel(uploaded_file, sheet_name="Main Data")
    st.success("✅ File successfully loaded!")

    # ===================== KPI CALCULATIONS =====================
    total_tasks = len(df_main)
    completed_tasks = len(df_main[df_main["Progress"].str.lower() == "completed"])
    in_progress_tasks = len(df_main[df_main["Progress"].str.lower() == "in progress"])
    overdue_tasks = len(
        df_main[
            (df_main["Due date"] < pd.Timestamp.today())
            & (df_main["Progress"].str.lower() != "completed")
        ]
    )
    pending_tasks = total_tasks - completed_tasks - in_progress_tasks - overdue_tasks
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks else 0

    # ===================== COLOR FUNCTION =====================
    def create_colored_gauge(value, total, title, color):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value,
                number={
                    "suffix": "%",
                    "font": {"size": 30, "color": color}
                },
                title={
                    "text": title,
                    "font": {"size": 20, "color": color}
                },
                gauge={
                    "axis": {"range": [0, total], "tickwidth": 1, "tickcolor": "gray"},
                    "bar": {"color": color, "thickness": 0.3},
                    "bgcolor": "#f9f9f9",
                    "steps": [{"range": [0, total], "color": "#e0e0e0"}],
                },
            )
        )
        fig.update_layout(height=260, margin=dict(l=10, r=10, t=40, b=20))
        return fig

    # ===================== DIAL SECTION =====================
    st.markdown("### 🎯 Key Metrics Overview")

    dial_col1, dial_col2, dial_col3, dial_col4, dial_col5 = st.columns(5)
    with dial_col1:
        st.plotly_chart(
            create_colored_gauge(total_tasks, total_tasks, "Total Tasks", "#6A0DAD"),
            use_container_width=True,
        )
    with dial_col2:
        st.plotly_chart(
            create_colored_gauge(completed_tasks / total_tasks * 100 if total_tasks else 0, 100, "Completed", "#00cc66"),
            use_container_width=True,
        )
    with dial_col3:
        st.plotly_chart(
            create_colored_gauge(in_progress_tasks / total_tasks * 100 if total_tasks else 0, 100, "In Progress", "#0099ff"),
            use_container_width=True,
        )
    with dial_col4:
        st.plotly_chart(
            create_colored_gauge(overdue_tasks / total_tasks * 100 if total_tasks else 0, 100, "Overdue", "#ff9933"),
            use_container_width=True,
        )
    with dial_col5:
        st.plotly_chart(
            create_colored_gauge(pending_tasks / total_tasks * 100 if total_tasks else 0, 100, "Pending", "#ffcc00"),
            use_container_width=True,
        )

    # ===================== CHARTS =====================
    st.markdown("### 📅 Tasks Overview Charts")

    # Tasks per bucket
    bucket_counts = df_main["Bucket Name"].value_counts()
    fig_bucket = go.Figure(
        data=[
            go.Bar(
                x=bucket_counts.index,
                y=bucket_counts.values,
                marker_color="#336699",
                text=bucket_counts.values,
                textposition="outside",
            )
        ]
    )
    fig_bucket.update_layout(
        title="Tasks per Bucket",
        xaxis_title="Bucket Name",
        yaxis_title="Task Count",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_bucket, use_container_width=True)

    # Completed tasks over time
    completed_over_time = (
        df_main[df_main["Progress"].str.lower() == "completed"]
        .groupby("Completed Date")
        .size()
        .reset_index(name="Completed Tasks")
    )
    fig_time = go.Figure(
        data=[
            go.Scatter(
                x=completed_over_time["Completed Date"],
                y=completed_over_time["Completed Tasks"],
                mode="lines+markers",
                line=dict(width=3, color="#00cc66"),
            )
        ]
    )
    fig_time.update_layout(
        title="Completed Tasks Over Time",
        xaxis_title="Date",
        yaxis_title="Tasks Completed",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
    )
    st.plotly_chart(fig_time, use_container_width=True)

    # ===================== ADDITIONAL INSIGHTS =====================
    with st.expander("📈 Additional Insights", expanded=True):
        st.markdown("### Expanded Project Insights")

        # --- Average Task Duration ---
        df_duration = df_main.copy()
        df_duration = df_duration.replace("Null", None)
        df_duration["Start date"] = pd.to_datetime(df_duration["Start date"], errors="coerce")
        df_duration["Due date"] = pd.to_datetime(df_duration["Due date"], errors="coerce")
        df_duration["Duration"] = (df_duration["Due date"] - df_duration["Start date"]).dt.days
        avg_duration = df_duration["Duration"].mean()
        max_duration = df_duration["Duration"].max()
        gauge_max = min(max(30, (max_duration if pd.notna(max_duration) else 30)), 120)

        def create_duration_gauge(value, title, dial_color):
            val = 0 if pd.isna(value) else value
            pct = min(val / gauge_max * 100, 100)

            # Shorter = greener
            if val <= gauge_max * 0.3:
                gradient_color = "green"
            elif val <= gauge_max * 0.7:
                gradient_color = "yellow"
            else:
                gradient_color = "red"

            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=val,
                    number={"suffix": " days", "font": {"size": 30, "color": dial_color}},
                    title={"text": title, "font": {"size": 20, "color": dial_color}},
                    gauge={
                        "axis": {"range": [0, gauge_max], "tickwidth": 1, "tickcolor": "gray"},
                        "bar": {"color": gradient_color, "thickness": 0.3},
                        "bgcolor": "#f9f9f9",
                        "steps": [{"range": [0, gauge_max], "color": "#e0e0e0"}],
                    },
                )
            )
            fig.update_layout(height=270, margin=dict(l=15, r=15, t=40, b=20))
            return fig

        st.markdown("#### ⏱️ Average Task Duration")
        st.plotly_chart(
            create_duration_gauge(avg_duration if avg_duration else 0, "Average Task Duration", "#336699"),
            use_container_width=True,
        )

        # --- Priority Distribution ---
        priority_counts = df_main["Priority"].value_counts(normalize=True) * 100

        st.markdown("#### 🔰 Priority Distribution")
        cols = st.columns(2)
        priority_colors = ["#ff6600", "#0099cc", "#00cc66", "#cc3366"]
        for i, (priority, pct) in enumerate(priority_counts.items()):
            with cols[i % 2]:
                st.plotly_chart(
                    create_colored_gauge(pct, 100, f"{priority} Priority", priority_colors[i % len(priority_colors)]),
                    use_container_width=True,
                )

        # --- Phase Completion Dials ---
        st.markdown("#### 🧭 Phase Completion Dials")
        completion_by_bucket = (
            df_main.groupby("Bucket Name")["Progress"]
            .apply(lambda x: (x.str.lower() == "completed").mean() * 100)
            .reset_index()
            .rename(columns={"Progress": "Completion %"})
        )
        bucket_cols = st.columns(2)
        for i, row in enumerate(completion_by_bucket.itertuples()):
            with bucket_cols[i % 2]:
                st.plotly_chart(
                    create_colored_gauge(row._2, 100, row._1, "#006666"),
                    use_container_width=True,
                )

    # ===================== EXPORT SECTION =====================
    st.markdown("---")
    st.subheader("📤 Export Dashboard Data")
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="Task Data", index=False)
    st.download_button(
        label="⬇️ Download Full Excel Report",
        data=output.getvalue(),
        file_name="Dashboard_Export.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

else:
    st.info("👆 Please upload an Excel file to generate your dashboard.")
