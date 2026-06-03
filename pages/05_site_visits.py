import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# सुरक्षा: केवल एडमिन के लिए
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) से लॉगिन करें!")
    st.stop()

if st.session_state.get("role") != "admin":
    st.error("🔒 यह पेज केवल एडमिन के लिए है!")
    st.stop()

# डेटा स्टोरेज
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

st.title("🏗️ Site Visits Dashboard")
st.write("Logged in as: **ADMIN**")

with st.expander("➕ Add New Site Visit", expanded=True):
    with st.form("visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name *")
            contact_number = st.text_input("Contact Number *")
            project_name = st.selectbox("Project", ["First Choice City 2", "First Choice City 3", "Sai Samruddhi", "Other"])
        with col2:
            visit_date = st.date_input("Visit Date", datetime.today())
            executive_name = st.text_input("Executive Name *")
        
        remarks = st.text_area("Remarks")
        
        submitted = st.form_submit_button("Save Record")
        
        if submitted:
            if customer_name and contact_number and executive_name:
                st.session_state.site_visits.append({
                    "Date": visit_date.strftime("%d-%m-%Y"),
                    "Customer": customer_name,
                    "Contact": contact_number,
                    "Project": project_name,
                    "Executive": executive_name,
                    "Remarks": remarks
                })
                st.success("✅ Record Saved Successfully!")
            else:
                st.error("⚠️ Please fill all required fields (*)")

st.divider()
st.subheader("📋 Recent Site Visits")
if st.session_state.site_visits:
    st.dataframe(pd.DataFrame(st.session_state.site_visits), use_container_width=True)
else:
    st.info("No records found.")
