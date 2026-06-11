import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Commission Statement")

# सिलेक्शन पैनल
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Business Partner", exec_list)
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    rows = []
    s_no = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    
                    # बेसिक कैलकुलेशन
                    comp_rate = float(info.get('company_rate', p_info.get('base_rate', 700)))
                    discount_sqft = float(info.get('discount', 0))
                    
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    # (यहाँ पेमेंट लॉजिक जारी रखें...)
                    
                    rows.append({
                        "S.No.": s_no, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, 
                        "Received Amt": 0, "Gross": 100, "Net": 98 
                    })
                    s_no += 1
    
    # डेटा को सेव करें ताकि ब्लैंक न आए
    st.session_state.df_view = pd.DataFrame(rows)

# डेटा दिखाएं
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    st.dataframe(st.session_state.df_view, use_container_width=True)
else:
    st.info("डेटा लोड करने के लिए बटन दबाएं।")

