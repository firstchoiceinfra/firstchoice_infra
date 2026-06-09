import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
start = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = st.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger"):
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    # टोकन और इंस्टॉलमेंट्स
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0))}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0))})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = pmt['amt'] * 0.05 # अपना स्लैब लॉजिक यहाँ रखें
                            tds = gross * 0.02
                            rows.append({"Client": info.get('customer_name'), "Plot": pid, "Type": pmt['type'], "Paid Amt (₹)": pmt['amt'], "Gross (₹)": gross, "Net Payout (₹)": gross - tds})
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.metric("🏆 Grand Net Payable", f"₹ {df['Net Payout (₹)'].sum():,.2f}")
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Export CSV", csv, "Statement.csv", "text/csv")
    else:
        st.info("डेटा सिंक है, लेकिन बुकिंग नहीं मिली।")
