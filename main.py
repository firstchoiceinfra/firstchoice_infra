import streamlit as st
import database

# 1. Initialize and Load Database
database.init_db()

# ====================================================================
# 🎨 Universal Theme Engine Integration
# ====================================================================
if 'db_projects' in st.session_state and '_app_settings' in st.session_state.db_projects:
    global_settings = st.session_state.db_projects['_app_settings']
    st.markdown(f"""
    <style>
    .stApp {{ background-image: url("{global_settings.get('bg_url')}"); background-attachment: fixed; background-size: cover; }}
    .block-container {{ background-color: {global_settings.get('card_bg', 'rgba(255, 255, 255, 0.92)')} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
    h1, h2, h3 {{ color: {global_settings.get('primary_color', '#1e3a8a')} !important; font-weight: 800; }}
    .stButton>button {{ background: linear-gradient(90deg, {global_settings.get('primary_color', '#1e3a8a')} 0%, {global_settings.get('secondary_color', '#3b82f6')} 100%); color: white !important; border-radius: 8px; border: none; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
    </style>
    """, unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>FirstChoice Infra - ERP System 🏗️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; color: #475569;'>Nagpur, Maharashtra</p>", unsafe_allow_html=True)

# --- Smart Case-Insensitive Login Authentication ---
def verify_user_login(user_id, password):
    # A. Master Administrator Authorization
    if user_id.strip().lower() == "admin" and password.strip() == "admin123":
        st.session_state.user_role = "admin"
        st.session_state.current_user_name = "Admin"
        return True
        
    # B. Dynamic Executive / Associate Authorization
    executives_db = st.session_state.db_projects.get('executives', {})
    user_clean = user_id.strip().lower()
    
    matched_exec = None
    for key, val in executives_db.items():
        if key.lower() == user_clean:
            matched_exec = val
            break
            
    if matched_exec and isinstance(matched_exec, dict):
        if str(matched_exec.get('mobile')).strip() == password.strip():
            st.session_state.user_role = "executive"
            st.session_state.current_user_name = matched_exec.get('name', user_id)
            return True
            
    return False

# --- User Interface Logic ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.subheader("🔒 Authentication Portal Required")
    username = st.text_input("Username / Registered Name (User ID)")
    password = st.text_input("Password / Contact Number (Password)", type="password")
    login_btn = st.button("Authenticate System Access", use_container_width=True)

    if login_btn:
        if verify_user_login(username, password):
            st.session_state.logged_in = True
            st.success(f"🎉 Access Granted! Welcome back, {st.session_state.current_user_name}.")
            st.rerun()
        else:
            st.error("🚨 Invalid Credentials! Please double-check your User ID and Password string layout.")
else:
    st.success(f"✅ Secure Session Active: **{st.session_state.current_user_name}** ({st.session_state.user_role.upper()})")
    st.info("← Expand the sidebar configuration panel (Sidebar ☰) to view the Inventory Grid Layout or generate Statements.")
    
    if st.sidebar.button("Secure Logout"):
        st.session_state.logged_in = False
        st.session_state.user_role = None
        st.session_state.current_user_name = None
        st.rerun()
