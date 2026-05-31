import streamlit as st
import datetime

# --- CSS फॉर कलर्स ---
st.markdown("""
    <style>
    div.stButton > button { width: 100%; color: white !important; font-weight: bold !important; border: none !important; }
    .available-btn { background-color: #28a745 !important; }
    .booked-btn { background-color: #dc3545 !important; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get('logged_in'): st.stop()

# डेटा की सुरक्षा के लिए चेक
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.title("📊 Inventory Dashboard")

# 1. प्रोजेक्ट सिलेक्शन (Safety Check)
if not st.session_state.projects:
    st.warning("No projects found. Please add a project in the Admin Panel first.")
else:
    proj_list = list(st.session_state.projects.keys())
    current_proj = st.selectbox("Select Project", proj_list)
    st.session_state.current_proj = current_proj

    data = st.session_state.projects[current_proj]
    st.info(f"KH: {data['khasra']} | PH: {data['ph_no']} | Mauza: {data['mauza']}")

    # 2. प्लॉट ग्रिड
    cols = st.columns(5)
    for i in range(1, data['total_plots'] + 1):
        key = f"{current_proj}_{i}"
        status = st.session_state.plot_status.get(key, "Available")
        
        # बटन स्टाइलिंग
        btn_style = "available-btn" if status == "Available" else "booked-btn"
        
        if cols[i%5].button(f"Plot {i}\n({status})", key=key):
            st.session_state.selected_plot = i
            st.rerun()

    # 3. बुकिंग या हिस्ट्री
    if 'selected_plot' in st.session_state:
        p_idx = st.session_state.selected_plot
        key = f"{current_proj}_{p_idx}"
        
        if st.session_state.plot_status.get(key) == "Booked":
            st.subheader(f"Plot {p_idx} History")
            b = st.session_state.bookings.get(key, {})
            st.write(f"**Client:** {b.get('c_name')} | **Exec:** {b.get('exec_name')}")
            st.write(f"**Received:** ₹{b.get('received_amt')} on {b.get('recv_date')}")
            if st.button("🖨️ Print"): st.write("Generating print...")
            if st.button("💬 WhatsApp"): st.write(f"WhatsApp link for {b.get('phone')}")
        else:
            st.subheader(f"Booking Form - Plot {p_idx}")
            with st.form("booking_form"):
                # (आपका वही बुकिंग फॉर्म)
                c_name = st.text_input("Client Name")
                received_amt = st.number_input("Received Amount")
                recv_date = st.date_input("Received Date")
                exec_name = st.text_input("Executive Name")
                
                if st.form_submit_button("Save Booking"):
                    st.session_state.plot_status[key] = "Booked"
                    st.session_state.bookings[key] = {
                        "c_name": c_name, "received_amt": received_amt, 
                        "recv_date": recv_date, "exec_name": exec_name
                    }
                    st.success("Booking Saved!")
                    st.rerun()
