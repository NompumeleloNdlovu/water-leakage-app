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
import base64

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

# Swapped background assignments
set_main_background("images/images/360_F_755817004_7CERvuUmlmK4p5cHNFo00S1oh5JVqoj8.jpg")


# Sidebar Navigation
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


# ---------------------- SUBMIT REPORT ----------------------
elif page == "Submit Report":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Submit a Water Leak Report")
    st.markdown("Provide accurate details to help your municipality respond promptly.")

    # --- Name Field ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/user.svg' width='20'>
        <span>Full Name</span>
    </div>
    """, unsafe_allow_html=True)
    name = st.text_input("", placeholder="Enter your full name")

    # --- Email Field ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/mail.svg' width='20'>
        <span>Email Address</span>
    </div>
    """, unsafe_allow_html=True)
    contact = st.text_input("", placeholder="example@email.com")

    # --- Location Field ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/map-pin.svg' width='20'>
        <span>Location of Leak</span>
    </div>
    """, unsafe_allow_html=True)
    location = st.text_input("", placeholder="e.g. 123 Main Rd, Soweto")

    # --- Leak Type Field ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/water.svg' width='20'>
        <span>Type of Leak</span>
    </div>
    """, unsafe_allow_html=True)
    leak_types = ["Burst Pipe", "Leakage", "Sewage Overflow", "Other"]
    leak_type = st.selectbox("", leak_types)

    # --- Municipality Field ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/building.svg' width='20'>
        <span>Select Municipality</span>
    </div>
    """, unsafe_allow_html=True)
    municipalities = [
        "City of Johannesburg", "City of Cape Town", "eThekwini",
        "Buffalo City", "Mangaung", "Nelson Mandela Bay", "Other"
    ]
    municipality = st.selectbox("", municipalities)

    # --- Image Upload ---
    st.markdown("""
    <div style='display:flex; align-items:center; gap:10px; margin-bottom:10px;'>
        <img src='https://cdn.jsdelivr.net/npm/lucide-static/icons/camera.svg' width='20'>
        <span>Upload Image (Optional)</span>
    </div>
    """, unsafe_allow_html=True)
    image = st.file_uploader("", type=["jpg", "jpeg", "png"])

    # --- Submit Button ---
    if st.button("Submit Report", use_container_width=True):
        if not name or not contact or not location:
            st.error("All fields are required.")
        elif not is_valid_email(contact):
            st.error("Please enter a valid email address.")
        else:
            image_path = ""
            if image:
                os.makedirs("leak_images", exist_ok=True)
                image_path = os.path.join("leak_images", f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.name}")
                with open(image_path, "wb") as f:
                    f.write(image.read())
                st.success("Image uploaded successfully.")

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
                st.success(f"Report submitted successfully! Reference Code: {ref_code}")
                st.info("Check your email for confirmation.")
            except Exception as e:
                st.error(f"Failed to save report: {e}")

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------- CHECK STATUS ----------------------
elif page == "Check Status":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.header("Check Report Status")
    user_ref = st.text_input("Enter Your Reference Code")

    if st.button("Check Status", use_container_width=True):
        try:
            client = get_gsheet_client()
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            records = sheet.get_all_records()
            match = next((row for row in records if row["Reference"] == user_ref), None)

            if match:
                st.success(f"Status for {user_ref}: {match['Status']}")
                st.write(match)
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
