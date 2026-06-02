import streamlit as st
import database
import datetime
import pandas as pd

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
# 🎨 यूनिवर्सल लग्जरी थीम सिंक + कॉम्पैक्ट CSS स्टाइलिंग (Font Size Fix)
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

/* 🌟 बड़े अक्षरों को छोटा और सुंदर बनाने के लिए विशेष CSS नियम 🌟 */
.ledger-box {{
    background-color: #ffffff;
    border-left: 5px solid {p_color};
    padding: 10px 15px !important;
    border-radius: 8px;
    box-shadow: 0px 2px 5px rgba(0,0,0,0.05);
    margin-bottom: 5px !important;
}}

/* स्ट्रीमलिट के बड़े-बड़े मैट्रिक्स (Metrics) का आकार छोटा करना */
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #475569 !important;
}}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
    font-size: 18px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>👑 Executive & Commission Channel Panel</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 15px; color: #475569; margin-bottom: 30px;'>कंपनी एसोसिएट्स, मोबाइल लॉगिन, मास्टर ड्यूल कमीशन एवं लाइव स्टेटमेंट इंजन</p>", unsafe_allow_html=True)

# --- SideBar: रिफ्रेश बटन ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("सिंक हो रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हुआ!")
        st.rerun()

# डेटाबेस से सिर्फ असली प्रोजेक्ट्स की लिस्ट अलग निकालें
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data or 'khasra' in data)]

# ====================================================================
# 🏢 ऐड मास्टर कमीशन फॉर्म (Add Global Commission Structure)
# ====================================================================
st.subheader("🏗️ नया पार्टनर एवं कमीशन चैनल सेट करें")

with st.form("commission_form"):
    st.markdown("#### 👤 एसोसिएट्स का विवरण (Associates Details)")
    col_a1, col_a2 = st.columns(2)
    exec_name = col_a1.text_input("👨‍💼 एग्जीक्यूटिव का पूरा नाम (Login ID) *")
    senior_name = col_a2.text_input("👨‍💼 सीनियर का नाम (Senior Name - यदि कोई हो)")

    exec_mobile = col_a1.text_input("📱 मोबाइल नंबर (Password के लिए अवश्य डालें) *", max_chars=10)
    st.caption("⚠️ *नोट: एग्जीक्यूटिव का नाम ही उसकी 'लॉगिन आईडी' होगी और यहाँ डाला गया मोबाइल नंबर ही उसका 'पासवर्ड' होगा।*")

    st.markdown("#### 💰 मास्टर कमीशन बजट निर्धारण (Global Dual Commission Engine)")
    st.info("💡 यहाँ आप जो भी रेट सेट करेंगे, वह प्रोजेक्ट के अनुसार (% या ₹) अपने आप इंवेंट्री और लेजर में काम करेगा।")
    
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
    save_comm = st.form_submit_button("💾 पूरा पार्टनर प्रोफाइल और लॉगिन सुरक्षित करें", use_container_width=True)

    if save_comm:
        if exec_name.strip() == "" or exec_mobile.strip() == "":
            st.error("🚨 कृपया एग्जीक्यूटिव का नाम और मोबाइल नंबर (पासवर्ड) दर्ज करना अनिवार्य है!")
        elif len(exec_mobile.strip()) < 10:
            st.error("🚨 कृपया सही 10-अंकों का मोबाइल नंबर दर्ज करें!")
        else:
            exec_clean = exec_name.strip()
            
            if 'executives' not in st.session_state.db_projects:
                st.session_state.db_projects['executives'] = {}
            
            st.session_state.db_projects['executives'][exec_clean] = {
                "name": exec_clean,
                "mobile": exec_mobile.strip(), 
                "senior_name": senior_name.strip() if senior_name.strip() else "Direct",
                "percentage_exec": exec_pct,
                "percentage_senior": senior_pct,
                "rupees_exec": exec_rs,
                "rupees_senior": senior_rs,
                "last_updated": str(datetime.date.today())
            }
            
            with st.spinner("क्लाउड में सुरक्षित हो रहा है..."):
                if database.save_db_data():
                    st.success(f"🎉 शानदार! {exec_clean} का प्रोफाइल, मोबाइल लॉगिन और मास्टर कमीशन एक साथ एक्टिवेट हो गए हैं!")
                    st.rerun()


