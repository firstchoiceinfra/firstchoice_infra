import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 1. Security & Database
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get('executives', {})

# 2. Hierarchy Logic (Downlines)
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name.lower())
            downlines.extend(get_all_downlines(ex_name)) 
    return list(set(downlines))

st.title("📄 Executive Commission Statement")

# 3. Inputs
c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 पार्टनर चुनें", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 स्कोप", ["Self", "Group"], horizontal=True)
start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate PDF-Format Statement"):
    # Team Filter
    valid_team = [search_exec.lower()] + (get_all_downlines(search_exec) if scope == "Group" else [])
    
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    if str(info.get('executive_name', '')).strip().lower() in valid_team:
                        
                        # Data Collection (Token + Payments)
                        all_txns = [{'date': info.get('booking_date', '2000-01-01'), 'amount': info.get('token_amount', 0)}]
                        all_txns.extend(info.get('partial_payments', []))
                        
                        for tx in all_txns:
                            t_date = datetime.datetime.strptime(str(tx.get('date', '2000-01-01')), "%Y-%m-%d").date()
                            if start_d <= t_date <= end_d:
                                amt = float(tx.get('amount', 0))
                                if amt > 0:
                                    gross = amt * 0.23
                                    disc = gross * 0.16
                                    net = gross - disc
                                    tds = net * 0.02
                                    rows.append({
                                        "Mauja": p_info.get('mauza', 'Mohadi'), "Project": p_name, "Plot": pid,
                                        "Customer": info.get('customer_name', 'N/A'), "Received": amt,
                                        "Date": t_date, "Gross": gross, "Discount": disc,
                                        "Net Comm": net, "TDS": tds, "In Hand": net - tds
                                    })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # PRINT BUTTON (JS)
        st.markdown("""
            <button onclick="window.print()" style="padding:15px 30px; font-size:16px; background:#1e3a8a; color:white; border:none; border-radius:8px; cursor:pointer;">
                🖨️ Print Statement
            </button>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ इस अवधि में कोई डेटा नहीं मिला।")

