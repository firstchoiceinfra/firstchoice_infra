# pages/01_admin_panel.py

import streamlit as st
import database # 👈 डेटाबेस सिस्टम को इम्पोर्ट किया

# 1. !!! सबसे ज़रूरी: पेज सेटअप (यह लाइन सबसे ऊपर होनी चाहिए) !!!
st.set_page_config(layout="wide", page_title="FC Infra - एडमिन पैनल")

# 2. सुरक्षा चेक: क्या यूजर लॉगिन है?
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) पर जाकर लॉगिन करें।")
    st.stop()

# 3. डेटाबेस लोड करना
database.init_db()

# आसान नामकरण (Firebase वाले डेटाबेस का इस्तेमाल)
if 'db_projects' not in st.session_state:
    st.session_state.db_projects = {}

# --- मुख्य पेज UI ---
st.markdown("## ⚙️ Admin Panel - Project & Commission Management")

# -------------------------------------------------------------
# नया प्रोजेक्ट और कमीशन सेट करना
# -------------------------------------------------------------
st.subheader("🏢 Add New Project", divider="blue")
with st.form("add_project_form"):
    proj_name = st.text_input("Project Name (e.g., First Choice City, Sai Samruddhi)")
   
    st.markdown("#### 📍 Land Details")
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("Khasra No.")
    ph_no = c2.text_input("PH No.")
    mauza = c3.text_input("Mauza")
   
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("Tahsil")
    dist = c5.text_input("District")
    total_plots = c6.number_input("Total Number of Plots", min_value=1, step=1)
   
    st.markdown("#### 💰 Total/Highest Commission Allowed for this Project")
    st.info("यहाँ कंपनी द्वारा तय किया गया 'Highest Commission' डालें।")
   
    comm_type = st.radio("Commission Type", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    max_comm = st.number_input(f"Total Highest Commission in {comm_type}", min_value=0.0)

    submit_proj = st.form_submit_button("💾 Save Project & Commission Budget", use_container_width=True)
   
    if submit_proj:
        if proj_name.strip() == "":
            st.error("🚨 Please enter a Project Name!")
        else:
            # इन्वेंट्री के लिए अपने आप खाली प्लॉट्स तैयार करना
            plots_dict = {}
            for i in range(1, int(total_plots) + 1):
                plots_dict[str(i)] = {"status": "Available"}

            st.session_state.db_projects[proj_name] = {
                "khasra": khasra, 
                "ph_no": ph_no, 
                "mauza": mauza,
                "tahsil": tahsil, 
                "district": dist,
                "total_plots": total_plots,
                "comm_type": comm_type,
                "max_commission": max_comm,
                "plots": plots_dict # 👈 इन्वेंट्री को यही डेटा चाहिए
            }
           
            # 👈 सबसे ज़रूरी लाइन: प्रोजेक्ट डेटा को क्लाउड (Firebase) में लॉक करना
            with st.spinner("क्लाउड में सेव हो रहा है..."):
                if database.save_db_data():
                    st.success(f"🎉 प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट और सुरक्षित हो गया!")
                    st.rerun()

# -------------------------------------------------------------
# मौजूदा प्रोजेक्ट्स देखना
# -------------------------------------------------------------
st.write("---")
st.subheader("📋 Existing Projects & Commission Budget", divider="green")

if st.session_state.db_projects:
    for p_name, p_data in st.session_state.db_projects.items():
        with st.expander(f"📁 {p_name} - (Total Plots: {p_data.get('total_plots', 0)})"):
            st.write(f"**Location:** KH: {p_data.get('khasra', '')} | PH: {p_data.get('ph_no', '')} | Mauza: {p_data.get('mauza', '')} | Tahsil: {p_data.get('tahsil', '')} | Dist: {p_data.get('district', '')}")
            if "Percentage" in p_data.get('comm_type', ''):
                st.success(f"**Total Company Budget:** {p_data.get('max_commission', 0)}%")
            else:
                st.success(f"**Total Company Budget:** ₹{p_data.get('max_commission', 0)}")
else:
    st.caption("No projects added yet.")
