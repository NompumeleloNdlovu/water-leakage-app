# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# -----------------------
# Squilla Fund Color Palette
# -----------------------
COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

st.set_page_config(page_title="Water Leakage Admin Dashboard", layout="wide")

# -----------------------
# Google Sheets Setup
# -----------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_ID = st.secrets["general"]["sheet_id"]
SHEET_NAME = "Sheet1"

try:
    sheet = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
except Exception as e:
    st.error(f"Failed to connect to Google Sheets: {e}")
    st.stop()

# -----------------------
# Load Data
# -----------------------
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

# -----------------------
# Update Report Status
# -----------------------
def update_status(row_index, new_status):
    try:
        # Google Sheets rows are 1-indexed + 1 for header
        sheet.update_cell(row_index + 2, df.columns.get_loc("Status") + 1, new_status)
        st.success("Status updated successfully!")
        return True
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False

# -----------------------
# Dashboard Page
# -----------------------
def dashboard():
    st.title("Water Leakage Admin Dashboard")
    df = load_data()

    st.markdown("---")
    st.subheader("Metrics")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] != "Resolved").sum())

    st.markdown("---")
    st.subheader("Charts")

    # Bar chart - Leak Types
    leak_counts = df["Leak Type"].value_counts()
    fig_bar, ax_bar = plt.subplots()
    leak_counts.plot.bar(color=COLORS["teal_blue"], ax=ax_bar)
    ax_bar.set_facecolor(COLORS["white_smoke"])
    ax_bar.set_ylabel("Number of Reports")
    st.pyplot(fig_bar)

    # Pie chart - Status Distribution
    status_counts = df["Status"].value_counts()
    fig_pie, ax_pie = plt.subplots()
    status_counts.plot.pie(
        autopct="%1.1f%%",
        colors=[COLORS["teal_blue"], COLORS["moonstone_blue"], COLORS["powder_blue"], COLORS["magic_mint"]],
        startangle=90,
        ylabel="",
        ax=ax_pie
    )
    ax_pie.set_facecolor(COLORS["white_smoke"])
    st.pyplot(fig_pie)

    # Time series chart - Reports over time
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    df_time = df.groupby(df["DateTime"].dt.date).size()
    fig_time, ax_time = plt.subplots()
    df_time.plot.line(
        color=COLORS["moonstone_blue"],
        marker="o",
        ax=ax_time
    )
    ax_time.set_facecolor(COLORS["white_smoke"])
    ax_time.set_ylabel("Number of Reports")
    ax_time.set_xlabel("Date")
    st.pyplot(fig_time)

# -----------------------
# Manage Reports Page
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
                update_status(i, new_status)

# -----------------------
# Sidebar Navigation
# -----------------------
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Manage Reports"])

    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()

if __name__ == "__main__":
    main()
