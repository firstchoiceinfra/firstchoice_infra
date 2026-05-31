
import streamlit as st

if not st.session_state.get('logged_in'): st.stop()

st.title("🏗️ Project & Executive Management")

with st.expander("➕ Add New Project"):
    # नए फील्ड्स के साथ फॉर्म
    p_name = st.text_input("Project Name")
    khasra = st.text_input("Khasra No")
    ph_no = st.text_input("PH No")
    mauza = st.text_input("Mauza")
    total_plots = st.number_input("Total Plots", min_value=1)
    
    if st.button("Save Project"):
        # प्रोजेक्ट को पूरी जानकारी के साथ सेव करें
        st.session_state.projects[p_name] = {
            "khasra": khasra,
            "ph_no": ph_no,
            "mauza": mauza,
            "total_plots": total_plots
        }
        # प्लॉट स्टेटस को भी इनिशियलाइज़ करें
        st.session_state.plot_status = st.session_state.get('plot_status', {})
        for i in range(1, total_plots + 1):
            st.session_state.plot_status[f"{p_name}_{i}"] = "Available"
            
        st.success(f"Project '{p_name}' saved successfully with all details!")
