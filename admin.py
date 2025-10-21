# -*- coding: utf-8 -*-
"""admin.py — Water Leakage Report Admin Dashboard"""

import streamlit as st
import gspread
import pandas as pd
import json
from google.oauth2.service_account import Credentials

# --- PAGE CONFIG ---
st.set_page_config(page_title="Admin Dashboard", layout="wide")

# --- GOOGLE SHEETS SETUP ---
SHEET_NAME = "WaterLeakReports"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ADMIN_CODE = "admin123"  # Change this to your own secret admin code

# --- LOAD CREDENTIALS SECURELY FROM STREAMLIT SECRETS ---
st.write(st.secrets["google"].keys())  # Should output: ['service_account']
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# --- APP HEADER ---
st.title("💧 Water Leakage Report Admin Dashboard")
st.markdown("Manage and monitor water leakage reports submitted by users in real-time.")

# --- LOGIN SECTION ---
admin_input = st.text_input("Enter admin access code:", type="password")

if admin_input == ADMIN_CODE:
    st.success("Access granted ✅")

    # --- LOAD DATA FROM GOOGLE SHEET ---
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if not df.empty:
        # --- SIDEBAR FILTERS ---
        st.sidebar.header("🔍 Filter Reports")
        selected_status = st.sidebar.selectbox("Filter by Status", ["All"] + list(df["Status"].unique()))
        selected_municipality = st.sidebar.selectbox("Filter by Municipality", ["All"] + list(df["Municipality"].unique()))

        # --- APPLY FILTERS ---
        filtered_df = df.copy()
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df["Status"] == selected_status]
        if selected_municipality != "All":
            filtered_df = filtered_df[filtered_df["Municipality"] == selected_municipality]

        # --- DISPLAY FILTERED DATA ---
        st.subheader("📋 Filtered Water Leakage Reports")
        st.dataframe(filtered_df, use_container_width=True)

        # --- DOWNLOAD SECTION ---
        st.subheader("📥 Download Reports")
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="water_leakage_reports.csv",
            mime="text/csv"
        )

        excel = pd.ExcelWriter("/tmp/water_leakage_reports.xlsx", engine='openpyxl')
        filtered_df.to_excel(excel, index=False, sheet_name="Reports")
        excel.close()

        with open("/tmp/water_leakage_reports.xlsx", "rb") as f:
            st.download_button(
                label="Download as Excel",
                data=f,
                file_name="water_leakage_reports.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # --- UPDATE STATUS SECTION ---
        st.subheader("🛠️ Update Report Status")
        if not df["ReportID"].empty:
            report_ids = df["ReportID"].tolist()
            selected_report = st.selectbox("Select Report ID to Update", report_ids)
            new_status = st.selectbox("Select New Status", ["Pending", "In Progress", "Resolved"])

            if st.button("Update Status"):
                try:
                    cell = sheet.find(str(selected_report))
                    if cell:
                        status_col = df.columns.get_loc("Status") + 1
                        sheet.update_cell(cell.row, status_col, new_status)
                        st.success(f"✅ Status updated for Report ID {selected_report}")
                        st.experimental_rerun()
                    else:
                        st.error("❌ Report ID not found in Google Sheet.")
                except Exception as e:
                    st.error(f"⚠️ An error occurred: {e}")
        else:
            st.info("No reports found to update.")
    else:
        st.info("No reports found yet.")
else:
    if admin_input:
        st.error("Incorrect access code ❌")
    st.stop()

# --- FOOTER ---
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:grey;'>© 2025 Water Leakage Reporting System | Powered by Streamlit</div>",
    unsafe_allow_html=True
)

