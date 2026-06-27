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

# सिलेक्शन पैनल्स
search_exec = st.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 कमीशन स्कोप", ["Self", "Group", "All"], horizontal=True)

if st.button("🚀 Generate Statement"):
    # 1. रिस्ट्रिक्शन: वैलिड टीम लिस्ट बनाना
    if scope == "Self":
        valid_team = [search_exec.lower()]
    elif scope == "Group":
        valid_team = [search_exec.lower()] + get_all_downlines(search_exec)
    else:
        valid_team = [n.lower() for n in exec_data.keys()]
    
    rows = []
    found_any = False
    
    # 2. डेटा स्कैन (बुकिंग्स फिल्टरिंग)
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    
                    # 🎯 यहाँ है सबसे जरूरी चेक
                    booked_by = str(info.get('executive_name', '')).strip().lower()
                    
                    if booked_by in valid_team:
                        amt = float(info.get('token_amount', 0))
                        for pmt in info.get('partial_payments', []):
                            amt += float(pmt.get('amount', 0))
                        
                        if amt > 0:
                            found_any = True
                            rows.append({
                                "Project": p_name, "Plot": pid, "Partner": booked_by.upper(),
                                "Customer": info.get('customer_name', 'N/A'), "Received": amt
                            })
    
    if found_any:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.error(f"❌ {search_exec} के लिए कोई बुकिंग रिकॉर्ड नहीं पाया गया।")

