import streamlit as st
import pandas as pd
import plotly.express as px

# ---- Squilla Fund palette ----
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

def dashboard():
    st.set_page_config(page_title="Water Leakage Admin Dashboard", layout="wide")
    
    # Sidebar styling
    st.sidebar.markdown(
        f"""
        <style>
        .css-1d391kg {{background-color: {PALETTE['TEAL_BLUE']};}}
        .css-1v3fvcr {{background-color: {PALETTE['WHITE_SMOKE']};}}
        </style>
        """, unsafe_allow_html=True
    )
    
    st.markdown(f"<div style='background-color:{PALETTE['WHITE_SMOKE']}; padding:10px'>", unsafe_allow_html=True)

    # Load data from Google Sheet (df must be loaded before calling this function)
    if df.empty:
        st.warning("No data available to display.")
        return

    # Clean column names
    df.columns = df.columns.str.strip()

    # --- Metrics ---
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum() if "Status" in df.columns else 0)
    col3.metric("Pending", (df["Status"] == "Pending").sum() if "Status" in df.columns else 0)
    col4.metric("In Progress", (df["Status"] == "In Progress").sum() if "Status" in df.columns else 0)

    st.markdown("---")

    # --- Bar Chart: Leak Types ---
    if 'Leak Type' in df.columns:
        leak_counts = df['Leak Type'].value_counts().reset_index()
        leak_counts.columns = ['Leak Type', 'Count']  # rename explicitly
        bar_colors = [PALETTE["MOONSTONE_BLUE"], PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]]

        fig_bar = px.bar(
            leak_counts,
            x='Leak Type',
            y='Count',
            color='Leak Type',
            color_discrete_sequence=bar_colors,
            title="Leak Reports by Type"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("No 'Leak Type' column found for bar chart.")

    # --- Pie Chart: Status Distribution ---
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        pie_colors = [PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"], PALETTE["MAGIC_MINT"]]

        fig_pie = px.pie(
            status_counts,
            names='Status',
            values='Count',
            color='Status',
            color_discrete_sequence=pie_colors,
            title="Reports by Status"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("No 'Status' column found for pie chart.")

    # --- Line Chart: Reports Over Time ---
    if 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        time_counts = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')

        fig_line = px.line(
            time_counts,
            x='DateTime',
            y='Count',
            title="Reports Over Time",
            line_shape='linear',
            markers=True,
            color_discrete_sequence=[PALETTE["MAGIC_MINT"]]
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.warning("No 'DateTime' column found for time chart.")
