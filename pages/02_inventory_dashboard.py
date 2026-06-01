import streamlit as st
import datetime
import database 
# 👈 पेज खुलते ही डेटाबेस से सारे प्रोजेक्ट और बुकिंग लोड करना
database.init_db()

if not st.session_state.get('logged_in'): st.stop()

st.markdown("## 🌈 Inventory & Booking Dashboard")

if not st.session_state.projects:
    st.error("🚨 कोई प्रोजेक्ट नहीं मिला। कृपया Admin Panel से प्रोजेक्ट जोड़ें।")
else:
    proj_list = list(st.session_state.projects.keys())
    current_proj = st.selectbox("📌 Select Project", proj_list)
    
    data = st.session_state.projects[current_proj]
    st.info(f"**🏢 {current_proj}** | **KH:** {data.get('khasra', '')} | **PH:** {data.get('ph_no', '')} | **Mauza:** {data.get('mauza', '')}")
    
    st.write("---")

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

    if 'selected_plot' in st.session_state:
        p_idx = st.session_state.selected_plot
        key = f"{current_proj}_{p_idx}"
        
        st.write("---") 

        if st.session_state.plot_status.get(key) == "Booked":
            st.subheader(f"🔴 Plot {p_idx} - Booking History", divider="red")
            b = st.session_state.bookings.get(key, {})
            
            c1, c2, c3 = st.columns(3)
            c1.metric("👤 Client Name", b.get('c_name', '-'))
            c2.metric("💰 Received Amt", f"₹{b.get('received_amt', 0)}")
            c3.metric("👔 Executive", b.get('exec_name', '-'))
            
            st.success(f"**💳 Payment:** Mode: {b.get('pay_mode')} | TX ID: {b.get('tx_id')} | Date: {b.get('recv_date')}")
            
            if b.get('exec_discount_penalty', 0) > 0:
                st.error(f"**💡 Discount Deducted from Exec:** ₹{b.get('exec_discount_penalty')}")
            
            c4, c5 = st.columns(2)
            if c4.button("🖨️ Print Receipt", use_container_width=True): st.write("Printing...")
            if c5.button("💬 Send to WhatsApp", use_container_width=True): st.write(f"WhatsApp initiated...")

        else:
            st.subheader(f"🟢 Booking Form - Plot {p_idx}", divider="green")
            
            with st.form("booking_form"):
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

                st.markdown("#### 🏡 Plot Details")
                c3, c4 = st.columns(2)
                area = c3.number_input("Plot Area (Sqft)")
                comp_rate = c4.number_input("Company Rate")
                sell_rate = c3.number_input("Selling Rate")
                
                st.info(f"💡 **Discount Given per Sqft:** ₹{int(comp_rate - sell_rate) if comp_rate else 0}")
                
                tah = c3.text_input("Tahsil")
                dist = c4.text_input("District")
                exec_name = c4.text_input("Executive Name")

                st.markdown("#### 💳 Payment Details")
                c5, c6 = st.columns(2)
                pay_mode = c5.selectbox("Payment Mode", ["Cash", "Cheque", "Online (UPI/RTGS)"])
                token = c6.number_input("Token Amount")
                received_amt = c5.number_input("Total Received Amount")
                recv_date = c6.date_input("Received Date")
                tx_id = c5.text_input("Transaction ID / Cheque No")
                
                submit = st.form_submit_button("✅ Save Booking", use_container_width=True)
                
                if submit:
                    total_discount = 0
                    if comp_rate > sell_rate and area > 0:
                        total_discount = (comp_rate - sell_rate) * area

                    st.session_state.plot_status[key] = "Booked"
                    
                    st.session_state.bookings[key] = {
                        "c_name": c_name, "phone": phone, "area": area,
                        "comp_rate": comp_rate, "sell_rate": sell_rate,
                        "pay_mode": pay_mode, "token": token,
                        "received_amt": received_amt, "recv_date": recv_date, 
                        "tx_id": tx_id, "exec_name": exec_name,
                        "exec_discount_penalty": total_discount,
                        "payment_history": [{
                            "amount": received_amt,
                            "date": recv_date,
                            "mode": pay_mode,
                            "tx_id": tx_id
                        }]
                    }
                    
                    # 👈 सबसे ज़रूरी लाइन: बुकिंग सेव होते ही फाइल में लॉक करना
                    database.save_db()
                    
                    st.success("🎉 शानदार! बुकिंग सफलतापूर्वक सेव हो गई।")
                    st.rerun()
