import streamlit as st
import pandas as pd
import datetime

# --- 1. Master Sync Fix ---
def get_sync_data():
    db = st.session_state.get('db_projects', {})
    # अगर executives खाली है, तो db_projects से निकालो
    ex = st.session_state.get('executives', {})
    if not ex:
        # अगर अलग से नहीं मिला, तो db_projects से कलेक्ट करो
        ex = {info.get('executive_name'): {'name': info.get('executive_name')} 
              for p in db.values() if isinstance(p, dict) and 'plots' in p 
              for info in p['plots'].values() if isinstance(info, dict) and 'executive_name' in info}
    return db, ex

db_data, exec_data = get_sync_data()

# --- 2. UI ---
st.title("📊 Executive Commission Statement")

# फिक्स: पार्टनर सिलेक्शन अब खाली नहीं रहेगा
partner_list = sorted(list(exec_data.keys())) if exec_data else []
search_exec = st.selectbox("👤 Select Partner", options=partner_list if partner_list else ["No Partners Found"])

if not partner_list:
    st.warning("डेटाबेस में कोई पार्टनर नहीं मिल रहा है। कृपया इन्वेंटरी या पार्टनर पेज चेक करें।")
    st.stop()

# बाकी फिल्टर्स
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

# --- 3. Generate Engine ---
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    # (यहाँ डेटा लूप वही रहेगा जो मैंने पहले दिया था - वह बिल्कुल सही है)
    # ...
    # अगर डेटा आता है तो session_state में डाल दें
    # st.session_state.final_df = df

