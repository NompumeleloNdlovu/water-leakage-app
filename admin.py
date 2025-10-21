# -*- coding: utf-8 -*-
"""admin_dashboard.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
from googleapiclient.discovery import build
import base64

# --- App Config ---
st.set_page_config(
    page_title="Drop Watch SA Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Secrets ---
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Google Sheet ID ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Helper: Connect to Google Sheets via gspread ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(google_creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet, creds

# --- Modern Header + Footer ---
def show_header_footer():
    st.markdown("""
        <style>
            /* Header container */
            .header {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 12px;
                background: linear-gradient(90deg, #0d6efd, #0b5ed7);
                color: white;
                padding: 18px 0;
                font-family: 'Cinzel', serif;
                font-weight: 600;
                font-size: 26px;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
                z-index: 999;
            }
            .header a {
                display: flex;
                align-items: center;
                gap: 12px;
                color: white !important;
                text-decoration: none !important;
                transition: transform 0.2s ease;
            }
            .header a:hover {
                transform: scale(1.03);
                text-shadow: 0 0 6px rgba(255,255,255,0.5);
            }
            .header img {
                height: 45px;
                width: auto;
                border-radius: 6px;
                margin-left: 10px;
            }
            .header-spacer {
                height: 90px;
            }
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background: #0d6efd;
                color: white;
                text-align: center;
                padding: 10px 0;
                font-family: 'Cinzel', serif;
                font-size: 14px;
                box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.15);
                z-index: 999;
            }
            .footer-spacer { height: 40px; }
            @media (max-width: 768px) {
                .header { flex-direction: column; font-size: 22px; padding: 14px 0; }
                .header img { height: 38px; }
            }
        </style>

        <div class="header">
            <a href="#dashboard">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png" alt="Drop Watch SA Logo">
                <span>Drop Watch SA Admin Panel</span>
            </a>
        </div>
        <div class="header-spacer"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="footer">&copy; 2025 Drop Watch SA | Water Security Initiative</div>
        <div class="footer-spacer"></div>
    """, unsafe_allow_html=True)

# --- Dashboard Page ---
def dashboard_page(df):
    st.markdown("<h3 id='dashboard'>Dashboard Overview</h3>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"] == "Pending").sum())
    col3.metric("In Progress", (df["Status"] == "In Progress").sum())
    col4.metric("Resolved", (df["Status"] == "Resolved").sum())

    st.markdown("<h4>Reports by Municipality</h4>", unsafe_allow_html=True)
    fig1 = px.bar(df, x="Municipality", color="Status", barmode="group")
    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("<h4>Leak Types Reported</h4>", unsafe_allow_html=True)
    fig2 = px.pie(df, names="Leak Type")
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<h4>Reports Over Time</h4>", unsafe_allow_html=True)
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        daily_reports = df.groupby(df["Timestamp"].dt.date).size().reset_index(name="Reports")
        fig3 = px.line(daily_reports, x="Timestamp", y="Reports", markers=True)
        st.plotly_chart(fig3, use_container_width=True)

# --- Manage Reports Page ---
def manage_reports_page(df, creds):
    st.markdown("<h3>Manage Reports</h3>", unsafe_allow_html=True)

    service = build("sheets", "v4", credentials=creds)
    sheet_id = SPREADSHEET_ID
    range_name = "Sheet1!A:I"

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

        # Image or Video Display
        if "Image" in report and report["Image"]:
            if report["Image"].endswith((".mp4", ".mov", ".avi")):
                st.video(report["Image"])
            else:
                st.image(report["Image"], use_container_width=True)

        current_status = report.get("Status", "Pending")
        status = st.selectbox(
            f"Update status for Report {report['ReportID']}",
            options=["Pending", "In Progress", "Resolved", "Rejected"],
            index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
            key=f"status_{idx}"
        )

        if st.button(f"Update Report {report['ReportID']}", key=f"update_{idx}"):
            try:
                updated_values = [[status, datetime.now().strftime("%Y-%m-%d %H:%M:%S")]]
                service.spreadsheets().values().update(
                    spreadsheetId=sheet_id,
                    range=f"Sheet1!H{idx}:I{idx}",
                    valueInputOption="RAW",
                    body={"values": updated_values}
                ).execute()
                st.success(f"Report {report['ReportID']} updated to '{status}'.")
            except Exception as e:
                st.error(f"Failed to update: {e}")

# --- Main App ---
def main():
    show_header_footer()

    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Cinzel&display=swap');
        .stApp { background-color: white !important; color: black !important; font-family: 'Cinzel', serif !important; }
        section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #e0e0e0; }
        section[data-testid="stSidebar"] * { color: black !important; font-family: 'Cinzel', serif !important; font-size:16px; }
        div.stButton > button { background-color: #0d6efd !important; color: white !important; border: none; border-radius: 6px; }
        div.stButton > button:hover { background-color: #0b5ed7 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Session login control
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.markdown("<h3>Admin Login</h3>", unsafe_allow_html=True)
        code = st.text_input("Enter Admin Code:", type="password")
        if st.button("Login"):
            if code == ADMIN_CODE:
                st.session_state["logged_in"] = True
                st.success("Login successful!")
            else:
                st.error("Invalid admin code")
        return

    with st.sidebar:
        st.markdown("### Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    sheet, creds = get_sheet()
    data = sheet.get_all_records()
    if not data:
        st.info("No reports found.")
        return

    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()

    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, creds)


if __name__ == "__main__":
    main()
