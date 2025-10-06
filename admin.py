# -*- coding: utf-8 -*-
"""admin_dashboard.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import os

# --- App Config ---
st.set_page_config(
    page_title="Drop Watch SA Admin Panel",
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

# --- Display header and fixed footer ---
def show_header_footer():
    # Header
    st.markdown(f"""
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #007bff;
            padding: 20px;
            width: 100%;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            position: fixed;
            top: 0;
            left: 0;
            z-index: 1000;
        ">
            <h2 style="color:white; margin:0;">Drop Watch SA</h2>
        </div>
        <div style="height:80px;"></div> <!-- spacer to avoid overlap with header -->
    """, unsafe_allow_html=True)

    # Footer fixed at bottom
    st.markdown("""
        <div style="
            background-color: #007bff;
            color: white;
            text-align: center;
            padding: 10px 0;
            width: 100%;
            position: fixed;
            bottom: 0;
            left: 0;
            z-index: 1000;
        ">
            &copy; 2025 Drop Watch SA
        </div>
        <div style="height:40px;"></div> <!-- spacer to avoid overlap with footer -->
    """, unsafe_allow_html=True)

# --- Admin Login Page ---
def login_page():
    st.markdown("""
        <div style="background-color:black; padding:20px; border-radius:8px;">
            <h2 style="text-align:center; color:white;">Admin Login</h2>
        </div>
    """, unsafe_allow_html=True)
    admin_input = st.text_input("Enter Admin Code:", type="password", key="login_input")
    if st.button("Login", key="login_btn"):
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

    st.markdown("<h4>Reports by Municipality</h4>", unsafe_allow_html=True)
    fig1 = px.bar(df, x="Municipality", color="Status", barmode="group")
    fig1.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black", family="Cinzel, serif"),
        hoverlabel=dict(font_color="white", bgcolor="black", font_family="Cinzel, serif"),
        legend=dict(font=dict(color="black", family="Cinzel, serif"))
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<h4>Leak Types Reported</h4>", unsafe_allow_html=True)
    fig2 = px.pie(df, names="Leak Type", title="")
    fig2.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="black", family="Cinzel, serif"),
        hoverlabel=dict(font_color="white", bgcolor="black", font_family="Cinzel, serif"),
        legend=dict(font=dict(color="black", family="Cinzel, serif"))
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Manage Reports Page ---
def manage_reports_page(df, sheet):
    st.markdown("<h3>Manage Reports</h3>", unsafe_allow_html=True)

    for idx, report in enumerate(df.to_dict('records'), start=2):
        st.write("---")
        st.markdown(f"""
            <div style="background-color:white; padding:12px; border-radius:6px; color:black; font-family:'Cinzel', serif;">
                <p><strong>Report ID:</strong> {report['ReportID']}</p>
                <p><strong>Name:</strong> {report['Name']}</p>
                <p><strong>Municipality:</strong> {report['Municipality']}</p>
                <p><strong>Leak Type:</strong> {report['Leak Type']}</p>
                <p><strong>Status:</strong> {report['Status']}</p>
            </div>
        """, unsafe_allow_html=True)

        current_status = report.get("Status", "Pending")
        status = st.selectbox(
            f"Update status for Report {report['ReportID']}",
            options=["Pending", "In Progress", "Resolved", "Rejected"],
            index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
            key=f"status_{idx}"
        )

        if st.button(f"Update Report {report['ReportID']}", key=f"update_{idx}"):
            try:
                sheet.update_cell(idx, 8, status)
                sheet.update_cell(idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.success(f"Report {report['ReportID']} updated to '{status}'.")
            except Exception as e:
                st.error(f"Failed to update: {e}")

# --- Main App ---
def main():
    show_header_footer()

    st.markdown("""
    <style>
    /* Import Google Font for body text only */
    @import url('https://fonts.googleapis.com/css2?family=Cinzel&display=swap');

    /* Overall App text */
    .stApp { 
        background-color: white !important; 
        color: black !important; 
        font-family: 'Cinzel', serif !important; 
    }

    /* Keep headings default font to avoid hiding */
    h1, h2, h3, h4, h5, h6 { font-family: inherit !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa !important;
        color: black !important;
        padding: 1.5rem 1rem; border-right: 1px solid #e0e0e0;
    }
    section[data-testid="stSidebar"] * {
        color: black !important;
        font-size:16px;
        font-family: 'Cinzel', serif !important;
    }

    /* Sidebar buttons */
    section[data-testid="stSidebar"] button {
        background-color:#007bff !important; color:white !important;
        border-radius:6px; padding:8px 14px; border:none;
        font-size:15px; font-weight:500; box-shadow:0 2px 6px rgba(0,0,0,0.15);
        font-family: 'Cinzel', serif !important;
    }
    section[data-testid="stSidebar"] button:hover { background-color:#0056b3 !important; cursor:pointer; }

    /* Metrics */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color:black !important; font-family: 'Cinzel', serif !important; }

    /* Plotly hover labels */
    .js-plotly-plot .hovertext { fill: white !important; font-family: 'Cinzel', serif !important; }

    /* Dark buttons (login, update report) */
    div.stButton > button {
        color: white !important;
        background-color: #007bff !important;
        font-family: 'Cinzel', serif !important;
    }
    div.stButton > button:hover {
        background-color: #0056b3 !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
        return

    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        st.info("No reports found.")
        return

    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()

    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, sheet)

if __name__ == "__main__":
    main()
