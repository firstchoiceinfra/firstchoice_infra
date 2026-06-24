import streamlit as st
import datetime

st.title("📊 Executive Commission Dashboard")

# 1. डेटा लोड करें
db_data, exec_data = load_all_data() # ऊपर वाला फंक्शन यूज़ करें

# 2. अगर डेटा खाली है तो यहाँ से चेक करें
if not exec_data:
    st.error("❌ Data not found! Please check if Partner Management has data.")
    st.stop() # यहीं रुक जाएं, आगे न बढ़ें

# 3. पार्टनर लिस्ट
partner_list = sorted([v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)])

if partner_list:
    search_exec = st.selectbox("👤 Select Partner", options=partner_list)
    # ... बाकी का कोड (Generate बटन आदि)
else:
    st.warning("Partner list is empty.")

