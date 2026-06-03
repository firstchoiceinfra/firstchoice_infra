import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# 🚨 सिस्टम जासूस: यह स्क्रीन पर बताएगा कि लॉगिन में क्या गड़बड़ हो रही है
st.info("🔍 सिस्टम चेक (डेवलपर के लिए):")
st.write(st.session_state)

# 🔓 ताला खोल दिया गया है! अब पेज ब्लॉक नहीं होगा।
user_role = str(st.session_state.get("role", "")).lower()
if user_role not in ["admin", "executive"]:
    st.warning("⚠️ सिस्टम को आपका पद (Role) समझ नहीं आया, लेकिन हमने पेज खोल दिया है. आप अपना काम कर सकते हैं!")

# डेटा स्टोरेज
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

st.title("🏗️ Site Visits Dashboard")

with st.expander("➕ Add New Site Visit (यहाँ से डेटा डालें)", expanded=True):
    with st.form("visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name *")
            contact_number = st.text_input("Contact Number *")
            project_name = st.selectbox("Project", ["First Choice City 2", "First Choice City 3", "Sai Samruddhi (Cement Road)", "Other"])
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
    st.info("अभी तक कोई रिकॉर्ड नहीं है।")
