# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt  # required for pie chart

# --- CONFIG ---
st.set_page_config(page_title="Drop Watch SA Admin Panel", layout="wide")

# --- GOOGLE SHEETS SETUP ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Load credentials from Streamlit secrets
creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

sheet_id = st.secrets["general"]["sheet_id"]
sheet = client.open_by_key(sheet_id).sheet1

# Admin code
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- HEADER + FOOTER ---
def show_header_footer():
    st.markdown("""
        <style>
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
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
                z-index: 999;
            }
            .header a {
                display: flex;
                align-items: center;
                gap: 12px;
                color: white !important;
                text-decoration: none !important;
            }
            .header img { height: 45px; width: auto; border-radius: 6px; }
            .header-spacer { height: 90px; }

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
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()  # strip whitespace
    return df

# --- UPDATE STATUS ---
def update_status(index, new_status):
    df = load_data()
    if 0 <= index < len(df):
        cell = f"H{index + 2}"  # column H = Status
        sheet.update(cell, new_status)
        return True
    return False

# --- LOGIN PAGE ---
def login_page():
    show_header_footer()

    st.markdown("""
        <style>
            .login-container { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 75vh; text-align: center; }
            .login-card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 380px; text-align: center; }
            .login-card h2 { font-family: 'Cinzel', serif; font-weight: 600; color: #0d6efd; margin-bottom: 10px; }
            .login-card img { height: 80px; margin-bottom: 15px; }
            .stTextInput input { border-radius: 8px !important; padding: 10px !important; font-size: 16px !important; }
            div.stButton > button { width: 100%; border-radius: 8px !important; font-weight: 600; background-color: #0d6efd !important; color: white !important; }
            div.stButton > button:hover { background-color: #0b5ed7 !important; }
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
        with st.expander(f"📍 Report #{i+1} — {row.get('Location', 'Unknown')}"):
            st.write(f"**Name:** {row.get('Name','N/A')}")
            st.write(f"**Contact:** {row.get('Contact','N/A')}")
            st.write(f"**Municipality:** {row.get('Municipality','N/A')}")
            st.write(f"**Leak Type:** {row.get('Leak Type','N/A')}")
            st.write(f"**Date/Time:** {row.get('DateTime','N/A')}")
            st.write(f"**Status:** {row.get('Status','Pending')}")
            st.write(f"**Image URL:** {row.get('Image','')}")

            image_url = row.get("Image", "")
            if image_url:
                if image_url.lower().endswith(('.mp4', '.mov', '.avi')):
                    st.video(image_url)
                else:
                    st.image(image_url, caption="Leak Evidence", use_container_width=True)

            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], key=f"status_{i}")
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

    # Convert DateTime to pandas datetime
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] == "Pending").sum())

    # --- Bar Chart ---
    st.markdown("### 📊 Status Breakdown (Bar Chart)")
    st.bar_chart(df["Status"].value_counts())

    # --- Pie Chart ---
    st.markdown("### 🥧 Leak Type Distribution (Pie Chart)")
    pie_data = df["Leak Type"].value_counts()
    fig, ax = plt.subplots(figsize=(5, 5))
    pie_data.plot.pie(
        autopct="%1.1f%%",
        startangle=90,
        ylabel="",
        colors=plt.get_cmap("tab20").colors,
        ax=ax
    )
    st.pyplot(fig)

    # --- Time Series Chart ---
    st.markdown("### 📈 Reports Over Time (Line Chart)")
    if not df["DateTime"].isnull().all():
        time_data = df.groupby(df["DateTime"].dt.date).size()
        st.line_chart(time_data)
    else:
        st.info("No valid dates for time chart.")

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
