import streamlit as st
import pandas as pd
import database

# 1. Page Setup
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# 2. Login Check
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# 3. DB Init
database.init_db() 
db_data = st.session_state.db_projects 

# 4. Refresh Button
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# 5. Sidebar Selection
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

# --- FIREBASE LIST/ARRAY AUTO-FIX ---
plots = project_data.get('plots')

if isinstance(plots, list):
    # Agar Firebase ne list bana diya hai, toh wapas dictionary banao
    plots = {str(i): plot for i, plot in enumerate(plots) if plot is not None}
elif plots is None:
    plots = {}

if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()
# ------------------------------------

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

# 6. Booking Popup
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']
    
    st.sidebar.divider()
    st.sidebar.subheader(f"प्लॉट {plt} पर कार्रवाई")
    
    # Update state properly if it's still a list in memory
    if isinstance(st.session_state.db_projects[proj].get('plots'), list):
        st.session_state.db_projects[proj]['plots'] = {str(idx): p for idx, p in enumerate(st.session_state.db_projects[proj]['plots']) if p is not None}
