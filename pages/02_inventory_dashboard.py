import streamlit as st
import pandas as pd
import database # Hamara database system import kiya

# --- 1. Sabse pehli Streamlit command: Page Setup ---
st.set_page_config(layout="wide", page_title="FC Infra - इन्वेंट्री")

# --- 2. App Title ---
st.title("FirstChoice Infra - इन्वेंट्री डैशबोर्ड 🏗️")

# --- 3. Suraksha Check (Security Check) ---
# Agar user login karke nahi aaya hai, toh use rokein
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# --- 4. Database Shuru Karein aur Data Load Karein ---
database.init_db() 
db_data = st.session_state.db_projects 

# --- 5. Refresh Button ---
if st.sidebar.button("🔄 क्लाउड से सिंक करें (रिफ्रेश)"):
    with st.spinner("क्लाउड से नवीनतम डेटा आ रहा है..."):
        database.load_db_data()
        st.success("डेटा सिंक हो गया!")
        st.rerun()

# --- 6. Sidebar: Project Chunein ---
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

# --- 7. Mukhya Screen: Project aur Plots ---
st.header(f"प्रोजेक्ट: {selected_project_name}")

# !!! PHONE CRASH FIX: Cloud se agar plots nahi mile toh crash na ho !!!
plots = project_data.get('plots')
if plots is None:
    plots = {}

if not plots:
    st.info("इस प्रोजेक्ट में अभी कोई प्लॉट नहीं है।")
    st.stop()

# --- 8. Plot Inventory Grid View ---
st.subheader("प्लॉट स्थिति")

# Ek line me kitne plot dikhane hai
cols_per_row = 6
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            
            # Sthiti ke hisab se Hindi label
            if status == "Available":
                status_hindi = "✅ उपलब्ध"
            else:
                status_hindi = "❌ बुक"
            
            # Plot ka box (Metric)
            st.metric(label=f"प्लॉट {plot_id}", value=status_hindi)
            
            # Booking/Khali karne ka button (Popup sidebar me kholne ke liye)
            if st.button("बुक/खाली करें", key=f"btn_{selected_project_name}_{plot_id}"):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_
