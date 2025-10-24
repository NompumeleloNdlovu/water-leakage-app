# -*- coding: utf-8 -*-
"""leak_report_app_modern_final.py"""

import streamlit as st
import os
import re
import gspread
import uuid
from datetime import datetime
from pathlib import Path
from email.message import EmailMessage
import smtplib
import base64

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from mimetypes import guess_type
# ---------------------- COLORS ----------------------
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

# ---------------------- GOOGLE SHEETS ----------------------
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

def get_gsheet_client():
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
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

# ---------------------- EMAIL ----------------------
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
        f"Hi {name},\n\nThank you for reporting the leak.\nYour reference number is: {ref_code}\n\n"
        "Use this code in the app to check the status.\n\nRegards,\nMunicipal Water Department"
    )

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as smtp:
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# ---------------------- BACKGROUNDS ----------------------
def set_main_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

def set_sidebar_background(image_file):
    with open(image_file, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            background-image: url("data:image/jpg;base64,{encoded}");
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# ---------------------- PAGE SETUP ----------------------
st.set_page_config(page_title="Drop Watch SA", page_icon="🚰", layout="centered")

set_sidebar_background("images/images/WhatsApp Image 2025-10-21 at 22.42.03_3d1ddaaa.jpg")
st.sidebar.title("Drop Watch SA")
page = st.sidebar.radio("Navigate", ["Home", "Submit Report", "Check Status"])

# ---------------------- GLOBAL STYLE ----------------------
st.markdown(f"""
<style>
body {{
    background-color: {COLORS['white_smoke']};
}}
.card {{
    background-color: rgba(255, 255, 255, 0.9);
    border-radius: 15px;
    padding: 25px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    margin-bottom: 25px;
}}
h1, h2, h3 {{
    color: {COLORS['teal_blue']};
}}
button[kind="primary"], div[data-testid="stButton"] button {{
    background-color: {COLORS['teal_blue']} !important;
    color: white !important;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    padding: 0.6em 1.2em;
}}
button[kind="primary"]:hover, div[data-testid="stButton"] button:hover {{
    background-color: {COLORS['moonstone_blue']} !important;
    color: black !important;
}}
</style>
""", unsafe_allow_html=True)



# ---------------------- HOME PAGE ----------------------
if page == "Home":
    set_main_background("images/images/360_F_1467195115_oNV9D8TzjhTF3rfhbty256ZTHgGodmtW.jpg")
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.title("Welcome to Drop Watch SA")
    st.markdown(
        "This platform enables citizens to report water leaks directly to their municipalities "
        "and track progress until resolution. Your reports help save water and strengthen community infrastructure."
    )
    st.markdown("### How It Works:")
    st.markdown("""
    1. Open **Submit Report** and fill in leak details.  
    2. Receive a **Reference Code** via email.  
    3. Use **Check Status** to monitor the repair progress.
    """)
    st.markdown("</div>", unsafe_allow_html=True)

    
# ---------------------- LOCAL IMAGE UPLOAD ----------------------
def save_image_locally(image):
    """Saves the uploaded image locally and returns the file path."""
    os.makedirs("leak_images", exist_ok=True)
    image_filename = f"{uuid.uuid4()}_{image.name}"
    image_path = os.path.join("leak_images", image_filename)
    with open(image_path, "wb") as f:
        f.write(image.read())
    return image_path

# ---------------------- SUBMIT REPORT PAGE ----------------------
elif page == "Submit Report":
    # --- Banner (small banner image) ---
    banner_path = Path("images/images/360_F_1467195115_oNV9D8TzjhTF3rfhbty256ZTHgGodmtW.jpg")
    if banner_path.exists():
        with open(banner_path, "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <div style="position:relative;width:100%;height:140px;overflow:hidden;border-radius:15px;margin-bottom:25px;">
                <img src="data:image/jpg;base64,{img_base64}" 
                     style="width:100%; height:100%; object-fit:cover; filter: brightness(0.65);">
                <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
                            color:white;font-size:26px;font-weight:bold;text-shadow:1px 1px 4px rgba(0,0,0,0.6);
                            font-family:'Poppins', sans-serif;">
                    Report a Water Leak
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠ Banner image not found. Please check the file path.")

    # --- Form Container ---
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Submit a Water Leak Report")
    st.markdown("Please fill in the details below to help your municipality respond promptly.")

    col1, col2 = st.columns(2)

    with col1:
        name = st.text_input("Full Name")
        contact = st.text_input("Email Address", placeholder="example@email.com")
        municipality = st.selectbox(
            "Select Municipality",
            [
                "City of Johannesburg", "City of Cape Town", "eThekwini",
                "Buffalo City", "Mangaung", "Nelson Mandela Bay", "Other"
            ]
        )

    with col2:
        leak_type = st.selectbox("Type of Leak", ["Burst Pipe", "Leakage", "Sewage Overflow", "Other"])
        location = st.text_input("Location of Leak", placeholder="e.g. 123 Main Rd, Soweto")
        image = st.file_uploader("Upload an image (optional)", type=["jpg", "jpeg", "png"])

    st.markdown("<div style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)
    submit_clicked = st.button("Submit Report", use_container_width=False)
    st.markdown("</div>", unsafe_allow_html=True)

    if submit_clicked:
        if not name or not contact or not location:
            st.error("All fields are required.")
        elif not is_valid_email(contact):
            st.error("Please enter a valid email address.")
        else:
            # --- Save Image Locally ---
            if image:
                os.makedirs("leak_images", exist_ok=True)
                image_path = os.path.join("leak_images", f"{uuid.uuid4()}_{image.name}")
                with open(image_path, "wb") as f:
                    f.write(image.read())
            else:
                image_path = ""

            ref_code = str(uuid.uuid4())[:8].upper()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            report = {
                "Reference": ref_code,
                "Name": name,
                "Contact": contact,
                "Municipality": municipality,
                "Leak Type": leak_type,
                "Location": location,
                "DateTime": timestamp,
                "ImageURL": image_path,
                "Status": "Pending"
            }

            try:
                save_report_to_sheet(report)
                send_reference_email(contact, ref_code, name)

                st.markdown(f"""
                    <div style="background-color:#E8F5E9;border-left:5px solid #008080;
                                border-radius:12px;padding:20px;margin-top:30px;box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                        <h3 style="color:#006666;">✅ Report Submitted Successfully!</h3>
                        <p><b>Reference Code:</b> {ref_code}</p>
                        <p><b>Date & Time:</b> {timestamp}</p>
                        <p><b>Confirmation sent to:</b> {contact}</p>
                        <p style="margin-top:10px;">Use your reference code under <b>Check Status</b> to track your report.</p>
                    </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Failed to save report: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------------- CHECK STATUS PAGE ----------------------
if page == "Check Status":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Check Report Status")
    user_ref = st.text_input("Enter Your Reference Code")

    if st.button("Check Status", use_container_width=True):
        try:
            client = get_gsheet_client()  # or your database client
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            records = sheet.get_all_records()
            match = next((row for row in records if row["Reference"] == user_ref), None)

            if match:
                st.success(f"Status for {user_ref}: {match['Status']}")
                st.write(match)

                # Display image if exists
                image_path = match.get("ImageURL", "")
                if image_path and os.path.exists(image_path):
                    st.image(image_path, caption=f"Report {user_ref}", use_column_width=True)
                else:
                    st.info("No image uploaded for this report.")
            else:
                st.warning("Reference code not found.")

        except Exception as e:
            st.error(f"Could not check status: {e}")

    st.markdown("</div>", unsafe_allow_html=True)

