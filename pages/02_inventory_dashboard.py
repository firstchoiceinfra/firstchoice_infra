import streamlit as st
import pandas as pd
import database
import datetime

# --- 1. पेज सेटअप ---
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# --- 2. सुरक्षा चेक ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 3. डेटाबेस शुरू करें ---
database.init_db() 
db_data = st.session_state.db_projects 

# =========================================================
# 🌟 असली एग्जीक्यूटिव लिस्ट (डेटाबेस से लाना)
# =========================================================
exec_list = ["एग्जीक्यूटिव चुनें (Select)", "Direct Sale"] # डिफ़ॉल्ट विकल्प

# चेक करें कि क्या आपके डेटाबेस में executives का डेटा है
if 'executives' in db_data:
    saved_execs = db_data['executives']
    if isinstance(saved_execs, dict):
        # अगर डेटा डिक्शनरी है, तो उसके नाम (keys) निकाल लें
        exec_list.extend(list(saved_execs.keys()))
    elif isinstance(saved_execs, list):
        # अगर डेटा लिस्ट है, तो सीधे जोड़ दें
        exec_list.extend([str(e) for e in saved_execs if e])
elif 'executives' in st.session_state:
    # अगर session state में अलग से है
    saved_execs = st.session_state.executives
    if isinstance(saved_execs, dict):
        exec_list.extend(list(saved_execs.keys()))
    elif isinstance(saved_execs, list):
        exec_list.extend([str(e) for e in saved_execs if e])
        
# डुप्लीकेट नाम हटाने के लिए (ताकि एक नाम दो बार ना दिखे)
exec_list = list(dict.fromkeys(exec_list))
# =========================================================

# --- 4. साइडबार ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("प्रोजेक्ट चुनें")
project_names = [name for name in db_data.keys() if name != 'executives'] # executives फोल्डर को प्रोजेक्ट लिस्ट से हटाएं

if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया लैपटॉप से 'Admin Panel' में जाकर प्रोजेक्ट जोड़ें।")
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट", project_names)
project_data = db_data[selected_project_name]

# प्लॉट्स डेटा को सुरक्षित तरीके से लोड करना
plots = project_data.get('plots')
if isinstance(plots, list):
    plots = {str(i): plot for i, plot in enumerate(plots) if plot is not None}
