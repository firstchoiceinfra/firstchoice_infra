import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 1. SECURITY LOCK
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get('executives', {})

# टीम चेन ढूँढने का पक्का लॉजिक
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name.lower())
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

# 2. सिलेक्शन पैनल
c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 कमीशन स्कोप", ["Self", "Group", "All"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Statement"):
    # यहाँ रिस्ट्रिक्शन लॉजिक है
    if scope == "Self":
        valid_team = [search_exec.lower()]
    elif scope == "Group":
        valid_team = [search_exec.lower()] + get_all_downlines(search_exec)
    else:
        valid_team = [n.lower() for n in exec_data.keys()] # 'All' में सबको ढूँढो
    
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    exec_name = str(info.get('executive_name', '')).strip().lower()
                    
                    # रिस्ट्रिक्शन: सिर्फ वैलिड टीम का ही डेटा दिखाओ
                    if exec_name in valid_team:
                        amt = float(info.get('token_amount', 0))
                        for pmt in info.get('partial_payments', []):
                            amt += float(pmt.get('amount', 0))
                        
                        rows.append({
                            "Project": p_name, "Plot": pid, "Partner": exec_name.upper(),
                            "Customer": info.get('customer_name', 'N/A'), "Received": amt
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # 🖨️ प्रिंट करने का बटन (Browser Print)
        if st.button("🖨️ Print Statement"):
            st.write("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.error(f"❌ '{search_exec}' के लिए इस स्कोप में कोई बुकिंग नहीं मिली।")

