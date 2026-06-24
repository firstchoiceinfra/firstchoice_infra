import streamlit as st
import pandas as pd
import datetime

st.title("📊 Executive Commission Dashboard")

# 1. डेटाबेस से पार्टनर डेटा को सीधे खींचने वाला फंक्शन
def get_partner_data():
    # यह चेक करेगा कि सेशन स्टेट में डेटा है या नहीं
    if 'executives' in st.session_state and st.session_state['executives']:
        return st.session_state['executives']
    
    # अगर नहीं है, तो इन्वेंटरी डेटा से पार्टनर ढूंढने की कोशिश करेगा
    if 'db_projects' in st.session_state:
        db = st.session_state['db_projects']
        partners = set()
        for project in db.values():
            if isinstance(project, dict) and 'plots' in project:
                for plot in (project['plots'].values() if isinstance(project['plots'], dict) else project['plots']):
                    if isinstance(plot, dict) and 'executive_name' in plot:
                        partners.add(plot['executive_name'])
        return {name: {'name': name} for name in partners}
    
    return {}

# 2. डेटा को लोड करें
exec_data = get_partner_data()

# 3. पार्टनर लिस्ट बनाएं
if not exec_data:
    st.error("❌ No data found! Please go to 'Partner Management' page and save/update data once.")
else:
    partner_names = sorted([val.get('name', k) for k, val in exec_data.items() if isinstance(val, dict)])
    
    # UI कंपोनेंट्स
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    
    col1, col2 = st.columns(2)
    start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Systematic Statement"):
        st.success(f"Statement generated for {search_exec}")
        # यहाँ अपना कैलकुलेशन लॉजिक डालें

