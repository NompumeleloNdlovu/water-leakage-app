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
    page_title="Drop Watch Admin",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
    <style>
    /* Background */
    .stApp {{
        background-color: {COLORS['white_smoke']};
    }}
    /* Hide hamburger menu and footer */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    </style>
""", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# ------------------ GOOGLE SHEET ------------------
scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
client = gspread.authorize(creds)

try:
    sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet1")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()  # remove extra spaces
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# ------------------ MODERN LOGIN PAGE ------------------
def login_page():
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;align-items:center;height:80vh;">
            <div style="background-color:white;padding:50px;border-radius:15px;box-shadow:0 8px 16px rgba(0,0,0,0.2);width:400px;">
                <h2 style="text-align:center;color:{COLORS['teal_blue']};margin-bottom:30px;">Drop Watch Admin Login</h2>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    with st.form("login_form", clear_on_submit=False):
        code = st.text_input("Admin Code", placeholder="Enter your admin code", type="password")
        submitted = st.form_submit_button("Login", help="Click to login")
        if submitted:
            if code == st.secrets["general"]["admin_code"]:
                st.session_state.logged_in = True
                st.experimental_rerun()
            else:
                st.error("Invalid admin code")

# ------------------ DASHBOARD ------------------
def show_dashboard():
    st.markdown(
        f"<h2 style='color:{COLORS['teal_blue']}'>Dashboard</h2>", unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar Chart
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

    # Pie Chart
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

    # Timeline
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

# ------------------ MANAGE REPORTS ------------------
def manage_reports():
    st.markdown(f"<h2 style='color:{COLORS['teal_blue']}'>Manage Reports</h2>", unsafe_allow_html=True)
    for i, row in df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(row)
            current_status = row["Status"]
            try:
                new_status = st.selectbox(
                    "Update Status",
                    ["Pending", "Resolved"],
                    index=["Pending", "Resolved"].index(current_status),
                    key=f"status_{i}"
                )
            except ValueError:
                new_status = current_status
            if st.button("Update", key=f"update_{i}"):
                try:
                    cell = sheet.find(str(row['ReportID']))
                    sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                    st.success(f"Status updated to {new_status}")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")

# ------------------ MAIN ------------------
if not st.session_state.logged_in:
    login_page()
else:
    st.sidebar.markdown(
        f"<div style='background-color:{COLORS['teal_blue']};padding:20px;border-radius:10px;'>"
        f"<h2 style='color:white;text-align:center;'>Drop Watch</h2></div>",
        unsafe_allow_html=True
    )

    page = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Manage Reports", "Logout"]
    )

    if page == "Dashboard":
        show_dashboard()
    elif page == "Manage Reports":
        manage_reports()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.experimental_rerun()
