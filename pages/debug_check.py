import streamlit as st
import database

st.set_page_config(layout="wide", page_title="Debug Check")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

if st.session_state.get('user_role', 'executive') != 'admin':
    st.error("🚨 Access Denied! Yeh page sirf Admin ke liye hai.")
    st.info("💡 Is page ke liye Admin se contact karo.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

st.title("🔍 Debug — Plot Data Check")

project_names = [n for n, d in db_data.items()
                 if isinstance(d, dict) and ('plots' in d or 'total_plots' in d)]

proj = st.selectbox("Project:", project_names)
if proj:
    plots = db_data[proj].get('plots', {})
    if isinstance(plots, list):
        plots = {str(i): p for i, p in enumerate(plots) if p is not None}
    
    booked = {k: v for k, v in plots.items() 
              if isinstance(v, dict) and v.get('status') == 'Booked'}
    
    plot_id = st.selectbox("Plot:", list(booked.keys()))
    if plot_id:
        p = booked[plot_id]
        st.subheader("Raw Data:")
        
        # Show key fields
        col1, col2 = st.columns(2)
        col1.metric("company_rate", p.get('company_rate', '❌ NOT FOUND'))
        col1.metric("rate_per_sqft", p.get('rate_per_sqft', '❌ NOT FOUND'))
        col1.metric("selling_rate", p.get('selling_rate', '❌ NOT FOUND'))
        col1.metric("plot_area", p.get('plot_area', '❌ NOT FOUND'))
        col2.metric("customer_name", p.get('customer_name', 'N/A'))
        col2.metric("executive_name", p.get('executive_name', 'N/A'))
        col2.metric("is_primary", p.get('is_primary', 'N/A'))
        col2.metric("primary_plot_id", p.get('primary_plot_id', 'N/A'))
        
        st.subheader("Full JSON:")
        st.json(p)

