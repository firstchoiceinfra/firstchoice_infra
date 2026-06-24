import streamlit as st
import pandas as pd
import datetime

# --- 1. Force Sync Fix ---
def get_sync_data():
    # यह सीधे session_state से उठाएगा
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    
    # अगर ex खाली है तो inventory से पार्टनर ढूंढो
    if not ex and isinstance(db, dict):
        ex = {}
        for p in db.values():
            if isinstance(p, dict) and 'plots' in p:
                for info in (p['plots'].values() if isinstance(p['plots'], dict) else p['plots']):
                    if isinstance(info, dict) and 'executive_name' in info:
                        ex[info['executive_name']] = {'name': info['executive_name']}
    return db, ex

db_data, exec_data = get_sync_data()

# --- 2. UI - फिक्स ---
st.title("📊 Executive Commission Statement")

# पार्टनर लिस्ट का सुरक्षित लोडिंग
partner_list = sorted(list(exec_data.keys())) if isinstance(exec_data, dict) else []
if not partner_list:
    st.error("डेटा नहीं मिल रहा है। कृपया सुनिश्चित करें कि Partner Management में डेटा भरा है।")
else:
    search_exec = st.selectbox("👤 Select Partner", options=partner_list)
    
    # अब बाकी के ऑप्शन (जो गायब थे)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    col1, col2 = st.columns(2)
    start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Systematic Statement"):
        st.success(f"पार्टनर {search_exec} के लिए डेटा ढूँढ रहा हूँ...")
        # (यहाँ डेटा प्रोसेसिंग लॉजिक)

