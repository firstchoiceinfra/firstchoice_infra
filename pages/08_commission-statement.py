import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

# 🔒 1. SECURITY LOCK
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied! यह पेज केवल बॉस/एडमिन के लिए है।")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get('executives', {})

# 🔄 टीम चेन ढूँढने का पक्का लॉजिक
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name.lower())
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

# 2. सिलेक्शन पैनल्स
c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 स्कोप", ["Self", "Group", "All"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    # सख्त टीम लिस्टिंग
    if scope == "Self": valid_team = [search_exec.lower()]
    elif scope == "Group": valid_team = [search_exec.lower()] + get_all_downlines(search_exec)
    else: valid_team = [n.lower() for n in exec_data.keys()]
    
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    exec_name = str(info.get('executive_name', '')).strip().lower()
                    
                    if exec_name in valid_team:
                        # बिज़नेस कैलकुलेशन
                        amt = float(info.get('token_amount', 0))
                        for pmt in info.get('partial_payments', []):
                            amt += float(pmt.get('amount', 0))
                        
                        if amt > 0:
                            # PDF फॉर्मेट के कॉलम
                            rows.append({
                                "Mauja": p_info.get('mauza', 'N/A'),
                                "Project": p_name,
                                "Plot": pid,
                                "Customer": info.get('customer_name', 'N/A'),
                                "Received": amt,
                                "Net Comm": amt * 0.15, # आपका फिक्स्ड %
                                "TDS": (amt * 0.15) * 0.02,
                                "In Hand": (amt * 0.15) * 0.98
                            })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        # प्रिंट बटन
        if st.button("🖨️ Print Statement"):
            st.write("<script>window.print();</script>", unsafe_allow_html=True)
    else:
        st.error(f"❌ {search_exec} के लिए इस स्कोप में कोई डेटा नहीं मिला।")
