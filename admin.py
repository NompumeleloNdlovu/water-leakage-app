# -*- coding: utf-8 -*-
"""admin_dashboard.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px

# --- App Title & Layout ---
st.set_page_config(page_title="Water Leakage Admin Dashboard", layout="wide")

# --- Secrets ---
mail_user = st.secrets["mailtrap"]["user"]
mail_pass = st.secrets["mailtrap"]["password"]
google_creds_dict = st.secrets["google_service_account"]
ADMIN_CODE = st.secrets["general"]["admin_code"]

# --- Google Sheets Config ---
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"  # Replace with your sheet ID


# --- Google Sheets Setup ---
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(google_creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    return sheet


# --- Load Data ---
def load_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
    return df


# --- Main App ---
def main():
    # Header Banner
    st.image("download.jpeg", use_container_width=True)
    st.title("🚰 Water Leakage Reporting - Admin Panel")
    st.markdown("### Empowering Municipalities with Real-Time Insights 💧")
    st.markdown("---")

    # --- Admin Authentication ---
    admin_input = st.text_input("🔐 Enter Admin Code:", type="password")
    if admin_input != ADMIN_CODE:
        st.warning("Please enter a valid admin code to access the reports.")
        return

    # --- Tabs for navigation ---
    tab1, tab2 = st.tabs(["📊 Dashboard Overview", "🛠 Manage Reports"])

    # --- Dashboard Tab ---
    with tab1:
        df = load_data()
        if df.empty:
            st.info("No reports found.")
            return

        st.success(f"✅ Loaded {len(df)} reports successfully.")
        st.markdown("#### Key Performance Indicators")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Reports", len(df))
        col2.metric("Pending", (df["Status"] == "Pending").sum())
        col3.metric("In Progress", (df["Status"] == "In Progress").sum())
        col4.metric("Resolved", (df["Status"] == "Resolved").sum())

        st.markdown("### 📍 Reports by Municipality")
        fig = px.bar(
            df,
            x="Municipality",
            color="Status",
            barmode="group",
            title="Reports by Municipality & Status",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("### 💧 Leak Types Reported")
        fig2 = px.pie(df, names="Leak Type", title="Distribution of Leak Types")
        st.plotly_chart(fig2, use_container_width=True)

    # --- Manage Reports Tab ---
    with tab2:
        df = load_data()
        if df.empty:
            st.info("No reports found.")
            return

        st.markdown("### Manage and Update Report Status")
        for idx, report in enumerate(df.to_dict(orient="records"), start=2):
            st.markdown(f"#### Report #{report.get('ReportID', idx-1)}")
            st.write(report)

            current_status = report.get("Status", "Pending")
            status = st.selectbox(
                f"Update status for Report #{report.get('ReportID', idx-1)}",
                options=["Pending", "In Progress", "Resolved", "Rejected"],
                index=["Pending", "In Progress", "Resolved", "Rejected"].index(current_status),
                key=f"status_{idx}",
            )

            if st.button(
                f"Update Status for Report #{report.get('ReportID', idx-1)}",
                key=f"update_{idx}",
            ):
                sheet = get_sheet()
                sheet.update_cell(idx, 8, status)  # col 8 = 'Status'
                sheet.update_cell(idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # timestamp
                st.success(
                    f"Status for Report #{report.get('ReportID', idx-1)} updated to '{status}'."
                )


if __name__ == "__main__":
    main()
