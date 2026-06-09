import streamlit as st
import database

st.set_page_config(page_title="Partner Management", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'executive')

st.markdown("""<style>.partner-card {background:white; padding:15px; border-left:6px solid #1e3a8a; border-radius:10px; box-shadow:0px 4px 10px rgba(0,0,0,0.1); margin-bottom:12px;}</style>""", unsafe_allow_html=True)

st.title("🏗️ Partner Management & Login Credentials")

if user_role == 'admin':
    with st.form("partner_form"):
        c1, c2 = st.columns(2)
        exec_name = c1.text_input("Partner Full Name (Login ID)")
        exec_mobile = c2.text_input("Mobile Number (Password)", max_chars=10)
        c3, c4 = st.columns(2)
        senior_name = c3.text_input("Senior / Upline Name")
        exec_pct = c4.number_input("Commission (%)", 0.0, 100.0)
        exec_rs = c3.number_input("Fixed Payout (₹)", 0.0)
        if st.form_submit_button("💾 Save Partner"):
            if exec_name and exec_mobile:
                db_data['executives'][exec_name] = {"name": exec_name, "mobile": exec_mobile, "senior_name": senior_name or "Direct", "percentage_exec": exec_pct, "rupees_exec": exec_rs}
                database.save_db_data(); st.rerun()

st.markdown("<hr><h4>📋 Master Slab Registry</h4>", unsafe_allow_html=True)
for ex_name, p in exec_data_root.items():
    if isinstance(p, dict):
        st.markdown(f'<div class="partner-card"><b>👤 {ex_name}</b> | 📱 Pass: {p.get("mobile")} | 👴 Senior: {p.get("senior_name")} | 📈 Slab: {p.get("percentage_exec")}%</div>', unsafe_allow_html=True)
