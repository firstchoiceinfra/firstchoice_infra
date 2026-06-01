import streamlit as st
import pandas as pd
import database

# 1. पेज सेटअप (यह लाइन सबसे ऊपर होनी चाहिए)
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")

# 2. ऐप का टाइटल
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# 3. सुरक्षा चेक (लॉगिन)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# 4. डेटाबेस शुरू करें
database.init_db() 
db_data = st.session_state.db_projects 

# 5. रिफ्रेश बटन
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# 6. साइडबार: प्रोजेक्ट चुनें
st.sidebar.divider()
st.sidebar.header("प्रोजेक्ट चुनें")
project_names = list(db_data.keys())

if not project_names:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया लैपटॉप से 'Admin Panel' में जाकर प्रोजेक्ट जोड़ें।")
    if st.button("डेटाबेस ट्रिगर करें (First Time)"):
        database.save_db_data()
        st.rerun()
    st.stop()

selected_project_name = st.sidebar.selectbox("प्रोजेक्ट", project_names)
project_data = db_data[selected_project_name]

st.header(f"प्रोजेक्ट: {selected_project_name}")

# 7. प्लॉट डेटा लाएं (फोन क्रैश से बचने के लिए)
plots = project_data.get('plots')
if plots is None:
    plots = {}

if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()

# 8. प्लॉट इन्वेंट्री दिखाना
st.subheader("प्लॉट स्थिति")

cols_per_row = 6
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            
            if status == "Available":
                status_hindi = "✅ उपलब्ध"
            else:
                status_hindi = "❌ बुक"
            
            st.metric(label=f"प्लॉट {plot_id}", value=status_hindi)
            
            if st.button("बुक/खाली करें", key=f"btn_{selected_project_name}_{plot_id}"):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }

# 9. बुकिंग पॉपअप (साइडबार में)
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']
    
    st.sidebar.divider()
    st.sidebar.subheader(f"प्लॉट {plt} पर कार्रवाई")
    
    if curr_stat == "Available":
        customer_name = st.sidebar.text_input(f"ग्राहक का नाम (प्लॉट {plt})", key=f"cust_{plt}")
        if st.sidebar.button("❌ प्लॉट बुक करें", key=f"confirm_bk_{plt}"):
            if customer_name:
                st.session_state.db_projects[proj]['plots'][plt]['status'] = "Booked"
                st.session_state.db_projects[proj]['plots'][plt]['customer_name'] = customer_name
                
                with st.spinner("क्लाउड में सेव हो रहा है..."):
                    if database.save_db_data():
                        st.success(f"प्लॉट {plt} बुक हो गया!")
                        del st.session_state['booking_popup']
                        st.rerun()
            else:
                st.sidebar.error("कृपया ग्राहक का नाम लिखें।")
    else:
        st.sidebar.warning(f"यह प्लॉट बुक है।")
        if st.sidebar.button("✅ प्लॉट उपलब्ध (खाली) कराएं", key=f"confirm_rel_{plt}"):
            st.session_state.db_projects[proj]['plots'][plt]['status'] = "Available"
            st.session_state.db_projects[proj]['plots'][plt].pop('customer_name', None)
            
            with st.spinner("क्लाउड में सेव हो रहा है..."):
                if database.save_db_data():
                    st.success(f"प्लॉट {plt} अब उपलब्ध है!")
                    del st.session_state['booking_popup']
                    st.rerun()
    
    if st.sidebar.button("बंद करें", key="close_popup"):
        del st.session_state['booking_popup']
        st.rerun()
