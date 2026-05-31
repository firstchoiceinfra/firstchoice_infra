import streamlit as st
import datetime

if not st.session_state.get('logged_in'): st.stop()

# डेटा का बेस सेट करना
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'plot_status' not in st.session_state: st.session_state.plot_status = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.markdown("## 🌈 Inventory & Booking Dashboard")

if not st.session_state.projects:
    st.error("🚨 कोई प्रोजेक्ट नहीं मिला। कृपया Admin Panel से प्रोजेक्ट जोड़ें।")
else:
    proj_list = list(st.session_state.projects.keys())
    current_proj = st.selectbox("📌 Select Project", proj_list)
    
    data = st.session_state.projects[current_proj]
    # कलरफुल प्रोजेक्ट हेडर
    st.info(f"**🏢 {current_proj}** | **KH:** {data.get('khasra', '')} | **PH:** {data.get('ph_no', '')} | **Mauza:** {data.get('mauza', '')}")
    
    st.write("---")

    # प्लॉट ग्रिड
    cols = st.columns(5)
    total_plots = data.get('total_plots', 0)
    
    for i in range(1, total_plots + 1):
        key = f"{current_proj}_{i}"
        status = st.session_state.plot_status.get(key, "Available")
        
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
        
        st.write("---") # पेज को बांटने के लिए लाइन

        if st.session_state.plot_status.get(key) == "Booked":
            # लाल रंग की लाइन के साथ कलरफुल हिस्ट्री हेडर
            st.subheader(f"🔴 Plot {p_idx} - Booking History", divider="red")
            b = st.session_state.bookings.get(key, {})
            
            # डैशबोर्ड स्टाइल में डिटेल्स दिखाना
            c1, c2, c3 = st.columns(3)
            c1.metric("👤 Client Name", b.get('c_name', '-'))
            c2.metric("💰 Received Amt", f"₹{b.get('received_amt', 0)}")
            c3.metric("👔 Executive", b.get('exec_name', '-'))
            
            st.success(f"**💳 Payment:** Mode: {b.get('pay_mode')} | TX ID: {b.get('tx_id')} | Date: {b.get('recv_date')}")
            
            c4, c5 = st.columns(2)
            if c4.button("🖨️ Print Receipt", use_container_width=True): st.write("Printing...")
            if c5.button("💬 Send to WhatsApp", use_container_width=True): st.write(f"WhatsApp initiated for {b.get('phone')}")

        else:
            # हरे रंग की लाइन के साथ कलरफुल फॉर्म हेडर
            st.subheader(f"🟢 Booking Form - Plot {p_idx}", divider="green")
            
            with st.form("booking_form"):
                # सेक्शन 1: क्लाइंट डिटेल्स
                st.markdown("#### 👤 Client Details")
                c1, c2 = st.columns(2)
                c_name = c1.text_input("Client Name")
                dob = c2.date_input("Date of Birth")
                phone = c1.text_input("Phone No")
                addr = c2.text_area("Client Address")
                adhar = c1.text_input("Aadhar No")
                pan = c2.text_input("PAN No")
                nominee = c1.text_input("Nominee Name")
                nom_age = c2.number_input("Nominee Age", min_value=0, max_value=100)

                # सेक्शन 2: प्लॉट डिटेल्स
                st.markdown("#### 🏡 Plot Details")
                c3, c4 = st.columns(2)
                area = c3.number_input("Plot Area (Sqft)")
                comp_rate = c4.number_input("Company Rate")
                sell_rate = c3.number_input("Selling Rate")
                
                # डिस्काउंट कैलकुलेशन नीले बक्से में
                st.info(f"💡 **Discount Given:** ₹{int(comp_rate - sell_rate) if comp_rate else 0}")
                
                tah = c3.text_input("Tahsil")
                dist = c4.text_input("District")
                exec_name = c4.text_input("Executive Name")

                # सेक्शन 3: पेमेंट डिटेल्स
                st.markdown("#### 💳 Payment Details")
                c5, c6 = st.columns(2)
                pay_mode = c5.selectbox("Payment Mode", ["Cash", "Cheque", "Online (UPI/RTGS)"])
                token = c6.number_input("Token Amount")
                received_amt = c5.number_input("Total Received Amount")
                recv_date = c6.date_input("Received Date")
                tx_id = c5.text_input("Transaction ID / Cheque No")
                
                st.write("") # थोड़ा स्पेस देने के लिए
                submit = st.form_submit_button("✅ Save Booking", use_container_width=True)
                
                if submit:
                    st.session_state.plot_status[key] = "Booked"
                    st.session_state.bookings[key] = {
                        "c_name": c_name, "phone": phone, "area": area,
                        "pay_mode": pay_mode, "token": token,
                        "received_amt": received_amt, "recv_date": recv_date, 
                        "tx_id": tx_id, "exec_name": exec_name
                    }
                    st.success("🎉 शानदार! बुकिंग सफलतापूर्वक सेव हो गई।")
                    st.balloons() # बुकिंग होने पर गुब्बारे उड़ेंगे!
                    st.rerun()
