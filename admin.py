import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# ------------------ SECRETS & CONFIG ------------------
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]
SHEET_KEY = st.secrets["general"]["sheet_id"]

# Squilla Fund color palette
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Drop Watch SA",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"
if "rerun_after_login" not in st.session_state:
    st.session_state.rerun_after_login = False

# ------------------ GOOGLE SHEET ------------------
scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
client = gspread.authorize(creds)

try:
    sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet1")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# ------------------ AUTHENTICATION ------------------
def login_page():
    st.markdown(
        f"""
        <div style="background-color:{COLORS['moonstone_blue']};padding:20px;border-radius:10px;">
            <h1 style="text-align:center;color:black;">Drop Watch SA - Admin Login</h1>
        </div>
        """,
        unsafe_allow_html=True
    )
    code = st.text_input("Enter Admin Code", type="password")
    if st.button("Login"):
        if code == st.secrets["general"]["admin_code"]:
            st.session_state.logged_in = True
            st.session_state.page = "Dashboard"
            st.session_state.rerun_after_login = True
        else:
            st.error("Invalid code")

# ------------------ DASHBOARD ------------------
def dashboard_page():
    st.markdown(
        f"""
        <div style="background-color:{COLORS['moonstone_blue']};padding:15px;border-radius:10px;margin-bottom:10px;">
            <h1 style="color:black;text-align:center;">Drop Watch SA - Dashboard</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(f"<div style='background-color:{COLORS['white_smoke']};padding:10px;border-radius:10px;'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] == "Pending").sum())

    if "Leak Type" in df.columns:
        bar_data = df['Leak Type'].value_counts().reset_index()
        bar_data.columns = ['Leak Type', 'Count']
        fig_bar = px.bar(
            bar_data,
            x='Leak Type',
            y='Count',
            color='Leak Type',
            color_discrete_sequence=[
                COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']
            ],
            title="Leak Reports by Type"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    if "Status" in df.columns:
        pie_data = df['Status'].value_counts().reset_index()
        pie_data.columns = ['Status', 'Count']
        fig_pie = px.pie(
            pie_data,
            names='Status',
            values='Count',
            color='Status',
            color_discrete_sequence=[COLORS['moonstone_blue'], COLORS['magic_mint']],
            title="Reports by Status"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    if "DateTime" in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        time_data = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
        fig_time = px.line(
            time_data,
            x='DateTime',
            y='Count',
            title="Reports Over Time",
            markers=True,
            color_discrete_sequence=[COLORS['teal_blue']]
        )
        st.plotly_chart(fig_time, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ MANAGE REPORTS ------------------
def manage_reports_page():
    st.markdown(f"<div style='background-color:{COLORS['powder_blue']};padding:10px;border-radius:10px;'>", unsafe_allow_html=True)
    st.markdown("## Manage Reports")

    for i, row in df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(row)
            # ---------------- FIXED STATUS DROPDOWN ----------------
            current_status = row.get("Status", "Pending")  # ensure status exists
            options = ["Pending", "Resolved"]
            if current_status not in options:
                current_status = "Pending"  # fallback for unknown status

            new_status = st.selectbox(
                "Update Status",
                options,
                index=options.index(current_status),
                key=f"status_{i}"
            )

            if st.button("Update", key=f"update_{i}"):
                try:
                    cell = sheet.find(str(row['ReportID']))
                    sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                    st.success(f"Status updated to {new_status}")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")
            # -------------------------------------------------------

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ SIDEBAR NAVIGATION ------------------
if st.session_state.logged_in:
    st.sidebar.markdown(f"<h3 style='color:black;'>Drop Watch SA</h3>", unsafe_allow_html=True)

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.experimental_rerun()

    page = st.sidebar.radio(
        "Navigation",
        ("Dashboard", "Manage Reports"),
        index=0 if st.session_state.page == "Dashboard" else 1
    )
    st.session_state.page = page

# ------------------ PAGE RENDER ------------------
if not st.session_state.logged_in:
    login_page()
    if st.session_state.rerun_after_login:
        st.session_state.rerun_after_login = False
        st.experimental_rerun()
else:
    if st.session_state.page == "Dashboard":
        dashboard_page()
    elif st.session_state.page == "Manage Reports":
        manage_reports_page()
