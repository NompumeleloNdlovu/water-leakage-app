# -*- coding: utf-8 -*-
"""admin.py - Clean White Background Admin Panel"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import os

# --- Streamlit page setup ---
st.set_page_config(
    page_title="Water Leakage Admin Panel",
    layout="wide",
)

# --- Secrets ---
mail_user = st.secrets["mailtrap"]["user"]
mail_pass = st.secrets["mailtrap"]["password"]
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Google Sheet Config ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Google Sheets setup ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


# --- Load data ---
def load_data(sheet):
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df


# --- Global Styles ---
st.markdown(
    """
    <style>
    body, .stApp {
        background-color: white !important;
        color: #000000;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        background-color: white;
    }
    h2, h3 {
        color: #003566;
        font-family: 'Arial', sans-serif;
    }
    .login-container {
        background: #ffffff;
        padding: 3rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
        text-align: center;
        width: 60%;
        margin: auto;
    }
    .stButton>button {
        background-color: #003566;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.6rem 1.2rem;
        font-weight: 500;
    }
    .stButton>button:hover {
        background-color: #002147;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Login Page ---
def login_page():
    st.markdown("<h2>Admin Login</h2>", unsafe_allow_html=True)

    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    admin_code = st.text_input("Enter Admin Code:", type="password")
    if st.button("Login", use_container_width=True):
        if admin_code == ADMIN_CODE:
            st.session_state["authenticated"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid admin code. Please try again.")
    st.markdown("</div>", unsafe_allow_html=True)


# --- Dashboard Page ---
def dashboard_page(df):
    st.markdown("<h2>Dashboard Overview</h2>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"] == "Pending").sum())
    col3.metric("In Progress", (df["Status"] == "In Progress").sum())
    col4.metric("Resolved", (df["Status"] == "Resolved").sum())

    st.markdown("---")

    st.subheader("Reports by Municipality")
    fig = px.bar(df, x="Municipality", color="Status", barmode="group", title="")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Leak Types Reported")
    fig2 = px.pie(df, names="Leak Type", title="")
    st.plotly_chart(fig2, use_container_width=True)


# --- Manage Reports Page ---
def manage_reports_page(sheet, df):
    st.markdown("<h2>Manage Reports</h2>", unsafe_allow_html=True)

    for idx, report in enumerate(df.to_dict('records'), start=2):
        with st.expander(f"Report {report['ReportID']} - {report['Municipality']}"):
            st.write(report)
            current_status = report.get("Status", "Pending")

            status = st.selectbox(
                f"Update Status for Report {report['ReportID']}",
                options=["Pending", "In Progress", "Resolved", "Rejected"],
                index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
                key=f"status_{idx}"
            )

            if st.button(f"Update Report {report['ReportID']}", key=f"update_{idx}"):
                sheet.update_cell(idx, 8, status)
                sheet.update_cell(idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.success(f"Status for Report {report['ReportID']} updated to '{status}'.")


# --- Header Image ---
def show_header():
    img_path = os.path.join("images", "images", "download.jpeg")
    if os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        st.warning("Header image not found.")


# --- Main App ---
def main():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        login_page()
        return

    # Header and sidebar
    show_header()
    st.sidebar.success("Logged in as Admin")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Dashboard", "Manage Reports"])

    sheet = get_sheet()
    df = load_data(sheet)

    if page == "Dashboard":
        dashboard_page(df)
    else:
        manage_reports_page(sheet, df)


if __name__ == "__main__":
    main()
