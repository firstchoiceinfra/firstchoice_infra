import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 SECURITY
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

if 'db_projects' not in st.session_state:
    database.init_db()

db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# 🔍 UNIVERSAL NAME FINDER
def get_exec_name_from_booking(info):
    """बुकिंग डेटा में किसी भी की-वर्ड के अंदर नाम ढूँढता है"""
    for key in ['executive_name', 'partner_name', 'agent', 'executive', 'name']:
        if key in info: return str(info[key]).strip().lower()
    return ""

def get_exec_details(target_name, exec_dict):
    target_clean = str(target_name).strip().lower()
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            if str(v.get('name', k)).strip().lower() == target_clean:
                upline = str(v.get('sponsor', v.get('upline', v.get('referred_by', '')))).split('|')[-1].strip().lower()
                perc = float(v.get('commission_percentage', 23)) / 100
                return upline, perc
    return "", 0.23

def get_all_downlines(target, exec_dict):
    downlines = []
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            name = str(v.get('name', k)).strip()
            u, _ = get_exec_details(name, exec_dict)
            if u == target.lower():
                downlines.append(name)
                downlines.extend(get_all_downlines(name, exec_dict))
    return list(set(downlines))

# 🌟 DASHBOARD
st.title("📊 Executive Commission Dashboard")
partner_names = sorted(list(set([str(v.get('name', k)).strip() for k, v in exec_data.items() if isinstance(v, dict)])))

if partner_names:
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    start_d = st.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Statement"):
        rows = []
        valid_execs = [search_exec.lower()] + [d.lower() for d in get_all_downlines(search_exec, exec_data)] if scope != "Self" else [search_exec.lower()]
        _, my_perc = get_exec_details(search_exec, exec_data)

        for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
            if isinstance(p_info, dict) and 'plots' in p_info:
                for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                    if isinstance(info, dict):
                        exec_name = get_exec_name_from_booking(info)
                        if exec_name in valid_execs:
                            # 💸 TOTAL BUSINESS (EMI + Token)
                            amt = 0.0
                            for key in ['transactions', 'emi_tracker', 'receipts', 'payment_history', 'plots']:
                                if isinstance(info.get(key), (list, dict)):
                                    items = info[key].values() if isinstance(info[key], dict) else info[key]
                                    for p in items:
                                        if isinstance(p, dict):
                                            try:
                                                p_date = datetime.datetime.strptime(str(p.get('date', '1900-01-01'))[:10], "%Y-%m-%d").date()
                                                if start_d <= p_date <= end_d: amt += float(p.get('amount', p.get('paid_amount', 0)))
                                            except: pass
                            
                            if amt > 0:
                                _, down_perc = get_exec_details(exec_name, exec_data)
                                diff_perc = my_perc - down_perc
                                if diff_perc >= 0:
                                    rows.append({
                                        "Project": p_name, "Customer": info.get('customer_name', 'N/A'),
                                        "Received": amt, "Comm %": round(diff_perc*100, 2),
                                        "Net Comm": amt * diff_perc
                                    })
        
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True)
        else:
            st.error("❌ कोई डेटा नहीं मिला। डेट रेंज या पार्टनर चेक करें।")

