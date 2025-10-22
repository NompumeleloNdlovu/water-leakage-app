import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import base64
from datetime import datetime, timedelta
import time

# ------------------ CONFIG ------------------
SERVICE_ACCOUNT_INFO = st.secrets["google_service_account"]
SHEET_KEY = st.secrets["general"]["sheet_id"]

COLORS = {
    "teal_blue": "#008080",
    "moonstone_blue": "#73A9C2",
    "powder_blue": "#B0E0E6",
    "magic_mint": "#AAF0D1",
    "white_smoke": "#F5F5F5"
}

st.set_page_config(page_title="Drop Watch SA", layout="wide", initial_sidebar_state="expanded")

# ------------------ SESSION ------------------
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "page" not in st.session_state: st.session_state.page = "Home"

# ------------------ BACKGROUND IMAGE ------------------
def set_background_local(image_path, show_on_page=None, sidebar=False):
    if show_on_page and st.session_state.page not in show_on_page:
        return
    with open(image_path, "rb") as f:
        data = f.read()
    encoded = base64.b64encode(data).decode()
    if sidebar:
        st.markdown(f"""
            <style>
            [data-testid="stSidebar"] > div:first-child {{
                background-image: url("data:image/jpg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            </style>
        """, unsafe_allow_html=True)

# ------------------ GOOGLE SHEETS ------------------
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=scopes)
client = gspread.authorize(creds)

# Load main reports
try:
    sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet1")
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
    df.columns = df.columns.str.strip()
    if "DateTime" in df.columns: df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
except Exception as e:
    st.error(f"Failed to load Google Sheet: {e}")
    st.stop()

# Load admin info
try:
    admin_sheet = client.open_by_key(SHEET_KEY).worksheet("Sheet2")
    admins_df = pd.DataFrame(admin_sheet.get_all_records())
    admins_df.columns = admins_df.columns.str.strip()
    admins_df['AdminCode'] = admins_df['AdminCode'].astype(str).str.strip()
except Exception as e:
    st.error(f"Failed to load Admin Sheet: {e}")
    st.stop()

# ------------------ AUTHENTICATION ------------------
def login_page():
    st.markdown(f"<div style='background-color:{COLORS['teal_blue']};padding:40px;border-radius:10px;margin-top:50px;text-align:center;'>"
                f"<h1 style='color:white;'>Drop Watch SA - Admin Login</h1></div>", unsafe_allow_html=True)
    code = st.text_input("", placeholder="Enter Admin Code", type="password")
    if st.button("Login"):
        admin_info = admins_df[admins_df['AdminCode'] == code.strip()]
        if not admin_info.empty:
            st.session_state.logged_in = True
            st.session_state.admin_name = admin_info.iloc[0]['AdminName']
            st.session_state.admin_municipality = admin_info.iloc[0]['Municipality']
            st.session_state.page = "Home"
        else:
            st.error("Invalid code")

