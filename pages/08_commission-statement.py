import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")

# 1. एग्जीक्यूटिव और प्रोजेक्ट्स लोड करना
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

# 2. इनपुट फिल्टर्स
col1, col2, col3 = st.columns(3)
search_exec = col1.selectbox("🔎 Select Executive", exec_list)
start_date = col2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = col3.date_input("📅 End Date", datetime.date.today())

# 3. जनरेट बटन और लूप
if st.button("🔍 Generate Comprehensive Ledger", use_container_width=True):
    statement_rows = []
    s_no = 1
    
    for p_name in project_names:
        p_info = db_data[p_name]
        plots = p_info.get('plots', {})
        # अगर plots लिस्ट है तो उसे डिक्शनरी में बदलें (पुराने स्ट्रक्चर के लिए)
        if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
        
        for plot_id, info in plots.items():
            if isinstance(info, dict):
                # यहाँ स्टेटस चेक करें - अगर 'booked' नहीं दिख रहा है, तो यहाँ 'Booked' या 'SOLD' लिख कर देखें
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    
                    # पेमेंट डिटेल्स उठाना
                    b_date = info.get('booking_date', datetime.date.today().strftime("%Y-%m-%d"))
                    amt = float(info.get('token_amount', 0))
                    
                    # कैलकुलेशन (Gross, TDS, Net)
                    gross = amt * 0.05 # यहाँ अपना % स्लैब का लॉजिक लगाएं
                    tds = gross * 0.02
                    
                    statement_rows.append({
                        "S.No.": s_no, "Client": info.get('customer_name', 'N/A'), 
                        "Plot": plot_id, "Paid": amt, "Gross (₹)": gross, 
                        "TDS (₹)": tds, "Net Payout (₹)": gross - tds
                    })
                    s_no += 1

    # 4. रिजल्ट दिखाना
    if statement_rows:
        df = pd.DataFrame(statement_rows)
        st.dataframe(df, use_container_width=True)
        t_net = df['Net Payout (₹)'].sum()
        st.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
    else:
        st.warning("कोई बुकिंग नहीं मिली। कृपया सुनिश्चित करें कि स्टेटस 'booked' ही है और एग्जीक्यूटिव का नाम सही है।")

