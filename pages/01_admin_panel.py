import streamlit as st

if not st.session_state.get('logged_in'): st.stop()

st.title("🏗️ Project & Executive Management")

# 1. Add New Executive
with st.expander("➕ Add New Executive"):
    n = st.text_input("Executive Name")
    m = st.text_input("Mobile No")
    if st.button("Save Executive"):
        st.session_state.executives[m] = n
        st.success(f"Executive {n} saved!")

# 2. Add New Project (सारे कॉलम्स के साथ)
with st.expander("➕ Add New Project"):
    p_name = st.text_input("Project Name")
    khasra = st.text_input("Khasra No")
    ph_no = st.text_input("PH No")
    mauza = st.text_input("Mauza")
    total_plots = st.number_input("Total Plots", min_value=1, step=1)
    
    if st.button("Save Project"):
        st.session_state.projects[p_name] = {
            "khasra": khasra,
            "ph_no": ph_no,
            "mauza": mauza,
            "total_plots": total_plots
        }
        # इनवेंट्री स्टेटस इनिशियलाइज़ करना
        if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
        for i in range(1, total_plots + 1):
            st.session_state.plot_status[f"{p_name}_{i}"] = "Available"
            
        st.success(f"Project '{p_name}' saved with all details!")
