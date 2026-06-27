import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

# 🔒 1. ADMIN ONLY SECURITY LOCK
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied! यह पेज केवल एडमिन/बॉस के लिए है।")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get('executives', {})

# 🔍 टीम चेन ढूँढने का लॉजिक (मास्टर स्लैब रजिस्टर के हिसाब से)
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

# 2. सिलेक्शन पैनल्स
c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 कमीशन स्कोप", ["Self", "Group", "All"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    # टीम मेंबर्स की लिस्ट
    if scope == "Self": valid_team = [search_exec.lower()]
    elif scope == "Group": valid_team = [search_exec.lower()] + [d.lower() for d in get_all_downlines(search_exec)]
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
                            # PDF फॉर्मेट जैसा कैलकुलेशन
                            gross = amt * 0.23
                            discount = gross * 0.16 # उदाहरण के लिए
                            net = gross - discount
                            tds = net * 0.02
                            in_hand = net - tds
                            
                            rows.append({
                                "Mauja": p_info.get('mauza', 'Mohadi'), "Project": p_name, "Plot": pid,
                                "Customer": info.get('customer_name', 'N/A'), "Received": amt,
                                "Gross": gross, "Net Comm": net, "TDS": tds, "In Hand": in_hand
                            })

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # 📄 PDF जैसा एक्सपोर्ट
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("🖨️ Download Statement (CSV)", csv, "Statement.csv", "text/csv")
    else:
        st.error("❌ इस स्कोप और डेट के बीच कोई डेटा नहीं मिला।")

