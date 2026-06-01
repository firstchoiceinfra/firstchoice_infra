import streamlit as st
# हमारे डेटाबेस सिस्टम को इम्पोर्ट करें
import database 

# !!! मल्टी-पेज ऐप के लिए set_page_config यहाँ नहीं, केवल पेजों के अंदर होनी चाहिए !!!

# डेटाबेस को शुरू करें (ताकि सत्र स्थिति/session state तैयार हो जाए)
database.init_db()

# --- ऐप का टाइटल ---
st.title("FirstChoice Infra - ERP सिस्टम 🏗️")
st.write("Nagpur, Maharashtra")

# --- लॉगिन सिस्टम का लॉजिक ---
def check_login(user, pwd):
    # सुरक्षा के लिए बहुत ही सरल पासवर्ड (admin / admin123)
    return user == "admin" and pwd == "admin123"

# यदि उपयोगकर्ता लॉगिन नहीं है, तो लॉगिन फॉर्म दिखाएं
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.subheader("क्रेडेन्शियल्स दर्ज करें")
    username = st.text_input("यूज़रनेम (Username)", key="login_user")
    password = st.text_input("पासवर्ड (Password)", type="password", key="login_pwd")
    login_btn = st.button("लॉगिन करें")

    if login_btn:
        if check_login(username, password):
            st.session_state.logged_in = True
            st.success("लॉगिन सफल! कृपया साइडबार से मेनू चुनें।")
            st.rerun() # पेज रिफ्रेश करके नए मेनू दिखाएं
        else:
            st.error("गलत यूज़रनेम या पासवर्ड।")
else:
    # यदि लॉगिन है, तो स्वागत संदेश दिखाएं
    st.success("आप सफलतापूर्वक लॉगिन हैं!")
    st.info("← बाईं ओर (Sidebar) से एडमिन पैनल या इन्वेंट्री डैशबोर्ड चुनें।")
    
    # लॉगआउट बटन साइडबार में
    if st.sidebar.button("लॉगआउट"):
        st.session_state.logged_in = False
        st.rerun()
