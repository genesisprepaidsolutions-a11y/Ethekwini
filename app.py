# ======================================================
#   KPIs + ANALOG-STYLE GAUGES
# ======================================================
if "Tasks" in sheets:
    st.subheader("Key Performance Indicators")

    tasks = sheets["Tasks"].copy()
    for col in ["Start date", "Due date", "Completed Date"]:
        if col in tasks.columns:
            tasks[col] = pd.to_datetime(tasks[col], dayfirst=True, errors='coerce')

    total = len(tasks)
    completed = tasks['Progress'].str.lower().eq('completed').sum() if 'Progress' in tasks.columns else 0
    inprogress = tasks['Progress'].str.lower().eq('in progress').sum() if 'Progress' in tasks.columns else 0
    notstarted = tasks['Progress'].str.lower().eq('not started').sum() if 'Progress' in tasks.columns else 0
    overdue = ((tasks['Due date'] < pd.Timestamp.today()) & (~tasks['Progress'].str.lower().eq('completed'))).sum() if 'Due date' in tasks.columns and 'Progress' in tasks.columns else 0

    gauges = [
        {"label": "Not Started", "value": notstarted, "color": "#5DADE2"},
        {"label": "In Progress", "value": inprogress, "color": "#2874A6"},
        {"label": "Completed", "value": completed, "color": "#1B4F72"},
        {"label": "Overdue", "value": overdue, "color": "#C0392B"},
    ]

    fig_gauges = go.Figure()

    for i, g in enumerate(gauges):
        fig_gauges.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=g["value"],
            title={'text': f"<b>{g['label']}</b>", 'font': {'size': 18, 'color': '#003366'}},
            number={'font': {'size': 20, 'color': '#003366'}},
            domain={'x': [i * 0.25, (i + 1) * 0.25], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, max(total, 1)], 'tickwidth': 1, 'tickcolor': "#666"},
                'bar': {'color': g["color"], 'thickness': 0.25},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "#B0B0B0",
                'steps': [
                    {'range': [0, total * 0.5 if total else 1], 'color': '#E0F3FF'},
                    {'range': [total * 0.5 if total else 1, total * 0.8 if total else 1], 'color': '#F7DC6F'},
                    {'range': [total * 0.8 if total else 1, total], 'color': '#F1948A'}
                ],
                'threshold': {
                    'line': {'color': "#2E4053", 'width': 4},
                    'thickness': 0.75,
                    'value': g["value"]
                }
            }
        ))

    fig_gauges.update_layout(
        grid={'rows': 1, 'columns': 4},
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=380,
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.plotly_chart(fig_gauges, use_container_width=True)