# ====================================================================
# 📊 Section: एग्जीक्यूटिव कमीशन स्ट्रक्चर / स्टेटमेंट जनरेटर
# ====================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📊 एग्जीक्यूटिव कमीशन स्टेटमेंट (Live Commission Ledger Dashboard)")

exec_data_root = db_data.get('executives', {})
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]

if not exec_clean_list:
    st.info("कमिशन स्टेटमेंट देखने के लिए पहले ऊपर कोई पार्टनर अकाउंट सेट करें।")
else:
    col_s1, col_s2, col_s3 = st.columns(3)
    search_exec = col_s1.selectbox("🔎 एग्जीक्यूटिव का नाम चुनें", exec_clean_list)
    start_date = col_s2.date_input("📅 कब से (Start Date)", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col_s3.date_input("📅 कब तक (End Date)", datetime.date.today())

    if st.button("🔍 स्टेटमेंट और रसीद जनरेट करें", use_container_width=True):
        st.markdown(f"### 📄 क्लोजिंग स्टेटमेंट: {search_exec}")
        st.caption(f"अवधि: {start_date} से {end_date}")
        
        ex_profile = exec_data_root[search_exec]
        ex_pct = float(ex_profile.get('percentage_exec', 0.0))
        ex_rs = float(ex_profile.get('rupees_exec', 0.0))

        statement_rows = []
        s_no = 1
        
        for p_name in project_names:
            p_info = db_data[p_name]
            p_mode = p_info.get('comm_type', 'Percentage (%)')
            p_mauza = p_info.get('mauza', 'N/A')
            p_plots = p_info.get('plots', {})
            
            if isinstance(p_plots, list):
                p_plots = {str(idx): p for idx, p in enumerate(p_plots) if p is not None}
                
            for plot_id, plot_info in p_plots.items():
                if isinstance(plot_info, dict) and plot_info.get('status') == 'Booked':
                    if plot_info.get('executive_name') == search_exec:
                        b_date_str = plot_info.get('booking_date', plot_info.get('receipt_date', ''))
                        try:
                            b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                        except:
                            b_date = datetime.date.today()
                            
                        if start_date <= b_date <= end_date:
                            t_amt = float(plot_info.get('token_amount', 0.0))
                            s_rate = float(plot_info.get('selling_rate', 0.0))
                            cust_name = plot_info.get('customer_name', 'N/A')
                            
                            if "Percentage" in p_mode:
                                gross_comm = (s_rate * ex_pct) / 100.0
                            else:
                                gross_comm = ex_rs
                                
                            discount_given = float(plot_info.get('discount', 0.0))
                            if discount_given < 0: discount_given = 0.0
                            
                            comm_after_disc = gross_comm - discount_given
                            if comm_after_disc < 0: comm_after_disc = 0.0
                            
                            tds_amt = (comm_after_disc * 2.0) / 100.0
                            net_comm = comm_after_disc - tds_amt
                            
                            statement_rows.append({
                                "क्र.सं.": s_no,
                                "क्लाइंट का नाम": cust_name,
                                "प्रोजेक्ट": p_name,
                                "प्लॉट नं.": plot_id,
                                "मौजा": p_mauza,
                                "प्राप्त टोकन (₹)": t_amt,
                                "भुगतान तारीख": b_date_str,
                                "सकल कमीशन (₹)": round(gross_comm, 2),
                                "डिस्काउंट कटौती (₹)": round(discount_given, 2),
                                "2% टीडीएस (₹)": round(tds_amt, 2),
                                "नेट कमीशन (₹)": round(net_comm, 2)
                            })
                            s_no += 1
                            
        if statement_rows:
            df_statement = pd.DataFrame(statement_rows)
            st.dataframe(df_statement, use_container_width=True, hide_index=True)
            
            total_token = df_statement["प्राप्त टोकन (₹)"].sum()
            total_gross = df_statement["सकल कमीशन (₹)"].sum()
            total_tds = df_statement["2% टीडीएस (₹)"].sum()
            total_net = df_statement["नेट कमीशन (₹)"].sum()
            
            st.write("---")
            c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
            c_sum1.metric("कुल प्राप्त राशि", f"₹ {total_token}")
            c_sum2.metric("कुल सकल कमीशन", f"₹ {total_gross}")
            c_sum3.metric("कुल टीडीएस कटौती (2%)", f"₹ {total_tds}")
            c_sum4.metric("🏆 शुद्ध देय नेट कमीशन", f"₹ {total_net}", delta="Final Payout")
            
            csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 एक्सपोर्ट स्टेटमेंट (Print / Share on WhatsApp)",
                data=csv_data,
                file_name=f"Statement_{search_exec}_{start_date}_to_{end_date}.csv",
                mime="text/csv",
                use_container_width=True
            )
            st.success("💡 सुझाव: ऊपर दिए गए बटन से फाइल डाउनलोड करके आप सीधे प्रिंट निकाल सकते हैं या व्हाट्सएप पर अटैचमेंट भेज सकते हैं!")
        else:
            st.warning("इस समय सीमा के बीच इस एग्जीक्यूटिव द्वारा की गई कोई भी बुकिंग नहीं मिली।")


