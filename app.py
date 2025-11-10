# ===================== INSTALLATIONS TAB =====================
with tabs[1]:
    st.subheader("🧰 Installations Overview")
    st.markdown("Below are the installation dials for each contractor based on the latest weekly update sheet.")

    # Load and clean data
    df_update.set_index(df_update.columns[0], inplace=True)
    df_update.columns = df_update.columns.str.strip().str.lower()
    df_update.index = df_update.index.str.strip().str.lower()

    # Safely extract "meters installed"
    if "meters installed" not in df_update.index:
        st.error("❌ The sheet doesn't contain a row named 'Meters installed'. Please verify your Excel file.")
        st.stop()

    installed = df_update.loc["meters installed"]

    # Helper to safely get values
    def safe_get(series, key):
        for col in series.index:
            if key.lower() in col.lower():
                return series[col]
        return None

    contractors = ["Deezlo", "Nimba", "Isindiso"]
    colors = ["#003366", "#007acc", "#00b386"]

    def create_installation_gauge(value, title, color):
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=value if value is not None else 0,
                title={"text": title, "font": {"size": 22, "color": color}},
                gauge={
                    "axis": {"range": [0, 200], "tickwidth": 1, "tickcolor": "gray"},
                    "bar": {"color": color, "thickness": 0.3},
                    "bgcolor": "#ffffff",
                    "steps": [{"range": [0, 200], "color": "#e0e0e0"}],
                },
                number={"font": {"size": 36, "color": color}}
            )
        )
        fig.update_layout(height=300, margin=dict(l=15, r=15, t=40, b=20))
        return fig

    # Show the dials in 1 row
    c1, c2, c3 = st.columns(3)
    for i, (contractor, col) in enumerate(zip(contractors, [c1, c2, c3])):
        val = safe_get(installed, contractor)
        if val is not None:
            with col:
                st.plotly_chart(create_installation_gauge(val, f"{contractor} Installed", colors[i]), use_container_width=True)
        else:
            with col:
                st.warning(f"⚠️ {contractor} data not found in Excel.")
    
    st.markdown("---")
    st.dataframe(df_update)
