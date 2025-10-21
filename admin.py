import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

# --- Squilla Fund Colors ---
TEAL_BLUE = "#008080"
MOONSTONE_BLUE = "#73A9C2"
POWDER_BLUE = "#B0E0E6"
MAGIC_MINT = "#AAF0D1"
WHITE_SMOKE = "#F5F5F5"

COLOR_PALETTE = [TEAL_BLUE, MOONSTONE_BLUE, POWDER_BLUE, MAGIC_MINT]

# --- App Styling ---
st.set_page_config(page_title="Water Leakage Admin", layout="wide")
st.markdown(
    f"""
    <style>
        .css-18e3th9 {{background-color: {WHITE_SMOKE};}}
        .css-1d391kg {{background-color: {TEAL_BLUE};}}
        .stButton>button {{background-color: {MOONSTONE_BLUE}; color: black;}}
        .stMetricValue {{color: black;}}
        .stText {{color: black;}}
    </style>
    """, unsafe_allow_html=True
)

# --- Load Google Sheet ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
client = gspread.authorize(creds)

SHEET_NAME = "WaterLeakReports"
SHEET_TAB = "Sheet1"

try:
    sheet = client.open(SHEET_NAME).worksheet(SHEET_TAB)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# --- Functions ---
def update_status(row_index, new_status):
    try:
        cell = f"I{row_index + 2}"  # Column I = Status
        sheet.update(cell, new_status)
        df.loc[row_index, "Status"] = new_status
        st.success(f"Report {row_index + 1} status updated to {new_status}")
    except Exception as e:
        st.error(f"Failed to update status: {e}")

def dashboard(df):
    st.title("Water Leakage Admin Dashboard")

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # --- Charts ---
    st.subheader("Leak Reports by Type")
    fig_bar = px.bar(
        df['Leak Type'].value_counts().reset_index(),
        x='index', y='Leak Type',
        color='index',
        color_discrete_sequence=COLOR_PALETTE,
        labels={'index':'Leak Type', 'Leak Type':'Count'},
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("Leak Reports Status Distribution")
    fig_pie = px.pie(
        df['Status'].value_counts().reset_index(),
        names='index',
        values='Status',
        color='index',
        color_discrete_sequence=COLOR_PALETTE,
        title="Reports by Status"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    st.subheader("Reports Over Time")
    if 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'])
        fig_line = px.line(
            df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count'),
            x='DateTime', y='Count',
            title="Reports Over Time",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)

def manage_reports(df):
    st.subheader("Manage Reports")
    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(row.to_dict())
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], key=f"status_{i}")
            if st.button("Update", key=f"btn_{i}"):
                update_status(i, new_status)

# --- Sidebar Navigation ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard", "Manage Reports"])

# --- Main ---
if page == "Dashboard":
    dashboard(df)
elif page == "Manage Reports":
    manage_reports(df)
