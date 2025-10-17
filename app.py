        # ===== Custom Gauge Function (Dark blue needle + visible % in center) =====
        def create_gauge(value, total, title, colors):
            pct = (value / total * 100) if total > 0 else 0
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=pct,
                    number={
                        "suffix": "%",
                        "font": {"size": 40, "color": "white"},
                        "valueformat": ".1f",
                    },
                    title={"text": title, "font": {"size": 20, "color": "white"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "darkgray"},
                        "bar": {"color": "darkblue", "thickness": 0.35},
                        "steps": [
                            {"range": [0, 33], "color": colors[0]},
                            {"range": [33, 66], "color": colors[1]},
                            {"range": [66, 100], "color": colors[2]},
                        ],
                    },
                )
            )
            fig.update_layout(
                margin=dict(l=10, r=10, t=50, b=10),
                height=250,
                paper_bgcolor="rgba(0,0,0,0)",
                font={"color": "white"},
            )
            return fig

        # ===== Gauges with counts underneath =====
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.plotly_chart(
                create_gauge(notstarted, total, "Not Started", ["green", "yellow", "red"]),
                use_container_width=True,
            )
            st.markdown(
                f"<p style='text-align:center; color:white; font-size:18px;'>"
                f"{notstarted} of {total} tasks</p>",
                unsafe_allow_html=True,
            )

        with c2:
            st.plotly_chart(
                create_gauge(inprogress, total, "In Progress", ["red", "yellow", "green"]),
                use_container_width=True,
            )
            st.markdown(
                f"<p style='text-align:center; color:white; font-size:18px;'>"
                f"{inprogress} of {total} tasks</p>",
                unsafe_allow_html=True,
            )

        with c3:
            st.plotly_chart(
                create_gauge(completed, total, "Completed", ["red", "yellow", "green"]),
                use_container_width=True,
            )
            st.markdown(
                f"<p style='text-align:center; color:white; font-size:18px;'>"
                f"{completed} of {total} tasks</p>",
                unsafe_allow_html=True,
            )

        with c4:
            st.plotly_chart(
                create_gauge(overdue, total, "Overdue", ["yellow", "red", "darkred"]),
                use_container_width=True,
            )
            st.markdown(
                f"<p style='text-align:center; color:white; font-size:18px;'>"
                f"{overdue} of {total} tasks</p>",
                unsafe_allow_html=True,
            )