elif plots is None:
    plots = {}

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

    st.markdown(f"## 📝 प्लॉट {plt} - बुकिंग मैनेजमेंट")
    
    # --- A. अगर प्लॉट खाली है (नया बुकिंग फॉर्म) ---
    if curr_stat == "Available":
        st.info(f"**प्रोजेक्ट:** {proj} | **खसरा:** {p_khasra} | **PH:** {p_ph} | **मौजा:** {p_mauza} | **तहसील:** {p_tahsil} | **जिला:** {p_dist}")
        
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
        company_rate = col9.number_input("कंपनी का रेट (Company Rate - ₹)", min_value=0.0, value=0.0, step=50.0)
        selling_rate = col10.number_input("सेलिंग रेट (Selling Rate - ₹)", min_value=0.0, value=0.0, step=50.0)
        
        discount = company_rate - selling_rate
        if discount > 0:
            st.success(f"🎉 **इंस्टेंट डिस्काउंट (Instant Discount): ₹ {discount}**")
        elif discount < 0:
            st.warning(f"⚠️ प्रीमियम चार्ज (Premium): ₹ {abs(discount)}")
            
        st.subheader("💳 पेमेंट डिटेल्स (Payment Details)", divider="blue")
        col11, col12 = st.columns(2)
        token_amt = col11.number_input("टोकन अमाउंट (Token Amount)", min_value=0.0, step=1000.0)
        received_amt = col12.number_input("प्राप्त राशि (Received Amount)", min_value=0.0, step=1000.0)
        
        col13, col14, col15 = st.columns(3)
        pay_mode = col13.selectbox("पेमेंट का प्रकार (Mode)", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
        trans_id = col14.text_input("ट्रांज़ैक्शन ID / चेक नंबर")
        receive_date = col15.date_input("भुगतान की तारीख (Date of Receipt)")
        
        st.subheader("👨‍💼 एग्जीक्यूटिव की जानकारी", divider="blue")
        
        # 🌟 ड्रॉपडाउन में अब डेटाबेस वाली लिस्ट दिखेगी
        exec_name = st.selectbox("एग्जीक्यूटिव चुनें (Executive Name)", exec_list)
        
        st.write("")
        if st.button("💾 पूरी बुकिंग सुरक्षित करें (Save Booking)", use_container_width=True, type="primary"):
            if c_name.strip() == "" or c_phone.strip() == "":
                st.error("🚨 कृपया क्लाइंट का नाम और फ़ोन नंबर ज़रूर डालें!")
            elif exec_name == "एग्जीक्यूटिव चुनें (Select)":
                st.error("🚨 कृपया एग्जीक्यूटिव का नाम चुनें!")
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
                    "received_amount": received_amt,
                    "payment_mode": pay_mode,
                    "transaction_id": trans_id,
                    "receipt_date": str(receive_date),
                    "executive_name": exec_name,
                    "booking_date": str(datetime.date.today())
                }
                
                st.session_state.db_projects[proj]['plots'][plt].update(booking_data)
                
                with st.spinner("क्लाउड में सेव हो रहा है..."):
                    if database.save_db_data():
                        st.success(f"🎉 प्लॉट {plt} सफलतापूर्वक बुक हो गया!")
                        del st.session_state['booking_popup']
                        st.rerun()

    # --- B. अगर प्लॉट बुक है (पूरी स्टेटमेंट/डिटेल्स दिखाना) ---
    else:
        p_data = st.session_state.db_projects[proj]['plots'][plt]
        st.error(f"⚠️ यह प्लॉट पहले से बुक है। नीचे पूरा स्टेटमेंट (Statement) दिया गया है:")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("क्लाइंट का नाम", p_data.get('customer_name', 'N/A'))
        c2.metric("फ़ोन नंबर", p_data.get('phone', 'N/A'))
        c3.metric("एग्जीक्यूटिव", p_data.get('executive_name', 'N/A'))
        
        with st.expander("📄 पूरी जानकारी (Full Details) खोलें", expanded=True):
            st.write(f"**प्लॉट एरिया:** {p_data.get('plot_area', 'N/A')} | **बुकिंग डेट:** {p_data.get('booking_date', 'N/A')}")
            st.write(f"**क्लाइंट का पता:** {p_data.get('address', 'N/A')} | **DOB:** {p_data.get('dob', 'N/A')}")
            st.write(f"**आधार:** {p_data.get('aadhaar', 'N/A')} | **पैन:** {p_data.get('pan', 'N/A')}")
            st.write(f"**नॉमिनी:** {p_data.get('nominee_name', 'N/A')} (उम्र: {p_data.get('nominee_age', 'N/A')})")
            
            st.divider()
            st.write(f"**कंपनी रेट:** ₹{p_data.get('company_rate', 0)} | **सेलिंग रेट:** ₹{p_data.get('selling_rate', 0)}")
            st.success(f"**डिस्काउंट दिया गया:** ₹{p_data.get('discount', 0)}")
            
            st.divider()
            st.write(f"**टोकन अमाउंट:** ₹{p_data.get('token_amount', 0)} | **प्राप्त राशि:** ₹{p_data.get('received_amount', 0)}")
            st.write(f"**पेमेंट प्रकार:** {p_data.get('payment_mode', 'N/A')} | **तारीख:** {p_data.get('receipt_date', 'N/A')}")
            st.write(f"**ट्रांज़ैक्शन ID:** {p_data.get('transaction_id', 'N/A')}")
            
        st.write("")
        st.warning("क्या आप इस प्लॉट की बुकिंग रद्द करके इसे वापस खाली (Available) करना चाहते हैं?")
        if st.button("✅ हाँ, प्लॉट खाली (Available) करें", use_container_width=True):
            st.session_state.db_projects[proj]['plots'][plt] = {"status": "Available"}
            
            with st.spinner("क्लाउड में अपडेट हो रहा है..."):
                if database.save_db_data():
                    st.success(f"प्लॉट {plt} अब खाली (Available) है!")
                    del st.session_state['booking_popup']
                    st.rerun()

    st.write("---")
    if st.button("❌ पीछे जाएं (Cancel / Back)", use_container_width=True):
        del st.session_state['booking_popup']
        st.rerun()

    st.stop() 


# =========================================================
# 6. इन्वेंट्री ग्रिड (प्लॉट्स की लिस्ट)
# =========================================================
st.header(f"प्रोजेक्ट: {selected_project_name}")
st.subheader("प्लॉट स्थिति")

cols_per_row = 5 
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            
            if status == "Available":
                st.success(f"**प्लॉट {plot_id}**\n\n✅ उपलब्ध")
                btn_txt = "📝 बुकिंग फॉर्म"
            else:
                cust = plot_info.get('customer_name', 'N/A')
                st.error(f"**प्लॉट {plot_id}**\n\n❌ बुक\n({cust})")
                btn_txt = "📄 डिटेल्स देखें"
            
            if st.button(btn_txt, key=f"btn_{selected_project_name}_{plot_id}"):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }
                st.rerun()
