# -*- coding: utf-8 -*-
"""leak_report_app.py"""

import streamlit as st
import os
import re
import gspread
import uuid
from datetime import datetime
from google.oauth2.service_account import Credentials
from email.message import EmailMessage
import smtplib

# --- Colors (used by the UI) ---
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}


# --- Google Sheets Setup ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

def get_gsheet_client():
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def save_report_to_sheet(report):
    client = get_gsheet_client()
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    row = [
        report["Reference"],
        report["Name"],
        report["Contact"],
        report["Municipality"],
        report["Leak Type"],
        report["Location"],
        report["DateTime"],
        report.get("ImageURL", ""),
        report["Status"]
    ]
    sheet.append_row(row)

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def send_reference_email(to_email, ref_code, name):
    smtp_server = "sandbox.smtp.mailtrap.io"
    smtp_port = 2525
    smtp_user = st.secrets["mailtrap"]["user"]
    smtp_password = st.secrets["mailtrap"]["password"]

    sender_email = "leak-reporter@municipality.org"
    subject = "Your Water Leak Report - Reference Code"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = to_email
    msg.set_content(
        f"Hi {name},\n\nThank you for reporting the leak.\nYour reference number is: {ref_code}\n\nUse this code in the app to check the status.\n\nRegards,\nMunicipal Water Department"
    )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --- UI ---
st.title("🚰 Water Leakage Reporting")
# --- Modernized UI ---
st.markdown(
    f"""
    <style>
        .main {{
            background-color: {COLORS['white_smoke']};
        }}
        .report-card {{
            background-color: white;
            padding: 25px 30px;
            border-radius: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .stTabs [data-baseweb="tab-list"] button {{
            background-color: {COLORS['teal_blue']}22;
            color: {COLORS['teal_blue']};
            border-radius: 10px;
            font-weight: 600;
        }}
        .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
            background-color: {COLORS['teal_blue']};
            color: white;
        }}
        .submit-btn {{
            background-color: {COLORS['teal_blue']} !important;
            color: white !important;
            border: none;
            border-radius: 10px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease;
        }}
        .submit-btn:hover {{
            background-color: {COLORS['moonstone_blue']} !important;
            color: white !important;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"<h1 style='text-align:center; color:{COLORS['teal_blue']};'>🚰 Water Leakage Reporting</h1>",
    unsafe_allow_html=True
)

tabs = st.tabs(["📤 Submit Report", "📄 Check Status"])

# -------------------- Submit Report --------------------
with tabs[0]:
    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    st.subheader("💧 Report a Leak")
    st.markdown("Help your community by reporting water leaks accurately and promptly. Fill in the details below:")

    name = st.text_input("Full Name")
    contact = st.text_input("Email Address", placeholder="example@email.com")
    location = st.text_input("Location of Leak", placeholder="e.g. 123 Main Rd, Soweto")
    leak_type = st.selectbox("Type of Leak", ["Burst Pipe", "Leakage", "Sewage Overflow", "Other"])
    municipality = st.selectbox(
        "Select Municipality",
        ["City of Johannesburg", "City of Cape Town", "eThekwini", "Buffalo City", "Mangaung", "Nelson Mandela Bay", "Other"]
    )
    image = st.file_uploader("Upload an image of the leak (optional)", type=["jpg", "jpeg", "png"])

    submit = st.button("🚀 Submit Report", key="submit_report", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        if not name or not contact or not location:
            st.error("❗ All required fields must be filled.")
        elif not is_valid_email(contact):
            st.error("❗ Please enter a valid email address.")
        else:
            image_path = ""
            if image:
                os.makedirs("leak_images", exist_ok=True)
                image_path = os.path.join("leak_images", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.name}")
                with open(image_path, "wb") as f:
                    f.write(image.read())

            ref_code = str(uuid.uuid4())[:8].upper()
            report = {
                "Reference": ref_code,
                "Name": name,
                "Contact": contact,
                "Municipality": municipality,
                "Leak Type": leak_type,
                "Location": location,
                "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ImageURL": image_path,
                "Status": "Pending"
            }

            try:
                save_report_to_sheet(report)
                send_reference_email(contact, ref_code, name)
                st.success(f"✅ Report submitted successfully!\n\nYour reference: **{ref_code}**\n\nCheck your email for confirmation.")
            except Exception as e:
                st.error(f"Failed to save report: {e}")

# -------------------- Check Status --------------------
with tabs[1]:
    st.markdown("<div class='report-card'>", unsafe_allow_html=True)
    st.subheader("🔍 Check Report Status")

    user_ref = st.text_input("Enter Your Reference Code", placeholder="e.g. 4A9F2CDE")

    if st.button("Check Status", use_container_width=True):
        try:
            client = get_gsheet_client()
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            records = sheet.get_all_records()
            match = next((row for row in records if row["Reference"] == user_ref), None)

            if match:
                st.info(f"ℹ️ Status for **{user_ref}**: {match['Status']}")
                st.write(match)

                image_path = match.get("ImageURL", "")
                if image_path and os.path.exists(image_path):
                    st.image(image_path, caption=f"Report {user_ref} Image", use_container_width=True)
                else:
                    st.info("No image uploaded for this report.")
            else:
                st.warning("Reference code not found.")
        except Exception as e:
            st.error(f"Could not check status: {e}")

    st.markdown("</div>", unsafe_allow_html=True)
