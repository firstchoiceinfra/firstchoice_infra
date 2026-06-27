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

# टीम चेन ढूँढने का फिक्स लॉजिक
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name.lower())
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

search_exec = st.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 स्कोप", ["Self", "Group"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Statement"):
    # यहाँ 'All' का ऑप्शन हटा दिया है ताकि आप कन्फ्यूज न हों
    # अब यह कोड सिर्फ 'Self' या 'Group' के लिए ही काम करेगा
    if scope == "Self":
        valid_team = [search_exec.lower()]
    else:
        valid_team = [search_exec.lower()] + get_all_downlines(search_exec)
    
    rows = []
    found = False
    
    # स्ट्रिक्ट स्कैनिंग
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    
                    booked_by = str(info.get('executive_name', '')).strip().lower()
                    
                    # अगर बुकिंग करने वाला बंदा हमारी टीम लिस्ट (valid_team) का हिस्सा है तभी आगे बढ़ो
                    if booked_by in valid_team:
                        
                        # बिज़नेस की गणना
                        amt = float(info.get('token_amount', 0))
                        for pmt in info.get('partial_payments', []):
                            amt += float(pmt.get('amount', 0))
                        
                        if amt > 0:
                            found = True
                            rows.append({
                                "Project": p_name, "Plot": pid, "Partner": booked_by.upper(),
                                "Customer": info.get('customer_name', 'N/A'), "Received": amt
                            })
    
    if found:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        if st.button("🖨️ Print"):
            st.write("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.error(f"❌ {search_exec} के अंडर में कोई बुकिंग रिकॉर्ड नहीं मिला।")

