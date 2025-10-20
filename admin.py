# -*- coding: utf-8 -*-
"""admin_dashboard_modern_professional_plus.py"""

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

# --- Status Colors (Professional Palette) ---
STATUS_COLORS = {
    "Pending": "#f4a261",      # soft yellow
    "In Progress": "#e76f51",  # orange/red
    "Resolved": "#2a9d8f",     # teal/blue
    "Rejected": "#e63946"      # red
}

# --- Professional Palette ---
HEADER_FOOTER_COLOR = "#006d77"  # deep teal
SIDEBAR_COLOR = "#83c5be"         # light teal
BUTTON_COLOR = "#00b4d8"          # cyan accent
METRIC_COLOR = "#333333"          # dark gray
BG_COLOR = "#f5f5f5"              # off-white

# --- Helper: Connect to Google Sheets ---
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
    st.markdown(f"""
    <style>
    /* Header & Footer */
    .header {{background-color:{HEADER_FOOTER_COLOR}; color:white; text-align:center; padding:25px; font-size:24px; font-family:Cinzel, serif;}}
    .footer {{background-color:{HEADER_FOOTER_COLOR}; color:white; text-align:center; padding:10px; font-family:Cinzel, serif; position:fixed; bottom:0; width:100%;}}

    /* Sidebar */
    section[data-testid="stSidebar"] {{ background-color:{SIDEBAR_COLOR} !important; color:{METRIC_COLOR} !important; padding:1.5rem 1rem; }}
    section[data-testid="stSidebar"] * {{ color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; font-size:16px; }}

    /* Buttons */
    div.stButton > button {{
        color: white !important;
        background-color: {BUTTON_COLOR} !important;
        font-family: 'Cinzel', serif !important;
    }}
    div.stButton > button:hover {{ background-color: #009acb !important; cursor:pointer; }}

    /* Metrics */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{ color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; }}

    /* App background */
    .stApp {{ background-color: {BG_COLOR} !important; color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; }}

    /* Hide keyboard label in sidebar */
    section[data-testid="stSidebar"] div[aria-label="Keyboard"] {{
        display: none !important;
    }}
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

    # --- New Plot 1: Trend Over Time ---
    if "DateReported" in df.columns:
        df['DateReported'] = pd.to_datetime(df['DateReported'])
        time_series = df.groupby(['DateReported','Status']).size().reset_index(name='Count')
        fig3 = px.line(
            time_series,
            x='DateReported',
            y='Count',
            color='Status',
            title="Reports Over Time",
            template="plotly_white",
            color_discrete_map=STATUS_COLORS
        )
        st.subheader("Reports Over Time")
        st.plotly_chart(fig3, use_container_width=True)

    # --- New Plot 2: Stacked Bar by Leak Type ---
    fig4 = px.bar(
        df,
        x='Leak Type',
        color='Status',
        barmode='stack',
        color_discrete_map=STATUS_COLORS,
        template="plotly_white",
        title="Leak Status by Type"
    )
    st.subheader("Leak Status by Type")
    st.plotly_chart(fig4, use_container_width=True)

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
