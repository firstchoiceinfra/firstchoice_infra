
import streamlit as st

if not st.session_state.get('logged_in'): st.stop()

st.title("📊 Inventory Dashboard")

# प्रोजेक्ट का सिलेक्शन
for p_name in st.session_state.projects.keys():
    if st.button(f"Open: {p_name}"):
        st.session_state.current_proj = p_name

if 'current_proj' in st.session_state:
    st.subheader(f"Project: {st.session_state.current_proj}")
    
    # प्लॉट ग्रिड
    cols = st.columns(5)
    total = st.session_state.projects[st.session_state.current_proj]['total_plots']
    
    for i in range(1, total + 1):
        # यहाँ हम स्टेटस चेक करेंगे (अभी के लिए डिफॉल्ट Available)
        if cols[i%5].button(f"Plot {i}"):
            st.session_state.selected_plot = i
            st.rerun()

    # बुकिंग फॉर्म - जो प्लॉट चुनने पर ही दिखेगा
    if 'selected_plot' in st.session_state:
        st.markdown("---")
        st.subheader(f"Booking Form - Plot {st.session_state.selected_plot}")
        with st.form("booking_form"):
            c_name = st.text_input("Client Name")
            phone = st.text_input("Phone Number")
            adhar = st.text_input("Aadhar No")
            rate = st.number_input("Selling Rate")
            
            if st.form_submit_button("Confirm Booking"):
                st.success(f"Plot {st.session_state.selected_plot} booked for {c_name}!")
                # यहाँ हम इस बुकिंग को सेव करेंगे
