# ======================================================
#   KPI SECTION — Gradient-style semi-circular gauges
# ======================================================
if isinstance(sheets, dict) and "Tasks" in sheets:
    st.subheader("Key Performance Indicators")

    tasks = sheets["Tasks"].copy()
    for col in ["Start date", "Due date", "Completed Date"]:
        if col in tasks.columns:
            tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

    if 'Progress' not in tasks.columns:
        tasks['Progress'] = ""
    else:
        tasks['Progress'] = tasks['Progress'].fillna("").astype(str)

    total = len(tasks)
    total_safe = max(total, 1)

    completed = tasks['Progress'].str.lower().eq('completed').sum()
    inprogress = tasks['Progress'].str.lower().eq('in progress').sum()
    notstarted = tasks['Progress'].str.lower().eq('not started').sum()
    overdue = 0
    if 'Due date' in tasks.columns:
        overdue = ((tasks['Due date'] < pd.Timestamp.today()) & (~tasks['Progress'].str.lower().eq('completed'))).sum()

    # Calculate percentages for gradient display
    gauges = [
        {"label": "Not Started", "value": notstarted / total_safe * 100},
        {"label": "In Progress", "value": inprogress / total_safe * 100},
        {"label": "Completed", "value": completed / total_safe * 100},
        {"label": "Overdue", "value": overdue / total_safe * 100},
    ]

    # Create 4 gradient gauges in one row
    cols = st.columns(4)
    for i, g in enumerate(gauges):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=g["value"],
            number={'suffix': "%", 'font': {'size': 28, 'color': '#003366'}},
            title={'text': f"<b>{g['label']}</b>", 'font': {'size': 18, 'color': '#003366'}},
            gauge={
                'axis': {'range': [0, 100], 'visible': False},
                'bar': {'color': "black", 'thickness': 0.15},
                'bgcolor': "white",
                'steps': [
                    {'range': [0, 33], 'color': '#ff4d4d'},
                    {'range': [33, 66], 'color': '#ffd633'},
                    {'range': [66, 100], 'color': '#33cc33'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': g["value"]
                },
                'shape': "angular",
                'angle': 180  # makes it semi-circular
            }
        ))

        fig.update_layout(
            height=250,
            margin=dict(l=10, r=10, t=40, b=0),
            paper_bgcolor="white",
            font={'color': '#003366', 'family': "Arial"}
        )
        cols[i].plotly_chart(fig, use_container_width=True)
