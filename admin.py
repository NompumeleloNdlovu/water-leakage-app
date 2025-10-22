import streamlit as st
import pandas as pd
import gspread
import plotly.express as px
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import time

# ------------------ CONFIG ------------------
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]
SHEET_KEY = st.secrets["general"]["sheet_id"]

COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

st.set_page_config(page_title="Drop Watch SA", layout="wide", initial_sidebar_state="expanded")

# ------------------ GOOGLE AUTH ------------------
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
client = gspread.authorize(creds)

# ------------------ DATA LOADING ------------------
@st.cache_data(ttl=60)
def load_reports():
    try:
        sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet1")
        df = pd.DataFrame(sheet.get_all_records())
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Failed to load Google Sheet: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def load_admins():
    try:
        sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet2")
        admins_df = pd.DataFrame(sheet.get_all_records())
        admins_df.columns = admins_df.columns.str.strip()
        admins_df = admins_df.applymap(lambda x: str(x).strip() if isinstance(x, str) else x)
        return admins_df
    except Exception as e:
        st.error(f"Failed to load Admin Sheet: {e}")
        return pd.DataFrame()

# ------------------ LOGIN ------------------
def login_page():
    st.title("🔐 Drop Watch SA - Admin Login")
    st.markdown("Enter your admin code to access your municipality dashboard.")
    code = st.text_input("Admin Code", type="password")

    admins_df = load_admins()

    if st.button("Login"):
        if not code:
            st.warning("Please enter your code.")
            return

        if not admins_df.empty and "AdminCode" in admins_df.columns:
            admin_info = admins_df[admins_df["AdminCode"] == code]
            if not admin_info.empty:
                st.session_state.logged_in = True
                st.session_state.admin_name = admin_info["AdminName"].iloc[0]
                st.session_state.admin_municipality = admin_info["Municipality"].iloc[0]
                st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                st.rerun()
            else:
                st.error("Invalid code. Please try again.")
        else:
            st.error("Admin sheet not loaded or missing AdminCode column.")

# ------------------ SIDEBAR ------------------
def custom_sidebar():
    with st.sidebar:
        st.image("images/images/WhatsApp Image 2025-10-21 at 22.42.03_3d1ddaaa.jpg", use_container_width=True)
        st.markdown(
            f"""
            <div style="background-color:{COLORS['teal_blue']};padding:15px;border-radius:10px;text-align:center;">
                <h2 style="color:white;">Drop Watch SA</h2>
            </div>
            """,
            unsafe_allow_html=True
        )

        page = st.radio("📍 Navigate", ["Home", "Dashboard", "Municipal Overview", "Manage Reports"])

        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Logged out successfully.")
            st.rerun()

        return page

