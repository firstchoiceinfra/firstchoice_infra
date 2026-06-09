import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")

# ऑटो-सिंक के लिए पार्टनर लिस्ट और प्रोजेक्ट्स
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

search_exec = st.selectbox("🔎 Select Executive", exec_list)
start_date = st.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger"):
    statement_rows = []
    # लूपिंग - प्रोजेक्ट्स ढूंढना
    for p_name in project_names:
        plots = db_data[p_name].get('plots', {})
        for plot_id, info in plots.items():
            if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                # यहाँ कैलकुलेशन का हिस्सा डालें
                statement_rows.append({"Client": info.get('customer_name'), "Paid": info.get('token_amount', 0), "Date": "2026-06-09"})
    
    if statement_rows:
        df = pd.DataFrame(statement_rows)
        st.dataframe(df, use_container_width=True)
        st.metric("🏆 Total Net Payable", f"₹ {df['Paid'].sum():,.2f}")
    else:
        st.info("कोई बुकिंग नहीं मिली। कृपया सुनिश्चित करें कि स्टेटस 'booked' (lowercase) लिखा है।")