# ====================================================================
# 📋 एडिट और मौजूदा एंट्रीज (Existing Partners Ledger - COMPACT VIEW)
# ====================================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<h4 style='margin-bottom:15px;'>📋 मौजूदा मास्टर पार्टनर्स प्रोफाइल एवं लॉगिन डिटेल्स</h4>", unsafe_allow_html=True)

exec_clean_list_view = {k: v for k, v in exec_data_root.items() if isinstance(v, dict) and 'name' in v}

if not exec_clean_list_view:
    st.caption("अभी तक कोई एग्जीक्यूटिव प्रोफाइल सेट नहीं की गई है।")
else:
    for ex_name, p_details in exec_clean_list_view.items():
        with st.container():
            # 🌟 यहाँ अक्षरों का आकार कॉम्पैक्ट (Medium-Small) और बेहद स्लीक कर दिया गया है
            st.markdown(f"""
            <div class="ledger-box">
                <span style="font-size: 15px; font-weight: bold; color: {p_color};">👨‍💼 पार्टनर आईडी: {ex_name}</span> 
                <span style="float: right; background-color: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size:11px; color: #475569; font-weight: 600;">🔑 पासवर्ड (Mob): {p_details.get('mobile','N/A')}</span>
                <br><span style="font-size: 13px; color: #475569;">👴 <b>सीनियर चैन हेड:</b> {p_details.get('senior_name','N/A')} | 📅 अपडेटेड: {p_details.get('last_updated','N/A')}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # छोटे और सुंदर 3D मेट्रिक्स
            c_m1, c_m2, c_m3, c_m4 = st.columns(4)
            c_m1.metric("Exec %", f"{p_details.get('percentage_exec', 0)} %")
            c_m2.metric("Senior %", f"{p_details.get('percentage_senior', 0)} %")
            c_m3.metric("Exec ₹ (Fixed)", f"₹ {p_details.get('rupees_exec', 0)}")
            c_m4.metric("Senior ₹ (Fixed)", f"₹ {p_details.get('rupees_senior', 0)}")
            
            col_del, _ = st.columns([1, 5])
            if col_del.button("🗑️ पार्टनर हटाएं", key=f"del_{ex_name}"):
                st.session_state.db_projects['executives'].pop(ex_name, None)
                database.save_db_data()
                st.success("पार्टनर प्रोफाइल सफलतापूर्वक हटा दी गई!")
                st.rerun()
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
