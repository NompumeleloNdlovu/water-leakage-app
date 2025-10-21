import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# -----------------------------
# Google Sheets Setup
# -----------------------------
SHEET_NAME = "Sheet1"  # your sheet name
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

# load credentials from st.secrets
creds_dict = st.secrets["google_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
client = gspread.authorize(creds)

sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)

# -----------------------------
# Colour Palette
# -----------------------------
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# Apply background, header, and sidebar colors
st.set_page_config(page_title="Water Leakage Admin", layout="wide")

st.markdown(f"""
    <style>
    .stApp {{
        background-color: {PALETTE['WHITE_SMOKE']};
    }}
    .css-18e3th9 {{
        background-color: {PALETTE['POWDER_BLUE']};
    }}
    .css-1d391kg {{
        background-color: {PALETTE['TEAL_BLUE']};
        color: white;
        font-weight: bold;
    }}
    </style>
""", unsafe_allow_html=True)

# -----------------------------
# Load DataFrame
# -----------------------------
def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    # remove any leading/trailing whitespace from column names
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# -----------------------------
# Update Status
# -----------------------------
def update_status(row_index, new_status):
    # Row index in Google Sheets starts from 2 (1 is header)
    cell = f"H{row_index + 2}"  # Status column is H
    try:
        sheet.update(cell, new_status)
        st.success(f"Status updated to {new_status}")
    except Exception as e:
        st.error(f"Failed to update status: {e}")

# -----------------------------
# Dashboard
# -----------------------------
def dashboard():
    st.title("Water Leakage Reports Dashboard")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] != "Resolved").sum())
    
    # Bar Chart: Leak Type
    st.subheader("Leak Type Distribution")
    bar_colors = [PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"], PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]]
    plt.figure(figsize=(8,5))
    df['Leak Type'].value_counts().plot(kind='bar', color=bar_colors)
    plt.xlabel("Leak Type")
    plt.ylabel("Count")
    plt.xticks(rotation=45)
    st.pyplot(plt)
    plt.clf()
    
    # Pie Chart: Status
    st.subheader("Report Status")
    status_counts = df['Status'].value_counts()
    plt.figure(figsize=(5,5))
    status_counts.plot.pie(autopct="%1.1f%%", colors=bar_colors, startangle=90, ylabel="")
    st.pyplot(plt)
    plt.clf()
    
    # Time Chart: Reports over time
    st.subheader("Reports Over Time")
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    time_data = df.groupby(df['DateTime'].dt.date).size()
    plt.figure(figsize=(10,5))
    time_data.plot(kind='line', marker='o', color=PALETTE["TEAL_BLUE"])
    plt.xlabel("Date")
    plt.ylabel("Number of Reports")
    st.pyplot(plt)
    plt.clf()

# -----------------------------
# Manage Reports
# -----------------------------
def manage_reports():
    st.subheader("Manage Reports")
    
    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID','Unknown')} — {row.get('Location','Unknown')}"):
            st.write(row.to_dict())
            new_status = st.selectbox("Update Status", options=["Pending","Resolved","In Progress"], key=f"status_{i}")
            if st.button("Update", key=f"btn_{i}"):
                update_status(i, new_status)

# -----------------------------
# Main
# -----------------------------
def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Manage Reports"])
    
    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()

if __name__ == "__main__":
    main()
