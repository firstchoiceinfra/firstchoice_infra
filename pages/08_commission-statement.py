import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 1. ADMIN SECURITY LOCK
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied! केवल एडमिन के लिए।")
    st.stop()

# 2. DATABASE INIT
if 'db_projects' not in st.session_state:
    database.init_db()

db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# 3. HELPER FUNCTIONS
def get_exec_details(name, exec_dict):
    perc = 0.23
    upline = ""
    target_clean = str(name).strip().lower()
    for k, v in exec_dict.items():
        if isinstance(v, dict) and str(v.get('name', k)).strip().lower() == target_clean:
            upline = str(v.get('sponsor', v.get('upline', v.get('referred_by', v.get('description', ''))))).split('|')[-1].strip().lower()
            perc = float(v.get('commission_percentage', 23)) / 100
            break
    return upline, perc

def get_all_downlines(target, exec_dict):
    downlines = []
    target_clean = target.lower()
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            name = str(v.get('name', k)).strip()
            _, u = get_exec_details(name, exec_dict)
            if u == target_clean:
                downlines.append(name)
                downlines.extend(get_all_downlines(name, exec_dict))
    return list(set(downlines))

# ==========================================
# 🌟 UI DASHBOARD
# ==========================================
st.title("📊 Executive Commission Dashboard")
partner_names = sorted(list(set([str(v.get('name', k)).strip() for k, v in exec_data.items() if isinstance(v, dict)])))

if partner_names:
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Commission Scope", ["Self", "Group", "All"], horizontal=True)
    start_d = st.date_input("📅 Start Date", datetime.date(2024, 6, 6))
    end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Systematic Statement"):
        rows = []
        valid_execs = [search_exec.lower()] + [d.lower() for d in get_all_downlines(search_exec, exec_data)] if scope != "Self" else [search_exec.lower()]
        _, my_perc = get_exec_details(search_exec, exec_data)

        for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
            if isinstance(p_info, dict) and 'plots' in p_info:
                for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                    if isinstance(info, dict):
                        exec_name = str(info.get('executive_name', '')).strip().lower()
                        if exec_name in valid_execs:
                            # EMI Tracker: हर पेमेंट स्कैन करें
                            amt = 0.0
                            for key in ['transactions', 'emi_tracker', 'receipts', 'payment_history', 'plots']:
                                if isinstance(info.get(key), list):
                                    for p in info[key]:
                                        if isinstance(p, dict):
                                            try:
                                                p_date = datetime.datetime.strptime(str(p.get('date', '1900-01-01')), "%Y-%m-%d").date()
                                                if start_d <= p_date <= end_d: amt += float(p.get('amount', 0))
                                            except: pass
                            
                            if amt > 0:
                                _, down_perc = get_exec_details(exec_name, exec_data)
                                diff_perc = my_perc - down_perc
                                if diff_perc >= 0:
                                    rows.append({
                                        "Project": p_name, "Plot": pid, "Customer": info.get('customer_name'),
                                        "Received": amt, "Gross Comm": amt * diff_perc,
                                        "TDS": (amt * diff_perc) * 0.02, "Net": (amt * diff_perc) * 0.98
                                    })
        
        if rows:
            df = pd.DataFrame(rows)
            st.success("✅ रिपोर्ट जनरेट हो गई!")
            # 🌟 यही वो टेबल है जो आपको नहीं दिख रही थी:
            st.dataframe(df, use_container_width=True) 
        else:
            st.error("❌ कोई डेटा नहीं मिला।")

