# -*- coding: utf-8 -*-
"""admin_dashboard.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# --- Secrets ---
mail_user = st.secrets["mailtrap"]["user"]
mail_pass = st.secrets["mailtrap"]["password"]
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Config ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"  # Your Google Sheet ID

# --- Google Sheets setup ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

# --- Main ---
def main():
    st.title("🚰 Water Leakage Reporting - Admin Dashboard")

    admin_input = st.text_input("Enter Admin Code:", type="password")
    if admin_input != ADMIN_CODE:
        st.warning("Please enter a valid admin code to access the reports.")
        return

    # Load data
    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        st.info("No reports found.")
        return

    df = pd.DataFrame(data)
    st.success(f"✅ Loaded {len(df)} reports.")

    # --- Dashboard Stats ---
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"] == "Pending").sum())
    col3.metric("In Progress", (df["Status"] == "In Progress").sum())
    col4.metric("Resolved", (df["Status"] == "Resolved").sum())

    # --- Visualizations ---
    st.subheader("📈 Reports Breakdown")

    if "Municipality" in df.columns:
        fig1 = px.bar(df, x="Municipality", color="Status", title="Reports by Municipality")
        st.plotly_chart(fig1, use_container_width=True)

    if "Leak Type" in df.columns:
        fig2 = px.pie(df, names="Leak Type", title="Leak Types Reported")
        st.plotly_chart(fig2, use_container_width=True)

    if {"Latitude", "Longitude"}.issubset(df.columns):
        st.subheader("🗺️ Leak Locations Map")
        st.map(df.rename(columns={"Latitude": "lat", "Longitude": "lon"}))

    # --- Report Management ---
    st.subheader("🛠 Manage Reports")
    for idx, report in enumerate(data, start=2):  # start=2 because sheet rows start at 1 with header
        with st.expander(f"Report #{idx-1}"):
            st.write(report)
            current_status = report.get("Status", "Pending")
            status = st.selectbox(
                f"Update status for Report #{idx-1}", 
                options=["Pending", "In Progress", "Resolved", "Rejected"], 
                index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
                key=f"status_{idx}"
            )
            
            if st.button(f"Update Status for Report #{idx-1}", key=f"update_{idx}"):
                sheet.update_cell(idx, 7, status)  # Assuming column 7 = 'Status'
                sheet.update_cell(idx, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # Status timestamp col 8
                st.success(f"✅ Status for Report #{idx-1} updated to '{status}'.")

if __name__ == "__main__":
    main()

