import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt
import seaborn as sns


# -----------------------
# Squilla Fund Color Palette
# -----------------------
PALETTE = {
    "TEAL_BLUE": "#008080",
    "MOONSTONE_BLUE": "#73A9C2",
    "POWDER_BLUE": "#B0E0E6",
    "MAGIC_MINT": "#AAF0D1",
    "WHITE_SMOKE": "#F5F5F5"
}

# -----------------------
# Set up Google Sheets
# -----------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets",
          "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_info(
    st.secrets["google_service_account"], scopes=SCOPES
)
client = gspread.authorize(creds)

SHEET_NAME = "Sheet1"  # Your sheet name
sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)

# -----------------------
# Load Data
# -----------------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

# -----------------------
# Custom CSS for Light Background
# -----------------------
st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {PALETTE['WHITE_SMOKE']};
        color: #000000;
    }}
    .css-1d391kg {{
        background-color: {PALETTE['WHITE_SMOKE']};
    }}
    .st-expander {{
        background-color: #ffffff;
        border-radius: 8px;
        padding: 10px;
    }}
    .stMetricValue {{
        color: {PALETTE['TEAL_BLUE']};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------
# Sidebar Navigation
# -----------------------
st.sidebar.title("Admin Panel")
page = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports"])

# -----------------------
# Dashboard
# -----------------------
def dashboard():
    st.header("Water Leakage Dashboard")

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] != "Resolved").sum())

    # -----------------------
    # Charts
    # -----------------------

    # Bar chart: Leak Type count
    st.subheader("Leak Types")
    leak_count = df["Leak Type"].value_counts()
    fig, ax = plt.subplots()
    sns.barplot(x=leak_count.index, y=leak_count.values, palette=[PALETTE["TEAL_BLUE"], PALETTE["MOONSTONE_BLUE"], PALETTE["POWDER_BLUE"], PALETTE["MAGIC_MINT"]], ax=ax)
    ax.set_ylabel("Count")
    ax.set_xlabel("Leak Type")
    st.pyplot(fig)

    # Pie chart: Status distribution
    st.subheader("Report Status")
    status_count = df["Status"].value_counts()
    fig2, ax2 = plt.subplots()
    ax2.pie(status_count.values, labels=status_count.index, autopct="%1.1f%%",
            startangle=90, colors=[PALETTE["TEAL_BLUE"], PALETTE["MAGIC_MINT"], PALETTE["POWDER_BLUE"]])
    ax2.axis("equal")
    st.pyplot(fig2)

    # Time series chart: Reports over time
    st.subheader("Reports Over Time")
    df["DateTime"] = pd.to_datetime(df["DateTime"])
    time_count = df.groupby(df["DateTime"].dt.date).size()
    fig3, ax3 = plt.subplots()
    ax3.plot(time_count.index, time_count.values, marker='o', color=PALETTE["MOONSTONE_BLUE"])
    ax3.set_xlabel("Date")
    ax3.set_ylabel("Number of Reports")
    ax3.grid(True, linestyle='--', alpha=0.5)
    st.pyplot(fig3)

# -----------------------
# Manage Reports
# -----------------------
def update_status(index, new_status):
    cell = f"I{index+2}"  # Assuming Status is column I
    try:
        sheet.update(cell, new_status)
        return True
    except Exception as e:
        st.error(f"Failed to update status: {e}")
        return False

def manage_reports():
    st.header("Manage Reports")
    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(f"Name: {row.get('Name','')}")
            st.write(f"Contact: {row.get('Contact','')}")
            st.write(f"Municipality: {row.get('Municipality','')}")
            st.write(f"Leak Type: {row.get('Leak Type','')}")
            st.write(f"Location: {row.get('Location','')}")
            st.write(f"DateTime: {row.get('DateTime','')}")
            st.write(f"Status: {row.get('Status','')}")
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=0 if row.get("Status")!="Resolved" else 1)
            if st.button("Update", key=i):
                success = update_status(i, new_status)
                if success:
                    st.success("Status updated successfully!")

# -----------------------
# Main
# -----------------------
def main():
    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()

if __name__ == "__main__":
    main()

