import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# --- SCOPES ---
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# --- AUTHORIZE ---
creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"], scopes=SCOPES
)
client = gspread.authorize(creds)

# --- OPEN SHEET BY ID ---
SHEET_ID = st.secrets["general"]["sheet_id"]  # your Google Sheet ID
try:
    sheet = client.open_by_key(SHEET_ID).sheet1
except gspread.exceptions.APIError as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# --- LOAD DATA INTO DATAFRAME ---
try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
except Exception as e:
    st.error(f"Failed to read sheet data: {e}")
    st.stop()

# Now `df` is your DataFrame ready for dashboard & manage_reports
st.write("Google Sheet loaded successfully!", df.head())

