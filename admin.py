# -*- coding: utf-8 -*-
"""Drop Watch SA Admin Dashboard (Modern, Multimedia & API-Safe)"""

import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from datetime import datetime
import plotly.express as px
import pydeck as pdk
import ast

# --- App Config ---
st.set_page_config(
    page_title="Drop Watch SA Admin Panel",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Secrets ---
ADMIN_CODE = st.secrets["general"]["admin_code"]
SPREADSHEET_ID = "1leh-sPgpoHy3E62l_Rnc11JFyyF-kBNlWTICxW1tam8"

# --- UI Theme Colors ---
HEADER_FOOTER_COLOR = "#264653"
SIDEBAR_COLOR = "#e9ecef"
BUTTON_COLOR = "#2a9d8f"
METRIC_COLOR = "#1d3557"
BG_COLOR = "#f7f9fb"

STATUS_COLORS = {
    "Pending": "#f4a261",
    "In Progress": "#e76f51",
    "Resolved": "#2a9d8f",
    "Rejected": "#e63946"
}

# --- Get Google Sheet Data ---
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

    # Ensure missing columns exist
    if "Images" not in df.columns:
        df["Images"] = ""
    if "VideoURL" not in df.columns:
        df["VideoURL"] = ""

    # Parse image lists safely
    def parse_images(img_str):
        if pd.isna(img_str) or img_str.strip() == "":
            return []
        try:
            imgs = ast.literal_eval(img_str)
            if isinstance(imgs, str):
                return [imgs]
            elif isinstance(imgs, list):
                return imgs
            else:
                return []
        except:
            return [img_str]
    df["Images"] = df["Images"].apply(parse_images)

    return sheet, df

# --- Update Report Using Google Sheets API ---
def update_report(sheet, row_idx, status):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["google_service_account"],
            scopes=scopes
        )

        service = build("sheets", "v4", credentials=creds)
        sheet_name = sheet.title

        body = {
            "valueInputOption": "USER_ENTERED",
            "data": [
                {"range": f"{sheet_name}!H{row_idx}", "values": [[status]]},
                {"range": f"{sheet_name}!I{row_idx}", "values": [[datetime.now().strftime('%Y-%m-%d %H:%M:%S')]]},
            ],
        }

        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body=body
        ).execute()

        st.success(f"✅ Report updated to '{status}'.")
    except Exception as e:
        st.error(f"Failed to update: {e}")

# --- Header / Footer ---
def show_header_footer():
    st.markdown(f"""
    <style>
    .header {{
        background-color:{HEADER_FOOTER_COLOR};
        color:white; text-align:center;
        padding:25px; font-size:24px;
        font-family:Cinzel, serif;
        position:fixed; top:0; width:100%; z-index:1000;
    }}
    .footer {{
        background-color:{HEADER_FOOTER_COLOR};
        color:white; text-align:center;
        padding:10px; font-family:Cinzel, serif;
        position:fixed; bottom:0; width:100%;
    }}
    section[data-testid="stSidebar"] {{
        background-color:{SIDEBAR_COLOR} !important;
        color:{METRIC_COLOR} !important;
        padding:1.5rem 1rem;
    }}
    section[data-testid="stSidebar"] * {{
        color:{METRIC_COLOR} !important;
        font-family:'Cinzel', serif !important;
        font-size:16px;
    }}
    div.stButton > button {{
        color:white !important;
        background-color:{BUTTON_COLOR} !important;
        font-family:'Cinzel', serif !important;
    }}
    div.stButton > button:hover {{
        background-color:#21867a !important; cursor:pointer;
    }}
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{
        color:{METRIC_COLOR} !important;
        font-family:'Cinzel', serif !important;
    }}
    .stApp {{
        background-color:{BG_COLOR} !important;
        color:{METRIC_COLOR} !important;
        font-family:'Cinzel', serif !important;
    }}
    section[data-testid="stSidebar"] div[aria-label="Keyboard"] {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="header">Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:100px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="footer">&copy; 2025 Drop Watch SA</div>', unsafe_allow_html=True)
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

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

    # Time Series
    if "DateReported" in df.columns:
        try:
            df["DateReported"] = pd.to_datetime(df["DateReported"])
            ts = df.groupby(["DateReported","Status"]).size().reset_index(name="Count")
            fig3 = px.line(ts, x="DateReported", y="Count", color="Status",
                           color_discrete_map=STATUS_COLORS, template="plotly_white",
                           title="Reports Over Time")
            st.subheader("Reports Over Time")
            st.plotly_chart(fig3, use_container_width=True)
        except Exception:
            pass

    # Map Visualization
    if "Latitude" in df.columns and "Longitude" in df.columns:
        st.subheader("Leak Locations Map")
        df_map = df.dropna(subset=["Latitude","Longitude"])
        if not df_map.empty:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position='[Longitude, Latitude]',
                get_radius=200,
                get_fill_color='[230, 80, 80, 160]',
                pickable=True
            )
            view_state = pdk.ViewState(
                latitude=df_map["Latitude"].mean(),
                longitude=df_map["Longitude"].mean(),
                zoom=6, pitch=0
            )
            r = pdk.Deck(layers=[layer], initial_view_state=view_state,
                         tooltip={"text": "ReportID: {ReportID}\nStatus: {Status}"})
            st.pydeck_chart(r)

# --- Manage Reports Page ---
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
            imgs = report.get("Images", [])
            if imgs:
                st.write("📸 Attached Images:")
                for img in imgs:
                    if img.strip():
                        st.image(img, width=300)

            # Video
            video = report.get("VideoURL")
            if video and video.strip() != "":
                st.write("🎥 Attached Video:")
                st.video(video)

            status = st.selectbox("Update Status",
                                  options=["Pending", "In Progress", "Resolved", "Rejected"],
                                  index=["Pending", "In Progress", "Resolved", "Rejected"].index(report.get("Status","Pending")),
                                  key=f"status_{idx}")
            if st.button("Update", key=f"update_{idx}"):
                update_report(sheet, idx, status)

# --- Main ---
def main():
    show_header_footer()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    # Login Page
    if not st.session_state["logged_in"]:
        st.markdown("### Admin Login")
        code = st.text_input("Enter Admin Code:", type="password")
        if st.button("Login"):
            if code == ADMIN_CODE:
                st.session_state["logged_in"] = True
                st.success("Login successful! Redirecting...")
                st.rerun()
            else:
                st.error("Invalid admin code")
        return

    # Sidebar
    with st.sidebar:
        st.header("Navigation")
        page = st.radio("Go to:", ["Dashboard", "Manage Reports"])
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.rerun()

    # Data Load
    sheet, df = get_sheet_data()
    if df.empty:
        st.info("No reports found.")
        return
    df.columns = df.columns.str.strip()

    # Render Page
    if page == "Dashboard":
        dashboard_page(df)
    elif page == "Manage Reports":
        manage_reports_page(df, sheet)

if __name__ == "__main__":
    main()
