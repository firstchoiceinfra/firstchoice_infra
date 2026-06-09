import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(layout="wide", page_title="Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")

# पार्टनर सिलेक्ट करें
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger", use_container_width=True):
    # पार्टनर की स्लैब जानकारी निकालें
    partner_profile = exec_data_root.get(search_exec, {})
    p_pct = float(partner_profile.get('percentage_exec', 0))
    p_fixed = float(partner_profile.get('rupees_exec', 0))
    
    rows = []
    s_no = 1
    
    # इन्वेंटरी डैशबोर्ड से डेटा उठाएं
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                
                # चेक करें कि यह प्लॉट इसी एग्जीक्यूटिव का है
                if str(info.get('executive_name', '')).lower() == search_exec.lower() and str(info.get('status', '')).lower() == 'booked':
                    
                    # प्लॉट की डिटेल्स
                    area = float(info.get('plot_area', 1))
                    comp_rate = float(info.get('company_rate', p_info.get('base_rate', 700)))
                    discount = float(info.get('discount', 0))
                    
                    # पेमेंट हिस्ट्री
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            # ग्रॉस कमीशन (स्लैब के हिसाब से)
                            gross = (pmt['amt'] * p_pct) / 100
                            # डिस्काउंट का असर (ग्रॉस से माइनस)
                            net_comm = max(0, gross - discount)
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            
                            rows.append({
                                "S.No.": s_no, "Customer": info.get('customer_name', 'N/A'), 
                                "Plot": pid, "Mauza": p_info.get('mauza', 'N/A'),
                                "Received Amt": pmt['amt'], "Date": pmt['date'], 
                                "Gross": gross, "Discount": discount, 
                                "Net Comm": net_comm, "TDS (2%)": tds, "Net In Hand": in_hand
                            })
                            s_no += 1
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        # टोटल्स
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Gross", f"₹ {df['Gross'].sum():,.2f}")
        c2.metric("Total Discount", f"₹ {df['Discount'].sum():,.2f}")
        c3.metric("Total TDS", f"₹ {df['TDS (2%)'].sum():,.2f}")
        c4.metric("🏆 Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
    else:
        st.info("इस एग्जीक्यूटिव के नाम पर कोई बुकिंग रिकॉर्ड नहीं मिला।")

