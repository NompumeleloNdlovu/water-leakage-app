import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# -----------------------
# Google Sheets Setup
# -----------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Connect using secrets
credentials = Credentials.from_service_account_info(
    st.secrets["google_service_account"],
    scopes=SCOPE
)
client = gspread.authorize(credentials)

# Sheet info
SHEET_NAME = "Sheet1"  # Name of the sheet inside the Google Sheets file
sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)

# -----------------------
# Squilla Fund Colors
# -----------------------
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# -----------------------
# Load Data
# -----------------------
@st.cache_data
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()  # Remove extra spaces
    return df

# -----------------------
# Update Status
# -----------------------
def update_status(df, row_index, new_status):
    try:
        status_col_index = df.columns.get_loc("Status") + 1
        sheet.update_cell(row_index + 2, status_col_index, new_status)
        st.success("Status updated successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False

# -----------------------
# Dashboard
# -----------------------
def dashboard():
    st.title("Admin Dashboard")
    df = load_data()

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # -----------------------
    # Bar Chart: Leak Types
    # -----------------------
    st.subheader("Leak Types")
    leak_counts = df["Leak Type"].value_counts()
    sns.set_palette(list(PALETTE.values())[:-1])  # exclude white smoke
    st.bar_chart(leak_counts)

    # -----------------------
    # Pie Chart: Status Distribution
    # -----------------------
    st.subheader("Status Distribution")
    status_counts = df["Status"].value_counts()
    fig, ax = plt.subplots()
    ax.pie(
        status_counts,
        labels=status_counts.index,
        autopct="%1.1f%%",
        startangle=90,
        colors=list(PALETTE.values())[:len(status_counts)]
    )
    ax.axis("equal")
    st.pyplot(fig)

    # -----------------------
    # Time Series Chart: Reports Over Time
    # -----------------------
    st.subheader("Reports Over Time")
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    time_data = df.groupby(df["DateTime"].dt.date).size()
    st.line_chart(time_data)

# -----------------------
# Manage Reports
# -----------------------
def manage_reports():
    st.title("Manage Reports")
    df = load_data()

    for i, row in df.iterrows():
        location = row.get("Location", "Unknown")
        report_id = row.get("ReportID", i+1)
        with st.expander(f"Report #{report_id} — {location}"):
            st.write(row)
            new_status = st.selectbox("Update Status", ["Pending", "In Progress", "Resolved"], key=i)
            if st.button("Update Status", key=f"btn_{i}"):
                update_status(df, i, new_status)

# -----------------------
# Sidebar Navigation
# -----------------------
def main():
    st.sidebar.title("Admin Panel")
    menu = ["Dashboard", "Manage Reports"]
    choice = st.sidebar.radio("Go to", menu)

    if choice == "Dashboard":
        dashboard()
    elif choice == "Manage Reports":
        manage_reports()

if __name__ == "__main__":
    main()
