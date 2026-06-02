import streamlit as st
import database
import datetime
import base64

# --- 1. पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - एडमिन पैनल")

# --- 2. सुरक्षा लॉक (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 सुरक्षा अलर्ट: आपको इस एडमिन पैनल को देखने की अनुमति नहीं है!")
    st.stop()

# --- 3. डेटाबेस शुरू और लोड करना ---
database.init_db()
db_data = st.session_state.db_projects

# डिफ़ॉल्ट थीम सेटिंग्स
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

# --- CSS स्टाइलिंग ---
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

# --- थीम मैनेजर ---
with st.expander("🎨 ऐप का रंग-रूप और बैकग्राउंड फोटो बदलें", expanded=False):
    uploaded_file = st.file_uploader("📁 डेस्कटॉप या मोबाइल से बैकग्राउंड फोटो चुनें", type=["jpg", "jpeg", "png"])
    col_t1, col_t2 = st.columns(2)
    new_primary = col_t1.color_picker("🎨 मुख्य हेडिंग और बटन का रंग", value=p_color)
    new_secondary = col_t2.color_picker("✨ सहायक ग्रेडिएंट रंग", value=s_color)
    new_transparency = st.select_slider("⬜ डेटा बॉक्स का गाढ़ापन", options=["rgba(255, 255, 255, 0.7)", "rgba(255, 255, 255, 0.85)", "rgba(255, 255, 255, 0.92)", "rgba(255, 255, 255, 1.0)"], value=c_bg)
    
    if st.button("💾 नया लुक लागू करें"):
        if uploaded_file is not None:
            encoded_img = base64.b64encode(uploaded_file.read()).decode("utf-8")
            bg_data_url = f"data:{uploaded_file.type};base64,{encoded_img}"
        else:
            bg_data_url = bg_url
            
        st.session_state.db_projects['_app_settings'] = {"bg_url": bg_data_url, "primary_color": new_primary, "secondary_color": new_secondary, "card_bg": new_transparency}
        if database.save_db_data():
            st.success("🎉 नया लुक पूरे ऐप पर लागू हो गया!")
            st.rerun()

# --- प्रोजेक्ट फॉर्म ---
st.markdown("### 🏢 नया प्रोजेक्ट सेट करें (Add New Project)")
with st.form("add_project_form"):
    proj_name = st.text_input("✨ प्रोजेक्ट का नाम (Project Name)")
    st.markdown("#### 📍 ज़मीन की जानकारी")
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("खसरा नं.")
    ph_no = c2.text_input("PH नं.")
    mauza = c3.text_input("मौजा")
   
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("तहसील")
    dist = c5.text_input("जिला")
    total_plots = c6.number_input("कुल प्लॉट्स की संख्या", min_value=1, step=1)
   
    st.markdown("#### 💰 कमीशन बजट निर्धारण")
    comm_type = st.radio("इस प्रोजेक्ट में कमीशन का प्रकार", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    max_comm = st.number_input(f"कुल अधिकतम कमीशन बजट ({comm_type})", min_value=0.0)

    if st.form_submit_button("💾 प्रोजेक्ट और इन्वेंट्री सुरक्षित करें", use_container_width=True):
        if proj_name.strip() == "":
            st.error("🚨 कृपया प्रोजेक्ट का नाम ज़रूर लिखें!")
        else:
            plots_dict = {str(i): {"status": "Available"} for i in range(1, int(total_plots) + 1)}
            st.session_state.db_projects[proj_name] = {
                "khasra": khasra, "ph_no": ph_no, "mauza": mauza, "tahsil": tahsil, "district": dist,
                "total_plots": total_plots, "comm_type": comm_type, "max_commission": max_comm, "plots": plots_dict 
            }
            if database.save_db_data():
                st.success(f"🎉 प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट हो गया!")
                st.rerun()

# --- प्रोजेक्ट लिस्ट ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📋 मौजूदा प्रोजेक्ट्स की सूची")
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if not project_names:
    st.caption("अभी कोई प्रोजेक्ट उपलब्ध नहीं है।")
else:
    for p_name in project_names:
        p_data = db_data[p_name]
        with st.expander(f"📁 {p_name} - (कुल प्लॉट्स: {p_data.get('total_plots', 0)})"):
            st.write(f"**लोकेशन:** खसरा: {p_data.get('khasra')} | मौजा: {p_data.get('mauza')} | जिला: {p_data.get('district')}")
            st.success(f"**कमीशन नियम:** {p_data.get('max_commission', 0)} ({p_data.get('comm_type')})")
