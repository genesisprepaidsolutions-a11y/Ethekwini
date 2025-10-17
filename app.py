# ======================================================
#   BLUE VISUALS (REPLACED PIE WITH 3 DIALS)
# ======================================================
blue_palette = px.colors.sequential.Blues

if "Tasks" in sheets:
    st.subheader("📊 Task Analytics")
    tasks = standardize_dates(sheets["Tasks"].copy())

    # Prepare progress counts
    if "Progress" in tasks.columns:
        prog = tasks["Progress"].fillna("").astype(str).str.lower().str.strip()
        completed_count = prog.eq("completed").sum()
        inprogress_count = prog.eq("in progress").sum()
        not_started_count = prog.isin(["to do", "pending", "to-do", "pending "]).sum()
        total_count = completed_count + inprogress_count  # ✅ exclude not started
    else:
        completed_count = inprogress_count = total_count = 0

    # Avoid division by zero
    axis_max = total_count if total_count > 0 else 1

    colors = {
        "inprogress": "yellow",
        "completed": "green"
    }

    # Only two dials now: In Progress and Completed
    gauge_inprogress = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=inprogress_count,
            number={'suffix': f" / {axis_max}"},
            title={'text': "In Progress", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, axis_max], 'tickmode': 'linear'},
                'bar': {'color': colors["inprogress"]},
                'steps': [
                    {'range': [0, axis_max * 0.5], 'color': "#fff9e6"},
                    {'range': [axis_max * 0.5, axis_max * 0.8], 'color': "#fff2cc"},
                    {'range': [axis_max * 0.8, axis_max], 'color': "#ffe699"},
                ],
                'threshold': {
                    'line': {'color': 'orange', 'width': 4},
                    'thickness': 0.75,
                    'value': inprogress_count
                }
            }
        )
    )
    gauge_inprogress.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)

    gauge_completed = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=completed_count,
            number={'suffix': f" / {axis_max}"},
            title={'text': "Completed", 'font': {'size': 14}},
            gauge={
                'axis': {'range': [0, axis_max], 'tickmode': 'linear'},
                'bar': {'color': colors["completed"]},
                'steps': [
                    {'range': [0, axis_max * 0.5], 'color': "#e6ffe6"},
                    {'range': [axis_max * 0.5, axis_max * 0.8], 'color': "#ccffcc"},
                    {'range': [axis_max * 0.8, axis_max], 'color': "#99ff99"},
                ],
                'threshold': {
                    'line': {'color': 'green', 'width': 4},
                    'thickness': 0.75,
                    'value': completed_count
                }
            }
        )
    )
    gauge_completed.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=300)

    # Display two gauges instead of three
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(gauge_inprogress, use_container_width=True)
    with g2:
        st.plotly_chart(gauge_completed, use_container_width=True)
