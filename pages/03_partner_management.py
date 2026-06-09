import streamlit as st
import database
import datetime

st.set_page_config(page_title="Partner Management", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'executive')

st.title("🏗️ Partner Management & Slab Registry")

# --- 1. ADMIN ONLY: ADD/EDIT PARTNER FORM ---
if user_role == 'admin':
    # यहाँ से वो एडमिन फॉर्म वाला कोड आएगा जो आपने पहले इस्तेमाल किया था
    with st.form("admin_partner_form"):
        st.subheader("Add/Update Partner")
        col1, col2 = st.columns(2)
        exec_name = col1.text_input("Partner Name")
        senior_name = col2.text_input("Senior Upline")
        col3, col4 = st.columns(2)
        exec_pct = col3.number_input("Percentage Slab (%)", 0.0, 100.0)
        exec_rs = col4.number_input("Fixed Payout (₹)", 0.0)
        
        if st.form_submit_button("💾 Save Partner Details"):
            db_data['executives'][exec_name] = {
                "name": exec_name, "senior_name": senior_name, 
                "percentage_exec": exec_pct, "rupees_exec": exec_rs
            }
            database.save_db_data()
            st.success("पार्टनर सेव हो गया!")
            st.rerun()

# --- 2. REGISTRY GRID WITH EDIT/DELETE BUTTONS ---
st.markdown("<hr><h4>📋 Master Slab Registry</h4>", unsafe_allow_html=True)

for ex_name, p_details in exec_data_root.items():
    if isinstance(p_details, dict):
        col_list = st.columns([3, 1, 1])
        col_list[0].markdown(f"**{ex_name}** | Senior: {p_details.get('senior_name')} | Slab: {p_details.get('percentage_exec')}%")
        
        # एडिट और डिलीट बटन
        if user_role == 'admin':
            if col_list[1].button("✏️ Edit", key=f"edit_{ex_name}"):
                # यहाँ वो फंक्शन कॉल करें जो फॉर्म में डेटा भरता है
                pass
            if col_list[2].button("🗑️ Delete", key=f"del_{ex_name}"):
                db_data['executives'].pop(ex_name)
                database.save_db_data()
                st.rerun()

