# -*- coding: utf-8 -*-
"""Drop Watch SA Admin Panel"""
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import json

# --- CONFIG ---
st.set_page_config(page_title="Drop Watch SA Admin Panel", layout="wide")

# --- Load Google Sheets credentials from secrets ---
try:
    creds_dict = json.loads(st.secrets["google_service_account"])
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    sheet = client.open("WaterLeakReports").sheet1
except KeyError:
    st.error("⚠️ Google service account secret not found. Check Streamlit secrets.")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Failed to connect to Google Sheets: {e}")
    st.stop()

# --- Admin code from secrets ---
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- HEADER + FOOTER ---
def show_header_footer():
    st.markdown("""
    <style>
    .header {position: fixed; top:0; left:0; width:100%; display:flex; align-items:center; justify-content:center; gap:12px; background:linear-gradient(90deg, #0d6efd, #0b5ed7); color:white; padding:18px 0; font-family: 'Cinzel', serif; font-weight:600; font-size:26px; box-shadow:0 4px 8px rgba(0,0,0,0.15); z-index:999;}
    .header img {height:45px; width:auto; border-radius:6px;}
    .header-spacer {height:90px;}
    .footer {position: fixed; bottom:0; left:0; width:100%; background:#0d6efd; color:white; text-align:center; padding:10px 0; font-family:'Cinzel', serif; font-size:14px; box-shadow:0 -2px 6px rgba(0,0,0,0.15); z-index:999;}
    .footer-spacer {height:40px;}
    </style>
    <div class="header">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png">
        <span>Drop Watch SA Admin Panel</span>
    </div>
    <div class="header-spacer"></div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="footer">&copy; 2025 Drop Watch SA | Water Security Initiative</div>
    <div class="footer-spacer"></div>
    """, unsafe_allow_html=True)

# --- Load data ---
@st.cache_data(ttl=60)
def load_data():
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"⚠️ Failed to load data: {e}")
        return pd.DataFrame()

# --- Update report status ---
def update_status(index, new_status):
    df = load_data()
    if 0 <= index < len(df):
        cell = f"H{index+2}"  # Column H = Status
        try:
            sheet.update(cell, new_status)
            st.cache_data.clear()
            return True
        except Exception as e:
            st.error(f"⚠️ Failed to update status: {e}")
            return False
    return False

# --- Login page ---
def login_page():
    show_header_footer()
    st.markdown("<h2 style='text-align:center; color:#0d6efd;'>Administrator Access</h2>", unsafe_allow_html=True)
    code = st.text_input("Enter Admin Code:", type="password")
    if st.button("Login"):
        if code == ADMIN_CODE:
            st.session_state["logged_in"] = True
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid admin code")
    st.stop()

# --- Manage reports ---
def manage_reports():
    show_header_footer()
    st.title("Manage Leak Reports")
    df = load_data()
    if df.empty:
        st.info("No reports found.")
        return

    for i, row in df.iterrows():
        with st.expander(f"📍 Report #{i+1} — {row.get('Location', 'Unknown')}"):
            st.write(f"**Description:** {row.get('Description','N/A')}")
            st.write(f"**Date:** {row.get('Timestamp','N/A')}")
            st.write(f"**Status:** {row.get('Status','Pending')}")
            
            image_url = row.get("Image", "")
            if image_url:
                if image_url.lower().endswith(('.mp4','.mov','.avi')):
                    st.video(image_url)
                else:
                    st.image(image_url, caption="Leak Evidence", use_container_width=True)

            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], key=f"status_{i}")
            if st.button("Save Update", key=f"save_{i}"):
                if update_status(i, new_status):
                    st.success("✅ Status updated successfully!")
                else:
                    st.error("⚠️ Failed to update status.")

# --- Dashboard ---
def dashboard():
    show_header_footer()
    st.title("📊 Dashboard Overview")
    df = load_data()
    if df.empty:
        st.info("No reports yet.")
        return
    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Total Reports", len(df))
    with col2: st.metric("Resolved", (df["Status"]=="Resolved").sum())
    with col3: st.metric("Pending", (df["Status"]=="Pending").sum())
    st.bar_chart(df["Status"].value_counts())

# --- Main ---
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()

    st.sidebar.title("🔧 Navigation")
    page = st.sidebar.radio("Go to:", ["Dashboard", "Manage Reports", "Logout"])
    if page == "Dashboard": dashboard()
    elif page == "Manage Reports": manage_reports()
    elif page == "Logout":
        st.session_state["logged_in"] = False
        st.experimental_rerun()

if __name__ == "__main__":
    main()

