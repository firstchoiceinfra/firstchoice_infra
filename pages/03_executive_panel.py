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
st.markdown("<p style='text-align: center; font-size: 16px; color: #475569; margin-bottom: 30px;'>कंपनी एसोसिएट्स, सीनियर चैन एवं मास्टर ड्यूल कमीशन मैनेजमेंट</p>", unsafe_allow_html=True)

# --- SideBar: रिफ्रेश बटन ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("सिंक हो रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हुआ!")
        st.rerun()

# ====================================================================
# 🏢 ऐड मास्टर कमीशन फॉर्म (Add Global Commission Structure)
# ====================================================================
st.subheader("🏗️ नया कमीशन चैनल सेट करें (Set Master Commission Structure)")

with st.form("commission_form"):
    st.markdown("#### 👤 एसोसिएट्स का विवरण (Associates Details)")
    col_a1, col_a2 = st.columns(2)
    exec_name = col_a1.text_input("👨‍💼 एग्जीक्यूटिव का पूरा नाम (Executive Name) *")
    senior_name = col_a2.text_input("👨‍💼 सीनियर का नाम (Senior Name - यदि कोई हो)")

    # 🌟 प्रोजेक्ट चुनने का झंझट खत्म - यहाँ मास्टर ड्यूल रेट सेट होगा
    st.markdown("#### 💰 मास्टर कमीशन बजट निर्धारण (Global Dual Commission Engine)")
    st.info("💡 यहाँ आप इस एग्जीक्यूटिव का मास्टर रेट सेट कर रहे हैं। यह रेट प्रोजेक्ट के अनुसार (% या ₹) अपने आप काम करेगा।")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("<h5 style='color: #0d9488;'>📈 चैनल 1: प्रतिशत आधार नियम (% Master Rate)</h5>", unsafe_allow_html=True)
        exec_pct = st.number_input("एग्जीक्यूटिव कमीशन (%)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        senior_pct = st.number_input("सीनियर कमीशन (%)", min_value=0.0, max_value=100.0, step=0.1, key="sp")
        
    with col_c2:
        st.markdown("<h5 style='color: #b45309;'>💵 चैनल 2: नगद राशि आधार नियम (₹ Master Rate)</h5>", unsafe_allow_html=True)
        exec_rs = st.number_input("एग्जीक्यूटिव कमीशन (₹ Fixed)", min_value=0.0, step=500.0, key="er")
        senior_rs = st.number_input("सीनियर कमीशन (₹ Fixed)", min_value=0.0, step=500.0, key="sr")

    st.write("")
    save_comm = st.form_submit_button("💾 पूरा मास्टर कमीशन चैनल सुरक्षित करें (Save Commission Profile)", use_container_width=True)

    if save_comm:
        if exec_name.strip() == "":
            st.error("🚨 कृपया एग्जीक्यूटिव का नाम दर्ज करना अनिवार्य है!")
        else:
            exec_clean = exec_name.strip()
            
            # डेटाबेस में 'executives' नाम का मुख्य फोल्डर पक्का करें
            if 'executives' not in st.session_state.db_projects:
                st.session_state.db_projects['executives'] = {}
            
            # ग्लोबल लेवल पर ड्यूल स्ट्रक्चर सेव करें (बिना किसी प्रोजेक्ट के झंझट के)
            st.session_state.db_projects['executives'][exec_clean] = {
                "name": exec_clean,
                "senior_name": senior_name.strip() if senior_name.strip() else "Direct",
                "percentage_exec": exec_pct,
                "percentage_senior": senior_pct,
                "rupees_exec": exec_rs,
                "rupees_senior": senior_rs,
                "last_updated": str(datetime.date.today())
            }
            
            with st.spinner("क्लाउड में सुरक्षित हो रहा है..."):
                if database.save_db_data():
                    st.success(f"🎉 शानदार! {exec_clean} का ग्लोबल मास्टर कमीशन सुरक्षित हो गया और इंवेंट्री बुकिंग फॉर्म से सिंक हो चुका है!")
                    st.rerun()


# ====================================================================
# 📋 एडिट और मौजूदा एंट्रीज (Existing Partners Ledger)
# ====================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📋 मौजूदा कमीशन स्ट्रक्चर एवं मास्टर पार्टनर्स लिस्ट")

exec_data_root = db_data.get('executives', {})

# किसी भी कचरा/नॉन-डिक्शनरी डेटा को फिल्टर करके सिर्फ असली पार्टनर लिस्ट निकालना
exec_clean_list = {k: v for k, v in exec_data_root.items() if isinstance(v, dict) and 'name' in v}

if not exec_clean_list:
    st.caption("अभी तक कोई एग्जीक्यूटिव या मास्टर कमीशन स्ट्रक्चर सेट नहीं किया गया है।")
else:
    for ex_name, p_details in exec_clean_list.items():
        with st.container():
            # लग्जरी स्टेटमेंट बॉक्स डिज़ाइन
            st.markdown(f"""
            <div class="ledger-box">
                <span style="font-size: 18px; font-weight: bold; color: {p_color};">👨‍💼 पार्टनर: {ex_name}</span> 
                <span style="float: right; background-color: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size:12px;">📅 अपडेटेड: {p_details.get('last_updated','N/A')}</span>
                <br>👴 <b>सीनियर चैन हेड:</b> {p_details.get('senior_name','N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            # ड्यूल मैट्रिक्स व्यू (एक साथ दोनों रेट्स डिस्प्ले)
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric("Exec %", f"{p_details.get('percentage_exec', 0)} %")
            c_m2.metric("Senior %", f"{p_details.get('percentage_senior', 0)} %")
            c_m3.metric("Exec ₹ (Fixed)", f"₹ {p_details.get('rupees_exec', 0)}")
            c_m4.metric("Senior ₹ (Fixed)", f"₹ {p_details.get('rupees_senior', 0)}")
            
            # डिलीट बटन का ऑप्शन
            col_del, _ = st.columns([1, 5])
            if col_del.button("🗑️ पार्टनर हटाएं", key=f"del_{ex_name}"):
                st.session_state.db_projects['executives'].pop(ex_name, None)
                database.save_db_data()
                st.success("पार्टनर प्रोफाइल सफलतापूर्वक हटा दी गई!")
                st.rerun()
            st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)
