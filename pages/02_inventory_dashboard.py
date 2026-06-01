import streamlit as st
import pandas as pd
import database # डेटाबेस सिस्टम इम्पोर्ट किया

# --- सबसे पहली Streamlit कमांड: पेज सेटअप ---
# यह कमांड हर पेज की पहली लाइन में होनी चाहिए (Imports के ठीक बाद)
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")

# --- टाइटल ---
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# --- सुरक्षा चेक (Security Check) ---
# यदि उपयोगकर्ता main.py से लॉगिन करके नहीं आया है, तो उसे रोकें
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop() # कोड को यहीं रोक दें

# --- डेटाबेस शुरू करें ---
database.init_db() # सत्र स्थिति सुनिश्चित करें
db_data = st.session_state.db_projects # डेटा का छोटा नाम

# --- रिफ्रेश बटन ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# --- साइडबार: प्रोजेक्ट चुनें ---
st.sidebar.divider()
st.sidebar.header("प्रोजेक्ट चुनें")
project_names = list(db_data.keys())

if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया लैपटॉप से 'Admin Panel' में जाकर प्रोजेक्ट जोड़ें।")
    # डेटा सेव करने का एक ट्रिगर देने के लिए बटन (ताकि खाली तिजोरी सिंक हो जाए)
    if st.button("डेटाबेस ट्रिगर करें (First Time)"):
        database.save_db_data()
        st.rerun()
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट", project_names)
project_data = db_data[selected_project_name]

# --- मुख्य स्क्रीन: प्रोजेक्ट और प्लॉट्स ---
st.header(f"प्रोजेक्ट: {selected_project_name}")

plots = project_data.get('plots', {})
if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()

# --- प्लॉट इन्वेंट्री ग्रिड (Grid View) ---
st.subheader("प्लॉट स्थिति")

# एक लाइन में कितने प्लॉट दिखाने हैं
cols_per_row = 6
# प्लॉट्स की लिस्ट को पंक्तियों (rows) में बांटें
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info['status']
            
            # स्थिति के हिसाब से हिंदी लेबल और रंग
            if status == "Available":
                status_hindi = "✅ उपलब्ध"
                bg_color = "#D4EDDA" # हल्का हरा
            else:
                status_hindi = "❌ बुक"
                bg_color = "#F8D7DA" # हल्का लाल
            
            # प्लॉट का बॉक्स (Metric)
            st.metric(label=f"प्लॉट {plot_id}", value=status_hindi)
            
            # बुकिंग/खाली करने का बटन (पॉपअप खोलने के लिए)
            button_label = "बुक/खाली करें"
            if st.button(button_label, key=f"btn_{selected_project_name}_{plot_id}"):
                # पॉपअप के लिए session state सेट करें
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }

# --- बुकिंग पॉपअप (साइडबार में) ---
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']
    
    st.sidebar.divider()
    st.sidebar.subheader(f"प्लॉट {plt} पर कार्रवाई")
    
    if curr_stat == "Available":
        # बुक करने का फॉर्म
        customer_name = st.sidebar.text_input(f"ग्राहक का नाम (प्लॉट {plt})", key=f"cust_{plt}")
        if st.sidebar.button("❌ प्लॉट बुक करें", key=f"confirm_bk_{plt}"):
            if customer_name:
                # 1. सत्र स्थिति अपडेट करें
                st.session_state.db_projects[proj]['plots'][plt]['status'] = "Booked"
                st.session_state.db_projects[proj]['plots'][plt]['customer_name'] = customer_name
                
                # 2. !!! क्लाउड में सेव करें !!!
                with st.spinner("क्लाउड में सेव हो रहा है..."):
                    if database.save_db_data():
                        st.success(f"प्लॉट {plt} बुक हो गया!")
                        del st.session_state['booking_popup'] # पॉपअप बंद करें
                        st.rerun()
            else:
                st.sidebar.error("कृपया ग्राहक का नाम लिखें।")
    else:
        # खाली करने का फॉर्म
        st.sidebar.warning(f"यह प्लॉट बुक है।")
        if st.sidebar.button("✅ प्लॉट उपलब्ध (खाली) कराएं", key=f"confirm_rel_{plt}"):
            # 1. सत्र स्थिति अपडेट करें
            st.session_state.db_projects[proj]['plots'][plt]['status'] = "Available"
            st.session_state.db_projects[proj]['plots'][plt].pop('customer_name', None) # नाम हटाएं
            
            # 2. !!! क्लाउड में सेव करें !!!
            with st.spinner("क्लाउड में सेव हो रहा है..."):
                if database.save_db_data():
                    st.success(f"प्लॉट {plt} अब उपलब्ध है!")
                    del st.session_state['booking_popup'] # पॉपअप बंद करें
                    st.rerun()
    
    # पॉपअप बंद करने का बटन
    if st.sidebar.button("बंद करें", key="close_popup"):
        del st.session_state['booking_popup']
        st.rerun()
