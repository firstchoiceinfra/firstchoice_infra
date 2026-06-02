import streamlit as st
import database

# 1. डेटाबेस को शुरू करें ताकि सेटिंग्स लोड हो सकें
database.init_db()

# ====================================================================
# 🎨 यूनिवर्सल थीम रेंडरर (Universal Theme Layout)
# ====================================================================
# यह कोड एडमिन पैनल से अपलोड की गई फोटो और रंगों को यहाँ भी लागू करेगा
if 'db_projects' in st.session_state and '_app_settings' in st.session_state.db_projects:
    global_settings = st.session_state.db_projects['_app_settings']
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("{global_settings.get('bg_url')}");
        background-attachment: fixed;
        background-size: cover;
    }}
    .block-container {{
        background-color: {global_settings.get('card_bg', 'rgba(255, 255, 255, 0.92)')} !important;
        padding: 2rem 3rem !important;
        border-radius: 20px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }}
    h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
        color: {global_settings.get('primary_color', '#1e3a8a')} !important;
        font-weight: 800;
    }}
    .stButton>button {{
        background: linear-gradient(90deg, {global_settings.get('primary_color', '#1e3a8a')} 0%, {global_settings.get('secondary_color', '#3b82f6')} 100%);
        color: white !important;
        border-radius: 8px;
        border: none;
        font-weight: bold;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)
# ====================================================================

# --- ऐप का टाइटल ---
st.markdown("<h1 style='text-align: center;'>FirstChoice Infra - ERP सिस्टम 🏗️</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; color: #475569;'>Nagpur, Maharashtra</p>", unsafe_allow_html=True)

# --- लॉगिन सिस्टम का लॉजिक ---
def check_login(user, pwd):
    return user == "admin" and pwd == "admin123"

# यदि उपयोगकर्ता लॉगिन नहीं है, तो लॉगिन फॉर्म दिखाएं
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.subheader("🔒 क्रेडेन्शियल्स दर्ज करें (Login Here)")
    username = st.text_input("यूज़रनेम (Username)", key="login_user")
    password = st.text_input("पासवर्ड (Password)", type="password", key="login_pwd")
    login_btn = st.button("लॉगिन करें")

    if login_btn:
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("🎉 लॉगिन सफल! कृपया साइडबार से मेनू चुनें।")
            st.rerun()
        else:
            st.error("🚨 गलत यूज़रनेम या पासवर्ड।")
else:
    st.success("✅ आप सफलतापूर्वक लॉगिन हैं!")
    st.info("← बाईं ओर (Sidebar ☰) से एडमिन पैनल या इन्वेंट्री डैशबोर्ड चुनें।")
    
    if st.sidebar.button("लॉगआउट (Logout)"):
        st.session_state.logged_in = False
        st.rerun()
