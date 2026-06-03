import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# 2. Security Lock: Allow Admin AND Executive
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) से लॉगिन करें!")
    st.stop()

if st.session_state.get("role") not in ["admin", "executive"]:
    st.error("🚫 यह पेज केवल एडमिन और एग्जीक्यूटिव के लिए है!")
    st.stop()

# 3. Data Storage (Session State)
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

st.title("🏗️ Site Visits Dashboard")
st.write(f"Logged in as: **{st.session_state.get('role').upper()}**")

# 4. Form for Executives to add field data
with st.expander("➕ Add New Site Visit (फील्ड से डेटा यहाँ डालें)", expanded=True):
    with st.form("visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name (ग्राहक का नाम) *")
            contact_number = st.text_input("Contact Number (मोबाइल नंबर) *")
            project_name = st.selectbox("Project Visited (प्रोजेक्ट) *", [
                "First Choice City 2 (Mohadi)", 
                "First Choice City 3 (Pachgaon)", 
                "Sai Samruddhi (Temsana - Cement Road)", 
                "Other"
            ])
            
        with col2:
            visit_date = st.date_input("Visit Date (विजिट की तारीख)", datetime.today())
            executive_name = st.text_input("Executive Name (एग्जीक्यूटिव का नाम) *")
            
        uploaded_photo = st.file_uploader("Upload Site Photo 📷 (साइट की लाइव फोटो)", type=['jpg', 'jpeg', 'png'])
        remarks = st.text_area("Remarks / Customer Feedback (कोई खास बात या फीडबैक)")
        
        submitted = st.form_submit_button("Save Site Visit Data")
        
        if submitted:
            if customer_name and contact_number and executive_name:
                # Save the new entry
                new_visit = {
                    "Date": visit_date.strftime("%d-%m-%Y"),
                    "Customer": customer_name,
                    "Contact": contact_number,
                    "Project": project_name,
                    "Executive": executive_name,
                    "Remarks": remarks,
                    "Photo": "Uploaded ✅" if uploaded_photo else "No Photo ❌"
                }
                st.session_state.site_visits.append(new_visit)
                st.success("✅ साइट विजिट का डेटा सफलतापूर्वक सेव हो गया है!")
            else:
                st.error("⚠️ कृपया स्टार (*) वाले सभी जरूरी बॉक्स भरें।")

st.divider()

# 5. Dashboard for Admin to view all visits real-time
st.subheader("📋 Recent Site Visits Records")

if st.session_state.site_visits:
    # Convert data to a beautiful table
    df = pd.DataFrame(st.session_state.site_visits)
    st.dataframe(df, use_container_width=True)
else:
    st.info("अभी तक कोई साइट विजिट रिकॉर्ड नहीं की गई है। एग्जीक्यूटिव द्वारा डेटा डालते ही वह यहाँ दिखेगा।")
