import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# ---------------- COLOR PALETTE ----------------
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

# ---------------- STREAMLIT PAGE CONFIG ----------------
st.set_page_config(
    page_title="Drop Watch",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- CUSTOM STYLING ----------------
st.markdown(
    f"""
    <style>
        /* Page background */
        .stApp {{
            background-color: {COLORS['white_smoke']};
            color: black;
        }}
        /* Sidebar background */
        [data-testid="stSidebar"] {{
            background-color: {COLORS['teal_blue']};
            color: black;
        }}
        /* Headers */
        .css-18e3th9 {{
            color: black;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- GOOGLE SHEETS SETUP ----------------
SHEET_NAME = "Sheet1"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)

try:
    sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# ---------------- LOGIN ----------------
def login_page():
    st.title("Drop Watch Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == st.secrets["general"]["admin_code"] and password == st.secrets["general"]["admin_code"]:
            st.session_state["logged_in"] = True
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

# ---------------- DASHBOARD ----------------
def dashboard():
    st.header("Dashboard")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar chart: Leak Type
    if "Leak Type" in df.columns:
        bar_data = df["Leak Type"].value_counts().reset_index()
        fig_bar = px.bar(
            bar_data,
            x="index",
            y="Leak Type",
            color="index",
            color_discrete_sequence=[COLORS["moonstone_blue"], COLORS["powder_blue"], COLORS["magic_mint"]],
            labels={"index":"Leak Type", "Leak Type":"Count"},
            title="Leak Reports by Type"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Column 'Leak Type' not found in Google Sheet.")

    # Pie chart: Status
    if "Status" in df.columns:
        pie_data = df["Status"].value_counts().reset_index()
        fig_pie = px.pie(
            pie_data,
            names="index",
            values="Status",
            color="index",
            color_discrete_sequence=[COLORS["moonstone_blue"], COLORS["magic_mint"]],
            title="Reports by Status"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Column 'Status' not found in Google Sheet.")

    # Time series chart
    if "DateTime" in df.columns:
        df_time = df.groupby("DateTime").size().reset_index(name="Count")
        fig_time = px.line(
            df_time,
            x="DateTime",
            y="Count",
            title="Reports Over Time",
            markers=True,
            color_discrete_sequence=[COLORS['moonstone_blue']]
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("Column 'DateTime' not found in Google Sheet.")

# ---------------- MANAGE REPORTS ----------------
def manage_reports():
    st.header("Manage Reports")
    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(row)
            status = row.get("Status", "Pending")
            new_status = st.selectbox(
                "Update Status",
                ["Pending", "Resolved"],
                index=["Pending", "Resolved"].index(status) if status in ["Pending", "Resolved"] else 0,
                key=f"status_{i}"
            )
            if st.button("Update", key=f"update_{i}"):
                try:
                    cell = sheet.find(str(row["ReportID"])).address.replace("A", "H")  # Assuming Status is column H
                    sheet.update(cell, new_status)
                    st.success("Status updated")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")

# ---------------- MAIN ----------------
def main():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        login_page()
    else:
        st.sidebar.title("Navigation")
        page = st.sidebar.radio("Go to", ["Dashboard", "Manage Reports", "Logout"])

        if page == "Dashboard":
            dashboard()
        elif page == "Manage Reports":
            manage_reports()
        elif page == "Logout":
            st.session_state["logged_in"] = False
            st.experimental_rerun()

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
