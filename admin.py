import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# --- Squilla Fund palette ---
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# --- Google Sheets setup ---
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SHEET_ID = st.secrets["general"]["sheet_id"]

def get_sheet():
    creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID).sheet1
    return sheet

def load_data():
    sheet = get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def update_status(row_index, new_status):
    sheet = get_sheet()
    cell = f"I{row_index + 2}"  # Assuming header is row 1, Status is column I
    sheet.update(cell, new_status)

# --- Dashboard function ---
def dashboard():
    try:
        df = load_data()
        if df.empty:
            st.warning("No reports found in the sheet.")
            return
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    df.columns = df.columns.str.strip()

    # --- Page style ---
    st.markdown(f"""
        <style>
        .stApp {{
            background-color: {PALETTE['WHITE_SMOKE']};
            color: black;
        }}
        [data-testid="stSidebar"] {{
            background-color: {PALETTE['TEAL_BLUE']};
        }}
        </style>
    """, unsafe_allow_html=True)

    st.title("Water Leakage Dashboard")

    # --- Metrics ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Reports", len(df))
    with col2:
        st.metric("Resolved", (df["Status"] == "Resolved").sum())
    with col3:
        st.metric("Pending", (df["Status"] == "Pending").sum())

    # --- Bar chart: Leak Types ---
    bar_colors = [PALETTE["MOONSTONE_BLUE"], PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]]
    fig_bar = px.bar(
        df['Leak Type'].value_counts().reset_index(),
        x='index', y='Leak Type',
        color='index',
        color_discrete_sequence=bar_colors,
        labels={'index':'Leak Type', 'Leak Type':'Count'},
        title="Leak Reports by Type"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Pie chart: Status distribution ---
    pie_colors = [PALETTE["MOONSTONE_BLUE"], PALETTE["MAGIC_MINT"]]
    fig_pie = px.pie(
        df, names='Status',
        title="Status Distribution",
        color='Status',
        color_discrete_sequence=pie_colors
    )
    st.plotly_chart(fig_pie, use_container_width=True)

    # --- Time series chart ---
    if 'DateTime' in df.columns:
        df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
        df_time = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
        fig_time = px.line(
            df_time,
            x='DateTime', y='Count',
            title="Reports Over Time",
            markers=True,
            line_shape='linear',
            color_discrete_sequence=[PALETTE["POWDER_BLUE"]]
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.info("DateTime column not found for time series chart.")

# --- Manage Reports ---
def manage_reports():
    try:
        df = load_data()
        if df.empty:
            st.warning("No reports to manage.")
            return
    except Exception as e:
        st.error(f"Failed to load data: {e}")
        return

    df.columns = df.columns.str.strip()

    st.subheader("Manage Reports")
    for i, row in df.iterrows():
        report_id = row.get("ReportID", i+1)
        location = row.get("Location", "Unknown")
        with st.expander(f"Report #{report_id} — {location}"):
            st.text(f"Name: {row.get('Name','')}")
            st.text(f"Contact: {row.get('Contact','')}")
            st.text(f"Municipality: {row.get('Municipality','')}")
            st.text(f"Leak Type: {row.get('Leak Type','')}")
            st.text(f"Date/Time: {row.get('DateTime','')}")
            st.text(f"Status: {row.get('Status','')}")
            # Update Status
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=["Pending","Resolved"].index(row.get("Status","Pending")), key=f"status_{i}")
            if st.button("Update", key=f"btn_{i}"):
                try:
                    update_status(i, new_status)
                    st.success("Status updated!")
                except Exception as e:
                    st.error(f"Failed to update status: {e}")

# --- Admin Login / Navigation ---
def admin_login_and_manage_page():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Manage Reports"])

    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()

# --- Main ---
def main():
    admin_login_and_manage_page()

if __name__ == "__main__":
    main()
