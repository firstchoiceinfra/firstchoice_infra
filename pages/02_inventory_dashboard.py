import streamlit as st
import pandas as pd
import database
import datetime

# --- 1. पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")

# --- 2. सुरक्षा चेक ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 3. डेटाबेस शुरू करें ---
database.init_db() 
db_data = st.session_state.db_projects 

# ====================================================================
# 🎨 यूनिवर्सल थीम सिंक + इन्वेंट्री का प्रीमियम CSS लुक
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
/* प्लॉट कार्ड्स की स्टाइलिंग */
.plot-card {{
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 10px;
    box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    font-weight: bold;
}}
.plot-available {{
    background-color: #d4edda !important;
    color: #155724 !important;
    border: 2px solid #c3e6cb;
}}
.plot-booked {{
    background-color: #f8d7da !important;
    color: #721c24 !important;
    border: 2px solid #f5c6cb;
}}
.stButton>button {{
    background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%);
    color: white !important;
    border-radius: 6px;
    font-weight: bold;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>🏗️ FirstChoice Infra - इन्वेंट्री डैशबोर्ड</h1>", unsafe_allow_html=True)

# =========================================================
# 🌟 स्मार्ट एग्जीक्यूटिव लिस्ट फाइंडर (डेटाबेस से असली नाम खींचना)
# =========================================================
project_names = []
exec_list_temp = []

for key, val in db_data.items():
    if isinstance(val, dict) and ('plots' in val or 'total_plots' in val or 'khasra' in val):
        project_names.append(key)
    else:
        if isinstance(val, dict):
            for k, v in val.items():
                exec_list_temp.append(str(k))
                if isinstance(v, dict):
                    if 'name' in v: exec_list_temp.append(str(v['name']))
                    if 'Name' in v: exec_list_temp.append(str(v['Name']))
                    if 'exec_name' in v: exec_list_temp.append(str(v['exec_name']))
        elif isinstance(val, list):
            exec_list_temp.extend([str(e) for e in val if isinstance(e, str)])

exec_list = ["Direct Sale"] 
for e in exec_list_temp:
    e_clean = e.strip()
    if e_clean and e_clean not in exec_list and e_clean.lower() not in ['true', 'false', 'none', 'select']:
        exec_list.append(e_clean)
exec_list.sort()
# =========================================================

# --- SideBar: प्रोजेक्ट सिलेक्शन ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("सिंक हो रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हुआ!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("प्रोजेक्ट चुनें")

if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया एडमिन पैनल से प्रोजेक्ट जोड़ें।")
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट की सूची", project_names)

# Firebase List Array Fix
if isinstance(st.session_state.db_projects[selected_project_name].get('plots'), list):
    fixed_plots = {str(i): plot for i, plot in enumerate(st.session_state.db_projects[selected_project_name]['plots']) if plot is not None}
    st.session_state.db_projects[selected_project_name]['plots'] = fixed_plots

project_data = st.session_state.db_projects[selected_project_name]
plots = project_data.get('plots', {})

if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()


# =========================================================
# 5. मेन स्क्रीन फॉर्म (बुकिंग फॉर्म या स्टेटमेंट)
# =========================================================
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']
    
    p_khasra = project_data.get('khasra', 'N/A')
    p_ph = project_data.get('ph_no', 'N/A')
    p_mauza = project_data.get('mauza', 'N/A')
    p_tahsil = project_data.get('tahsil', 'N/A')
    p_dist = project_data.get('district', 'N/A')

    st.markdown(f"### 📝 प्रोजेक्ट: {proj} | प्लॉट नंबर: {plt} की बुकिंग जानकारी")
    
    # --- A. नया बुकिंग फॉर्म (अगर प्लॉट खाली है) ---
    if curr_stat == "Available":
        st.info(f"📍 **लोकेशन विवरण:** खसरा: {p_khasra} | PH: {p_ph} | मौजा: {p_mauza} | तहसील: {p_tahsil} | जिला: {p_dist}")
        
        st.subheader("👤 क्लाइंट की जानकारी (Client Details)", divider="blue")
        col1, col2, col3 = st.columns(3)
        c_name = col1.text_input("क्लाइंट का नाम (Client Name) *")
        c_dob = col2.date_input("जन्म तिथि (DOB)", min_value=datetime.date(1950, 1, 1))
        c_phone = col3.text_input("फ़ोन नंबर (Phone No.) *")
        
        c_address = st.text_area("क्लाइंट का पता (Address)")
        
        col4, col5 = st.columns(2)
        c_aadhaar = col4.text_input("आधार नंबर (Aadhaar Number)")
        c_pan = col5.text_input("पैन नंबर (PAN Number)")
        
        col6, col7 = st.columns(2)
        n_name = col6.text_input("नॉमिनी का नाम (Nominee Name)")
        n_age = col7.text_input("नॉमिनी की उम्र (Nominee Age)")
        
        st.subheader("📐 प्लॉट और रेट की जानकारी", divider="blue")
        col8, col9, col10 = st.columns(3)
        plot_area = col8.text_input("प्लॉट एरिया (Sq.Ft/Sq.M)")
        company_rate = col9.number_input("कंपनी का रेट (Company Rate - ₹)", min_value=0.0, step=50.0)
        selling_rate = col10.number_input("सेलिंग रेट (Selling Rate - ₹)", min_value=0.0, step=50.0)
        
        discount = company_rate - selling_rate
        if discount > 0:
            st.success(f"🎉 **इंस्टेंट डिस्काउंट (Instant Discount): ₹ {discount}**")
        elif discount < 0:
            st.warning(f"⚠️ प्रीमियम चार्ज (Premium): ₹ {abs(discount)}")
            
        # 🌟 पेमेंट डिटेल्स (सिर्फ टोकन अमाउंट कॉलम रखा गया है, प्राप्त राशि हटा दी गई है)
        st.subheader("💳 पेमेंट डिटेल्स (Payment Details)", divider="blue")
        col11, col12, col13 = st.columns(3)
        token_amt = col11.number_input("टोकन अमाउंट (Token Amount - ₹) *", min_value=0.0, step=1000.0)
        pay_mode = col12.selectbox("पेमेंट का प्रकार (Mode)", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
        trans_id = col13.text_input("ट्रांज़ैक्शन ID / चेक नंबर")
        
        receive_date = st.date_input("टोकन भुगतान की तारीख (Date of Receipt)")
        
        st.subheader("👨‍💼 एग्जीक्यूटिव की जानकारी (Executive)", divider="blue")
        st.caption("💡 नीचे बॉक्स पर क्लिक करके नाम का पहला अक्षर (Initial) टाइप करें, नाम तुरंत आ जाएगा।")
        
        # 🌟 असली इनिशियल-सर्च बॉक्स
        final_exec_name = st.selectbox("एग्जीक्यूटिव का नाम चुनें या टाइप करें", exec_list, index=0)
        
        st.write("")
        if st.button("💾 पूरी बुकिंग सुरक्षित करें (Confirm Booking)", use_container_width=True, type="primary"):
            if c_name.strip() == "" or c_phone.strip() == "":
                st.error("🚨 कृपया क्लाइंट का नाम और फ़ोन नंबर ज़रूर डालें!")
            elif token_amt <= 0:
                st.error("🚨 कृपया टोकन अमाउंट दर्ज करें!")
            else:
                booking_data = {
                    "status": "Booked",
                    "customer_name": c_name,
                    "dob": str(c_dob),
                    "phone": c_phone,
                    "address": c_address,
                    "aadhaar": c_aadhaar,
                    "pan": c_pan,
                    "nominee_name": n_name,
                    "nominee_age": n_age,
                    "plot_area": plot_area,
                    "company_rate": company_rate,
                    "selling_rate": selling_rate,
                    "discount": discount,
                    "token_amount": token_amt,
                    "payment_mode": pay_mode,
                    "transaction_id": trans_id,
                    "receipt_date": str(receive_date),
                    "executive_name": final_exec_name, 
                    "booking_date": str(datetime.date.today())
                }
                
                st.session_state.db_projects[proj]['plots'][plt].update(booking_data)
                
                with st.spinner("क्लाउड में सुरक्षित हो रहा है..."):
                    if database.save_db_data():
                        st.success(f"🎉 बधाई हो! प्लॉट {plt} सफलतापूर्वक बुक हो गया है!")
                        del st.session_state['booking_popup']
                        st.rerun()

    # --- B. पूरा स्टेटमेंट (अगर प्लॉट पहले से बुक है) ---
    else:
        p_data = st.session_state.db_projects[proj]['plots'][plt]
        st.error(f"⚠️ यह प्लॉट पहले से बुक है। नीचे इसका पूरा स्टेटमेंट दिया गया है:")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("कस्टमर का नाम", p_data.get('customer_name', 'N/A'))
        c1.write(f"**DOB:** {p_data.get('dob', 'N/A')} | **पता:** {p_data.get('address', 'N/A')}")
        
        c2.metric("फ़ोन नंबर", p_data.get('phone', 'N/A'))
        c2.write(f"**आधार:** {p_data.get('aadhaar', 'N/A')} | **पैन:** {p_data.get('pan', 'N/A')}")
        
        c3.metric("बुक करने वाला एग्जीक्यूटिव", p_data.get('executive_name', 'N/A'))
        c3.write(f"**नॉमिनी:** {p_data.get('nominee_name', 'N/A')} (उम्र: {p_data.get('nominee_age', 'N/A')})")
        
        with st.expander("📄 प्लॉट, रेट एवं पेमेंट स्टेटमेंट (Full Statement)", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.write(f"📐 **प्लॉट एरिया:** {p_data.get('plot_area', 'N/A')}")
            col_s1.write(f"📆 **बुकिंग की तारीख:** {p_data.get('booking_date', 'N/A')}")
            
            col_s2.write(f"🏢 **कंपनी रेट:** ₹{p_data.get('company_rate', 0)}")
            col_s2.write(f"💰 **सेलिंग रेट:** ₹{p_data.get('selling_rate', 0)}")
            col_s2.success(f"💸 **दिया गया डिस्काउंट:** ₹{p_data.get('discount', 0)}")
            
            # सिर्फ टोकन अमाउंट का ही स्टेटमेंट दिखेगा
            col_s3.warning(f"💳 **टोकन अमाउंट जमा:** ₹{p_data.get('token_amount', 0)}")
            col_s3.write(f"🏪 **पेमेंट मोड:** {p_data.get('payment_mode', 'N/A')}")
            col_s3.write(f"🔑 **ट्रांज़ैक्शन/चेक ID:** {p_data.get('transaction_id', 'N/A')}")
            col_s3.write(f"📅 **भुगतान रसीद डेट:** {p_data.get('receipt_date', 'N/A')}")
            
        st.write("")
        st.warning("क्या आप इस प्लॉट की बुकिंग रद्द करके इसे वापस उपलब्ध (Available) करना चाहते हैं?")
        if st.button("✅ हाँ, बुकिंग रद्द करें और प्लॉट खाली करें", use_container_width=True):
            st.session_state.db_projects[proj]['plots'][plt] = {"status": "Available"}
            with st.spinner("क्लाउड अपडेट हो रहा है..."):
                if database.save_db_data():
                    st.success(f"प्लॉट {plt} अब खाली और उपलब्ध है!")
                    del st.session_state['booking_popup']
                    st.rerun()

    st.write("---")
    if st.button("❌ पीछे जाएं (Cancel / Back)", use_container_width=True):
        del st.session_state['booking_popup']
        st.rerun()

    st.stop() 


# =========================================================
# 6. प्रोफेशनल इन्वेंट्री ग्रिड (प्लॉट्स का शानदार लेआउट मैप)
# =========================================================
st.markdown(f"### 📋 प्रोजेक्ट गैलरी: {selected_project_name}")
st.write(f"📍 खसरा नं: {project_data.get('khasra','N/A')} | मौजा: {project_data.get('mauza','N/A')} | कुल प्लॉट्स: {project_data.get('total_plots', 0)}")

cols_per_row = 5 
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            
            # सुंदर 3D कार्ड डिज़ाइन HTML द्वारा
            if status == "Available":
                st.markdown(f'<div class="plot-card plot-available">🏠 प्लॉट {plot_id}<br>✅ उपलब्ध</div>', unsafe_allow_html=True)
                btn_txt = "📝 बुक करें"
            else:
                cust = plot_info.get('customer_name', 'N/A')
                st.markdown(f'<div class="plot-card plot-booked">🛑 प्लॉट {plot_id}<br>❌ बुक ({cust})</div>', unsafe_allow_html=True)
                btn_txt = "📄 स्टेटमेंट"
            
            if st.button(btn_txt, key=f"btn_{selected_project_name}_{plot_id}", use_container_width=True):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }
                st.rerun()
