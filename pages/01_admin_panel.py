import streamlit as st

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
    
    # कंपनी की तरफ से तय किया गया कुल कमीशन
    st.markdown("#### 💰 Total/Highest Commission Allowed for this Project")
    st.info("यहाँ कंपनी द्वारा तय किया गया 'Highest Commission' (उदा. 20%) डालें। आगे एग्जीक्यूटिव चेन (सीनियर/जूनियर) इसी में से अपना हिस्सा बांटेंगे।")
    
    comm_type = st.radio("Commission Type", ["Percentage (%)", "Rupees (₹)"], horizontal=True)
    
    # सिर्फ़ एक ही कॉलम - Highest Commission के लिए
    max_comm = st.number_input(f"Total Highest Commission in {comm_type}", min_value=0.0)

    submit_proj = st.form_submit_button("💾 Save Project & Commission Budget", use_container_width=True)
    
    if submit_proj:
        if proj_name.strip() == "":
            st.error("🚨 Please enter a Project Name!")
        else:
            # प्रोजेक्ट की डिटेल्स और कुल कमीशन लॉक हो गया
            st.session_state.projects[proj_name] = {
                "khasra": khasra, "ph_no": ph_no, "mauza": mauza,
                "tahsil": tahsil, "district": dist,
                "total_plots": total_plots,
                "comm_type": comm_type,
                "max_commission": max_comm # सिर्फ़ टोटल कमीशन सेव हो रहा है
            }
            st.success(f"🎉 प्रोजेक्ट '{proj_name}' सफलतापूर्वक सेट हो गया (Highest Budget: {max_comm})!")
            st.rerun()

# -------------------------------------------------------------
# सेक्शन 2: मौजूदा प्रोजेक्ट्स देखना
# -------------------------------------------------------------
st.write("---")
st.subheader("📋 Existing Projects & Commission Budget", divider="green")

if st.session_state.projects:
    for p_name, p_data in st.session_state.projects.items():
        with st.expander(f"📁 {p_name} - (Total Plots: {p_data['total_plots']})"):
            st.write(f"**Location:** KH: {p_data['khasra']} | PH: {p_data['ph_no']} | Mauza: {p_data['mauza']} | Tahsil: {p_data['tahsil']} | Dist: {p_data['district']}")
            
            # कंपनी का हाईएस्ट कमीशन दिखाना
            if "Percentage" in p_data['comm_type']:
                st.success(f"**Total Company Budget:** {p_data['max_commission']}%")
            else:
                st.success(f"**Total Company Budget:** ₹{p_data['max_commission']}")
else:
    st.caption("No projects added yet. Please add a project above.")
