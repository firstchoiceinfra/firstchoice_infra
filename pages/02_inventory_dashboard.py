import streamlit as st
import pandas as pd
import database

# 1. पेज सेटअप
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# 2. लॉगिन चेक
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# 3. डेटाबेस कनेक्ट करें
database.init_db() 
db_data = st.session_state.db_projects 

# 4. रिफ्रेश बटन (साइडबार में)
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# 5. प्रोजेक्ट चुनना (साइडबार में)
st.sidebar.divider()
st.sidebar.header("प्रोजेक्ट चुनें")
project_names = list(db_data.keys())

if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया लैपटॉप से 'Admin Panel' में जाकर प्रोजेक्ट जोड़ें।")
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट", project_names)
project_data = db_data[selected_project_name]

# --- Firebase List Error Fix ---
plots = project_data.get('plots')
if isinstance(plots, list):
    plots = {str(i): plot for i, plot in enumerate(plots) if plot is not None}
elif plots is None:
    plots = {}

if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()

# =========================================================
# 6. बुकिंग फॉर्म (मेन स्क्रीन पर - यह बटन दबाने के बाद दिखेगा)
# =========================================================
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']

    st.markdown(f"## 📝 प्लॉट {plt} - बुकिंग फॉर्म")
    st.info(f"प्रोजेक्ट: {proj}")
    
    # अगर क्लाउड ने लिस्ट बना दी है, तो डिक्शनरी फिक्स करें
    if isinstance(st.session_state.db_projects[proj].get('plots'), list):
        st.session_state.db_projects[proj]['plots'] = {str(idx): p for idx, p in enumerate(st.session_state.db_projects[proj]['plots']) if p is not None}

    with st.container():
        # --- जब प्लॉट खाली हो (नयी बुकिंग) ---
        if curr_stat == "Available":
            with st.form(key=f"book_form_{plt}"):
                st.subheader("ग्राहक की जानकारी दर्ज करें")
                
                # सारे नए कॉलम (Columns)
                col1, col2 = st.columns(2)
                customer_name = col1.text_input("ग्राहक का नाम (Customer Name) *")
                phone_number = col2.text_input("मोबाइल नंबर (Mobile No.)")
                
                col3, col4 = st.columns(2)
                booking_amt = col3.text_input("बुकिंग राशि (Booking Amount - ₹)")
                remarks = col4.text_input("अन्य जानकारी (Remarks)")
                
                st.write("") # थोड़ा स्पेस
                submit_btn = st.form_submit_button("💾 प्लॉट बुक करें और सुरक्षित करें", use_container_width=True)
                
                if submit_btn:
                    if customer_name.strip() == "":
                        st.error("🚨 कृपया ग्राहक का नाम ज़रूर लिखें!")
                    else:
                        st.session_state.db_projects[proj]['plots'][plt]['status'] = "Booked"
                        st.session_state.db_projects[proj]['plots'][plt]['customer_name'] = customer_name
                        st.session_state.db_projects[proj]['plots'][plt]['phone'] = phone_number
                        st.session_state.db_projects[proj]['plots'][plt]['amount'] = booking_amt
                        st.session_state.db_projects[proj]['plots'][plt]['remarks'] = remarks
                        
                        with st.spinner("क्लाउड में सेव हो रहा है..."):
                            if database.save_db_data():
                                st.success(f"🎉 प्लॉट {plt} सफलतापूर्वक बुक हो गया!")
                                del st.session_state['booking_popup'] # फॉर्म बंद करें
                                st.rerun()

        # --- जब प्लॉट पहले से बुक हो (बुकिंग रद्द करना) ---
        else:
            cust = st.session_state.db_projects[proj]['plots'][plt].get('customer_name', 'N/A')
            ph = st.session_state.db_projects[proj]['plots'][plt].get('phone', 'N/A')
            amt = st.session_state.db_projects[proj]['plots'][plt].get('amount', 'N/A')
            
            st.error(f"⚠️ यह प्लॉट पहले से **{cust}** के नाम पर बुक है।")
            st.write(f"**मोबाइल नंबर:** {ph} | **बुकिंग राशि:** ₹{amt}")
            
            with st.form(key=f"release_form_{plt}"):
                st.warning("क्या आप इस प्लॉट की बुकिंग रद्द करके इसे वापस खाली (Available) करना चाहते हैं?")
                rel_btn = st.form_submit_button("✅ हाँ, प्लॉट खाली (Available) करें", use_container_width=True)
                
                if rel_btn:
                    st.session_state.db_projects[proj]['plots'][plt]['status'] = "Available"
                    st.session_state.db_projects[proj]['plots'][plt].pop('customer_name', None)
                    st.session_state.db_projects[proj]['plots'][plt].pop('phone', None)
                    st.session_state.db_projects[proj]['plots'][plt].pop('amount', None)
                    st.session_state.db_projects[proj]['plots'][plt].pop('remarks', None)
                    
                    with st.spinner("क्लाउड में अपडेट हो रहा है..."):
                        if database.save_db_data():
                            st.success(f"प्लॉट {plt} अब खाली (Available) है!")
                            del st.session_state['booking_popup']
                            st.rerun()

    # फॉर्म बंद करके वापस ग्रिड पर जाने का बटन
    st.write("---")
    if st.button("❌ पीछे जाएं (Cancel / Back)", use_container_width=True):
        del st.session_state['booking_popup']
        st.rerun()

    # जब फॉर्म खुला हो, तो नीचे प्लॉट्स की लिस्ट न दिखाएं
    st.stop() 


# =========================================================
# 7. इन्वेंट्री ग्रिड (प्लॉट्स की लिस्ट)
# =========================================================
st.header(f"प्रोजेक्ट: {selected_project_name}")
st.subheader("प्लॉट स्थिति")

# एक लाइन में कितने प्लॉट दिखाने हैं (मोबाइल के लिए 5 अच्छा रहता है)
cols_per_row = 5 
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            
            # रंग और डिज़ाइन
            if status == "Available":
                st.success(f"**प्लॉट {plot_id}**\n\n✅ उपलब्ध")
            else:
                cust = plot_info.get('customer_name', '')
                st.error(f"**प्लॉट {plot_id}**\n\n❌ बुक\n({cust})")
            
            # बुकिंग एक्शन बटन
            if st.button("📝 फॉर्म खोलें", key=f"btn_{selected_project_name}_{plot_id}"):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }
                st.rerun() # बटन दबाते ही पेज रिफ्रेश होकर फॉर्म आ जाएगा
