import streamlit as st
import database

# --- 1. पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - एडमिन पैनल")

# ==========================================
# 🎨 एडमिन पैनल का कस्टम UI (सुंदर डिज़ाइन)
# ==========================================
st.markdown("""
<style>
/* पीछे की बैकग्राउंड इमेज सेट करना */
.stApp {
    background-image: url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop");
    background-attachment: fixed;
    background-size: cover;
}

/* बीच वाले बॉक्स (फॉर्म) को पारदर्शी सफेद (Glass effect) बनाना */
.block-container {
    background-color: rgba(255, 255, 255, 0.92) !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    border-radius: 20px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}

/* मेन टाइटल का रंग */
h1 {
    color: #1e3a8a !important; /* डार्क ब्लू */
    font-weight: 800;
}

/* ग्रेडिएंट और 3D सेव बटन */
.stButton>button {
    background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
    color: white !important;
    border-radius: 8px;
    border: none;
    font-size: 18px;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    padding: 0.5rem 1rem;
}

/* बटन पर माउस ले जाने का इफ़ेक्ट */
.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    background: linear-gradient(90deg, #1e40af 0%, #2563eb 100%);
}

/* फॉर्म का बैकग्राउंड थोड़ा और हल्का सफेद करना */
[data-testid="stForm"] {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
}
</style>
""", unsafe_allow_html=True)
# ==========================================

# --- 2. सुरक्षा चेक ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 3. डेटाबेस लोड करना ---
database.init_db()

if 'db_projects' not in st.session_state:
    st.session_state.db_projects = {}

# --- मुख्य पेज UI ---
st.markdown("<h1 style='text-align: center;'>⚙️ FirstChoice Infra - Admin Panel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #64748b; margin-bottom: 30px;'>प्रोजेक्ट और कमीशन मैनेजमेंट सिस्टम</p>", unsafe_allow_html=True)

# -------------------------------------------------------------
# नया प्रोजेक्ट और कमीशन सेट करना
# -------------------------------------------------------------
st.markdown("<h3 style='color: #0f172a;'>🏢 नया प्रोजेक्ट सेट करें (Add New Project)</h3>", unsafe_allow_html=True)

with st.form("add_project_form"):
    proj_name = st.text_input("✨ प्रोजेक्ट का नाम (Project Name - e.g., First Choice City, Sai Samruddhi)")
   
    st.markdown("<h4 style='color: #047857; margin-top: 15px;'>📍 ज़मीन की जानकारी (Land Details)</h4>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("खसरा नं. (Khasra No.)")
    ph_no = c2.text_input("PH नं. (PH No.)")
    mauza = c3.text_input("मौजा (Mauza)")
   
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("तहसील (Tahsil)")
    dist = c5.text_input("जिला (District)")
    total_plots = c6.number_input("कुल प्लॉट्स की संख्या (Total Plots)", min_value=1, step=1)
   
    st.markdown("<h4 style='color: #b45309; margin-top: 20px;'>💰 कमीशन बजट (Commission Budget)</h4>", unsafe_allow_html=True)
    st.info("यहाँ कंपनी द्वारा तय किया गया 'Highest Commission' (सबसे बड़ा कमीशन बजट) डालें।")
   
    comm_type = st.radio("कमीशन का प्रकार (Commission Type)", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    max_comm = st.number_input(f"कुल अधिकतम कमीशन ({comm_type})", min_value=0.0)

    st.write("") # बटन के ऊपर थोड़ा स्पेस
    submit_proj = st.form_submit_button("💾 प्रोजेक्ट और इन्वेंट्री सुरक्षित करें (Save)", use_container_width=True)
   
    if submit_proj:
        if proj_name.strip() == "":
            st.error("🚨 कृपया प्रोजेक्ट का नाम ज़रूर लिखें!")
        else:
            # इन्वेंट्री के लिए अपने आप खाली प्लॉट्स तैयार करना
            plots_dict = {}
            for i in range(1, int(total_plots) + 1):
                plots_dict[str(i)] = {"status": "Available"}

            st.session_state.db_projects[proj_name] = {
                "khasra": khasra, 
                "ph_no": ph_no, 
                "mauza": mauza,
                "tahsil": tahsil, 
                "district": dist,
                "total_plots": total_plots,
                "comm_type": comm_type,
                "max_commission": max_comm,
                "plots": plots_dict # इन्वेंट्री को यही डेटा चाहिए
            }
           
            # सबसे ज़रूरी लाइन: प्रोजेक्ट डेटा को क्लाउड (Firebase) में लॉक करना
            with st.spinner("क्लाउड में सेव हो रहा है..."):
                if database.save_db_data():
                    st.success(f"🎉 शानदार! प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट हो गया है!")
                    st.rerun()

# -------------------------------------------------------------
# मौजूदा प्रोजेक्ट्स देखना
# -------------------------------------------------------------
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<h3 style='color: #0f172a;'>📋 मौजूदा प्रोजेक्ट्स (Existing Projects)</h3>", unsafe_allow_html=True)

if st.session_state.db_projects:
    # सिर्फ उन फाइलों को दिखाएं जो प्रोजेक्ट हैं (एग्जीक्यूटिव लिस्ट को छुपाएं)
    projects_only = {k: v for k, v in st.session_state.db_projects.items() if isinstance(v, dict) and 'plots' in v}
    
    if not projects_only:
        st.caption("कोई प्रोजेक्ट नहीं मिला।")
    else:
        for p_name, p_data in projects_only.items():
            with st.expander(f"📁 {p_name} - (कुल प्लॉट्स: {p_data.get('total_plots', 0)})"):
                st.write(f"**लोकेशन:** खसरा: {p_data.get('khasra', 'N/A')} | PH: {p_data.get('ph_no', 'N/A')} | मौजा: {p_data.get('mauza', 'N/A')} | तहसील: {p_data.get('tahsil', 'N/A')} | जिला: {p_data.get('district', 'N/A')}")
                
                if "Percentage" in p_data.get('comm_type', ''):
                    st.success(f"**कंपनी का कुल कमीशन बजट:** {p_data.get('max_commission', 0)}%")
                else:
                    st.success(f"**कंपनी का कुल कमीशन बजट:** ₹{p_data.get('max_commission', 0)}")
else:
    st.caption("अभी तक कोई प्रोजेक्ट नहीं जोड़ा गया है।")
