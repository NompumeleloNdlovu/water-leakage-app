import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="Water Leakage Admin Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---- STYLES ----
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F5F5;  /* White Smoke background */
        color: #000000; /* Black text */
    }
    .css-1d391kg {
        background-color: #008080;  /* Teal Blue sidebar */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---- GOOGLE SHEETS SETUP ----
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_NAME = "WaterLeakReports"
sheet = client.open(SHEET_NAME).sheet1

# Load sheet into pandas
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ---- CLEAN COLUMNS & DATA ----
df.columns = df.columns.str.strip().str.replace('\n','')
df['Status'] = df['Status'].str.strip().replace({'pending':'Pending','resolved':'Resolved'})
df['Leak Type'] = df['Leak Type'].str.strip()

# ---- SIDEBAR ----
st.sidebar.title("Admin Panel")
menu = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports"])

# ---- SQUILLA FUND COLORS ----
colors_palette = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# ---- DASHBOARD ----
if menu == "Dashboard":
    st.title("Water Leakage Dashboard")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())
    
    # Leak Type Bar Chart
    bar_data = df['Leak Type'].value_counts().reset_index()
    bar_data.columns = ['Leak Type','Count']
    fig_bar = px.bar(
        bar_data,
        x='Leak Type',
        y='Count',
        color='Leak Type',
        color_discrete_sequence=[colors_palette["TEAL_BLUE"], colors_palette["MOONSTONE_BLUE"], colors_palette["POWDER_BLUE"], colors_palette["MAGIC_MINT"]],
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Status Pie Chart
    pie_data = df['Status'].value_counts().reset_index()
    pie_data.columns = ['Status','Count']
    fig_pie = px.pie(
        pie_data,
        names='Status',
        values='Count',
        color='Status',
        color_discrete_map={'Resolved': colors_palette["MOONSTONE_BLUE"], 'Pending': colors_palette["MAGIC_MINT"]},
        title="Report Status Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # Time Chart (Reports over time)
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    time_data = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
    fig_time = px.line(
        time_data,
        x='DateTime',
        y='Count',
        title="Reports Over Time",
        markers=True,
        line_shape="spline",
        color_discrete_sequence=[colors_palette["TEAL_BLUE"]]
    )
    st.plotly_chart(fig_time, use_container_width=True)

# ---- MANAGE REPORTS ----
if menu == "Manage Reports":
    st.title("Manage Reports")
    
    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(f"Name: {row.get('Name','')}")
            st.write(f"Contact: {row.get('Contact','')}")
            st.write(f"Municipality: {row.get('Municipality','')}")
            st.write(f"Leak Type: {row.get('Leak Type','')}")
            st.write(f"DateTime: {row.get('DateTime','')}")
            st.write(f"Status: {row.get('Status','')}")
            
            status = row.get('Status','Pending').strip()
            new_status = st.selectbox(
                "Update Status",
                ["Pending","Resolved"],
                index=["Pending","Resolved"].index(status)
            )
            
            if st.button(f"Update Report #{row.get('ReportID', i+1)}"):
                try:
                    cell = sheet.find(str(row['ReportID']))
                    sheet.update_cell(cell.row, df.columns.get_loc('Status')+1, new_status)
                    st.success("Status updated successfully!")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")
