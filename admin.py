def login_page():
    show_header_footer()

    # Your original HTML for the login card stays completely the same
    st.markdown("""
        <style>
            .login-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 75vh;
                text-align: center;
            }
            .login-card {
                background: white;
                padding: 40px;
                border-radius: 12px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                width: 380px;
                text-align: center;
            }
            .login-card h2 {
                font-family: 'Cinzel', serif;
                font-weight: 600;
                color: #0d6efd;
                margin-bottom: 10px;
            }
            .login-card img {
                height: 80px;
                margin-bottom: 15px;
            }
            .stTextInput input {
                border-radius: 8px !important;
                padding: 10px !important;
                font-size: 16px !important;
            }
            div.stButton > button {
                width: 100%;
                border-radius: 8px !important;
                font-weight: 600;
                background-color: #0d6efd !important;
                color: white !important;
            }
            div.stButton > button:hover {
                background-color: #0b5ed7 !important;
            }
        </style>
        <div class="login-container">
            <div class="login-card">
                <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/5/59/Water_drop_icon.svg/1024px-Water_drop_icon.svg.png" alt="Drop Watch Logo">
                <h2>Drop Watch SA</h2>
                <p style='color:#555;'>Administrator Access</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    code = st.text_input("Enter Admin Code:", type="password", key="login_input")
    
    if st.button("Login", use_container_width=True):
        if code == ADMIN_CODE:
            st.session_state["logged_in"] = True
        else:
            st.error("Invalid admin code")
    
    # Stop everything else until logged in
    if not st.session_state.get("logged_in", False):
        st.stop()
