import streamlit as st

# एक्जीक्यूटिव डेटा (अस्थायी)
if 'executives' not in st.session_state:
    st.session_state.executives = {"8317259986": "shubham dekate"}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

# ----------------- पुराना डैशबोर्ड फंक्शन -----------------
def show_dashboard():
    st.title("🏢 Firstchoice Infra ERP System")
    st.markdown("---")
    st.subheader("सिस्टम डैशबोर्ड")
    st.write("स्वागत है! कृपया नीचे दिए गए विकल्पों में से किसी एक को चुनें:")
    col1, col2 = st.columns(2)
    with col1:
        st.button("📊 डैशबोर्ड देखें")
    with col2:
        st.button("📝 नई बुकिंग करें")
    st.markdown("---")

# ----------------- लॉगिन फंक्शन -----------------
def login():
    st.title("🔐 Firstchoice Infra - Login")
    username = st.text_input("Username (Name for Exec)")
    password = st.text_input("Password (Mobile for Exec)", type="password")
    
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        elif username in st.session_state.executives.values() and password in st.session_state.executives.keys():
            st.session_state.logged_in = True
            st.session_state.role = "executive"
            st.session_state.username = username
            st.rerun()
        else:
            st.error("गलत Username या Password!")

# ----------------- मेन लॉजिक -----------------
if not st.session_state.logged_in:
    login()
else:
    # एडमिन का अलग पैनल
    if st.session_state.role == "admin":
        st.title("🏢 Admin Panel")
        with st.expander("➕ Add New Executive"):
            new_name = st.text_input("Executive Name")
            new_mobile = st.text_input("Mobile Number")
            if st.button("Save Executive"):
                st.session_state.executives[new_mobile] = new_name
                st.success(f"Executive {new_name} saved!")
        st.write("Registered Executives:", st.session_state.executives)
        st.markdown("---")
        show_dashboard() # एडमिन को डैशबोर्ड भी दिखेगा
    
    # एक्जीक्यूटिव का डैशबोर्ड
    elif st.session_state.role == "executive":
        show_dashboard() # एक्जीक्यूटिव को डैशबोर्ड दिखेगा

    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()
