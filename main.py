import streamlit as st

# एक्जीक्यूटिव डेटा को स्टोर करने के लिए (अस्थायी डेटाबेस)
if 'executives' not in st.session_state:
    st.session_state.executives = {} # {mobile: name}

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role = None
    st.session_state.username = None

def login():
    st.title("🔐 Firstchoice Infra - Login")
    username = st.text_input("Username (Name for Executives)")
    password = st.text_input("Password (Mobile for Executives)", type="password")
    
    if st.button("Login"):
        # एडमिन का फिक्स लॉगिन
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        # एक्जीक्यूटिव का डायनामिक लॉगिन
        elif username in st.session_state.executives.values() and password in st.session_state.executives.keys():
            st.session_state.logged_in = True
            st.session_state.role = "executive"
            st.session_state.username = username
            st.rerun()
        else:
            st.error("गलत Username या Password!")

# मेन प्रोग्राम
if not st.session_state.logged_in:
    login()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.role}**")
    
    if st.session_state.role == "admin":
        st.title("🏢 Admin Panel")
        # एक्जीक्यूटिव रजिस्टर करने का पेज
        with st.expander("➕ Add New Executive"):
            new_name = st.text_input("Executive Name")
            new_mobile = st.text_input("Mobile Number (as password)")
            if st.button("Save Executive"):
                st.session_state.executives[new_mobile] = new_name
                st.success(f"Executive {new_name} saved!")
        st.write("Registered Executives:", st.session_state.executives)
    
    elif st.session_state.role == "executive":
        st.title("🏠 Executive Dashboard")
        st.write(f"नमस्ते {st.session_state.username}, आप अपनी बुकिंग्स यहाँ देख सकते हैं।")
    
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()
