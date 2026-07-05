import streamlit as st
import database

st.set_page_config(layout="wide", page_title="FC Infra - Partner Portal")

# ---------------------------------------------------------------
# SECURITY — ADMIN ONLY
# ---------------------------------------------------------------
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

if st.session_state.get('user_role', 'executive') != 'admin':
    st.error("🚨 Access Denied! Yeh page sirf Admin ke liye hai.")
    st.info("💡 Partner details dekhne ke liye Admin se contact karo.")
    st.stop()

# ---------------------------------------------------------------
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'admin')

def apply_theme():
    settings = db_data.get('_app_settings', {})
    bg_url = settings.get('bg_url', "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop")
    p_color = settings.get('primary_color', "#1e3a8a")
    st.markdown(f"""<style>
    .stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
    .block-container {{ background: rgba(255, 255, 255, 0.7) !important; backdrop-filter: blur(15px);
        padding: 2.5rem !important; border-radius: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
    .luxury-card {{ background: rgba(255, 255, 255, 0.85); padding: 18px; border-radius: 15px;
        border-left: 10px solid {p_color}; box-shadow: 0 6px 15px rgba(0,0,0,0.15);
        margin-bottom: 15px; display: flex; align-items: center; justify-content: space-between; }}
    h1, h3 {{ color: {p_color} !important; font-weight: 900 !important; }}
    .stButton>button {{ background: linear-gradient(90deg, {p_color}, #3b82f6) !important;
        color: white !important; border-radius: 8px; font-weight: 700; }}
    </style>""", unsafe_allow_html=True)

apply_theme()

st.title("👑 Executive Partner Portal")

with st.expander("➕ Register New Partner / Update Slab", expanded=False):
    with st.form("partner_form"):
        c1, c2 = st.columns(2)
        name = c1.text_input("Partner Name")
        mob = c2.text_input("Mobile (Pass)", max_chars=10)
        c3, c4 = st.columns(2)
        senior = c3.text_input("Senior Upline")
        pct = c4.number_input("Comm %", 0.0, 100.0)
        rs = c3.number_input("Fixed Payout ₹", 0.0)
        if st.form_submit_button("🚀 Deploy Associate"):
            if name.strip() == "":
                st.error("Partner name required!")
            else:
                db_data['executives'][name] = {
                    "name": name, "mobile": mob,
                    "senior_name": senior or "company",
                    "percentage_exec": pct,
                    "rupees_exec": rs
                }
                database.save_db_data()
                st.success(f"✅ {name} successfully added!")
                st.rerun()

st.markdown("<hr><h3>📋 Master Slab Registry</h3>", unsafe_allow_html=True)

settings = db_data.get('_app_settings', {})
p_color = settings.get('primary_color', "#1e3a8a")

for ex_name, p in exec_data_root.items():
    if isinstance(p, dict):
        col1, col2, col3 = st.columns([8, 1, 1])
        col1.markdown(f'''<div class="luxury-card">
            <div><b style="font-size:18px; color:{p_color};">👤 {ex_name}</b>
            <br><small>📱 {p.get("mobile","N/A")} | 👴 {p.get("senior_name","N/A")}</small></div>
            <div style="display:flex; gap:10px;">
                <span style="background:#e0f2fe;color:#0369a1;padding:5px 10px;border-radius:8px;font-weight:bold;">
                    📈 {p.get("percentage_exec", 0)}%</span>
                <span style="background:#fef3c7;color:#b45309;padding:5px 10px;border-radius:8px;font-weight:bold;">
                    💵 ₹{p.get("rupees_exec", 0):,.0f}</span>
            </div>
        </div>''', unsafe_allow_html=True)

        if col3.button("🗑️", key=f"d_{ex_name}"):
            db_data['executives'].pop(ex_name)
            database.save_db_data()
            st.rerun()

