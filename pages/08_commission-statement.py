import streamlit as st
import datetime

st.title("📊 Executive Commission Dashboard")

# Force Sync to get partners
db_data = st.session_state.get('db_projects', {})
exec_data = st.session_state.get('executives', {})

# Extract partner names clearly
partner_list = []
if isinstance(exec_data, dict):
    partner_list = sorted([v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)])

if not partner_list:
    st.warning("No partners found. Ensure data is saved in 'Partner Management'.")
    if st.button("🔄 Refresh Data"):
        st.rerun()
else:
    search_exec = st.selectbox("👤 Select Partner", options=partner_list)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    
    col1, col2 = st.columns(2)
    start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Data"):
        # Logic to filter data and save to session_state
        st.session_state.target_partner = search_exec
        st.session_state.scope = scope
        st.session_state.start_date = start_d
        st.session_state.end_date = end_d
        st.success("Data processed! Please go to 'Commission Report' page.")

