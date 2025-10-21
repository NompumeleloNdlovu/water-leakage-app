import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# ------------------ COLORS ------------------
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
    page_icon="💧",
    layout="wide"
)

# ------------------ STYLES ------------------
st.markdown(f"""
    <style>
    .reportview-container {{
        background-color: {COLORS['white_smoke']};
        color: black;
    }}
    .sidebar .sidebar-content {{
        background-color: {COLORS['teal_blue']};
        color: white;
    }}
    .stButton>button {{
        background-color: {COLORS['moonstone_blue']};
        color: white;
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Login"

# ------------------ CREDENTIALS ------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
SHEET_NAME = "Sheet1"
sheet = client.open_by_key(st.secrets["general"]["sheet_id"]).worksheet(SHEET_NAME)

# ------------------ DATA ------------------
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# ------------------ LOGIN PAGE ------------------
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
        submitted = st.form_submit_button("Login")
        if submitted:
            if code == st.secrets["general"]["admin_code"]:
                st.session_state.logged_in = True
                st.session_state.page = "Dashboard"
                st.experimental_rerun()
            else:
                st.error("Invalid admin code")

# ------------------ SIDEBAR NAVIGATION ------------------
def sidebar():
    st.sidebar.title("Drop Watch Admin")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports", "Logout"])
    if page == "Logout":
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.experimental_rerun()
    else:
        st.session_state.page = page

# ------------------ DASHBOARD ------------------
def dashboard():
    st.title("Drop Watch Dashboard")
    df = load_data()
    if df.empty:
        st.info("No reports yet.")
        return

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar chart - Leak Type
    bar_data = df["Leak Type"].value_counts().reset_index()
    fig_bar = px.bar(
        bar_data,
        x="index",
        y="Leak Type",
        color="index",
        color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
        labels={"index": "Leak Type", "Leak Type": "Count"},
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart - Status
    pie_data = df["Status"].value_counts().reset_index()
    fig_pie = px.pie(
        pie_data,
        names="index",
        values="Status",
        color="index",
        color_discrete_sequence=[COLORS['teal_blue'], COLORS['magic_mint']],
        title="Reports by Status"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Time chart - Reports over time
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    fig_time = px.line(
        df.groupby(df["DateTime"].dt.date).size().reset_index(name="Count"),
        x="DateTime",
        y="Count",
        title="Reports Over Time",
        markers=True,
        color_discrete_sequence=[COLORS['moonstone_blue']]
    )
    st.plotly_chart(fig_time, use_container_width=True)

# ------------------ MANAGE REPORTS ------------------
def manage_reports():
    st.title("Manage Reports")
    df = load_data()
    if df.empty:
        st.info("No reports to manage.")
        return

    for i, row in df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(row)
            status_options = ["Pending", "Resolved"]
            current_status = row.get("Status", "Pending")
            if current_status not in status_options:
                current_status = "Pending"
            new_status = st.selectbox("Update Status", status_options, index=status_options.index(current_status), key=f"status_{i}")
            if st.button("Update", key=f"btn_{i}"):
                sheet.update_cell(i+2, df.columns.get_loc("Status")+1, new_status)
                st.success("Status updated!")

# ------------------ MAIN ------------------
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        sidebar()
        if st.session_state.page == "Dashboard":
            dashboard()
        elif st.session_state.page == "Manage Reports":
            manage_reports()

if __name__ == "__main__":
    main()
