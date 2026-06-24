import streamlit as st
import pandas as pd
import datetime

# 1. डेटा फेचिंग फंक्शन
def get_data():
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    partners = sorted([v.get('name', k) for k, v in ex.items() if isinstance(v, dict)])
    return db, partners

db_data, partner_list = get_data()

# 2. पेज स्टेट मैनेजमेंट (Dashboard vs Report)
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# --- DASHBOARD SECTION ---
if st.session_state.page == 'dashboard':
    st.title("📊 Executive Commission Dashboard")
    
    if not partner_list:
        st.warning("No partners found. Ensure data is saved in 'Partner Management'.")
    else:
        search_exec = st.selectbox("👤 Select Partner", options=partner_list)
        scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
        col1, col2 = st.columns(2)
        start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
        end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

        if st.button("🚀 Generate Systematic Statement"):
            # यहाँ अपना कैलकुलेशन लॉजिक डालें और रिजल्ट df में सेव करें
            # st.session_state.final_df = df
            st.session_state.meta_data = {"partner": search_exec, "start": start_d, "end": end_d}
            st.session_state.page = 'report'
            st.rerun()

# --- REPORT SECTION ---
elif st.session_state.page == 'report':
    st.title("📄 Executive Commission Statement")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    # यहाँ अपनी टेबल और प्रिंट वाला लॉजिक दिखाएं
    if 'final_df' in st.session_state:
        st.table(st.session_state.final_df)
        
        if st.button("🖨️ Print to A4"):
            # वही HTML प्रिंट कोड यहाँ रखें
            pass
    else:
        st.error("No data found!")
        st.session_state.page = 'dashboard'

