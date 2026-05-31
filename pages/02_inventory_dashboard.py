import streamlit as st

# --- CSS फॉर कलर्स (Green/Red) ---
st.markdown("""
    <style>
    /* Available बटन ग्रीन */
    div.stButton > button {
        background-color: #28a745 !important;
        color: white !important;
        width: 100%;
    }
    /* बुक होने पर रेड (इसे हम 'booked' क्लास मानेंगे) */
    .booked-btn {
        background-color: #dc3545 !important;
    }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get('logged_in'): st.stop()

st.title("📊 Inventory Dashboard")

# प्रोजेक्ट का सिलेक्शन
for p_name in st.session_state.projects.keys():
    if st.button(f"Open: {p_name}", key=p_name):
        st.session_state.current_proj = p_name

if 'current_proj' in st.session_state:
    proj_name = st.session_state.current_proj
    data = st.session_state.projects[proj_name]
    
    st.subheader(f"Project: {proj_name}")
    st.info(f"**Khasra No:** {data['khasra']} | **PH No:** {data['ph_no']} | **Mauza:** {data['mauza']}")
    
    total = data['total_plots']
    if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
    
    cols = st.columns(5)
    for i in range(1, total + 1):
        key = f"{proj_name}_{i}"
        status = st.session_state.plot_status.get(key, "Available")
        
        # स्टेटस के अनुसार लेबल
        label = f"Plot {i}\n({status})"
        
        # अगर बटन दबाया
        if cols[i%5].button(label, key=key):
            st.session_state.selected_plot = i
            st.rerun()

    # बुकिंग फॉर्म - अगर प्लॉट सेलेक्ट हुआ है
    if 'selected_plot' in st.session_state:
        plot_idx = st.session_state.selected_plot
        key = f"{proj_name}_{plot_idx}"
        
        if st.session_state.plot_status.get(key) == "Booked":
            st.warning(f"Plot {plot_idx} is already Booked!")
        else:
            st.subheader(f"Booking Form: Plot {plot_idx}")
            with st.form("booking_form"):
                col1, col2 = st.columns(2)
                with col1:
                    c_name = st.text_input("Client Name")
                    phone = st.text_input("Phone No")
                with col2:
                    adhar = st.text_input("Aadhar No")
                    pay_mode = st.selectbox("Payment Mode", ["Cash", "Cheque", "Online"])
                
                if st.form_submit_button("Confirm Booking"):
                    st.session_state.plot_status[key] = "Booked"
                    st.success(f"Plot {plot_idx} booked successfully!")
                    st.rerun()
