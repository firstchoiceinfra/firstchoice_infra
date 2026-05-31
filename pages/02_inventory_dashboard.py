import streamlit as st
import datetime

# --- CSS फॉर कलर्स (Green = Available, Red = Booked) ---
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }
    .available-btn { background-color: #28a745 !important; }
    .booked-btn { background-color: #dc3545 !important; }
    </style>
""", unsafe_allow_html=True)

if not st.session_state.get('logged_in'): st.stop()
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.title("📊 Inventory Dashboard")

# 1. प्रोजेक्ट सिलेक्शन
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
    
    # CSS क्लास सिलेक्ट करना
    btn_class = "available-btn" if status == "Available" else "booked-btn"
    
    # बटन्स का रेंडरिंग
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
        st.write(f"**Total Received:** ₹{b.get('received_amt')} on {b.get('recv_date')}")
        if st.button("🖨️ Print"): st.write("Generating print...")
        if st.button("💬 WhatsApp"): st.write(f"https://wa.me/{b.get('phone')}")
    else:
        st.subheader(f"Booking Form - Plot {p_idx}")
        with st.form("booking_form"):
            c1, c2 = st.columns(2)
            with c1:
                c_name = st.text_input("Client Name"); dob = st.date_input("DOB"); phone = st.text_input("Phone")
                addr = st.text_area("Address"); adhar = st.text_input("Aadhar"); pan = st.text_input("PAN")
                nominee = st.text_input("Nominee"); nom_age = st.number_input("Nominee Age")
            with c2:
                area = st.number_input("Area (Sqft)"); comp_rate = st.number_input("Company Rate")
                sell_rate = st.number_input("Selling Rate"); tah = st.text_input("Tahsil")
                dist = st.text_input("District"); exec_name = st.text_input("Executive Name")
                pay_mode = st.selectbox("Mode", ["Cash", "Cheque", "Online"])
                recv_date = st.date_input("Received Date") # यह रहा नया कॉलम
                token = st.number_input("Token"); received_amt = st.number_input("Received Amount")
                tx_id = st.text_input("Transaction ID")
            
            if st.form_submit_button("Save Booking"):
                st.session_state.plot_status[key] = "Booked"
                st.session_state.bookings[key] = {
                    "c_name": c_name, "phone": phone, "received_amt": received_amt, 
                    "exec_name": exec_name, "recv_date": recv_date
                }
                st.success("Booking Saved!")
                st.rerun()
