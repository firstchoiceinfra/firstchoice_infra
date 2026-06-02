import streamlit as st
import database
import datetime

# --- 1. पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - कमीशन चैनल")

# --- 2. सुरक्षा चेक ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 3. डेटाबेस शुरू और लोड करना ---
database.init_db()
db_data = st.session_state.db_projects

# ====================================================================
# 🎨 यूनिवर्सल लग्जरी थीम सिंक + CSS स्टाइलिंग
# ====================================================================
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255, 255, 255, 0.92)"

if '_app_settings' in db_data:
    global_settings = db_data['_app_settings']
    bg_url = global_settings.get('bg_url', bg_url)
    p_color = global_settings.get('primary_color', p_color)
    s_color = global_settings.get('secondary_color', s_color)
    c_bg = global_settings.get('card_bg', c_bg)

st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_url}");
    background-attachment: fixed;
    background-size: cover;
}}
.block-container {{
    background-color: {c_bg} !important;
    padding: 2rem 3rem !important;
    border-radius: 20px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}}
h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
    color: {p_color} !important;
    font-weight: 800;
}}
.stButton>button {{
    background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%);
    color: white !important;
    border-radius: 8px;
    font-weight: bold;
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}}
.ledger-box {{
    background-color: #ffffff;
    border-left: 5px solid {p_color};
    padding: 15px;
    border-radius: 8px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    margin-bottom: 15px;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>👑 Executive & Commission Channel Panel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 16px; color: #475569; margin-bottom: 30px;'>कंपनी एसोसिएट्स, सीनियर चैन एवं ड्यूल कमीशन मैनेजमेंट</p>", unsafe_allow_html=True)

# डेटाबेस से सिर्फ असली प्रोजेक्ट्स की लिस्ट अलग निकालें
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data or 'khasra' in data)]

if not project_names:
    st.warning("⚠️ कोई प्रोजेक्ट नहीं मिला। कृपया पहले 'Admin Panel' में जाकर प्रोजेक्ट जोड़ें।")
    st.stop()

# ====================================================================
# 🏢 ऐड कमीशन स्ट्रक्चर फॉर्म (Add Commission Structure)
# ====================================================================
st.subheader("🏗️ नया कमीशन चैनल सेट करें (Set Commission Structure)")

