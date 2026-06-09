import streamlit as st
import database

st.set_page_config(layout="wide", page_title="FC Infra - Partner Management")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
user_role = st.session_state.get('user_role', 'admin') # यहाँ एडमिन एक्सेस चेक करें

# प्रीमियम लग्जरी CSS
st.markdown("""
<style>
.stApp {background-image: url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"); background-attachment: fixed; background-size: cover;}
.block-container {background: rgba(255, 255, 255, 0.95); padding: 2.5rem; border-radius: 25px; box-shadow: 0 15px 35px rgba(0,0,0,0.3);}
.luxury-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    padding: 20px; border-radius: 15px;
    border-left: 8px solid #b8860b;
    box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    margin-bottom: 15px; transition: 0.3s;
}
.luxury-card:hover {transform: translateY(-5px); box-shadow: 0 12px 25px rgba(0,0,0,0.2);}
h1, h2 {color: #1e3a8a !important; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);}
</style>
""", unsafe_allow_html=True)

st.title("👑 Partner Management & Master Slab Registry")

# --- 1. ADMIN FORM ---
if user_role == 'admin':
    with st.expander("➕ Register New Partner / Update Slab", expanded=False):
        with st.form("partner_form"):
            c1, c2 = st.columns(2)
            exec_name = c1.text_input("Partner Name")
            exec_mobile = c2.text_input("Mobile (Pass)", max_chars=10)
            c3, c4 = st.columns(2)
            senior = c3.text_input("Senior / Upline")
            pct = c4.number_input("Comm. Percentage (%)", 0.0, 100.0)
            rs = c3.number_input("Fixed Payout (₹)", 0.0)
            if st.form_submit_button("💾 Save Partner Registry"):
                db_data['executives'][exec_name] = {"name": exec_name, "mobile": exec_mobile, "senior_name": senior or "Direct", "percentage_exec": pct, "rupees_exec": rs}
                database.save_db_data(); st.rerun()

# --- 2. LUXURY REGISTRY LIST ---
st.markdown("<hr><h3>📋 Master Slab Registry</h3>", unsafe_allow_html=True)

for ex_name, p in exec_data_root.items():
    if isinstance(p, dict):
        card = st.container()
        with card:
            st.markdown(f"""
            <div class="luxury-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <b style="font-size:20px; color:#1e3a8a;">👤 {ex_name}</b><br>
                        <small>📱 Password: {p.get("mobile")} | 👴 Senior: {p.get("senior_name")}</small>
                    </div>
                    <div style="text-align:right;">
                        <b style="color:#b8860b; font-size:18px;">📈 {p.get("percentage_exec")}% | 💵 ₹{p.get("rupees_exec", 0):,.0f}</b>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # एडिट और डिलीट बटन्स
            c1, c2 = st.columns([10, 1])
            if c1.button("✏️ Edit Slab", key=f"edit_{ex_name}"): pass # अपना एडिट लॉजिक
            if c2.button("🗑️", key=f"del_{ex_name}"):
                db_data['executives'].pop(ex_name)
                database.save_db_data(); st.rerun()

