import streamlit as st
import database

st.set_page_config(layout="wide", page_title="Partner Management")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'admin')

# प्रीमियम ग्लोबल थीम फंक्शन - Glassmorphism के साथ
def apply_premium_theme():
    settings = db_data.get('_app_settings', {})
    bg_url = settings.get('bg_url', "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop")
    p_color = settings.get('primary_color', "#1e3a8a")
    st.markdown(f"""
    <style>
    .stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
    .block-container {{ background: rgba(255, 255, 255, 0.7) !important; backdrop-filter: blur(10px); padding: 2.5rem !important; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
    .luxury-card {{ background: rgba(255, 255, 255, 0.8) !important; padding: 15px; border-left: 8px solid {p_color}; border-radius: 10px; margin-bottom: 12px; transition: 0.3s; }}
    h1, h3 {{ color: {p_color} !important; font-weight: 900 !important; }}
    </style>
    """, unsafe_allow_html=True)

apply_premium_theme()

st.title("👑 Executive Partner Portal")

if user_role == 'admin':
    with st.expander("➕ Register New Partner / Update Slab", expanded=False):
        with st.form("partner_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Partner Full Name (Login ID)")
            mob = c2.text_input("Mobile Number (Password)", max_chars=10)
            c3, c4 = st.columns(2)
            senior = c3.text_input("Senior / Upline Name")
            pct = c4.number_input("Commission (%)", 0.0, 100.0)
            rs = c3.number_input("Fixed Payout (₹)", 0.0)
            if st.form_submit_button("🚀 Deploy Associate"):
                db_data['executives'][name] = {"name": name, "mobile": mob, "senior_name": senior or "Direct", "percentage_exec": pct, "rupees_exec": rs}
                database.save_db_data(); st.rerun()

st.markdown("<hr><h3>📋 Master Slab Registry</h3>", unsafe_allow_html=True)
for ex_name, p in exec_data_root.items():
    if isinstance(p, dict):
        cols = st.columns([8, 1, 1])
        cols[0].markdown(f'<div class="luxury-card"><b>👤 {ex_name}</b> | 📱 {p.get("mobile")} | 📈 {p.get("percentage_exec")}% | 💵 ₹{p.get("rupees_exec", 0):,.0f}</div>', unsafe_allow_html=True)
        if cols[1].button("✏️", key=f"e_{ex_name}"): pass
        if cols[2].button("🗑️", key=f"d_{ex_name}"):
            db_data['executives'].pop(ex_name); database.save_db_data(); st.rerun()

