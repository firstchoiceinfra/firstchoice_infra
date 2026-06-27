import streamlit as st
import pandas as pd
import database
import datetime

# 1. पेज कॉन्फ़िगरेशन
st.set_page_config(layout="wide")

# 2. एडमिन चेक (सबसे पहले)
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied! केवल एडमिन के लिए।")
    st.stop()

st.title("📊 Commission Dashboard")

# 3. डेटा लोड करना
try:
    if 'db_projects' not in st.session_state:
        database.init_db()
    
    db_data = st.session_state.get('db_projects', {})
    exec_data = db_data.get('executives', {})
    st.success("डेटा लोड हो गया!") # चेक करने के लिए
except Exception as e:
    st.error(f"डेटाबेस एरर: {e}")
    st.stop()

# 4. पार्टनर सिलेक्शन (सिंपल)
if exec_data:
    partner_names = [v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)]
    selected_partner = st.selectbox("पार्टनर चुनें", partner_names)
    
    if st.button("डेटा दिखाएं"):
        st.write(f"आप {selected_partner} का डेटा देख रहे हैं।")
        # यहाँ हम अपना कैलकुलेशन लॉजिक बाद में जोड़ेंगे
else:
    st.warning("पार्टनर लिस्ट खाली है।")

