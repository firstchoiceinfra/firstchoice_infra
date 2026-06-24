import streamlit as st
import pandas as pd
import datetime

st.title("📊 Executive Commission Dashboard")

# 1. डेटा लोड करने का सुरक्षित तरीका
db_data = st.session_state.get('db_projects', {})
exec_data = st.session_state.get('executives', {})

# पार्टनर लिस्ट बनाना
partner_list = []
if isinstance(exec_data, dict):
    partner_list = sorted([v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)])

# 2. ऑप्शंस हमेशा दिखेंगे (चाहे डेटा हो या न हो)
if not partner_list:
    st.warning("⚠️ No partners found in 'Partner Management'. Refresh the data.")

search_exec = st.selectbox("👤 Select Partner", options=partner_list if partner_list else ["No Data Found"])
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

# 3. जनरेट बटन हमेशा दिखेगा
if st.button("🚀 Generate Systematic Statement"):
    if not partner_list:
        st.error("Cannot generate: Partner list is empty.")
    else:
        # यहाँ आपका कैलकुलेशन लॉजिक जो डेटा जनरेट करेगा
        st.session_state.final_df = pd.DataFrame() # यहाँ अपना DataFrame भरें
        st.session_state.meta_data = {"partner": search_exec, "start": start_d, "end": end_d}
        st.session_state.page = 'report'
        st.rerun()

# 4. रिपोर्ट सेक्शन का स्विच
if st.session_state.get('page') == 'report':
    st.info("Report is ready. Please proceed to the report section.")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

