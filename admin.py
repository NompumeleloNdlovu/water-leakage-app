import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
from google.oauth2.service_account import Credentials

# ------------------ COLOURS ------------------
COLORS = {
    'teal_blue': '#008080',
    'moonstone_blue': '#73A9C2',
    'powder_blue': '#B0E0E6',
    'magic_mint': '#AAF0D1',
    'white_smoke': '#F5F5F5'
}

# ------------------ PAGE CONFIG ------------------
st.set_page_config(
    page_title="Drop Watch Admin",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Set background and text colours
st.markdown(f"""
    <style>
    .stApp {{
        background-color: {COLORS['white_smoke']};
        color: black;
    }}
    .css-1d391kg {{
        background-color: {COLORS['teal_blue']};
    }}
    </style>
""", unsafe_allow_html=True)

# ------------------ SESSION STATE ------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "Login"

# ------------------ GOOGLE SHEET ------------------
SCOPE = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(st.secrets["google_service_account"], scopes=SCOPE)
client = gspread.authorize(creds)
SHEET_NAME = "Sheet1"
sheet = client.open("WaterLeakReports").worksheet(SHEET_NAME)

def load_data():
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.strip()  # strip extra spaces
    return df

# ------------------ LOGIN PAGE ------------------
def login_page():
    st.markdown(
        f"""
        <style>
        .login-card {{
            background-color:white;
            padding:50px;
            border-radius:15px;
            box-shadow:0 8px 16px rgba(0,0,0,0.2);
            width:400px;
            margin:auto;
            position:absolute;
            top:50%;
            left:50%;
            transform:translate(-50%, -50%);
        }}
        .login-card h2 {{
            text-align:center;
            color:{COLORS['teal_blue']};
            margin-bottom:30px;
        }}
        </style>
        """, unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="login-card">
            <h2>Drop Watch Admin Login</h2>
        </div>
        """,
        unsafe_allow_html=True
    )
    with st.form("login_form", clear_on_submit=False):
        code = st.text_input("Admin Code", placeholder="Enter your admin code", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if code == st.secrets["general"]["admin_code"]:
                st.session_state.logged_in = True
                st.session_state.page = "Dashboard"
                st.experimental_rerun()
            else:
                st.error("Invalid admin code")

# ------------------ SIDEBAR ------------------
def sidebar_navigation():
    st.sidebar.markdown(f"<h2 style='color:{COLORS['white_smoke']}; text-align:center;'>Drop Watch</h2>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    selection = st.sidebar.radio("Navigation", ["Dashboard", "Manage Reports", "Logout"])
    return selection

# ------------------ DASHBOARD ------------------
def dashboard():
    st.title("Drop Watch Dashboard")
    df = load_data()
    if df.empty:
        st.info("No reports yet.")
        return

    df.columns = df.columns.str.strip()  # sanitize columns again

    # Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    # Bar chart - Leak Type
    if "Leak Type" in df.columns:
        bar_data = df["Leak Type"].value_counts().reset_index()
        fig_bar = px.bar(
            bar_data,
            x="index",
            y="Leak Type",
            color="index",
            color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
            labels={"index": "Leak Type", "Leak Type": "Count"},
            title="Leak Reports by Type"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Column 'Leak Type' not found in Google Sheet.")

    # Pie chart - Status
    if "Status" in df.columns:
        pie_data = df["Status"].value_counts().reset_index()
        fig_pie = px.pie(
            pie_data,
            names="index",
            values="Status",
            color="index",
            color_discrete_sequence=[COLORS['teal_blue'], COLORS['magic_mint']],
            title="Reports by Status"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.warning("Column 'Status' not found in Google Sheet.")

    # Time chart - Reports over time
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"], errors='coerce')
        df_time = df.groupby(df["DateTime"].dt.date).size().reset_index(name="Count")
        fig_time = px.line(
            df_time,
            x="DateTime",
            y="Count",
            title="Reports Over Time",
            markers=True,
            color_discrete_sequence=[COLORS['moonstone_blue']]
        )
        st.plotly_chart(fig_time, use_container_width=True)
    else:
        st.warning("Column 'DateTime' not found in Google Sheet.")

# ------------------ MANAGE REPORTS ------------------
def manage_reports():
    st.title("Manage Reports")
    df = load_data()
    if df.empty:
        st.info("No reports yet.")
        return

    for i, row in df.iterrows():
        with st.expander(f"Report #{row.get('ReportID', i+1)} — {row.get('Location','Unknown')}"):
            st.write(row)
            status = row.get("Status", "Pending")
            new_status = st.selectbox("Update Status", ["Pending", "Resolved"], index=["Pending", "Resolved"].index(status))
            if st.button(f"Update Report {row.get('ReportID', i+1)}"):
                sheet.update_cell(i+2, df.columns.get_loc("Status")+1, new_status)
                st.success("Status updated.")
                st.experimental_rerun()

# ------------------ MAIN ------------------
def main():
    if not st.session_state.logged_in:
        login_page()
        return

    page = sidebar_navigation()
    if page == "Dashboard":
        dashboard()
    elif page == "Manage Reports":
        manage_reports()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.session_state.page = "Login"
        st.experimental_rerun()

if __name__ == "__main__":
    main()
