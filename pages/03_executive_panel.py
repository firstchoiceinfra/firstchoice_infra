import streamlit as st
import database
import datetime
import base64

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Admin Panel")

# --- 2. Security Check (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 Security Alert: You do not have permission to access the Admin Panel!")
    st.stop()

# --- 3. Database Initialization ---
database.init_db()
db_data = st.session_state.db_projects

# Set default theme settings if not present
if '_app_settings' not in st.session_state.db_projects:
    st.session_state.db_projects['_app_settings'] = {
        "bg_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop",
        "primary_color": "#1e3a8a",
        "secondary_color": "#3b82f6",
        "card_bg": "rgba(255, 255, 255, 0.92)"
    }

settings = st.session_state.db_projects['_app_settings']
bg_url = settings.get('bg_url', '')
p_color = settings.get('primary_color', '#1e3a8a')
s_color = settings.get('secondary_color', '#3b82f6')
c_bg = settings.get('card_bg', 'rgba(255, 255, 255, 0.92)')

# --- CSS Styling (Global Theme Integration) ---
st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: {c_bg} !important; padding: 1.5rem 2.5rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 1.5rem; margin-bottom: 1.5rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 8px; font-weight: bold; }}
div[data-testid="stForm"] {{ background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>⚙️ FirstChoice Infra - Admin Panel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 25px;'>Project Customization, Infrastructure Budget & Branding Control Center</p>", unsafe_allow_html=True)

# --- Theme Configuration Manager ---
with st.expander("🎨 Change App Appearance & Background Photo (Theme Settings)", expanded=False):
    uploaded_file = st.file_uploader("📁 Choose background photo from desktop or mobile", type=["jpg", "jpeg", "png"])
    col_t1, col_t2 = st.columns(2)
    new_primary = col_t1.color_picker("🎨 Primary Headings & Buttons Color", value=p_color)
    new_secondary = col_t2.color_picker("✨ Secondary Gradient Accent Color", value=s_color)
    new_transparency = st.select_slider("⬜ Card Box Opacity / Transparency", options=["rgba(255, 255, 255, 0.7)", "rgba(255, 255, 255, 0.85)", "rgba(255, 255, 255, 0.92)", "rgba(255, 255, 255, 1.0)"], value=c_bg)
    
    if st.button("💾 Apply New Theme Layout"):
        if uploaded_file is not None:
            encoded_img = base64.b64encode(uploaded_file.read()).decode("utf-8")
            bg_data_url = f"data:{uploaded_file.type};base64,{encoded_img}"
        else:
            bg_data_url = bg_url
            
        st.session_state.db_projects['_app_settings'] = {"bg_url": bg_data_url, "primary_color": new_primary, "secondary_color": new_secondary, "card_bg": new_transparency}
        if database.save_db_data():
            st.success("🎉 New theme layout successfully applied across the app!")
            st.rerun()

# --- Project Configuration Form ---
st.markdown("### 🏢 Add New Project Setup")
with st.form("add_project_form"):
    proj_name = st.text_input("✨ Project Name (e.g., First Choice City 2, Sai Samruddhi)")
    st.markdown("#### 📍 Land & Layout Specifications")
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("Khasra No.")
    ph_no = c2.text_input("PH No.")
    mauza = c3.text_input("Mauza / Location")
   
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("Tahsil")
    dist = c5.text_input("District")
    total_plots = c6.number_input("Total Number of Plots", min_value=1, step=1)
   
    st.markdown("#### 💰 Project Commission Rules Setup")
    comm_type = st.radio("Commission Type Rule for This Project", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    max_comm = st.number_input(f"Maximum Allocated Project Commission Budget ({comm_type})", min_value=0.0)

    if st.form_submit_button("💾 Save Project & Initialize Inventory", use_container_width=True):
        if proj_name.strip() == "":
            st.error("🚨 Project Name is required!")
        else:
            plots_dict = {str(i): {"status": "Available"} for i in range(1, int(total_plots) + 1)}
            st.session_state.db_projects[proj_name] = {
                "khasra": khasra, "ph_no": ph_no, "mauza": mauza, "tahsil": tahsil, "district": dist,
                "total_plots": total_plots, "comm_type": comm_type, "max_commission": max_comm, "plots": plots_dict 
            }
            if database.save_db_data():
                st.success(f"🎉 Project '{proj_name}' successfully created with plot matrix!")
                st.rerun()

# --- Active Project List ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📋 Existing Active Projects Registry")
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if not project_names:
    st.caption("No projects found in cloud registry.")
else:
    for p_name in project_names:
        p_data = db_data[p_name]
        with st.expander(f"📁 {p_name} - (Total Plots: {p_data.get('total_plots', 0)})"):
            st.write(f"**Location Details:** Khasra: {p_data.get('khasra')} | Mauza: {p_data.get('mauza')} | District: {p_data.get('district')}")
            st.success(f"**Budget Rule:** {p_data.get('max_commission', 0)} ({p_data.get('comm_type')}) Allocated")

