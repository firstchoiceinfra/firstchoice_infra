import streamlit as st
import database

st.set_page_config(page_title="Partner Management", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'executive')

st.title("🏗️ Partner Management & Login Credentials")

# --- 1. ADMIN ONLY: PARTNER SETUP & CREDENTIALS ---
if user_role == 'admin':
    with st.form("partner_form"):
        st.subheader("Add/Update Partner")
        col1, col2 = st.columns(2)
        exec_name = col1.text_input("Partner Full Name (Login ID)")
        exec_mobile = col2.text_input("Mobile Number (Used as Password)", max_chars=10)
        
        col3, col4 = st.columns(2)
        senior_name = col3.text_input("Senior / Upline Name")
        exec_pct = col4.number_input("Commission Percentage (%)", 0.0, 100.0)
        exec_rs = col3.number_input("Fixed Payout (₹)", 0.0)

        if st.form_submit_button("💾 Save Partner"):
            if exec_name and exec_mobile:
                db_data['executives'][exec_name] = {
                    "name": exec_name, "mobile": exec_mobile,
                    "senior_name": senior_name if senior_name else "Direct",
                    "percentage_exec": exec_pct, "rupees_exec": exec_rs
                }
                database.save_db_data()
                st.success(f"पार्टनर '{exec_name}' सुरक्षित हो गया!")
                st.rerun()
            else:
                st.error("नाम और मोबाइल नंबर अनिवार्य हैं!")

# --- 2. MASTER SLAB REGISTRY (WITH EDIT/DELETE) ---
st.markdown("<hr><h4>📋 Master Slab Registry & Credentials</h4>", unsafe_allow_html=True)

for ex_name, p_details in exec_data_root.items():
    if isinstance(p_details, dict):
        # यहाँ हमने मोबाइल नंबर भी शो किया है ताकि एडमिन देख सके
        c1, c2, c3 = st.columns([4, 1, 1])
        c1.markdown(f"""
        <div class="ledger-box">
            <b>👤 Name:</b> {ex_name} | <b>📱 Pass (Mobile):</b> {p_details.get('mobile', 'N/A')}
            <br><b>👴 Senior:</b> {p_details.get('senior_name')} | <b>📈 Slab:</b> {p_details.get('percentage_exec')}% (₹{p_details.get('rupees_exec')})
        </div>
        """, unsafe_allow_html=True)
        
        if user_role == 'admin':
            if c2.button("✏️ Edit", key=f"edit_{ex_name}"):
                # यहाँ आप अपनी पहले वाली prepare_edit लॉजिक कॉल कर सकते हैं
                st.info(f"Edit feature for {ex_name} active.")
            if c3.button("🗑️ Delete", key=f"del_{ex_name}"):
                db_data['executives'].pop(ex_name)
                database.save_db_data()
                st.rerun()
