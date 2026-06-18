import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re
import datetime

st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

# --- Security: Only Admin Access ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login first.")
    st.stop()
if st.session_state.get('user_role', 'executive').lower() != 'admin':
    st.error("🚨 ACCESS DENIED: Admin Only.")
    st.stop()

# --- Helper Functions ---
def safe_float(val, default=0.0):
    try: 
        if val is None or str(val).strip() == "": return float(default)
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else float(default)
    except: return float(default)

def clean_txt(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

# --- Sync Data ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})
parents_tree = {}
partner_rates = {}
real_names = {}

for ex_name, details in exec_data.items():
    if isinstance(details, dict):
        name = details.get('name', ex_name).strip()
        senior = str(details.get('senior_name', '')).replace('Direct', '').strip()
        pct = safe_float(details.get('percentage_exec', 0.0))
        c_name = clean_txt(name)
        if c_name:
            partner_rates[c_name] = pct
            real_names[c_name] = name
            c_senior = clean_txt(senior)
            if c_senior and c_senior != c_name: parents_tree[c_name] = c_senior

def get_all_downlines_recursive(boss_clean):
    downlines = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            downlines.append(child)
            downlines.extend(get_all_downlines_recursive(child))
    return list(set(downlines))

# --- UI ---
st.title("📊 Master Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(real_names.values())))
comm_type = st.radio("📑 Scope", ["Self", "Group", "All (Self + Group)"], horizontal=True)
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", datetime.date(2020, 1, 1))
end_date = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    target_clean = clean_txt(search_exec)
    boss_pct = partner_rates.get(target_clean, 0.0)
    all_downlines = get_all_downlines_recursive(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = str(p_info.get('mauja', p_info.get('location', 'N/A'))).strip()
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller_clean = clean_txt(info.get('executive_name', ''))
                    is_valid = (comm_type == "Self" and seller_clean == target_clean) or \
                               (comm_type == "Group" and seller_clean in all_downlines) or \
                               (comm_type == "All (Self + Group)" and (seller_clean == target_clean or seller_clean in all_downlines))
                    
                    if is_valid:
                        # Logic to calculate based on your Master Ledger engine
                        amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                        diff_pct = boss_pct - partner_rates.get(seller_clean, 0.0)
                        gross = (amt * diff_pct) / 100
                        rows.append({
                            "Customer": info.get('customer_name', 'N/A'),
                            "Plot": pid, "Mauja": mauja, "Amount": amt,
                            "Gross Comm": gross, "Net": gross * 0.98
                        })
    
    st.session_state.df = pd.DataFrame(rows)

if 'df' in st.session_state:
    st.table(st.session_state.df)

