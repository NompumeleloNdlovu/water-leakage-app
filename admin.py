import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# -------------------- Squilla Fund Palette --------------------
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# -------------------- Google Sheets --------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(creds)
SHEET_NAME = "WaterLeakReports"
sheet = client.open(SHEET_NAME).worksheet("Sheet1")

# -------------------- Load Data --------------------
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# -------------------- Update Status --------------------
def update_status(row_index, new_status):
    try:
        cell = f"I{row_index + 2}"  # 'Status' column is 9th -> I
        sheet.update(cell, new_status)
        return True
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False

# -------------------- Dashboard --------------------
def dashboard():
    df = load_data()
    
    # ---------------- Metrics ----------------
    st.title("Admin Dashboard")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] != "Resolved").sum())
    
    st.markdown("---")
    
    # ---------------- Bar Chart ----------------
    bar_data = df['Leak Type'].value_counts().reset_index()
    bar_data.columns = ['Leak Type', 'Count']
    
    fig_bar = px.bar(
        bar_data,
        x='Leak Type',
        y='Count',
        color='Leak Type',
        color_discrete_sequence=[PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"],
                                 PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]],
        labels={'Leak Type':'Leak Type', 'Count':'Count'},
        title="Leak Types"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # ---------------- Pie Chart ----------------
    pie_data = df['Leak Type'].value_counts().reset_index()
    pie_data.columns = ['Leak Type', 'Count']
    
    fig_pie = px.pie(
        pie_data,
        values='Count',
        names='Leak Type',
        color='Leak Type',
        color_discrete_sequence=[PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"],
                                 PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]],
        title="Leak Type Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)
    
    # ---------------- Time Series ----------------
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    time_data = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Reports')
    fig_time = px.line(
        time_data,
        x='DateTime',
        y='Reports',
        markers=True,
        line_shape='linear',
        title="Reports Over Time",
        color_discrete_sequence=[PALETTE["MOONSTONE_BLUE"]]
    )
    st.plotly_chart(fig_time, use_container_width=True)

# -------------------- Manage Reports --------------------
def manage_reports():
    df = load_data()
    
    st.header("Manage Reports")
    for i, row in df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(f"Name: {row['Name']}")
            st.write(f"Contact: {row['Contact']}")
            st.write(f"Municipality: {row['Municipality']}")
            st.write(f"Leak Type: {row['Leak Type']}")
            st.write(f"Location: {row['Location']}")
            st.write(f"DateTime: {row['DateTime']}")
            st.write(f"Status: {row['Status']}")
            
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=0, key=f"status_{i}")
            if st.button("Update", key=f"update_{i}"):
                success = update_status(i, new_status)
                if success:
                    st.success("Status updated successfully!")
                else:
                    st.error("Failed to update status.")

# -------------------- Admin Login & Navigation --------------------
def admin_login_and_manage_page():
    st.sidebar.title("Admin Panel")
    menu = ["Dashboard", "Manage Reports"]
    choice = st.sidebar.radio("Navigate", menu)
    
    if choice == "Dashboard":
        dashboard()
    elif choice == "Manage Reports":
        manage_reports()

# -------------------- App Background & Styling --------------------
st.markdown(f"""
<style>
/* App background */
.stApp {{
    background-color: {PALETTE['WHITE_SMOKE']};
    color: black;
}}

/* Sidebar background and text */
.css-1d391kg {{
    background-color: {PALETTE['TEAL_BLUE']} !important;
    color: white !important;
}}

/* Sidebar radio highlight */
.css-1v3fvcr input:checked + label {{
    background-color: {PALETTE['MOONSTONE_BLUE']} !important;
    color: black !important;
}}
</style>
""", unsafe_allow_html=True)

# -------------------- Main --------------------
def main():
    admin_login_and_manage_page()

if __name__ == "__main__":
    main()
