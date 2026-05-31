import streamlit as st

if not st.session_state.get('logged_in'): st.stop()

st.title("📊 Inventory Dashboard")

# प्रोजेक्ट का सिलेक्शन
for p_name in st.session_state.projects.keys():
    if st.button(f"Open: {p_name}"):
        st.session_state.current_proj = p_name

if 'current_proj' in st.session_state:
    proj_name = st.session_state.current_proj
    data = st.session_state.projects[proj_name]
    
    # प्रोजेक्ट की जानकारी को हेडिंग में दिखाना
    st.subheader(f"Project: {proj_name}")
    st.info(f"**Khasra No:** {data['khasra']} | **PH No:** {data['ph_no']} | **Mauza:** {data['mauza']}")
    
    # प्लॉट ग्रिड
    total = data['total_plots']
    cols = st.columns(5)
    
    if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
    
    for i in range(1, total + 1):
        key = f"{proj_name}_{i}"
        status = st.session_state.plot_status.get(key, "Available")
        
        # बटन का लेबल
        label = f"Plot {i}\n({status})"
        if cols[i%5].button(label):
            st.session_state.selected_plot = i
            st.rerun()

    # बुकिंग या हिस्ट्री सेक्शन
    if 'selected_plot' in st.session_state:
        # यहाँ आगे हिस्ट्री और बुकिंग फॉर्म का कोड जुड़ेगा
        st.write(f"Selected: Plot {st.session_state.selected_plot}")