# ------------------ HOME PAGE with WELCOME BANNER ------------------
def home_page(df):
    if df.empty:
        st.warning("No reports found yet.")
        return

    # --- Time-based greeting ---
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    # --- Banner with background image ---
    banner_image = "images/images/WhatsApp Image 2025-10-22 at 00.08.08_8c98bfbb.jpg"

    st.markdown(
        f"""
        <style>
        .banner {{
            position: relative;
            background-image: url("{banner_image}");
            background-size: cover;
            background-position: center;
            height: 250px;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 32px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.6);
            margin-bottom: 20px;
        }}
        .overlay {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.35);
            border-radius: 20px;
        }}
        .banner-text {{
            position: relative;
            z-index: 2;
            text-align: center;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(255,0,0,0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(255,0,0,0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(255,0,0,0); }}
        }}
        .pulse-box {{
            background-color: #ffcccc;
            color: #a80000;
            padding: 10px 15px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 18px;
            animation: pulse 1.5s infinite;
        }}
        </style>

        <div class="banner">
            <div class="overlay"></div>
            <div class="banner-text">
                {greeting}, {st.session_state.admin_name}!<br>
                Welcome to the {st.session_state.admin_municipality} Admin Portal
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Date range picker ---
    min_date = df['DateTime'].min() if "DateTime" in df.columns else datetime.today() - timedelta(days=30)
    max_date = df['DateTime'].max() if "DateTime" in df.columns else datetime.today()
    start_date, end_date = st.date_input("Select Date Range", [min_date, max_date])

    df_filtered_range = df
    if "DateTime" in df.columns:
        df_filtered_range = df[(df['DateTime'].dt.date >= start_date) & (df['DateTime'].dt.date <= end_date)]

    # --- Municipality selector ---
    municipalities = df_filtered_range['Municipality'].dropna().unique() if "Municipality" in df_filtered_range.columns else []
    if len(municipalities) > 0:
        selected_municipality = st.selectbox("Select Municipality for Detailed Metrics", municipalities)
        df_filtered = df_filtered_range[df_filtered_range['Municipality'] == selected_municipality]
    else:
        df_filtered = df_filtered_range

    # --- Metrics calculations ---
    total_reports = len(df_filtered)
    resolved_reports = (df_filtered["Status"] == "Resolved").sum() if "Status" in df_filtered.columns else 0
    pending_reports = (df_filtered["Status"] == "Pending").sum() if "Status" in df_filtered.columns else 0

    # Reports since last login
    reports_at_login = st.session_state.get("reports_at_login", total_reports)
    new_reports = max(total_reports - reports_at_login, 0)

    # --- Live Counter Metrics ---
    col1, col2, col3, col4 = st.columns(4)

    # Total Reports
    col1.markdown(f"""
    <div style="font-size:20px;font-weight:bold;color:black;text-align:center;" id="total_reports">0</div>
    <script>
    let i_total = 0;
    let total = {total_reports};
    let elem_total = document.getElementById('total_reports');
    let timer_total = setInterval(() => {{
        if(i_total <= total){{
            elem_total.innerHTML = "Total Reports: " + i_total;
            i_total++;
        }} else {{
            clearInterval(timer_total);
        }}
    }}, 50);
    </script>
    """, unsafe_allow_html=True)

    # Resolved Reports
    col2.markdown(f"""
    <div style="font-size:20px;font-weight:bold;color:black;text-align:center;" id="resolved_reports">0</div>
    <script>
    let i_resolved = 0;
    let resolved = {resolved_reports};
    let elem_resolved = document.getElementById('resolved_reports');
    let timer_resolved = setInterval(() => {{
        if(i_resolved <= resolved){{
            elem_resolved.innerHTML = "Resolved Reports: " + i_resolved;
            i_resolved++;
        }} else {{
            clearInterval(timer_resolved);
        }}
    }}, 50);
    </script>
    """, unsafe_allow_html=True)

    # Pending Reports (with pulse if >0)
    with col3:
        if pending_reports > 0:
            st.markdown(f"""
            <div class='pulse-box' id='pending_reports'>0</div>
            <script>
            let i_pending = 0;
            let pending = {pending_reports};
            let elem_pending = document.getElementById('pending_reports');
            let timer_pending = setInterval(() => {{
                if(i_pending <= pending){{
                    elem_pending.innerHTML = "⚠️ Pending Reports: " + i_pending;
                    i_pending++;
                }} else {{
                    clearInterval(timer_pending);
                }}
            }}, 50);
            </script>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='text-align:center;font-weight:bold;'>Pending Reports: {pending_reports}</div>", unsafe_allow_html=True)

    # New Since Last Login
    col4.markdown(f"""
    <div style="font-size:20px;font-weight:bold;color:black;text-align:center;" id="new_reports">0</div>
    <script>
    let i_new = 0;
    let newR = {new_reports};
    let elem_new = document.getElementById('new_reports');
    let timer_new = setInterval(() => {{
        if(i_new <= newR){{
            elem_new.innerHTML = "New Since Last Login: " + i_new;
            i_new++;
        }} else {{
            clearInterval(timer_new);
        }}
    }}, 50);
    </script>
    """, unsafe_allow_html=True)

    # --- Charts ---
    if not df_filtered.empty:
        # Leak Type Distribution
        st.markdown("### Leak Type Distribution")
        if "Leak Type" in df_filtered.columns:
            bar_data = df_filtered['Leak Type'].value_counts().reset_index()
            bar_data.columns = ['Leak Type', 'Count']
            fig_bar = px.bar(
                bar_data,
                x='Leak Type',
                y='Count',
                color='Leak Type',
                color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
                title=f"Leak Reports by Type - {selected_municipality}"
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        # Status Distribution
        st.markdown("### Status Distribution")
        if "Status" in df_filtered.columns:
            pie_data = df_filtered['Status'].value_counts().reset_index()
            pie_data.columns = ['Status', 'Count']
            fig_pie = px.pie(
                pie_data,
                names='Status',
                values='Count',
                color='Status',
                color_discrete_sequence=[COLORS['moonstone_blue'], COLORS['magic_mint']],
                title=f"Status Breakdown - {selected_municipality}"
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Reports Over Time
        st.markdown("### Reports Over Time")
        if "DateTime" in df_filtered.columns:
            time_data = df_filtered.groupby(df_filtered['DateTime'].dt.date).size().reset_index(name='Count')
            fig_line = px.line(
                time_data,
                x='DateTime',
                y='Count',
                title=f"Reports Over Time - {selected_municipality}",
                markers=True,
                color_discrete_sequence=[COLORS['teal_blue']]
            )
            st.plotly_chart(fig_line, use_container_width=True)


# ------------------ MUNICIPAL OVERVIEW ------------------
def municipal_overview_page():
    st.markdown(f"<div style='background-color: rgba(245,245,245,0.8); padding:15px; border-radius:10px; margin-bottom:10px;'>"
                f"<h1 style='text-align:center;color:black;'>Municipal Overview</h1></div>", unsafe_allow_html=True)

    min_date = df['DateTime'].min() if "DateTime" in df.columns else datetime.today() - timedelta(days=30)
    max_date = df['DateTime'].max() if "DateTime" in df.columns else datetime.today()
    start_date, end_date = st.date_input("Select Date Range", [min_date, max_date])

    df_filtered_range = df
    if "DateTime" in df.columns:
        df_filtered_range = df[(df['DateTime'].dt.date >= start_date) & (df['DateTime'].dt.date <= end_date)]

    if "Municipality" in df_filtered_range.columns:
        municipalities = df_filtered_range['Municipality'].dropna().unique()
        selected_municipality = st.selectbox("Select Municipality for Detailed Metrics", municipalities)
        df_filtered = df_filtered_range[df_filtered_range['Municipality'] == selected_municipality]
    else:
        df_filtered = df_filtered_range

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df_filtered))
    col2.metric("Resolved", (df_filtered["Status"] == "Resolved").sum() if "Status" in df_filtered.columns else 0)
    col3.metric("Pending", (df_filtered["Status"] == "Pending").sum() if "Status" in df_filtered.columns else 0)

    # Municipal Overview Charts
    if not df_filtered.empty:
        st.markdown("### Leak Type Distribution")
        if "Leak Type" in df_filtered.columns:
            bar_data = df_filtered['Leak Type'].value_counts().reset_index()
            bar_data.columns = ['Leak Type', 'Count']
            fig_bar = px.bar(bar_data, x='Leak Type', y='Count',
                             color='Leak Type',
                             color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
                             title=f"Leak Reports by Type - {selected_municipality}")
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("### Status Distribution")
        if "Status" in df_filtered.columns:
            pie_data = df_filtered['Status'].value_counts().reset_index()
            pie_data.columns = ['Status', 'Count']
            fig_pie = px.pie(pie_data, names='Status', values='Count',
                             color='Status',
                             color_discrete_sequence=[COLORS['moonstone_blue'], COLORS['magic_mint']],
                             title=f"Status Breakdown - {selected_municipality}")
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("### Reports Over Time")
        if "DateTime" in df_filtered.columns:
            time_data = df_filtered.groupby(df_filtered['DateTime'].dt.date).size().reset_index(name='Count')
            fig_line = px.line(time_data, x='DateTime', y='Count',
                               title=f"Reports Over Time - {selected_municipality}",
                               markers=True,
                               color_discrete_sequence=[COLORS['teal_blue']])
            st.plotly_chart(fig_line, use_container_width=True)

# ------------------ DASHBOARD ------------------
def dashboard_page():
    st.markdown(f"<div style='background-color: rgba(115,169,194,0.8); padding:15px; border-radius:10px; margin-bottom:10px;'>"
                f"<h1 style='text-align:center;color:black;'>Drop Watch SA - Dashboard (All Municipalities)</h1></div>", unsafe_allow_html=True)

    st.markdown(f"<div style='background-color: rgba(245,245,245,0.8); padding:10px; border-radius:10px;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Reports", len(df))
    col2.metric("Resolved", (df["Status"] == "Resolved").sum())
    col3.metric("Pending", (df["Status"] == "Pending").sum())

    if "Leak Type" in df.columns:
        bar_data = df['Leak Type'].value_counts().reset_index()
        bar_data.columns = ['Leak Type', 'Count']
        fig_bar = px.bar(bar_data, x='Leak Type', y='Count',
                         color='Leak Type',
                         color_discrete_sequence=[COLORS['teal_blue'], COLORS['moonstone_blue'], COLORS['powder_blue'], COLORS['magic_mint']],
                         title="Leak Reports by Type")
        st.plotly_chart(fig_bar, use_container_width=True)

    if "Status" in df.columns:
        pie_data = df['Status'].value_counts().reset_index()
        pie_data.columns = ['Status', 'Count']
        fig_pie = px.pie(pie_data, names='Status', values='Count',
                         color='Status',
                         color_discrete_sequence=[COLORS['moonstone_blue'], COLORS['magic_mint']],
                         title="Status Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)

    if "DateTime" in df.columns:
        time_data = df.groupby(df['DateTime'].dt.date).size().reset_index(name='Count')
        fig_time = px.line(time_data, x='DateTime', y='Count', title="Reports Over Time",
                           markers=True, color_discrete_sequence=[COLORS['teal_blue']])
        st.plotly_chart(fig_time, use_container_width=True)

    if "Municipality" in df.columns:
        top_muni = df['Municipality'].value_counts().nlargest(3).reset_index()
        top_muni.columns = ['Municipality', 'Reports']
        st.markdown("### 🏆 Top 3 Municipalities by Number of Reports")
        cols = st.columns(3)
        for i, row in top_muni.iterrows():
            cols[i].metric(row['Municipality'], row['Reports'])

    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ MANAGE REPORTS ------------------
def manage_reports_page():
    if not st.session_state.get("logged_in") or "admin_municipality" not in st.session_state:
        st.warning("Please log in to view this page.")
        return

    st.markdown(f"<div style='background-color: rgba(176,224,230,0.8); padding:10px; border-radius:10px;margin-top:10px;'>", unsafe_allow_html=True)
    st.markdown("## Manage Reports")

    admin_muni = st.session_state.admin_municipality
    df_admin = df[df['Municipality'] == admin_muni]

    if df_admin.empty:
        st.info("No reports for your municipality.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    for i, row in df_admin.iterrows():
        with st.expander(f"Report #{row['ReportID']} — {row.get('Location','N/A')}"):
            st.write(row)
            current_status = row.get("Status", "Pending")
            options = ["Pending", "Resolved"]
            if current_status not in options: current_status = "Pending"
            new_status = st.selectbox("Update Status", options, index=options.index(current_status), key=f"status_{i}")
            if st.button("Update", key=f"update_{i}"):
                try:
                    cell = sheet.find(str(row['ReportID']))
                    sheet.update_cell(cell.row, df.columns.get_loc("Status")+1, new_status)
                    st.success(f"Status updated to {new_status}")
                    df.at[i, "Status"] = new_status
                except Exception as e:
                    st.error(f"Failed to update status: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ SIDEBAR ------------------
def custom_sidebar():
    set_background_local("images/images/WhatsApp Image 2025-10-21 at 22.42.03_3d1ddaaa.jpg",
                         show_on_page=["Home","Municipal Overview","Dashboard","Manage Reports"], sidebar=True)

    st.sidebar.markdown(f"<div style='background-color: rgba(255,255,255,0.8); padding:15px;border-radius:10px;text-align:center;'>"
                        f"<h3 style='color:black;'>Drop Watch SA</h3></div>", unsafe_allow_html=True)

    if st.sidebar.button("Home"): st.session_state.page = "Home"
    if st.sidebar.button("Municipal Overview"): st.session_state.page = "Municipal Overview"
    if st.sidebar.button("Dashboard"): st.session_state.page = "Dashboard"
    if st.sidebar.button("Manage Reports"): st.session_state.page = "Manage Reports"
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.page = "Login"

# ------------------ PAGE RENDER ------------------
if not st.session_state.logged_in:
    st.session_state.page = "Login"
    set_background_local("images/images/WhatsApp Image 2025-10-21 at 22.42.03_3d1ddaaa.jpg", show_on_page=["Login"])
    login_page()
else:
    custom_sidebar()
    if st.session_state.page == "Home": home_page(df)
    elif st.session_state.page == "Municipal Overview": municipal_overview_page()
    elif st.session_state.page == "Dashboard": dashboard_page()
    elif st.session_state.page == "Manage Reports": manage_reports_page()
