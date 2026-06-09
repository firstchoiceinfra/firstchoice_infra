import streamlit as st
import database

st.set_page_config(page_title="Partner Management", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'executive')

# प्रीमियम बैकग्राउंड स्टाइलिंग
st.markdown("""<style>
.stApp {background-image:url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop");background-attachment:fixed;background-size:cover;}
.block-container {background:rgba(255,255,255,0.92);padding:2rem;border-radius:20px;}
.partner-card {background:white;padding:15px;border-left:6px solid #b8860b;border-radius:10px;box-shadow:0px 4px 10px rgba(0,0,0,0.1);margin-bottom:12px;}
</style>""", unsafe_allow_html=True)

st.title("🏗️ Partner Management & Login Credentials")

# एडमिन फॉर्म
if user_role == 'admin':
    with st.form("partner_form"):
        col1, col2 = st.columns(2)
        exec_name = col1.text_input("Partner Full Name (Login ID)")
        exec_mobile = col2.text_input("Mobile Number (Password)", max_chars=10)
        col3, col4 = st.columns(2)
        senior_name = col3.text_input("Senior / Upline Name")
        exec_pct = col4.number_input("Commission (%)", 0.0, 100.0)
        exec_rs = col3.number_input("Fixed Payout (₹)", 0.0)
        if st.form_submit_button("💾 Save Partner"):
            if exec_name and exec_mobile:
                db_data['executives'][exec_name] = {"name": exec_name, "mobile": exec_mobile, "senior_name": senior_name or "Direct", "percentage_exec": exec_pct, "rupees_exec": exec_rs}
                database.save_db_data(); st.success("Saved!"); st.rerun()

# रजिस्ट्री लिस्ट
st.markdown("<hr><h4>📋 Master Slab Registry</h4>", unsafe_allow_html=True)
for ex_name, p_details in exec_data_root.items():
    if isinstance(p_details, dict):
        st.markdown(f'<div class="partner-card"><b>👤 {ex_name}</b> | 📱 Pass: {p_details.get("mobile")} | 👴 Senior: {p_details.get("senior_name")} | 📈 Slab: {p_details.get("percentage_exec")}%</div>', unsafe_allow_html=True)
