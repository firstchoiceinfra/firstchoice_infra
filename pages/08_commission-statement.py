import streamlit as st
import pandas as pd
import datetime

# --- 1. Bulletproof Data Fetcher ---
def get_all_data():
    # यह सेशन स्टेट को चेक करेगा, अगर नहीं है तो रिफ्रेश करेगा
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    return db, ex

st.title("📊 Executive Commission Dashboard")

db_data, exec_data = get_all_data()

# --- 2. Force Partner Load ---
# अगर exec_data खाली है, तो inventory से नाम निकालने का जुगाड़
if not exec_data and db_data:
    partner_list = set()
    for p in db_data.values():
        if isinstance(p, dict) and 'plots' in p:
            for info in (p['plots'].values() if isinstance(p['plots'], dict) else p['plots']):
                if isinstance(info, dict) and 'executive_name' in info:
                    partner_list.add(info['executive_name'])
    exec_data = {name: {'name': name} for name in partner_list}

# --- 3. UI ---
partner_names = sorted([val.get('name', k) for k, val in exec_data.items() if isinstance(val, dict)])

if not partner_names:
    st.warning("No partners found. Ensure data is saved in 'Partner Management'.")
    if st.button("🔄 Refresh Data"):
        st.rerun()
else:
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    
    col1, col2 = st.columns(2)
    start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Systematic Statement"):
        # यहाँ अपना कैलकुलेशन लॉजिक रखें...
        st.success(f"Statement generated for {search_exec}")

