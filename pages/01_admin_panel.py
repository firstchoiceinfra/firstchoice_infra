import streamlit as st

# चेक करें कि यूजर लॉग इन है या नहीं
if not st.session_state.get('logged_in'): st.stop()

# डेटाबेस इनिशियलाइज़ेशन
if 'projects' not in st.session_state: st.session_state.projects = {}

st.markdown("## ⚙️ Admin Panel - Project & Commission Management")

# -------------------------------------------------------------
# सेक्शन 1: नया प्रोजेक्ट और कमीशन सेट करना
# -------------------------------------------------------------
st.subheader("🏢 Add New Project", divider="blue")
with st.form("add_project_form"):
    proj_name = st.text_input("Project Name (e.g., First Choice City, Sai Samruddhi)")
    
    # प्रोजेक्ट की जमीन की डिटेल्स
    st.markdown("#### 📍 Land Details")
    c1, c2, c3 = st.columns(3)
    khasra = c1.text_input("Khasra No.")
    ph_no = c2.text_input("PH No.")
    mauza = c3.text_input("Mauza")
    
    c4, c5, c6 = st.columns(3)
    tahsil = c4.text_input("Tahsil")
    dist = c5.text_input("District")
    total_plots = c6.number_input("Total Number of Plots", min_value=1, step=1)
    
    # इसी प्रोजेक्ट के लिए डिफ़ॉल्ट कमीशन सेटिंग
    st.markdown("#### 💰 Default Commission Structure for this Project")
    st.info("यहाँ सेट किया गया कमीशन इस प्रोजेक्ट की हर बुकिंग पर ऑटोमैटिक लागू हो जाएगा।")
    
    comm_type = st.radio("Commission Type", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    
    c7, c8 = st.columns(2)
    exec_comm = c7.number_input(f"Executive Commission ({comm_type})", min_value=0.0)
    senior_comm = c8.number_input(f"Senior Commission ({comm_type})", min_value=0.0)

    submit_proj = st.form_submit_button("💾 Save Project & Commission Sync", use_container_width=True)
    
    if submit_proj:
        if proj_name.strip() == "":
            st.error("🚨 Please enter a Project Name!")
        else:
            # प्रोजेक्ट की सारी डिटेल्स और कमीशन एक ही जगह लॉक हो गया
            st.session_state.projects[proj_name] = {
                "khasra": khasra, "ph_no": ph_no, "mauza": mauza,
                "tahsil": tahsil, "district": dist,
                "total_plots": total_plots,
                "comm_type": comm_type,
                "exec_comm": exec_comm,
                "senior_comm": senior_comm
            }
            st.success(f"🎉 प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट हो गया (कमीशन रूल्स के साथ)!")
            st.rerun()

# -------------------------------------------------------------
# सेक्शन 2: मौजूदा प्रोजेक्ट्स देखना
# -------------------------------------------------------------
st.write("---")
st.subheader("📋 Existing Projects & Commission Rules", divider="green")

if st.session_state.projects:
    for p_name, p_data in st.session_state.projects.items():
        with st.expander(f"📁 {p_name} - (Total Plots: {p_data['total_plots']})"):
            st.write(f"**Location:** KH: {p_data['khasra']} | PH: {p_data['ph_no']} | Mauza: {p_data['mauza']} | Tahsil: {p_data['tahsil']} | Dist: {p_data['district']}")
            
            # हाईलाइटेड कमीशन डिटेल्स
            if "Percentage" in p_data['comm_type']:
                st.success(f"**Commission Rule:** Executive: {p_data['exec_comm']}% | Senior: {p_data['senior_comm']}%")
            else:
                st.success(f"**Commission Rule:** Executive: ₹{p_data['exec_comm']} | Senior: ₹{p_data['senior_comm']}")
else:
    st.caption("No projects added yet. Please add a project above.")
