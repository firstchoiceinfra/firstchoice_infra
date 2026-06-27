import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 SECURITY
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get('executives', {})

# 🔍 1. पार्टनर की पूरी चेन ढूँढने का फंक्शन
def get_downline_info(manager_name, exec_dict):
    """पार्टनर और उसकी पूरी डाउनलाइन + उनके कमीशन % का मैप बनाता है"""
    chain = {}
    manager_clean = str(manager_name).strip().lower()
    
    # चेन बनाएं
    def build_chain(name):
        res = [name.lower()]
        for ex, det in exec_dict.items():
            if str(det.get('senior_name', '')).strip().lower() == name.lower():
                res.extend(build_chain(ex))
        return res
        
    team_list = build_chain(manager_clean)
    
    # कमीशन % मैप करें
    for name in team_list:
        details = exec_dict.get(name, {})
        # यहाँ आपके पार्टनर मैनेजमेंट के 'percentage_exec' का इस्तेमाल हो रहा है
        chain[name] = float(details.get('percentage_exec', 0))
    return chain

# 2. UI
st.title("📊 Master Sync Commission Dashboard")
partner_names = sorted(list(exec_data.keys()))
search_exec = st.selectbox("👤 Select Senior/Admin", options=partner_names)
start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Sync Statement"):
    # पार्टनर का अपना कमीशन %
    my_perc = float(exec_data.get(search_exec, {}).get('percentage_exec', 23))
    # पूरी टीम और उनका %
    team_map = get_downline_info(search_exec, exec_data)
    
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    exec_name = str(info.get('executive_name', '')).strip().lower()
                    
                    if exec_name in team_map:
                        # EMI & Token Calculation (Date Range Sync)
                        total_amt = 0.0
                        # 1. Token Check
                        b_date = datetime.datetime.strptime(str(info.get('booking_date', '2000-01-01')), "%Y-%m-%d").date()
                        if start_d <= b_date <= end_d:
                            total_amt += float(info.get('token_amount', 0))
                        
                        # 2. EMI Check
                        for pmt in info.get('partial_payments', []):
                            p_date = datetime.datetime.strptime(str(pmt.get('date', '2000-01-01')), "%Y-%m-%d").date()
                            if start_d <= p_date <= end_d:
                                total_amt += float(pmt.get('amount', 0))
                        
                        if total_amt > 0:
                            # डिफरेंस कमीशन कैलकुलेशन
                            junior_perc = team_map[exec_name]
                            diff = max(0, my_perc - junior_perc) # अगर सीनियर का % ज्यादा है
                            
                            rows.append({
                                "Project": p_name, "Plot": pid, "Member": exec_name.upper(),
                                "Total Collection": total_amt,
                                "Comm % (Diff)": f"{diff}%",
                                "Difference Amount (₹)": (total_amt * diff) / 100
                            })
    
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.error("❌ कोई बिज़नेस डेटा नहीं मिला।")

