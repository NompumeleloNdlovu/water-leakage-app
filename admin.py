import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# ---------------------------
# App configuration
# ---------------------------
st.set_page_config(page_title="Water Leakage Admin Dashboard", layout="wide")

# ---------------------------
# Squilla Fund color palette
# ---------------------------
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

st.markdown(
    f"""
    <style>
    .css-1d391kg {{background-color: {PALETTE['WHITE_SMOKE']};}}
    .css-1d391kg .stSidebar {{background-color: {PALETTE['TEAL_BLUE']}; color: black;}}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# Google Sheets setup
# ---------------------------
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials from secrets
creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
client = gspread.authorize(creds)

SHEET_NAME = "WaterLeakReports"
try:
    sheet = client.open(SHEET_NAME).worksheet("Sheet1")
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# ---------------------------
# Sidebar navigation
# ---------------------------
page = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports"])

# ---------------------------
# Dashboard page
# ---------------------------
def dashboard():
    st.title("Water Leakage Dashboard")

    if df.empty:
        st.warning("No data available.")
        return

    # Summary metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar chart: Leak Type
    bar_colors = [PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"], PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]]
    bar_data = df["Leak Type"].value_counts().reset_index()
    bar_data.columns = ["Leak Type", "Count"]
    fig_bar = px.bar(
        bar_data,
        x="Leak Type",
        y="Count",
        color="Leak Type",
        color_discrete_sequence=bar_colors,
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart: Status
    pie_data = df["Status"].value_counts().reset_index()
    pie_data.columns = ["Status", "Count"]
    fig_pie = px.pie(
        pie_data,
        values="Count",
        names="Status",
        color_discrete_sequence=bar_colors,
        title="Report Status Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Time series chart: Reports over time
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    time_data = df.groupby(df["DateTime"].dt.date).size().reset_index(name="Count")
    fig_time = px.line(
        time_data,
        x="DateTime",
        y="Count",
        title="Reports Over Time",
        markers=True
    )
    st.plotly_chart(fig_time, use_container_width=True)

# ---------------------------
# Manage Reports page
# ---------------------------
def manage_reports():
    st.title("Manage Reports")

    if df.empty:
        st.warning("No reports to manage.")
        return

    for i, row in df.iterrows():
        report_id = row.get("ReportID", i+1)
        location = row.get("Location", "Unknown")
        status = row.get("Status", "Pending")
        with st.expander(f"Report #{report_id} — {location}"):
            st.write(row)
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=["Pending", "Resolved"].index(status))
            if st.button(f"Update Report #{report_id}"):
                try:
                    cell = sheet.find(str(report_id))
                    sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                    st.success(f"Status updated to {new_status}")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")

# ---------------------------
# Main app logic
# ---------------------------
def main():
    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()

if __name__ == "__main__":
    main()
