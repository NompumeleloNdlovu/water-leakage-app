import streamlit as st
import pandas as pd
import plotly.express as px

# --- Squilla Fund Color Palette ---
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}
bar_colors = [PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"], 
              PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]]

# --- Dashboard function ---
def dashboard():
    st.set_page_config(page_title="Water Leakage Admin Dashboard", layout="wide")
    
    # Custom background and sidebar colors
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {PALETTE['WHITE_SMOKE']};
            color: black;
        }}
        .css-1d391kg {{
            background-color: {PALETTE['TEAL_BLUE']} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("Water Leakage Admin Dashboard")
    
    # --- Load data from Google Sheet ---
    df = load_data()  # Replace with your existing function to read Google Sheet
    
    if df.empty:
        st.warning("No data available.")
        return
    
    # --- KPI Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] != "Resolved").sum())
    
    # --- Bar Chart: Leak Types ---
    bar_data = df['Leak Type'].value_counts().reset_index()
    bar_data.columns = ['Leak Type', 'Count']
    
    fig_bar = px.bar(
        bar_data,
        x='Leak Type',
        y='Count',
        color='Leak Type',
        color_discrete_sequence=bar_colors,
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # --- Pie Chart: Status ---
    pie_data = df['Status'].value_counts().reset_index()
    pie_data.columns = ['Status', 'Count']
    
    fig_pie = px.pie(
        pie_data,
        names='Status',
        values='Count',
        color='Status',
        color_discrete_sequence=[PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"]],
        title="Report Status Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # --- Line/Time Chart: Reports Over Time ---
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    time_data = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
    
    fig_time = px.line(
        time_data,
        x='DateTime',
        y='Count',
        title="Reports Over Time",
        line_shape='linear',
        markers=True
    )
    fig_time.update_traces(line_color=PALETTE["MAGIC_MINT"])
    st.plotly_chart(fig_time, use_container_width=True)

