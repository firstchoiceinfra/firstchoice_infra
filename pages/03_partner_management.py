import streamlit as st
import database

st.set_page_config(layout="wide", page_title="FC Infra - Elite Partner Portal")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'admin')

# प्रीमियम ग्लोबल थीम फंक्शन
def apply_premium_theme():
    settings = db_data.get('_app_settings', {})
    bg_url = settings.get('bg_url', "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop")
    p_color = settings.get('primary_color', "#1e3a8a")
    st.markdown(f"""
    <style>
    .stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
    .block-container {{ background: rgba(255, 255, 255, 0.96) !important; padding: 2.5rem !important; border-radius: 30px; box-shadow: 0 20px 50px rgba(0,0,0,0.3); }}
    .luxury-row {{ 
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%); 
        padding: 20px; border-radius: 15px; border-left: 8px solid {p_color}; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.1); margin-bottom: 15px;
        transition: 0.3s;
    }}
    .luxury-row:hover {{ transform: scale(1.01); box-shadow: 0 8px 25px rgba(0,0,0,0.15); }}
    h1, h3 {{ color: {p_color} !important; font-weight: 900 !important; text-transform: uppercase; letter-spacing: 1px; }}
    </style>
    """, unsafe_allow_html=True)

apply_premium_theme()

st.title("👑 Executive Partner Portal")

# एडमिन फॉर्म (एकल सुव्यवस्थित एक्सपांडर में)
if user_role == 'admin':
    with st.expander("✨ Register New Associate", expanded=False):
        with st.form("partner_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Partner Full Name")
            mob = c2.text_input("Mobile (Pass)", max_chars=10)
            c3, c4 = st.columns(2)
            senior = c3.text_input("Senior Upline")
            pct = c4.number_input("Comm %", 0.0, 100.0)
            rs = c3.number_input("Fixed Payout ₹", 0.0)
            if st.form_submit_button("🚀 Deploy Associate"):
                db_data['executives'][name] = {"name": name, "mobile": mob, "senior_name": senior or "Direct", "percentage_exec": pct, "rupees_exec": rs}
                database.save_db_data(); st.rerun()

st.markdown("<hr><h3>📋 Master Slab Registry</h3>", unsafe_allow_html=True)
for ex_name, p in exec_data_root.items():
    if isinstance(p, dict):
        col1, col2, col3 = st.columns([8, 1, 1])
        col1.markdown(f'<div class="luxury-row"><b>👤 {ex_name}</b> | 📱 {p.get("mobile")} | 📈 {p.get("percentage_exec")}% | 💵 ₹{p.get("rupees_exec", 0):,.0f}</div>', unsafe_allow_html=True)
        if col2.button("✏️", key=f"e_{ex_name}"): pass
        if col3.button("🗑️", key=f"d_{ex_name}"):
            db_data['executives'].pop(ex_name); database.save_db_data(); st.rerun()

