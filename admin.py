# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage

# --- CONFIG ---
st.set_page_config(page_title="Drop Watch SA Admin Panel", layout="wide")

# --- SECRETS & GOOGLE SHEETS SETUP ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Load secrets
GSA = st.secrets["google_service_account"]           # your service account JSON fields
MAIL_SECR = st.secrets.get("mailtrap", {})           # mailtrap user/password
GENERAL = st.secrets.get("general", {})              # admin_code, sheet_id, optional notify_email

# Required checks
if "sheet_id" not in GENERAL:
    st.error("Missing sheet_id in st.secrets['general']. Please add it and redeploy.")
    st.stop()
if "admin_code" not in GENERAL:
    st.error("Missing admin_code in st.secrets['general']. Please add it and redeploy.")
    st.stop()

SHEET_ID = GENERAL["sheet_id"]
ADMIN_CODE = GENERAL["admin_code"]

# Create Google credentials & client
try:
    creds = Credentials.from_service_account_info(GSA, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    sheet = sh.sheet1  # uses the first worksheet (Sheet1)
except Exception as e:
    st.error("Failed to connect to Google Sheets. Check service account, sheet_id and sharing (share the sheet with the service account email).")
    st.exception(e)
    st.stop()

# --- UTILS ---
def colnum_to_letter(n):
    """Convert 1-indexed column number to Excel-style letters"""
    string = ""
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        string = chr(65 + remainder) + string
    return string

def load_data():
    """Load sheet into DataFrame and normalize columns"""
    try:
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        # Ensure consistent columns and strip spaces
        df.columns = df.columns.str.strip()
        # If empty, create expected columns
        if df.empty:
            df = pd.DataFrame(columns=["ReportID","Name","Contact","Municipality","Leak Type","Location","DateTime","Status","Image"])
        return df
    except Exception as e:
        st.error("Failed to load Google Sheet data.")
        st.exception(e)
        return pd.DataFrame(columns=["ReportID","Name","Contact","Municipality","Leak Type","Location","DateTime","Status","Image"])

def find_column_index(df, col_name):
    """Return 1-indexed column number for col_name. Returns None if not found."""
    try:
        idx = df.columns.get_loc(col_name) + 1
        return idx
    except Exception:
        return None

def update_status(index, new_status):
    """
    Update the 'Status' column for row index (0-based) using a 2D array update,
    and dynamic detection of the 'Status' column.
    """
    df = load_data()
    if df.empty or not (0 <= index < len(df)):
        return False, "Invalid row index or empty sheet."

    status_col_idx = find_column_index(df, "Status")
    if status_col_idx is None:
        return False, "'Status' column not found in sheet."

    col_letter = colnum_to_letter(status_col_idx)
    cell = f"{col_letter}{index + 2}"  # +2 because header is row 1
    try:
        sheet.update(cell, [[new_status]])  # 2D array required by gspread
        return True, None
    except Exception as e:
        return False, str(e)

def append_report(row_dict):
    """
    Append a new report row. row_dict keys: Name, Contact, Municipality, Leak Type, Location, Image(optional)
    Generates ReportID (max+1), DateTime now, Status="Pending"
    """
    df = load_data()
    # determine next ReportID
    try:
        if "ReportID" in df.columns and not df["ReportID"].empty:
            # handle numeric or string ids
            existing = pd.to_numeric(df["ReportID"], errors="coerce")
            max_id = int(existing.max()) if not existing.isna().all() else 0
            next_id = max_id + 1
        else:
            next_id = 1
    except Exception:
        next_id = 1

    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    new_row = [
        next_id,
        row_dict.get("Name", ""),
        row_dict.get("Contact", ""),
        row_dict.get("Municipality", ""),
        row_dict.get("Leak Type", ""),
        row_dict.get("Location", ""),
        now_str,
        "Pending",
        row_dict.get("Image", "")
    ]

    try:
        # Append as a new row at the bottom
        sheet.append_row(new_row, value_input_option="USER_ENTERED")
        return True, next_id
    except Exception as e:
        return False, str(e)

def send_mailtrap_notification(report_id, row_dict):
    """
    Sends a simple email via Mailtrap SMTP. Mailtrap credentials are expected in st.secrets['mailtrap'].
    If no recipient is set in st.secrets['general']['notify_email'], message is sent to a default
    dummy address which Mailtrap will capture.
    """
    user = MAIL_SECR.get("user")
    password = MAIL_SECR.get("password")
    if not user or not password:
        # mailtrap not configured; skip silently (or show a small warning in UI)
        return False, "Mailtrap credentials not found in st.secrets['mailtrap']."

    recipient = GENERAL.get("notify_email", "reports@dropwatch.local")
    msg = EmailMessage()
    msg["From"] = "no-reply@dropwatch.local"
    msg["To"] = recipient
    msg["Subject"] = f"New Leak Report #{report_id}"
    body = f"""
    A new leak report was submitted.

    ReportID: {report_id}
    Name: {row_dict.get('Name')}
    Contact: {row_dict.get('Contact')}
    Municipality: {row_dict.get('Municipality')}
    Leak Type: {row_dict.get('Leak Type')}
    Location: {row_dict.get('Location')}
    Image: {row_dict.get('Image')}
    """
    msg.set_content(body)

    try:
        # Mailtrap default port is 2525; host is smtp.mailtrap.io
        with smtplib.SMTP("smtp.mailtrap.io", 2525, timeout=10) as server:
            server.login(user, password)
            server.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

# --- UI blocks ---
def show_header_footer():
    st.markdown("""
    <style>
    .header {position: fixed; top:0; left:0; width:100%; display:flex; align-items:center; justify-content:center; gap:12px; background: linear-gradient(90deg,#0d6efd,#0b5ed7); color:white; padding:18px 0; font-weight:600; font-size:24px; z-index:999;}
    .header img{height:40px; margin-right:8px;}
    .header-spacer{height:70px;}
    .footer {position: fixed; bottom:0; left:0; width:100%; background:#0d6efd; color:#fff; text-align:center; padding:8px 0; z-index:999;}
    .footer-spacer{height:40px;}
    </style>
    <div class="header"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png">Drop Watch SA Admin Panel</div>
    <div class="header-spacer"></div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='footer'>© 2025 Drop Watch SA</div><div class='footer-spacer'></div>", unsafe_allow_html=True)

# --- Pages ---
def dashboard_page():
    show_header_footer()
    st.title("📊 Dashboard")
    df = load_data()

    if df.empty:
        st.info("No reports yet.")
        return

    # Normalize DateTime
    if "DateTime" in df.columns:
        df["DateTimeParsed"] = pd.to_datetime(df["DateTime"], errors="coerce")
    else:
        df["DateTimeParsed"] = pd.NaT

    # Metrics row
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", int((df.get("Status","") == "Resolved").sum()))
    with col3:
        st.metric("Pending", int((df.get("Status","") == "Pending").sum()))

    # Bar chart: Reports per Municipality
    st.subheader("Reports by Municipality")
    muni_counts = df["Municipality"].fillna("Unknown").value_counts()
    st.bar_chart(muni_counts)

    # Pie chart: Leak Type distribution (modern palette)
    st.subheader("Leak Type Distribution")
    lt_counts = df["Leak Type"].fillna("Unknown").value_counts()
    fig, ax = plt.subplots(figsize=(5,5))
    colors = plt.get_cmap("tab20").colors
    lt_counts.plot.pie(autopct="%1.1f%%", startangle=90, ylabel="", ax=ax, colors=colors)
    st.pyplot(fig)

    # Time series: reports over time (by date)
    st.subheader("Reports Over Time")
    if not df["DateTimeParsed"].isnull().all():
        time_series = df.groupby(df["DateTimeParsed"].dt.date).size()
        st.line_chart(time_series)
    else:
        st.info("No valid DateTime values to plot time series.")

    # Show data table
    st.subheader("All Reports (raw data)")
    st.dataframe(df)

def submit_report_page():
    show_header_footer()
    st.title("📝 Submit a Leak Report")
    with st.form("report_form", clear_on_submit=True):
        name = st.text_input("Name")
        contact = st.text_input("Contact")
        municipality = st.text_input("Municipality")
        leak_type = st.selectbox("Leak Type", ["Burst", "Drip", "Other"])
        location = st.text_input("Location / Address")
        image_url = st.text_input("Image URL (optional)")
        submitted = st.form_submit_button("Submit Report")

    if submitted:
        row = {
            "Name": name,
            "Contact": contact,
            "Municipality": municipality,
            "Leak Type": leak_type,
            "Location": location,
            "Image": image_url
        }
        ok, info = append_report(row)
        if ok:
            report_id = info
            st.success(f"Report submitted (ReportID {report_id}). Thank you!")
            # Try sending Mailtrap notification if configured
            sent, sent_info = send_mailtrap_notification(report_id, row)
            if not sent:
                st.warning(f"Notification not sent: {sent_info}")
        else:
            st.error(f"Failed to submit report: {info}")

def admin_login_and_manage_page():
    show_header_footer()
    st.title("🔐 Admin Login / Manage Reports")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        code = st.text_input("Admin code", type="password")
        if st.button("Login"):
            if code == ADMIN_CODE:
                st.session_state["logged_in"] = True
                st.success("Logged in.")
                st.experimental_rerun()
            else:
                st.error("Invalid admin code.")
        return

    # Admin is logged in -> show manage interface
    st.write("You are logged in as admin. You can update report statuses below.")
    df = load_data()
    if df.empty:
        st.info("No reports to manage.")
        return

    # Show each report with controls
    for i, row in df.iterrows():
        with st.expander(f"Report #{int(row.get('ReportID', i+1))} — {row.get('Location','Unknown')}"):
            st.write(f"**Name:** {row.get('Name','N/A')}")
            st.write(f"**Contact:** {row.get('Contact','N/A')}")
            st.write(f"**Municipality:** {row.get('Municipality','N/A')}")
            st.write(f"**Leak Type:** {row.get('Leak Type','N/A')}")
            st.write(f"**DateTime:** {row.get('DateTime','N/A')}")
            st.write(f"**Current Status:** {row.get('Status','Pending')}")
            img = row.get("Image","")
            if img:
                if img.lower().endswith(('.mp4', '.mov', '.avi')):
                    st.video(img)
                else:
                    st.image(img, use_container_width=True)

            # Status update control
            options = ["Pending", "In Progress", "Resolved"]
            current = row.get("Status","Pending")
            try:
                index_default = options.index(current) if current in options else 0
            except Exception:
                index_default = 0
            new_status = st.selectbox("Update Status", options, index=index_default, key=f"status_{i}")
            if st.button("Save Status", key=f"save_{i}"):
                success, err = update_status(i, new_status)
                if success:
                    st.success("Status updated.")
                else:
                    st.error(f"Failed to update status: {err}")

    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.experimental_rerun()

# --- App main ---
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to:", ["Dashboard", "Submit Report", "Admin"])

    if page == "Dashboard":
        dashboard_page()
    elif page == "Submit Report":
        submit_report_page()
    elif page == "Admin":
        admin_login_and_manage_page()

if __name__ == "__main__":
    main()
