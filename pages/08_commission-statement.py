import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(layout="wide", page_title="Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger"):
    statement_rows = []
    s_no = 1
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for plot_id, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    amt = float(info.get('token_amount', 0))
                    gross = amt * 0.05 # यहाँ आप स्लैब लॉजिक लगा सकते हैं
                    statement_rows.append({"S.No.": s_no, "Client": info.get('customer_name', 'N/A'), "Paid Amt (₹)": amt, "Gross (₹)": gross, "Net Payout (₹)": gross * 0.98})
                    s_no += 1
    
    if statement_rows:
        df = pd.DataFrame(statement_rows)
        st.dataframe(df, use_container_width=True)
        st.metric("🏆 Grand Net Payable", f"₹ {df['Net Payout (₹)'].sum():,.2f}")
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 Export CSV", csv, "Statement.csv", "text/csv")
    else:
        st.info("कोई बुकिंग नहीं मिली।")
