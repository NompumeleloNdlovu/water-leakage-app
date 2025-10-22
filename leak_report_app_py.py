# -*- coding: utf-8 -*-
import streamlit as st
import os
import re
import gspread
import uuid
from datetime import datetime
from google.oauth2.service_account import Credentials
from email.message import EmailMessage
import smtplib

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
        report["Status"],
        report.get("ImageURL", "")
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

tabs = st.tabs(["📤 Submit Report", "📄 Check Status"])

with tabs[0]:
    st.subheader("Report a Leak")
    st.markdown("👥 **Help your community by reporting water leaks accurately and promptly.**")
    st.markdown("Fill in the details below:")

    name = st.text_input("Full Name")
    contact = st.text_input("Email Address", placeholder="example@email.com")
    location = st.text_input("Location of Leak", placeholder="e.g. 123 Main Rd, Soweto")
    leak_types = ["Burst Pipe", "Leakage", "Sewage Overflow", "Other"]
    description = st.selectbox("Type of Leak", leak_types)

    municipalities = [
        "City of Johannesburg", "City of Cape Town", "eThekwini",
        "Buffalo City", "Mangaung", "Nelson Mandela Bay", "Other"
    ]
    municipality = st.selectbox("Select Municipality", municipalities)

    image = st.file_uploader("Upload an image of the leak (optional)", type=["jpg", "jpeg", "png"])

    if st.button("Submit Report"):
        if not name or not contact or not location:
            st.error("❗ All fields are required.")
        elif not is_valid_email(contact):
            st.error("❗ Please enter a valid email.")
        else:
            # Save uploaded image to shared folder
            image_path = ""
            if image:
                os.makedirs("static/leak_images", exist_ok=True)
                image_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.name}"
                image_path = os.path.join("static/leak_images", image_filename)
                with open(image_path, "wb") as f:
                    f.write(image.read())
                st.success(f"Image uploaded successfully: {image_filename}")

            # Generate reference
            ref_code = str(uuid.uuid4())[:8].upper()

            report = {
                "Reference": ref_code,
                "Name": name,
                "Contact": contact,
                "Municipality": municipality,
                "Leak Type": description,
                "Location": location,
                "DateTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Status": "Pending",
                "ImageURL": image_path
            }

            try:
                save_report_to_sheet(report)
                send_reference_email(contact, ref_code, name)
                st.success(f"✅ Report submitted. Reference: **{ref_code}**\n\nCheck your email for confirmation.")
            except Exception as e:
                st.error(f"Failed to save report: {e}")

with tabs[1]:
    st.subheader("Check Report Status")
    user_ref = st.text_input("Enter Your Reference Code")

    if st.button("Check Status"):
        try:
            client = get_gsheet_client()
            sheet = client.open_by_key(SPREADSHEET_ID).sheet1
            records = sheet.get_all_records()
            match = next((row for row in records if row["Reference"] == user_ref), None)

            if match:
                st.info(f"ℹ️ Status for **{user_ref}**: {match['Status']}")
                st.write(match)

                # Display uploaded image if available
                image_path = match.get("ImageURL", "")
                if image_path and os.path.exists(image_path):
                    st.image(image_path, caption=f"Report {user_ref} Image", use_column_width=True)
                else:
                    st.markdown("<i>No image uploaded for this report.</i>", unsafe_allow_html=True)
            else:
                st.warning("Reference code not found.")
        except Exception as e:
            st.error(f"Could not check status: {e}")
