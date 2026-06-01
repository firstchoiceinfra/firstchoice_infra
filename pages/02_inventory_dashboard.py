import streamlit as st
import pandas as pd
import database # 👈 हमारा अपडेट किया हुआ डेटाबेस सिस्टम इम्पोर्ट किया

# पेज सेटअप
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# उपयोगकर्ता लॉगिन चेक करें
if not st.session_state.get('logged_in'):
    st.warning("कृपया ऐप को फिर से खोलें और लॉगिन करें।")
    st.stop()

# डेटाबेस को शुरू करें और डेटा लोड करें
database.init_db()
db_data = st.session_state.db_projects

# सिंक करने का बटन
if st.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)", key="refresh_db"):
    with st.spinner("क्लाउड से डेटा सिंक हो रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# साइडबार में प्रोजेक्ट चयन
st.sidebar.header("प्रोजेक्ट चुनें")
project_names = list(db_data.keys())
if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया एडमिन पैनल से प्रोजेक्ट जोड़ें।")
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट", project_names)
project_data = db_data[selected_project_name]

# प्रोजेक्ट की डिटेल्स दिखाएं
st.header(f"प्रोजेक्ट: {selected_project_name}")


# प्लॉट इन्वेंट्री ग्रिड
plots = project_data.get('plots', {})
if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()

# ग्रिड व्यू
col_per_row = 5
rows = [list(plots.items())[i:i + col_per_row] for i in range(0, len(plots), col_per_row)]

st.subheader("प्लॉट स्थिति")
for row in rows:
    cols = st.columns(col_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info['status']
            # हिंदी लेबल
            status_hindi = "✅ उपलब्ध" if status == "Available" else "❌ बुक"
            
            st.metric(label=f"प्लॉट {plot_id}", value=status_hindi)
            
            # प्लॉट के लिए बुकिंग कार्रवाई बटन
            if st.button(f"{plot_id} बुक/खाली करें", key=f"action_{plot_id}"):
                st.session_state['selected_plot_for_booking'] = (selected_project_name, plot_id, status)

# बुकिंग पॉपअप (साइडबार में)
if 'selected_plot_for_booking' in st.session_state:
    proj_name, p_id, current_status = st.session_state['selected_plot_for_booking']
    st.sidebar.divider()
    st.sidebar.subheader(f"प्लॉट {p_id} के लिए बुकिंग कार्रवाई")
    
    new_status = ""
    action_text = ""
    if current_status == "Available":
        new_status = "Booked"
        action_text = "❌ प्लॉट बुक करें"
    else:
        new_status = "Available"
        action_text = "✅ प्लॉट उपलब्ध कराएं (रद्द करें)"
        
    # ग्राहक का नाम पूछें (केवल बुकिंग के लिए)
    customer_name = ""
    if new_status == "Booked":
        customer_name = st.sidebar.text_input(f"ग्राहक का नाम (प्लॉट {p_id} के लिए)", key=f"cust_name_{p_id}")
    
    if st.sidebar.button(action_text, key=f"confirm_booking_{p_id}"):
        # 1. सत्र स्थिति में डेटा अपडेट करें
        st.session_state.db_projects[proj_name]['plots'][p_id]['status'] = new_status
        if new_status == "Booked":
            st.session_state.db_projects[proj_name]['plots'][p_id]['customer_name'] = customer_name
        elif new_status == "Available":
            # पुराने डेटा को साफ़ करें
            st.session_state.db_projects[proj_name]['plots'][p_id].pop('customer_name', None)
        
        # 2. !!! क्लाउड में डेटा सेव करें !!! (यही वह चरण है जो लैपटॉप और मोबाइल को सिंक में रखता है)
        with st.spinner("क्लाउड में बुकिंग डेटा सेव हो रहा है..."):
            if database.save_db_data():
                st.success(f"प्लॉट {p_id} की स्थिति सफलतापूर्वक अपडेट की गई और क्लाउड में सेव हो गई!")
                # पेज को रिफ्रेश करें और Pop-up को साफ़ करें
                del st.session_state['selected_plot_for_booking']
                st.rerun()
            else:
                st.error("डेटा सेव करने में समस्या आई।")
    
    if st.sidebar.button("रद्द करें", key=f"cancel_booking_{p_id}"):
        del st.session_state['selected_plot_for_booking']
        st.rerun()
