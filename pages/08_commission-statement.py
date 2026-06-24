import streamlit as st
import pandas as pd
import datetime

st.title("📊 Executive Commission Dashboard")

# 1. सीधे session_state से डेटा उठाएं (कोई फंक्शन नहीं, कोई एरर नहीं)
db_data = st.session_state.get('db_projects', {})
exec_data = st.session_state.get('executives', {})

# 2. पार्टनर की लिस्ट बनाने का सुरक्षित तरीका
partner_names = []
if isinstance(exec_data, dict):
    for k, v in exec_data.items():
        if isinstance(v, dict):
            partner_names.append(v.get('name', k))
elif isinstance(exec_data, list):
    partner_names = exec_data

partner_names = sorted(list(set(partner_names)))

# 3. UI दिखाना
if not partner_names:
    st.warning("No partners found. Please make sure data is saved in 'Partner Management'.")
else:
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    
    col1, col2 = st.columns(2)
    start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Data"):
        st.success(f"Data generated for {search_exec}!")
        # यहाँ अपना कैलकुलेशन लूप रखें...

