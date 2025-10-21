# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt

# --- CONFIG ---
st.set_page_config(page_title="Drop Watch SA Admin Panel", layout="wide")

# --- GOOGLE SHEETS SETUP ---
SHEET_NAME = "WaterLeakReports"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "service_account.json"  # Make sure this matches your secret
ADMIN_CODE = st.secrets["general"]["admin_code"]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"], scopes=SCOPES
)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# --- HEADER + FOOTER ---
def show_header_footer():
    st.markdown("""
        <style>
            .header {position: fixed;top: 0;left: 0;width: 100%;display: flex;align-items: center;justify-content: center;gap: 12px;background: linear-gradient(90deg, #0d6efd, #0b5ed7);color: white;padding: 18px 0;font-family: 'Cinzel', serif;font-weight: 600;font-size: 26px;box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);z-index: 999;}
            .header a {display: flex;align-items: center;gap: 12px;color: white !important;text-decoration: none !important;}
            .header img {height: 45px;width: auto;border-radius: 6px;}
            .header-spacer {height: 90px;}
            .footer {position: fixed;bottom: 0;left: 0;width: 100%;background: #0d6efd;color: white;text-align: center;padding: 10px 0;font-family: 'Cinzel', serif;font-size: 14px;box-shadow: 0 -2px 6px rgba(0, 0, 0, 0.15);z-index: 999;}
            .footer-spacer {height: 40px;}
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
        df = pd.DataFrame(data)
        if df.empty:
            df = pd.DataFrame(columns=["ReportID", "Name", "Contact", "Municipality",
                                       "Leak Type", "Location", "DateTime", "Status", "Image"])
        return df
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")
        return pd.DataFrame()

# --- UPDATE STATUS ---
def update_status(index, new_status):
    df = load_data()
    if 0 <= index < len(df):
        cell_range = f"H{index + 2}"  # Column H = Status
        try:
            sheet.update(cell_range, [[new_status]])  # 2D array required
            return True
        except Exception as e:
            st.error(f"Failed to update Google Sheet: {e}")
            return False
    return False

# --- LOGIN PAGE ---
def login_page():
    show_header_footer()
    st.markdown("""
        <div style="display:flex;justify-content:center;margin-top:5%;">
            <div style="background:white;padding:40px;border-radius:12px;box-shadow:0 4px 20px rgba(0,0,0,0.1);width:380px;text-align:center;">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png" alt="Drop Watch Logo" style="height:80px;margin-bottom:15px;">
                <h2 style="font-family:'Cinzel', serif;color:#0d6efd;">Drop Watch SA</h2>
                <p style='color:#555;'>Administrator Access</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    code = st.text_input("Enter Admin Code:", type="password", key="login_input")
    if st.button("Login", use_container_width=True):
        if code == ADMIN_CODE:
            st.session_state["logged_in"] = True
            st.success("✅ Login successful! Redirecting...")
            st.rerun()
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
        with st.expander(f"📍 Report #{row.get('ReportID', i+1)} — {row.get('Location', 'Unknown')}"):
            st.write(f"**Name:** {row.get('Name', 'N/A')}")
            st.write(f"**Contact:** {row.get('Contact', 'N/A')}")
            st.write(f"**Municipality:** {row.get('Municipality', 'N/A')}")
            st.write(f"**Leak Type:** {row.get('Leak Type', 'N/A')}")
            st.write(f"**Description / DateTime:** {row.get('DateTime', 'N/A')}")
            st.write(f"**Status:** {row.get('Status', 'Pending')}")

            image_url = row.get("Image", "")
            if image_url:
                if image_url.lower().endswith(('.mp4', '.mov', '.avi')):
                    st.video(image_url)
                else:
                    st.image(image_url, caption="Leak Evidence", use_container_width=True)

            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], index=["Pending","In Progress","Resolved"].index(row.get('Status','Pending')), key=f"status_{i}")
            if st.button("Save Update", key=f"save_{i}"):
                success = update_status(i, new_status)
                if success:
                    st.success("✅ Status updated successfully!")
                else:
                    st.error("⚠️ Failed to update status.")

# --- DASHBOARD PAGE ---
def dashboard():
    show_header_footer()
    st.title("📊 Dashboard Overview")
    df = load_data()

    if df.empty:
        st.info("No reports yet.")
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar chart
    st.subheader("Status Distribution")
    status_counts = df["Status"].value_counts()
    st.bar_chart(status_counts)

    # Pie chart
    st.subheader("Status Breakdown (Pie)")
    fig1, ax1 = plt.subplots(figsize=(5,5))
    status_counts.plot.pie(autopct="%1.1f%%", colors=["#0d6efd", "#ffc107", "#198754"], startangle=90, ylabel="", ax=ax1)
    st.pyplot(fig1)

    # Time chart
    st.subheader("Reports Over Time")
    if "DateTime" in df.columns and not df["DateTime"].isnull().all():
        df["DateTimeParsed"] = pd.to_datetime(df["DateTime"], errors='coerce')
        df_time = df.groupby(df["DateTimeParsed"].dt.date).size()
        st.line_chart(df_time)

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
        st.rerun()

if __name__ == "__main__":
    main()
