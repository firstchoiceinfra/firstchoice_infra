import streamlit as st
import database
import base64

# --- 1. सबसे पहली कमांड: पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - एडमिन पैनल")

# --- 2. सुरक्षा चेक ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 3. डेटाबेस शुरू और लोड करना ---
database.init_db()

# यदि डेटाबेस में कोई थीम सेटिंग्स नहीं है, तो डिफ़ॉल्ट सेट करें
if '_app_settings' not in st.session_state.db_projects:
    st.session_state.db_projects['_app_settings'] = {
        "bg_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop",
        "primary_color": "#1e3a8a",
        "secondary_color": "#3b82f6",
        "card_bg": "rgba(255, 255, 255, 0.92)"
    }

# क्लाउड से थीम की सेटिंग्स निकालना
settings = st.session_state.db_projects['_app_settings']

# ====================================================================
# 🎨 डायनामिक कस्टम UI (जो सभी पेजों में हेडिंग और बैकग्राउंड बदलेगा)
# ====================================================================
st.markdown(f"""
<style>
/* पीछे की बैकग्राउंड इमेज - डायनामिक */
.stApp {{
    background-image: url("{settings.get('bg_url')}");
    background-attachment: fixed;
    background-size: cover;
}}

/* बीच वाले बॉक्स (फॉर्म) का ग्लास इफेक्ट */
.block-container {{
    background-color: {settings.get('card_bg')} !important;
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    border-radius: 20px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}}

/* सभी हेडिंग्स और मार्कडाउन टाइटल्स का रंग एक साथ बदलना */
h1, h2, h3, h4, h5, h6, 
[data-testid="stMarkdownContainer"] h1, 
[data-testid="stMarkdownContainer"] h2, 
[data-testid="stMarkdownContainer"] h3 {{
    color: {settings.get('primary_color')} !important;
    font-weight: 800;
}}

/* ग्रेडिएंट और 3D सेव बटन */
.stButton>button {{
    background: linear-gradient(90deg, {settings.get('primary_color')} 0%, {settings.get('secondary_color')} 100%);
    color: white !important;
    border-radius: 8px;
    border: none;
    font-size: 18px;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
    padding: 0.5rem 1rem;
}}

.stButton>button:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 15px rgba(0,0,0,0.3);
    background: linear-gradient(90deg, {settings.get('secondary_color')} 0%, {settings.get('primary_color')} 100%);
}}

[data-testid="stForm"] {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 20px;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

# --- मुख्य पेज टाइटल्स ---
st.markdown("<h1 style='text-align: center;'>⚙️ FirstChoice Infra - Admin Panel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: #475569; margin-bottom: 30px;'>प्रोजेक्ट, कमीशन और यूनिवर्सल थीम सिस्टम</p>", unsafe_allow_html=True)

# ====================================================================
# 🛠️ कंट्रोल पैनल: डायरेक्ट फोटो अपलोड और कलर कस्टमाइज़ेशन
# ====================================================================
with st.expander("🎨 ऐप का रंग-रूप और गैलरी से फोटो बदलें (Theme Settings)", expanded=False):
    st.markdown("#### यहाँ से फोटो अपलोड करें और रंग बदलें:")
    
    # 🌟 पुराना यूआरएल बॉक्स हटाकर डायरेक्ट फाइल अपलोडर लगाया
    uploaded_file = st.file_uploader("📁 अपने डेस्कटॉप या मोबाइल से बैकग्राउंड फोटो चुनें (Upload Photo)", type=["jpg", "jpeg", "png"])
    
    col_t1, col_t2 = st.columns(2)
    new_primary = col_t1.color_picker("🎨 मुख्य हेडिंग और बटन का रंग", value=settings.get('primary_color'))
    new_secondary = col_t2.color_picker("✨ सहायक ग्रेडिएंट रंग (Gradient Accent)", value=settings.get('secondary_color'))
    
    new_transparency = st.select_slider(
        "⬜ डेटा बॉक्स का गाढ़ापन (Transparency)",
        options=["rgba(255, 255, 255, 0.7)", "rgba(255, 255, 255, 0.85)", "rgba(255, 255, 255, 0.92)", "rgba(255, 255, 255, 1.0)"],
        value=settings.get('card_bg', 'rgba(255, 255, 255, 0.92)')
    )
    
    if st.button("💾 नया लुक पूरे ऐप पर लागू करें (Save Theme Layout)"):
        # अगर नयी फोटो चुनी है तो उसे सेव करें, नहीं तो पुरानी रहने दें
        if uploaded_file is not None:
            file_bytes = uploaded_file.read()
            encoded_img = base64.b64encode(file_bytes).decode("utf-8")
            bg_data_url = f"data:{uploaded_file.type};base64,{encoded_img}"
        else:
            bg_data_url = settings.get('bg_url')
            
        st.session_state.db_projects['_app_settings'] = {
            "bg_url": bg_data_url,
            "primary_color": new_primary,
            "secondary_color": new_secondary,
            "card_bg": new_transparency
        }
        with st.spinner("नयी थीम क्लाउड में लॉक हो रही है..."):
            if database.save_db_data():
                st.success("🎉 नया लुक सफलतापूर्वक पूरे ऐप के सभी पेजों पर लागू हो गया!")
                st.rerun()

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# नया प्रोजेक्ट और कमीशन सेट करना (यथावत पुराना लॉजिक)
# -------------------------------------------------------------
st.markdown("### 🏢 नया प्रोजेक्ट सेट करें (Add New Project)")

with st.form("add_project_form"):
    proj_name = st.text_input("✨ प्रोजेक्ट का नाम (Project Name)")
   
    st.markdown("#### 📍 ज़मीन की जानकारी (Land Details)")
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("खसरा नं. (Khasra No.)")
    ph_no = c2.text_input("PH नं. (PH No.)")
    mauza = c3.text_input("मौजा (Mauza)")
   
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("तहसील (Tahsil)")
    dist = c5.text_input("जिला (District)")
    total_plots = c6.number_input("कुल प्लॉट्स की संख्या (Total Plots)", min_value=1, step=1)
   
    st.markdown("#### 💰 कमीशन बजट (Commission Budget)")
    st.info("यहाँ कंपनी द्वारा तय किया गया 'Highest Commission' डालें।")
   
    comm_type = st.radio("कमीशन का प्रकार", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
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
                    st.success(f"**company का कुल कमीशन बजट:** ₹{p_data.get('max_commission', 0)}")
else:
    st.caption("अभी तक कोई प्रोजेक्ट नहीं जोड़ा गया है।")
