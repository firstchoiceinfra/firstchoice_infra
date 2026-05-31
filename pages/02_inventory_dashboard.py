import streamlit as st
import datetime

# हमने CSS का झंझट हटा दिया है ताकि Light/Dark mode दोनों में परफेक्ट दिखे

if not st.session_state.get('logged_in'): st.stop()

# डेटा का बेस सेट करना
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.title("📊 Inventory Dashboard")

if not st.session_state.projects:
    st.warning("कोई प्रोजेक्ट नहीं मिला। कृपया Admin Panel से प्रोजेक्ट जोड़ें।")
else:
    proj_list = list(st.session_state.projects.keys())
    current_proj = st.selectbox("Select Project", proj_list)
    
    data = st.session_state.projects[current_proj]
    st.write(f"**KH:** {data.get('khasra', '')} | **PH:** {data.get('ph_no', '')} | **Mauza:** {data.get('mauza', '')}")

    # प्लॉट ग्रिड
    cols = st.columns(5)
    total_plots = data.get('total_plots', 0)
    
    for i in range(1, total_plots + 1):
        key = f"{current_proj}_{i}"
        status = st.session_state.plot_status.get(key, "Available")
        
        # 🟢 और 🔴 Emojis का उपयोग, जो कभी गायब नहीं होंगे
        if status == "Available":
            btn_label = f"🟢 Plot {i}\n(Available)"
        else:
            btn_label = f"🔴 Plot {i}\n(Booked)"
            
        if cols[i%5].button(btn_label, key=key):
            st.session_state.selected_plot = i
            st.rerun()

    # बुकिंग फॉर्म या हिस्ट्री
    if 'selected_plot' in st.session_state:
        p_idx = st.session_state.selected_plot
        key = f"{current_proj}_{p_idx}"
        
        if st.session_state.plot_status.get(key) == "Booked":
            st.subheader(f"🔴 Plot {p_idx} History")
            b = st.session_state.bookings.get(key, {})
            st.write(f"**Client:** {b.get('c_name')} | **Exec:** {b.get('exec_name')}")
            st.write(f"**Amount Received:** ₹{b.get('received_amt')} on {b.get('recv_date')}")
            if st.button("🖨️ Print"): st.write("Print feature in progress...")
            if st.button("💬 WhatsApp"): st.write(f"WhatsApp initiated for {b.get('phone')}")
        else:
            st.subheader(f"🟢 Booking Form - Plot {p_idx}")
            with st.form("booking_form"):
                c1, c2 = st.columns(2)
                with c1:
                    c_name = st.text_input("Client Name"); phone = st.text_input("Phone")
                    addr = st.text_area("Address"); adhar = st.text_input("Aadhar")
                    pan = st.text_input("PAN"); nominee = st.text_input("Nominee Name")
                with c2:
                    area = st.number_input("Area (Sqft)"); comp_rate = st.number_input("Company Rate")
                    sell_rate = st.number_input("Selling Rate"); exec_name = st.text_input("Executive Name")
                    recv_date = st.date_input("Received Date"); received_amt = st.number_input("Received Amount")
                
                if st.form_submit_button("Save Booking"):
                    st.session_state.plot_status[key] = "Booked"
                    st.session_state.bookings[key] = {
                        "c_name": c_name, "phone": phone, "received_amt": received_amt, 
                        "recv_date": recv_date, "exec_name": exec_name
                    }
                    st.success("Booking Saved!")
                    st.rerun()
