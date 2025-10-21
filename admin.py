import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# -------------------------
# Google Sheets Authentication
# -------------------------
SHEET_NAME = "Sheet1"

scopes = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)

# -------------------------
# Squilla Fund color palette
# -------------------------
PALETTE = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}
bar_colors = [PALETTE["teal_blue"], PALETTE["moonstone_blue"], PALETTE["powder_blue"], PALETTE["magic_mint"]]

# -------------------------
# App style
# -------------------------
st.set_page_config(page_title="Water Leakage Admin", layout="wide")
st.markdown(
    f"""
    <style>
    .reportview-container {{
        background-color: {PALETTE['white_smoke']};
        color: black;
    }}
    .sidebar .sidebar-content {{
        background-color: {PALETTE['teal_blue']};
        color: black;
    }}
    .stButton>button {{
        background-color: {PALETTE['moonstone_blue']};
        color: black;
    }}
    .stMetric-value {{
        color: black;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# Load data from Google Sheets
# -------------------------
@st.cache_data
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = [col.strip() for col in df.columns]  # normalize column names
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')  # safe datetime
    return df

# -------------------------
# Dashboard
# -------------------------
def dashboard():
    df = load_data()

    st.markdown(f"<h1 style='color:{PALETTE['teal_blue']}'>Water Leakage Admin Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Metrics cards with palette
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] != "Resolved").sum())

    st.markdown("---")

    # Bar chart: Leak Type
    fig_bar = px.bar(
        df['Leak Type'].value_counts().reset_index(),
        x='index', y='Leak Type',
        color='index',
        color_discrete_sequence=bar_colors,
        labels={'index':'Leak Type', 'Leak Type':'Count'},
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # Pie chart: Status
    status_counts = df['Status'].value_counts().reset_index()
    fig_pie = px.pie(
        status_counts,
        names='index',
        values='Status',
        color_discrete_sequence=bar_colors,
        title="Report Status Distribution"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # Time chart: Reports over time
    time_counts = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
    fig_time = px.line(
        time_counts,
        x='DateTime', y='Count',
        title="Reports Over Time",
        markers=True,
        color_discrete_sequence=[PALETTE["teal_blue"]]
    )
    st.plotly_chart(fig_time, use_container_width=True)

# -------------------------
# Main
# -------------------------
def main():
    # Sidebar navigation
    page = st.sidebar.radio("Navigation", ["Dashboard"])
    if page == "Dashboard":
        dashboard()

if __name__ == "__main__":
    main()