# ------------------ HOME PAGE ------------------
def home_page():
    current_hour = datetime.now().hour
    if current_hour < 12:
        greeting = "Good morning"
    elif current_hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    st.markdown(
        f"""
        <style>
        .banner {{
            position: relative;
            background-image: url('images/images/WhatsApp Image 2025-10-22 at 00.08.08_8c98bfbb.jpg');
            background-size: cover;
            background-position: center;
            border-radius: 15px;
            height: 330px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            text-shadow: 2px 2px 6px #000;
        }}
        .banner::before {{
            content: "";
            position: absolute;
            inset: 0;
            background: rgba(0, 0, 0, 0.55);
            border-radius: 15px;
        }}
        .banner-content {{
            position: relative;
            z-index: 1;
            text-align: center;
        }}
        </style>

        <div class="banner">
            <div class="banner-content">
                <h1>{greeting}, {st.session_state.admin_name}</h1>
                <p>Welcome to the {st.session_state.admin_municipality} Admin Portal</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 👋 Overview")
    st.info("Here’s a snapshot of your municipality’s recent reports and activity.")

    reports_df = load_reports()
    if reports_df.empty:
        st.warning("No reports found yet.")
        return

    muni_df = reports_df[reports_df["Municipality"] == st.session_state.admin_municipality]

    total_reports = len(muni_df)
    resolved = (muni_df["Status"] == "Resolved").sum() if "Status" in muni_df.columns else 0
    pending = (muni_df["Status"] == "Pending").sum() if "Status" in muni_df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", total_reports)
    col2.metric("Resolved", resolved)
    col3.metric("Pending", pending)

    st.markdown("### 📈 Report Trends (Last 30 Days)")
    if "Date" in muni_df.columns:
        muni_df["Date"] = pd.to_datetime(muni_df["Date"], errors="coerce")
        recent = muni_df[muni_df["Date"] >= (datetime.now() - timedelta(days=30))]
        if not recent.empty:
            trend = recent.groupby(recent["Date"].dt.date).size().reset_index(name="Reports")
            fig = px.area(trend, x="Date", y="Reports", title=f"Recent Reports - {st.session_state.admin_municipality}", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No reports in the last 30 days.")
    else:
        st.info("No date column available in data.")

# ------------------ DASHBOARD ------------------
def dashboard_page():
    df = load_reports()
    if df.empty:
        st.warning("No data found.")
        return

    st.title("📊 Overall Dashboard Metrics")
    st.metric("Total Reports", len(df))
    st.metric("Resolved", (df["Status"] == "Resolved").sum())
    st.metric("Pending", (df["Status"] == "Pending").sum())

    if "Leak Type" in df.columns:
        bar_data = df['Leak Type'].value_counts().reset_index()
        bar_data.columns = ['Leak Type', 'Count']
        fig_bar = px.bar(bar_data, x='Leak Type', y='Count', color='Leak Type', title="Leak Reports by Type")
        st.plotly_chart(fig_bar, use_container_width=True)

    if "Status" in df.columns:
        pie_data = df['Status'].value_counts().reset_index()
        pie_data.columns = ['Status', 'Count']
        fig_pie = px.pie(pie_data, names='Status', values='Count', title="Reports by Status")
        st.plotly_chart(fig_pie, use_container_width=True)

# ------------------ MUNICIPAL OVERVIEW ------------------
def municipal_overview_page():
    st.title("🏙 Municipal Overview")
    df = load_reports()
    if df.empty:
        st.warning("No data found.")
        return

    muni_counts = df["Municipality"].value_counts().reset_index()
    muni_counts.columns = ["Municipality", "Reports"]
    fig = px.bar(muni_counts, x="Municipality", y="Reports", color="Municipality", title="Reports per Municipality")
    st.plotly_chart(fig, use_container_width=True)

# ------------------ MANAGE REPORTS ------------------
def manage_reports_page():
    st.title("🛠 Manage Reports")
    df = load_reports()
    if df.empty:
        st.warning("No data found.")
        return

    admin_muni = st.session_state.admin_municipality
    muni_df = df[df["Municipality"] == admin_muni]

    for i, row in muni_df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(row)
            current_status = row.get("Status", "Pending")
            new_status = st.selectbox(
                "Update Status", ["Pending", "Resolved"],
                index=["Pending", "Resolved"].index(current_status) if current_status in ["Pending", "Resolved"] else 0,
                key=f"status_{i}"
            )
            if st.button("Update", key=f"update_{i}"):
                try:
                    sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet1")
                    cell = sheet.find(str(row["ReportID"]))
                    sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                    st.success("Status updated!")
                    st.cache_data.clear()
                except Exception as e:
                    st.error(f"Failed to update status: {e}")

# ------------------ MAIN APP ------------------
if "logged_in" not in st.session_state:
    login_page()
else:
    page = custom_sidebar()
    if page == "Home":
        home_page()
    elif page == "Dashboard":
        dashboard_page()
    elif page == "Municipal Overview":
        municipal_overview_page()
    elif page == "Manage Reports":
        manage_reports_page()

