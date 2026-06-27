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
scope = c2.radio("📑 स्कोप", ["Self", "Group"], horizontal=True)

start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    valid_team = [search_exec.lower()] + (get_all_downlines(search_exec) if scope == "Group" else [])
    
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    if str(info.get('executive_name', '')).strip().lower() in valid_team:
                        
                        # 1. टोकन ट्रांजैक्शन चेक
                        t_date = datetime.datetime.strptime(str(info.get('booking_date', '2000-01-01')), "%Y-%m-%d").date()
                        if start_d <= t_date <= end_d:
                            amt = float(info.get('token_amount', 0))
                            if amt > 0:
                                rows.append({"Mauja": p_info.get('mauza', '-'), "Project": p_name, "Plot": pid, "Customer": info.get('customer_name', '-'), "Received": amt, "Date": t_date, "Type": "Token"})
                        
                        # 2. EMI/Partial Payments ट्रांजैक्शन चेक
                        for pmt in info.get('partial_payments', []):
                            p_date = datetime.datetime.strptime(str(pmt.get('date', '2000-01-01')), "%Y-%m-%d").date()
                            if start_d <= p_date <= end_d:
                                amt = float(pmt.get('amount', 0))
                                rows.append({"Mauja": p_info.get('mauza', '-'), "Project": p_name, "Plot": pid, "Customer": info.get('customer_name', '-'), "Received": amt, "Date": p_date, "Type": pmt.get('remarks', 'EMI')})

    if rows:
        df = pd.DataFrame(rows)
        # कैलकुलेशन: Gross, Net, TDS, In Hand
        df['Gross'] = df['Received'] * 0.23
        df['Discount'] = df['Gross'] * 0.16
        df['Net Comm'] = df['Gross'] - df['Discount']
        df['TDS'] = df['Net Comm'] * 0.02
        df['In Hand'] = df['Net Comm'] - df['TDS']
        
        st.dataframe(df, use_container_width=True)
        
        # 🖨️ पक्का प्रिंट बटन (JavaScript ट्रिगर)
        st.markdown("""
            <button onclick="window.print()" style="padding:10px 20px; background:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer;">
                🖨️ Print this Statement
            </button>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ कोई डेटा नहीं मिला।")

