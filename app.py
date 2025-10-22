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

