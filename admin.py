# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import io

# --- CONFIG ---
st.set_page_config(page_title="Drop Watch SA Admin Panel", layout="wide")
SHEET_NAME = "WaterLeakReports"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
ADMIN_CODE = "admin123"  # Change this

# --- GOOGLE SHEETS SETUP ---
try:
    # Load credentials from Streamlit Secrets
    creds_dict = st.secrets["google"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME).sheet1
except gspread.SpreadsheetNotFound:
    st.error(f"Spreadsheet '{SHEET_NAME}' not found. Please check the name and share it with the service account.")
    st.stop()
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {e}")
    st.stop()

# --- HEADER + FOOTER ---
def show_header_footer():
    st.markdown("""
        <style>
            .header {position: fixed; top: 0; left: 0; width: 100%; display: flex; align-items: center; justify-content: center; gap: 12px; background: linear-gradient(90deg, #0d6efd, #0b5ed7); color: white; padding: 18px 0; font-family: 'Cinzel', serif; font-weight: 600; font-size: 26px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15); z-index: 999;}
            .header a {display: flex; align-items: center; gap: 12px; color: white !important; text-decoration: none !important;}
            .header img {height: 45px; width: auto; border-radius: 6px;}
            .header-spacer { height: 90px; }
            .footer {position: fixed; bottom: 0; left: 0; width: 100%; background: #0d6efd; color: white; text-align: center; padding: 10px 0; font-family: 'Cinzel', serif; font-size: 14px; box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.15); z-index: 999;}
            .footer-spacer { height: 40px; }
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

# --- LOAD DATA ---
def load_data():
    try:
        data = sheet.get_all_records()
        if not data:
            # Empty sheet, return DataFrame with correct headers
            return pd.DataFrame(columns=["ReportID","Name","Contact","Municipality","Leak Type","Location","DateTime","Status","Image"])
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to load data from Google Sheets: {e}")
        return pd.DataFrame()

# --- UPDATE STATUS ---
def update_status(index, new_status):
    df = load_data()
    if df.empty or not (0 <= index < len(df)):
        st.warning("No data or invalid row index.")
        return False

    # Find column index dynamically
    try:
        status_col_idx = df.columns.get_loc("Status") + 1  # Google Sheets 1-indexed
    except KeyError:
        st.error("⚠️ 'Status' column not found in the sheet.")
        return False

    # Convert column index to letter (A-Z, AA, etc.)
    def colnum_to_letter(n):
        string = ""
        while n > 0:
            n, remainder = divmod(n-1, 26)
            string = chr(65 + remainder) + string
        return string

    col_letter = colnum_to_letter(status_col_idx)
    cell = f"{col_letter}{index + 2}"  # +2 because row 1 = header

    try:
        sheet.update(cell, new_status)
        return True
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False

# --- LOGIN PAGE ---
def login_page():
    show_header_footer()

    st.markdown("""
        <style>
            .login-container {display: flex; flex-direction: column; align-items: center; justify-content: center; height: 75vh; text-align: center;}
            .login-card {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 380px; text-align: center;}
            .login-card h2 {font-family: 'Cinzel', serif; font-weight: 600; color: #0d6efd; margin-bottom: 10px;}
            .login-card img {height: 80px; margin-bottom: 15px;}
            .stTextInput input {border-radius: 8px !important; padding: 10px !important; font-size: 16px !important;}
            div.stButton > button {width: 100%; border-radius: 8px !important; font-weight: 600; background-color: #0d6efd !important; color: white !important;}
            div.stButton > button:hover {background-color: #0b5ed7 !important;}
        </style>
        <div class="login-container">
            <div class="login-card">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png" alt="Drop Watch Logo">
                <h2>Drop Watch SA</h2>
                <p style='color:#555;'>Administrator Access</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    code = st.text_input("Enter Admin Code:", type="password", key="login_input")
    if st.button("Login", use_container_width=True):
        if code == ADMIN_CODE:
            st.session_state["logged_in"] = True
            st.success("✅ Login successful! Redirecting...")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid admin code")
    st.stop()

# --- MANAGE REPORTS PAGE ---
def manage_reports():
    show_header_footer()
    st.title("Manage Leak Reports")
    df = load_data()

    if df.empty:
        st.info("No reports found.")
        return

    for i, row in df.iterrows():
        with st.expander(f" Report #{i+1} — {row.get('Location', 'Unknown')}"):
            st.write(f"**Description:** {row.get('Description', 'N/A')}")
            st.write(f"**Date:** {row.get('DateTime', 'N/A')}")
            st.write(f"**Status:** {row.get('Status', 'Pending')}")

            # Show image/video if available
            image_url = row.get("Image", "")
            if image_url:
                if image_url.lower().endswith(('.mp4', '.mov', '.avi')):
                    st.video(image_url)
                else:
                    st.image(image_url, caption="Leak Evidence", use_container_width=True)

            # Update status
            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], key=f"status_{i}", index=["Pending","In Progress","Resolved"].index(row.get("Status","Pending")))
            if st.button("Save Update", key=f"save_{i}"):
                success = update_status(i, new_status)
                if success:
                    st.success(" Status updated successfully!")
                else:
                    st.error(" Failed to update status.")

# --- DASHBOARD PAGE ---
def dashboard():
    show_header_footer()
    st.title(" Dashboard Overview")
    df = load_data()

    if df.empty:
        st.info("No reports yet.")
        return

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Reports", len(df))
    with col2: st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3: st.metric("Pending", (df["Status"] == "Pending").sum())

    st.bar_chart(df["Status"].value_counts())

# --- MAIN ---
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()

    st.sidebar.title("🔧 Navigation")
    page = st.sidebar.radio("Go to:", ["Dashboard", "Manage Reports", "Logout"])

    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()
    elif page == "Logout":
        st.session_state["logged_in"] = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()

