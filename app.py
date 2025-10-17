# ======================================================
#   KPIs + ANALOG-STYLE GAUGES (gradient + % display)
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
        overdue = ((tasks['Due date'] < pd.Timestamp.today()) &
                   (~tasks['Progress'].str.lower().eq('completed'))).sum()

    gauges = [
        {"label": "Not Started", "value": notstarted, "start_color": "#00FF00", "end_color": "#FF0000"},  # green→red
        {"label": "In Progress", "value": inprogress, "start_color": "#FF0000", "end_color": "#00FF00"},  # red→green
        {"label": "Completed", "value": completed, "start_color": "#FF0000", "end_color": "#00FF00"},     # red→green
        {"label": "Overdue", "value": overdue, "start_color": "#FFFF00", "end_color": "#FF0000"},         # yellow→red
    ]

    fig_gauges = go.Figure()

    def create_gradient_steps(start_hex, end_hex, steps_count=40):
        """Generate a smooth color gradient list between two hex colors."""
        import matplotlib.colors as mcolors
        start_rgb = mcolors.hex2color(start_hex)
        end_rgb = mcolors.hex2color(end_hex)
        gradient_steps = []
        for i in range(steps_count):
            ratio = i / (steps_count - 1)
            color_rgb = [
                start_rgb[j] + (end_rgb[j] - start_rgb[j]) * ratio for j in range(3)
            ]
            color_hex = mcolors.to_hex(color_rgb)
            gradient_steps.append(color_hex)
        return gradient_steps

    for i, g in enumerate(gauges):
        gradient_colors = create_gradient_steps(g["start_color"], g["end_color"], steps_count=40)
        steps = []
        for j, color in enumerate(gradient_colors):
            steps.append({
                'range': [
                    total_safe * j / len(gradient_colors),
                    total_safe * (j + 1) / len(gradient_colors)
                ],
                'color': color
            })

        percent = round((g["value"] / total_safe) * 100, 1)

        fig_gauges.add_trace(go.Indicator(
            mode="gauge+number",
            value=percent,
            title={'text': f"<b>{g['label']}</b>", 'font': {'size': 16, 'color': '#003366'}},
            number={'suffix': "%", 'font': {'size': 22, 'color': '#003366'}},
            domain={'x': [i * 0.25, (i + 1) * 0.25], 'y': [0, 1]},
            gauge={
                'axis': {'range': [0, 100], 'tickwidth': 0, 'visible': False},
                'bar': {'color': 'rgba(0,0,0,0)'},
                'bgcolor': "white",
                'borderwidth': 3,
                'bordercolor': "#B0B0B0",
                'steps': steps,
                'threshold': {
                    'line': {'color': "#002B5B", 'width': 5},  # dark blue needle
                    'thickness': 0.9,
                    'value': percent
                }
            }
        ))

    fig_gauges.update_layout(
        grid={'rows': 1, 'columns': 4},
        paper_bgcolor="white",
        plot_bgcolor="white",
        height=380,
        margin=dict(l=10, r=10, t=10, b=10)
    )

    st.plotly_chart(fig_gauges, use_container_width=True)
