# -*- coding: utf-8 -*-
"""admin.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import os

# --- Secrets ---
mail_user = st.secrets["mailtrap"]["user"]
mail_pass = st.secrets["mailtrap"]["password"]
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Config ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Google Sheets setup ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet

# --- Main ---
def main():
    st.set_page_config(page_title="Water Leakage Admin", layout="wide")

    # ✅ Use correct image path
    img_path = os.path.join("images", "images", "download.jpeg")
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.warning(f"Header image not found at {img_path}")

    # App title
    st.markdown(
        """
        <h1 style='text-align:center; color:#1E90FF;'>
        💧 Water Leakage Reporting - Admin Panel
        </h1>
        """,
        unsafe_allow_html=True
    )

    admin_input = st.text_input("Enter Admin Code:", type="password")
    if admin_input != ADMIN_CODE:
        st.warning("Please enter a valid admin code to access the admin panel.")
        return

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["📊 Dashboard", "🛠 Manage Reports"])

    # Load data
    sheet = get_sheet()
    data = sheet.get_all_records()

    if not data:
        st.info("No reports found.")
        return

    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()

    if page == "📊 Dashboard":
        show_dashboard(df)
    elif page == "🛠 Manage Reports":
        manage_reports(sheet, data)


def show_dashboard(df):
    """Display analytics dashboard"""
    st.header("📊 Dashboard Overview")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"] == "Pending").sum())
    col3.metric("In Progress", (df["Status"] == "In Progress").sum())
    col4.metric("Resolved", (df["Status"] == "Resolved").sum())

    st.markdown("---")

    st.subheader("📍 Reports by Municipality")
    fig = px.bar(
        df, x="Municipality", color="Status", barmode="group",
        title="Reports by Municipality & Status"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("💧 Leak Types Reported")
    fig2 = px.pie(df, names="Leak Type", title="Distribution of Leak Types")
    st.plotly_chart(fig2, use_container_width=True)


def manage_reports(sheet, data):
    """Allow admin to update report statuses"""
    st.header("🛠 Manage Reports")

    for idx, report in enumerate(data, start=2):
        with st.expander(f"Report {report['ReportID']}"):
            st.write(report)
            current_status = report.get("Status", "Pending")
            status = st.selectbox(
                f"Update status for Report {report['ReportID']}",
                options=["Pending", "In Progress", "Resolved", "Rejected"],
                index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
                key=f"status_{idx}"
            )
            if st.button(f"Update Report {report['ReportID']}", key=f"update_{idx}"):
                sheet.update_cell(idx, 8, status)  # col 8 = 'Status'
                sheet.update_cell(idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # col 9 = updated timestamp
                st.success(f"✅ Status for Report {report['ReportID']} updated to '{status}'.")


if __name__ == "__main__":
    main()

