import streamlit as st
import database # 👈 डेटाबेस सिस्टम को इम्पोर्ट किया

# 👈 पेज खुलते ही पुराना डेटा लोड करना
database.init_db()

if not st.session_state.get('logged_in'): st.stop()

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
            st.session_state.projects[proj_name] = {
                "khasra": khasra, "ph_no": ph_no, "mauza": mauza,
                "tahsil": tahsil, "district": dist,
                "total_plots": total_plots,
                "comm_type": comm_type,
                "max_commission": max_comm 
            }
            
            # 👈 सबसे ज़रूरी लाइन: प्रोजेक्ट डेटा को फाइल में लॉक करना
            database.save_db()
            
            st.success(f"🎉 प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट और सुरक्षित हो गया!")
            st.rerun()

# -------------------------------------------------------------
# मौजूदा प्रोजेक्ट्स देखना
# -------------------------------------------------------------
st.write("---")
st.subheader("📋 Existing Projects & Commission Budget", divider="green")

if st.session_state.projects:
    for p_name, p_data in st.session_state.projects.items():
        with st.expander(f"📁 {p_name} - (Total Plots: {p_data['total_plots']})"):
            st.write(f"**Location:** KH: {p_data['khasra']} | PH: {p_data['ph_no']} | Mauza: {p_data['mauza']} | Tahsil: {p_data['tahsil']} | Dist: {p_data['district']}")
            if "Percentage" in p_data['comm_type']:
                st.success(f"**Total Company Budget:** {p_data['max_commission']}%")
            else:
                st.success(f"**Total Company Budget:** ₹{p_data['max_commission']}")
else:
    st.caption("No projects added yet.")
