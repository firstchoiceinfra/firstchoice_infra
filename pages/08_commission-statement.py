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

def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name.lower())
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 स्कोप", ["Self", "Group", "All"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Statement"):
    # 1. अधिकार क्षेत्र (Valid Team) तय करना
    if scope == "Self":
        valid_team = [search_exec.lower()]
    elif scope == "Group":
        valid_team = [search_exec.lower()] + get_all_downlines(search_exec)
    else:
        valid_team = [n.lower() for n in exec_data.keys()]
    
    rows = []
    # 2. डेटा स्कैन (Strict Matching)
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    
                    # बुकिंग करने वाले का नाम
                    booked_by = str(info.get('executive_name', '')).strip().lower()
                    
                    # 🎯 यहाँ है 'Strict Filtering' - अगर नाम वैलिड टीम में नहीं है, तो लूप आगे बढ़ जाएगा
                    if booked_by in valid_team:
                        
                        # डेट रेंज चेक (Booking Date OR Payment Date)
                        b_date = datetime.datetime.strptime(str(info.get('booking_date', '2000-01-01')), "%Y-%m-%d").date()
                        
                        # EMI पेमेंट्स स्कैन
                        amt = float(info.get('token_amount', 0))
                        for pmt in info.get('partial_payments', []):
                            p_date = datetime.datetime.strptime(str(pmt.get('date', '2000-01-01')), "%Y-%m-%d").date()
                            if start_d <= p_date <= end_d:
                                amt += float(pmt.get('amount', 0))
                        
                        # सिर्फ वही डेटा दिखाएं जो सिलेक्टेड पार्टनर/टीम का है
                        rows.append({
                            "Project": p_name, "Plot": pid, "Partner": booked_by.upper(),
                            "Customer": info.get('customer_name', 'N/A'), "Received": amt
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        # 3. नाम के आधार पर फ़िल्टर (डुप्लीकेट रोकने के लिए)
        st.dataframe(df, use_container_width=True)
        if st.button("🖨️ Print"):
            st.write("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.error(f"❌ {search_exec} के लिए इस स्कोप में कोई बुकिंग नहीं मिली।")

