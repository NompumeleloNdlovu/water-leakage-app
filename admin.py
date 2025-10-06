# -*- coding: utf-8 -*-
"""admin_dashboard.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import os
import base64

# --- App Config ---
st.set_page_config(
    page_title="Water Leakage Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Secrets ---
mail_user = st.secrets["mailtrap"]["user"]
mail_pass = st.secrets["mailtrap"]["password"]
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Google Sheet ID ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Helper to connect to Google Sheets ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet


# --- Convert image to base64 for embedding ---
def get_base64_of_image(image_path):
    """Convert image to base64 so it can be embedded cleanly in HTML."""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# --- Display header image ---
def show_header():
    img_path = os.path.join("images", "images", "download.jpeg")
    if os.path.exists(img_path):
        st.markdown(
            f"""
            <div style="
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #ffffff;
                padding: 0.5rem 0;
                border-bottom: 1px solid #e0e0e0;
            ">
                <img src="data:image/jpeg;base64,{get_base64_of_image(img_path)}" 
                     style="width: 30%; max-height: 100px; object-fit: contain;" />
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning("Header image not found.")


# --- Admin Login Page ---
def login_page():
    st.markdown("<h2 style='text-align:center;'>Admin Login</h2>", unsafe_allow_html=True)
    admin_input = st.text_input("Enter Admin Code:", type="password")
    if st.button("Login"):
        if admin_input == ADMIN_CODE:
            st.session_state["logged_in"] = True
            st.success("Login successful! Redirecting...")
            st.rerun()
        else:
            st.error("Invalid admin code.")


# --- Dashboard Page ---
def dashboard_page(df):
    st.markdown("<h3>Dashboard Overview</h3>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"] == "Pending").sum())
    col3.metric("In Progress", (df["Status"] == "In Progress").sum())
    col4.metric("Resolved", (df["Status"] == "Resolved").sum())

    # Reports by Municipality
    st.markdown("<h4>Reports by Municipality</h4>", unsafe_allow_html=True)
    fig1 = px.bar(df, x="Municipality", color="Status", barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    # Leak Types Reported
    st.markdown("<h4>Leak Types Reported</h4>", unsafe_allow_html=True)
    fig2 = px.pie(df, names="Leak Type", title="")
    st.plotly_chart(fig2, use_container_width=True)


# --- Manage Reports Page ---
def manage_reports_page(df, sheet):
    st.markdown("<h3>Manage Reports</h3>", unsafe_allow_html=True)

    for idx, report in enumerate(df.to_dict('records'), start=2):
        st.write("---")
        st.markdown(f"**Report ID:** {report['ReportID']}")
        st.markdown(f"**Name:** {report['Name']}")
        st.markdown(f"**Municipality:** {report['Municipality']}")
        st.markdown(f"**Leak Type:** {report['Leak Type']}")
        st.markdown(f"**Status:** {report['Status']}")

        current_status = report.get("Status", "Pending")
        status = st.selectbox(
            f"Update status for Report {report['ReportID']}",
            options=["Pending", "In Progress", "Resolved", "Rejected"],
            index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
            key=f"status_{idx}"
        )

        if st.button(f"Update Report {report['ReportID']}", key=f"update_{idx}"):
            try:
                sheet.update_cell(idx, 8, status)  # col 8 = 'Status'
                sheet.update_cell(idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # col 9 = timestamp
                st.success(f"Report {report['ReportID']} updated to '{status}'.")
            except Exception as e:
                st.error(f"Failed to update: {e}")


# --- Main App ---
def main():
    show_header()
    st.markdown("<style>body{background-color:white;}</style>", unsafe_allow_html=True)

    # Check login status
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    # Logout option
    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    # Load data
    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        st.info("No reports found.")
        return
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()

    # Display selected page
    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, sheet)


if __name__ == "__main__":
    main()
