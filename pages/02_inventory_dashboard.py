import streamlit as st

if not st.session_state.get('logged_in'): st.stop()

st.title("📊 Inventory & Booking")

# प्रोजेक्ट का सिलेक्शन
for p_name in st.session_state.projects.keys():
    if st.button(f"Open: {p_name}"):
        st.session_state.current_proj = p_name

if 'current_proj' in st.session_state:
    st.subheader(f"Project: {st.session_state.current_proj}")
    
    # प्लॉट ग्रिड
    total = st.session_state.projects[st.session_state.current_proj]['total_plots']
    cols = st.columns(5)
    for i in range(1, total + 1):
        if cols[i%5].button(f"Plot {i}"):
            st.session_state.selected_plot = i
            st.rerun()

    # पूरा बुकिंग फॉर्म
    if 'selected_plot' in st.session_state:
        st.markdown("---")
        st.subheader(f"Booking Form: Plot {st.session_state.selected_plot}")
        with st.form("full_booking_form"):
            col1, col2 = st.columns(2)
            with col1:
                c_name = st.text_input("Client Name")
                phone = st.text_input("Phone No")
                nominee = st.text_input("Nominee Name")
                area = st.number_input("Area (Sqft)")
            with col2:
                adhar = st.text_input("Aadhar No")
                pan = st.text_input("PAN No")
                rate = st.number_input("Selling Rate")
                pay_mode = st.selectbox("Payment Mode", ["Cash", "Cheque", "Online"])
            
            received_amt = st.number_input("Received Amount")
            
            if st.form_submit_button("Save Booking"):
                # डेटा सेव करने का लॉजिक (यहाँ हम इसे बाद में CSV में भेजेंगे)
                st.success(f"Plot {st.session_state.selected_plot} booked successfully!")
                st.balloons()
