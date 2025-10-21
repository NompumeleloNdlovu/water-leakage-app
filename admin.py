import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Drop Watch", layout="wide")

# ------------------ COLORS ------------------
COLORS = {
    'teal_blue': '#008080',
    'moonstone_blue': '#73A9C2',
    'powder_blue': '#B0E0E6',
    'magic_mint': '#AAF0D1',
    'white_smoke': '#F5F5F5'
}

# ------------------ GOOGLE SHEETS SETUP ------------------
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)
SHEET_ID = st.secrets["general"]["sheet_id"]
SHEET_NAME = "Sheet1"

# ------------------ HELPER FUNCTIONS ------------------
@st.cache_data(ttl=60)
def load_data():
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df, sheet

def update_status(sheet, row_index, new_status):
    cell = f"I{row_index+2}"  # Assuming "Status" is column I
    sheet.update(cell, new_status)

# ------------------ LOGIN ------------------
def login_page():
    st.markdown(
        f"""
        <style>
        .login-container {{
            background-color: {COLORS['white_smoke']};
            padding: 2rem;
            border-radius: 1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.title("Drop Watch Admin Login")
    st.markdown("---")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if username == "admin" and password == st.secrets["general"]["admin_code"]:
                st.session_state.logged_in = True
            else:
                st.error("Invalid credentials")

# ------------------ DASHBOARD ------------------
def dashboard(df):
    st.markdown("## Dashboard")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())
    
    st.markdown("### Leak Reports by Type")
    bar_data = df["Leak Type"].value_counts().reset_index()
    bar_data.columns = ["Leak Type", "Count"]
    fig_bar = px.bar(
        bar_data,
        x="Leak Type",
        y="Count",
        color="Leak Type",
        color_discrete_sequence=[
            COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint'], COLORS['teal_blue']
        ],
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("### Reports Over Time")
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
        df_time = df.groupby("DateTime").size().reset_index(name="Count")
        fig_time = px.line(
            df_time,
            x="DateTime",
            y="Count",
            markers=True,
            title="Reports Over Time",
            color_discrete_sequence=[COLORS['moonstone_blue']]
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("Column 'DateTime' not found in Google Sheet.")

# ------------------ MANAGE REPORTS ------------------
def manage_reports(df, sheet):
    st.markdown("## Manage Reports")
    st.markdown("---")
    for i, row in df.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row['Location']}"):
            st.write(f"Name: {row['Name']}")
            st.write(f"Contact: {row['Contact']}")
            st.write(f"Municipality: {row['Municipality']}")
            st.write(f"Leak Type: {row['Leak Type']}")
            st.write(f"Location: {row['Location']}")
            st.write(f"DateTime: {row['DateTime']}")
            st.write(f"Status: {row['Status']}")
            st.image(row['Image'], use_column_width=True)
            
            new_status = st.selectbox(
                "Update Status",
                ["Pending", "Resolved"],
                index=["Pending", "Resolved"].index(row["Status"])
            )
            if st.button(f"Update Report #{row['ReportID']}", key=f"update_{i}"):
                update_status(sheet, i, new_status)
                st.success("Status updated successfully")

# ------------------ MAIN ------------------
def main():
    st.markdown(
        f"""
        <style>
        .css-1d391kg {{background-color: {COLORS['white_smoke']};}}
        [data-testid="stSidebar"] {{background-color: {COLORS['teal_blue']};}}
        </style>
        """,
        unsafe_allow_html=True
    )

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
        return

    df, sheet = load_data()

    with st.sidebar:
        st.title("Drop Watch Admin")
        page = st.radio("Navigate", ["Dashboard", "Manage Reports", "Logout"])
        st.markdown("---")

    if page == "Dashboard":
        dashboard(df)
    elif page == "Manage Reports":
        manage_reports(df, sheet)
    elif page == "Logout":
        st.session_state.logged_in = False
        st.experimental_rerun()  # Only rerun here to refresh app

# ------------------ RUN ------------------
if __name__ == "__main__":
    main()
