import streamlit as st
import pandas as pd
import datetime

if not st.session_state.get('logged_in'): st.stop()

# डेटाबेस इनिशियलाइज़ेशन
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.markdown("## 📚 Master Ledger & EMI Management")

# -------------------------------------------------------------
# डेटाबेस माइग्रेशन (पुराने डेटा को नए EMI सिस्टम में ढालना)
# -------------------------------------------------------------
for b_key, b_val in st.session_state.bookings.items():
    if "payment_history" not in b_val:
        # अगर पुरानी बुकिंग है, तो पहले पेमेंट को हिस्ट्री का हिस्सा बना देंगे
        b_val["payment_history"] = [{
            "amount": float(b_val.get("received_amt", 0)),
            "date": b_val.get("recv_date", datetime.date.today()),
            "mode": b_val.get("pay_mode", "N/A"),
            "tx_id": b_val.get("tx_id", "N/A")
        }]

if not st.session_state.projects:
    st.error("🚨 कोई प्रोजेक्ट नहीं मिला। कृपया Admin Panel से प्रोजेक्ट जोड़ें।")
else:
    # -------------------------------------------------------------
    # सेक्शन 1: प्रोजेक्ट सिलेक्शन
    # -------------------------------------------------------------
    proj_list = list(st.session_state.projects.keys())
    current_proj = st.selectbox("📌 Select Project to View Ledger", proj_list)
    
    data = st.session_state.projects[current_proj]
    
    st.info(f"**🏢 Project:** {current_proj} | **Mauza:** {data.get('mauza', 'N/A')} | **KH:** {data.get('khasra', 'N/A')} | **PH:** {data.get('ph_no', 'N/A')} | **Total Plots:** {data.get('total_plots', 0)}")
    
    st.write("---")

    # -------------------------------------------------------------
    # सेक्शन 2: लेजर टेबल जनरेट करना
    # -------------------------------------------------------------
    st.subheader(f"📊 Ledger Statement - {current_proj}", divider="green")
    
    ledger_data = []
    booked_plots_in_proj = []
    sr_no = 1
    total_project_collection = 0

    for b_key, b_val in st.session_state.bookings.items():
        if "_" in b_key:
            proj_name, plot_no = b_key.rsplit("_", 1)
            
            if proj_name == current_proj:
                booked_plots_in_proj.append(plot_no) # बाद में EMI ऐड करने के लिए लिस्ट बना रहे हैं
                
                # पूरी पेमेंट हिस्ट्री का जोड़ (Total) और हिस्ट्री टेक्स्ट बनाना
                total_received = 0
                history_text = ""
                
                for payment in b_val.get("payment_history", []):
                    amt = float(payment.get("amount", 0))
                    total_received += amt
                    # डेट और अमाउंट को एक लाइन में जोड़ना
                    p_date = payment.get('date')
                    date_str = p_date.strftime('%d-%m-%Y') if isinstance(p_date, datetime.date) else p_date
                    history_text += f"₹{amt} ({date_str}) | "

                total_project_collection += total_received
                
                sell_rate = b_val.get("sell_rate", "N/A") 
                
                ledger_data.append({
                    "Sr.": sr_no,
                    "Plot No": plot_no,
                    "Client Name": b_val.get("c_name", "N/A"),
                    "Area (Sqft)": b_val.get("area", 0),
                    "Selling Rate": f"₹{sell_rate}" if sell_rate != "N/A" else "N/A",
                    "Payment History (Date Wise)": history_text.strip(" | "), # सारी पेमेंट्स एक ही कॉलम में दिखेंगी
                    "Total Received": f"₹{total_received}"
                })
                sr_no += 1

    # लेजर टेबल दिखाना
    if ledger_data:
        df_ledger = pd.DataFrame(ledger_data)
        st.dataframe(df_ledger, use_container_width=True, hide_index=True)
        st.success(f"### 💰 Total Collection from {current_proj}: ₹{total_project_collection}")
        
        c1, c2, c3 = st.columns([1, 1, 2])
        csv = df_ledger.to_csv(index=False).encode('utf-8')
        c1.download_button("📥 Download Excel", data=csv, file_name=f"{current_proj}_Ledger.csv", mime="text/csv", use_container_width=True)
        if c2.button("🖨️ Print Ledger", use_container_width=True): st.info("प्रिंट कमांड भेजी जा रही है...")

    else:
        st.warning(f"ℹ️ {current_proj} में अभी तक कोई प्लॉट नहीं बिका है।")

    # -------------------------------------------------------------
    # सेक्शन 3: EMI / नया पेमेंट ऐड करना (बिना नई रो बनाए)
    # -------------------------------------------------------------
    st.write("---")
    st.subheader("➕ Add EMI / Installment for Sold Plot", divider="orange")
    st.caption("यहाँ से जोड़ी गई किश्त सीधे ऊपर वाले टेबल में उसी प्लॉट के खाते में डेट के साथ जुड़ जाएगी।")
    
    if booked_plots_in_proj:
        with st.form("add_emi_form"):
            c4, c5 = st.columns(2)
            selected_plot = c4.selectbox("Select Sold Plot No.", booked_plots_in_proj)
            emi_amt = c5.number_input("Installment / EMI Amount (₹)", min_value=1.0)
            
            c6, c7, c8 = st.columns(3)
            emi_date = c6.date_input("Payment Date")
            emi_mode = c7.selectbox("Payment Mode", ["Cash", "Cheque", "Online", "NEFT/RTGS"])
            emi_txid = c8.text_input("Transaction ID / Cheque No.")
            
            if st.form_submit_button("✅ Save Installment"):
                key = f"{current_proj}_{selected_plot}"
                
                # नई पेमेंट को हिस्ट्री लिस्ट में जोड़ना
                st.session_state.bookings[key]["payment_history"].append({
                    "amount": emi_amt,
                    "date": emi_date,
                    "mode": emi_mode,
                    "tx_id": emi_txid
                })
                
                # टोटल अमाउंट को भी अपडेट कर देना
                st.session_state.bookings[key]["received_amt"] = float(st.session_state.bookings[key].get("received_amt", 0)) + emi_amt
                
                st.success(f"🎉 Plot {selected_plot} के लिए ₹{emi_amt} की किश्त सफलतापूर्वक जुड़ गई!")
                st.rerun()
    else:
        st.info("किश्त जोड़ने के लिए पहले इन्वेंट्री से कोई प्लॉट बुक करें।")
