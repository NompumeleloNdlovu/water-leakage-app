# -*- coding: utf-8 -*-
"""admin_dashboard_modern_minimal.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# --- App Config ---
st.set_page_config(
    page_title="Drop Watch SA Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Secrets ---
ADMIN_CODE = st.secrets["general"]["admin_code"]
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Status Colors ---
STATUS_COLORS = {
    "Pending": "#f4a261",
    "In Progress": "#e76f51",
    "Resolved": "#2a9d8f",
    "Rejected": "#e63946"
}

# --- Helper: Connect to Google Sheets and load data ---
@st.cache_data
def get_sheet_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    return sheet, df

# --- Helper: Update report ---
def update_report(sheet, row_idx, status):
    try:
        sheet.update_cell(row_idx, 8, status)
        sheet.update_cell(row_idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.success(f"Report updated to '{status}'.")
    except Exception as e:
        st.error(f"Failed to update: {e}")

# --- Login Page ---
def login_page():
    st.markdown("### Admin Login")
    code = st.text_input("Enter Admin Code:", type="password")
    if st.button("Login"):
        if code == ADMIN_CODE:
            st.session_state["logged_in"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid admin code")

# --- Decorator for pages requiring login ---
def login_required(func):
    if not st.session_state.get("logged_in", False):
        login_page()
        return False
    return True

# --- Header / Footer ---
def show_header_footer():
    st.markdown("""
    <style>
    /* Header & Footer */
    .header {background-color:#4a4e69; color:white; text-align:center; padding:25px; font-size:24px; font-family:Cinzel, serif;}
    .footer {background-color:#4a4e69; color:white; text-align:center; padding:10px; font-family:Cinzel, serif; position:fixed; bottom:0; width:100%;}

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color:#9a8c98 !important; color:#222222 !important; padding:1.5rem 1rem; }
    section[data-testid="stSidebar"] * { color:#222222 !important; font-family:'Cinzel', serif !important; font-size:16px; }

    /* Buttons */
    div.stButton > button {
        color: white !important;
        background-color: #c9ada7 !important;
        font-family: 'Cinzel', serif !important;
    }
    div.stButton > button:hover { background-color: #b794a3 !important; cursor:pointer; }

    /* Metrics */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color:#222222 !important; font-family:'Cinzel', serif !important; }

    /* App background */
    .stApp { background-color: #ffffff !important; color:#222222 !important; font-family:'Cinzel', serif !important; }

    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header">Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">&copy; 2025 Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:80px; margin-bottom:60px;'></div>", unsafe_allow_html=True)

# --- Dashboard Page ---
def dashboard_page(df):
    st.header("Dashboard Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"]=="Pending").sum())
    col3.metric("In Progress", (df["Status"]=="In Progress").sum())
    col4.metric("Resolved", (df["Status"]=="Resolved").sum())

    st.subheader("Reports by Municipality")
    fig1 = px.bar(
        df,
        x="Municipality",
        color="Status",
        barmode="group",
        color_discrete_map=STATUS_COLORS,
        template="plotly_white"
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Leak Types Reported")
    fig2 = px.pie(
        df,
        names="Leak Type",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# --- Manage Reports Page ---
def manage_reports_page(df, sheet):
    st.header("Manage Reports")
    for idx, report in enumerate(df.to_dict("records"), start=2):
        with st.expander(f"Report {report['ReportID']} - {report['Name']}"):
            st.markdown(f"""
                **Municipality:** {report['Municipality']}  
                **Leak Type:** {report['Leak Type']}  
                **Status:** {report['Status']}  
            """)
            status = st.selectbox(
                "Update Status",
                options=["Pending", "In Progress", "Resolved", "Rejected"],
                index=["Pending", "In Progress", "Resolved", "Rejected"].index(report.get("Status", "Pending")),
                key=f"status_{idx}"
            )
            if st.button("Update", key=f"update_{idx}"):
                update_report(sheet, idx, status)

# --- Main App ---
def main():
    show_header_footer()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not login_required(main):
        return

    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.experimental_rerun()

    sheet, df = get_sheet_data()
    if df.empty:
        st.info("No reports found.")
        return

    df.columns = df.columns.str.strip()
    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, sheet)

if __name__ == "__main__":
    main()

