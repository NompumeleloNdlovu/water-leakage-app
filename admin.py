# -*- coding: utf-8 -*-
"""admin_dashboard_modern_multimedia_images_fixed.py"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import plotly.express as px
import pydeck as pdk
import ast  # For parsing image lists

# --- App Config ---
st.set_page_config(
    page_title="Drop Watch SA Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Secrets ---
ADMIN_CODE = st.secrets["general"]["admin_code"]
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- Status Colors ---
STATUS_COLORS = {
    "Pending": "#f4a261",
    "In Progress": "#e76f51",
    "Resolved": "#2a9d8f",
    "Rejected": "#e63946"
}

# --- Professional Palette ---
HEADER_FOOTER_COLOR = "#006d77"
SIDEBAR_COLOR = "#83c5be"
BUTTON_COLOR = "#00b4d8"
METRIC_COLOR = "#333333"
BG_COLOR = "#f5f5f5"

# --- Connect to Google Sheets ---
@st.cache_data
def get_sheet_data():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["google_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SPREADSHEET_ID).sheet1
    df = pd.DataFrame(sheet.get_all_records())

    # --- Parse Images Column ---
    if "Images" in df.columns:
        def parse_images(img_str):
            if pd.isna(img_str) or img_str.strip() == "":
                return []
            try:
                return ast.literal_eval(img_str)
            except:
                return [img_str]
        df["Images"] = df["Images"].apply(parse_images)

    # --- Ensure VideoURL column exists ---
    if "VideoURL" not in df.columns:
        df["VideoURL"] = ""
        
    return sheet, df

# --- Update report ---
def update_report(sheet, row_idx, status):
    try:
        sheet.update_cell(row_idx, 8, status)
        sheet.update_cell(row_idx, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.success(f"Report updated to '{status}'.")
    except Exception as e:
        st.error(f"Failed to update: {e}")

# --- Header / Footer ---
def show_header_footer():
    st.markdown(f"""
    <style>
    .header {{background-color:{HEADER_FOOTER_COLOR}; color:white; text-align:center; padding:25px; font-size:24px; font-family:Cinzel, serif;}}
    .footer {{background-color:{HEADER_FOOTER_COLOR}; color:white; text-align:center; padding:10px; font-family:Cinzel, serif; position:fixed; bottom:0; width:100%;}}
    section[data-testid="stSidebar"] {{ background-color:{SIDEBAR_COLOR} !important; color:{METRIC_COLOR} !important; padding:1.5rem 1rem; }}
    section[data-testid="stSidebar"] * {{ color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; font-size:16px; }}
    div.stButton > button {{ color: white !important; background-color: {BUTTON_COLOR} !important; font-family: 'Cinzel', serif !important; }}
    div.stButton > button:hover {{ background-color: #009acb !important; cursor:pointer; }}
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{ color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; }}
    .stApp {{ background-color: {BG_COLOR} !important; color:{METRIC_COLOR} !important; font-family:'Cinzel', serif !important; }}
    section[data-testid="stSidebar"] div[aria-label="Keyboard"] {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="header">Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">&copy; 2025 Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown("<div style='margin-top:80px; margin-bottom:60px;'></div>", unsafe_allow_html=True)

# --- Dashboard Page ---
def dashboard_page(df):
    st.header("Dashboard Overview")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Reports", len(df))
    col2.metric("Pending", (df["Status"]=="Pending").sum())
    col3.metric("In Progress", (df["Status"]=="In Progress").sum())
    col4.metric("Resolved", (df["Status"]=="Resolved").sum())

    st.subheader("Reports by Municipality")
    fig1 = px.bar(df, x="Municipality", color="Status", barmode="group",
                  color_discrete_map=STATUS_COLORS, template="plotly_white")
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Leak Types Reported")
    fig2 = px.pie(df, names="Leak Type", color="Status",
                  color_discrete_map=STATUS_COLORS, template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)

    if "DateReported" in df.columns:
        df['DateReported'] = pd.to_datetime(df['DateReported'])
        ts = df.groupby(['DateReported','Status']).size().reset_index(name='Count')
        fig3 = px.line(ts, x='DateReported', y='Count', color='Status',
                       color_discrete_map=STATUS_COLORS, template="plotly_white",
                       title="Reports Over Time")
        st.subheader("Reports Over Time")
        st.plotly_chart(fig3, use_container_width=True)

    fig4 = px.bar(df, x='Leak Type', color='Status', barmode='stack',
                  color_discrete_map=STATUS_COLORS, template="plotly_white",
                  title="Leak Status by Type")
    st.subheader("Leak Status by Type")
    st.plotly_chart(fig4, use_container_width=True)

    # Map
    if "Latitude" in df.columns and "Longitude" in df.columns:
        st.subheader("Leak Locations Map")
        df_map = df.dropna(subset=['Latitude','Longitude'])
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_map,
            get_position='[Longitude, Latitude]',
            get_radius=200,
            get_fill_color='[230, 80, 80, 160]',
            pickable=True
        )
        view_state = pdk.ViewState(
            latitude=df_map['Latitude'].mean(),
            longitude=df_map['Longitude'].mean(),
            zoom=6, pitch=0
        )
        r = pdk.Deck(layers=[layer], initial_view_state=view_state,
                     tooltip={"text": "ReportID: {ReportID}\nStatus: {Status}"})
        st.pydeck_chart(r)

# --- Manage Reports with Images/Videos ---
def manage_reports_page(df, sheet):
    st.header("Manage Reports")
    for idx, report in enumerate(df.to_dict("records"), start=2):
        with st.expander(f"Report {report['ReportID']} - {report['Name']}"):
            st.markdown(f"""
                **Municipality:** {report['Municipality']}  
                **Leak Type:** {report['Leak Type']}  
                **Status:** {report['Status']}  
            """)
            # Images
            for img in report.get("Images", []):
                st.image(img, width=300)
            # Video
            video = report.get("VideoURL")
            if video and video.strip() != "":
                st.video(video)

            status = st.selectbox("Update Status",
                                  options=["Pending", "In Progress", "Resolved", "Rejected"],
                                  index=["Pending", "In Progress", "Resolved", "Rejected"].index(report.get("Status","Pending")),
                                  key=f"status_{idx}")
            if st.button("Update", key=f"update_{idx}"):
                update_report(sheet, idx, status)

# --- Main App ---
def main():
    show_header_footer()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # --- Login Check ---
    if not st.session_state["logged_in"]:
        st.markdown("### Admin Login")
        code = st.text_input("Enter Admin Code:", type="password")
        if st.button("Login"):
            if code == ADMIN_CODE:
                st.session_state["logged_in"] = True
                st.success("Login successful! Please navigate using the sidebar.")
            else:
                st.error("Invalid admin code")
        return

    # --- Sidebar Navigation ---
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.experimental_rerun()

    # --- Load Data ---
    sheet, df = get_sheet_data()
    if df.empty:
        st.info("No reports found.")
        return
    df.columns = df.columns.str.strip()

    # --- Page Rendering ---
    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, sheet)

if __name__ == "__main__":
    main()