with st.form("commission_form"):
    col_f1, col_f2 = st.columns(2)
    selected_proj = col_f1.selectbox("🏢 प्रोजेक्ट चुनें (Select Project)", project_names)
    
    st.markdown("#### 👤 एसोसिएट्स का विवरण (Associates Details)")
    col_a1, col_a2 = st.columns(2)
    exec_name = col_a1.text_input("👨‍💼 एग्जीक्यूटिव का पूरा नाम (Executive Name) *")
    senior_name = col_a2.text_input("👨‍💼 सीनियर का नाम (Senior Name - यदि कोई हो)")

    st.markdown("#### 💰 कमीशन बजट निर्धारण (Dual Commission Engine)")
    st.info("💡 आप इस एग्जीक्यूटिव के लिए परसेंटेज (%) और रुपए (₹) दोनों कमीशन एक साथ भर सकते हैं।")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("<h5 style='color: #0d9488;'>📈 चैनल 1: प्रतिशत आधार (% Structure)</h5>", unsafe_allow_html=True)
        exec_pct = st.number_input("एग्जीक्यूटिव कमीशन (%)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        senior_pct = st.number_input("सीनियर कमीशन (%)", min_value=0.0, max_value=100.0, step=0.1, key="sp")
        
    with col_c2:
        st.markdown("<h5 style='color: #b45309;'>💵 चैनल 2: नगद राशि आधार (₹ Structure)</h5>", unsafe_allow_html=True)
        exec_rs = st.number_input("एग्जीक्यूटिव कमीशन (₹ Fixed)", min_value=0.0, step=500.0, key="er")
        senior_rs = st.number_input("सीनियर कमीशन (₹ Fixed)", min_value=0.0, step=500.0, key="sr")

    st.write("")
    save_comm = st.form_submit_button("💾 पूरा कमीशन चैनल सुरक्षित करें (Save Commission Channel)", use_container_width=True)

    if save_comm:
        if exec_name.strip() == "":
            st.error("🚨 कृपया एग्जीक्यूटिव का नाम दर्ज करना अनिवार्य है!")
        else:
            exec_clean = exec_name.strip()
            
            # डेटाबेस में 'executives' नाम का मुख्य फोल्डर पक्का करें
            if 'executives' not in st.session_state.db_projects:
                st.session_state.db_projects['executives'] = {}
                
            if exec_clean not in st.session_state.db_projects['executives']:
                st.session_state.db_projects['executives'][exec_clean] = {
                    "name": exec_clean,
                    "commissions": {}
                }
            
            # एक ही एंट्री में दोनों डेटा (% और ₹) एक साथ प्रोजेक्ट के अंदर मैप करें
            st.session_state.db_projects['executives'][exec_clean]['commissions'][selected_proj] = {
                "senior_name": senior_name.strip() if senior_name.strip() else "Direct",
                "percentage_exec": exec_pct,
                "percentage_senior": senior_pct,
                "rupees_exec": exec_rs,
                "rupees_senior": senior_rs,
                "last_updated": str(datetime.date.today())
            }
            
            with st.spinner("क्लाउड में सुरक्षित हो रहा है..."):
                if database.save_db_data():
                    st.success(f"🎉 शानदार! {exec_clean} का ड्यूल कमीशन स्ट्रक्चर सुरक्षित हो गया और इंवेंट्री बुकिंग फॉर्म से सिंक हो चुका है!")
                    st.rerun()


# ====================================================================
# 📋 एडिट और मौजूदा एंट्रीज (Edit/View Existing Entries)
# ====================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📋 मौजूदा कमीशन स्ट्रक्चर एवं पार्टनर्स लिस्ट")

exec_data_root = db_data.get('executives', {})

if not exec_data_root:
    st.caption("अभी तक कोई एग्जीक्यूटिव या कमीशन स्ट्रक्चर सेट नहीं किया गया है।")
else:
    for ex_name, ex_info in exec_data_root.items():
        if isinstance(ex_info, dict) and 'commissions' in ex_info:
            comms = ex_info['commissions']
            
            for p_title, p_details in comms.items():
                with st.container():
                    st.markdown(f"""
                    <div class="ledger-box">
                        <span style="font-size: 18px; font-weight: bold; color: {p_color};">👨‍💼 पार्टनर: {ex_name}</span> 
                        <span style="float: right; background-color: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size:12px;">📅 अपडेटेड: {p_details.get('last_updated','N/A')}</span>
                        <br>🏢 <b>प्रोजेक्ट:</b> {p_title} | 👴 <b>सीनियर चैन:</b> {p_details.get('senior_name','N/A')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_m1, c_m2, c_m3, c_m4 = st.columns(4)
                    c_m1.metric("Exec %", f"{p_details.get('percentage_exec', 0)} %")
                    c_m2.metric("Senior %", f"{p_details.get('percentage_senior', 0)} %")
                    c_m3.metric("Exec ₹ (Fixed)", f"₹ {p_details.get('rupees_exec', 0)}")
                    c_m4.metric("Senior ₹ (Fixed)", f"₹ {p_details.get('rupees_senior', 0)}")
                    
                    col_del, _ = st.columns([1, 5])
                    if col_del.button("🗑️ एंट्री हटाएं", key=f"del_{ex_name}_{p_title}"):
                        st.session_state.db_projects['executives'][ex_name]['commissions'].pop(p_title, None)
                        if not st.session_state.db_projects['executives'][ex_name]['commissions']:
                            st.session_state.db_projects['executives'].pop(ex_name, None)
                            
                        database.save_db_data()
                        st.success("एंट्री सफलतापूर्वक हटा दी गई!")
                        st.rerun()
                    st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
