import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# -------------------------
# App config
# -------------------------
st.set_page_config(page_title="Drop Watch", layout="wide")

# -------------------------
# Color palette
# -------------------------
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

# -------------------------
# Background & sidebar style
# -------------------------
st.markdown(
    f"""
    <style>
        .reportview-container {{
            background-color: {COLORS['white_smoke']};
            color: black;
        }}
        .sidebar .sidebar-content {{
            background-color: {COLORS['teal_blue']};
            color: white;
        }}
    </style>
    """, unsafe_allow_html=True
)

# -------------------------
# Google Sheets setup
# -------------------------
SHEET_NAME = "Sheet1"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)
data = sheet.get_all_records()
df = pd.DataFrame(data)

# -------------------------
# Session state
# -------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# -------------------------
# Login page
# -------------------------
def login_page():
    st.title("Drop Watch Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == st.secrets["general"]["admin_code"]:
            st.session_state.logged_in = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# -------------------------
# Dashboard page
# -------------------------
def dashboard():
    st.title("Drop Watch Dashboard")

    # Metrics
    if "Status" in df.columns:
        col1, col2 = st.columns(2)
        col1.metric("Pending", (df["Status"] == "Pending").sum())
        col2.metric("Resolved", (df["Status"] == "Resolved").sum())

    # Bar chart - Leak Type
    if "Leak Type" in df.columns:
        bar_data = df["Leak Type"].value_counts().reset_index()
        bar_data.columns = ["Leak Type", "Count"]
        fig_bar = px.bar(
            bar_data,
            x="Leak Type",
            y="Count",
            color="Leak Type",
            color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
            title="Leak Reports by Type"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart - Status
    if "Status" in df.columns:
        pie_data = df["Status"].value_counts().reset_index()
        pie_data.columns = ["Status", "Count"]
        fig_pie = px.pie(
            pie_data,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_sequence=[COLORS['teal_blue'], COLORS['magic_mint']],
            title="Reports by Status"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# -------------------------
# Manage Reports page
# -------------------------
def manage_reports():
    st.title("Manage Reports")
    if df.empty:
        st.warning("No reports found.")
        return

    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(row)
            if "Status" in row:
                status = row.get("Status", "Pending")
                try:
                    new_status = st.selectbox(
                        "Update Status",
                        ["Pending", "Resolved"],
                        index=["Pending", "Resolved"].index(status)
                    )
                    if st.button("Update", key=f"update_{i}"):
                        cell = sheet.find(str(row["ReportID"]))
                        sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                        st.success(f"Status updated to {new_status}")
                except ValueError:
                    st.error("Current status not recognized. Cannot select.")

# -------------------------
# Main app
# -------------------------
def main():
    if not st.session_state.logged_in:
        login_page()
        return

    st.sidebar.title("Drop Watch Admin")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports", "Logout"])

    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.experimental_rerun()

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    main()
