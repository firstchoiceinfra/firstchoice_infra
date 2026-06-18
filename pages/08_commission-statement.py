import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Page Configuration & Security ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Commission Statement")
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Helper Functions ---
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

# --- 3. Data Extraction Engine ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# Partner Registry
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
parents_tree = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in exec_data.items()}

# Recursive Downline Engine (यह पूरी टीम का डेटा निकालता है)
def get_downlines(boss_clean):
    res = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_downlines(child)) # Recursive call
    return list(set(res))

# --- 4. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d, end_d = col1.date_input("Start", datetime.date(2020, 1, 1)), col2.date_input("End", datetime.date.today())

if st.button("🚀 Generate Final Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    # Iterate all projects
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            plots = p_info.get('plots', {})
            # List to Dict fix
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    # Logic Check
                    is_valid = (scope=="Self" and seller==target_clean) or \
                               (scope=="Group" and seller in all_downlines) or \
                               (scope=="All" and (seller==target_clean or seller in all_downlines))
                    
                    if is_valid:
                        # Amounts
                        amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                        
                        # Calculation Logic
                        boss_pct = partner_rates.get(target_clean, 0.0)
                        seller_pct = partner_rates.get(seller, 0.0)
                        diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                        
                        gross = (amt * diff_pct) / 100
                        
                        # 🔥 DISCOUNT AS PERCENTAGE (New Logic)
                        disc_pct = safe_float(info.get('discount', 0)) # Assuming discount is saved as %
                        disc_amt = amt * (disc_pct / 100)
                        
                        net_comm = max(0, gross - disc_amt)
                        tds = net_comm * 0.02
                        
                        rows.append({
                            "Customer": info.get('customer_name', 'N/A'),
                            "Plot": str(pid).upper(),
                            "Mauja": str(p_info.get('mauja', 'N/A')),
                            "Received": amt,
                            "Gross": gross,
                            "Disc %": f"{disc_pct}%",
                            "Disc Amt": disc_amt,
                            "Net Comm": net_comm,
                            "TDS": tds,
                            "In Hand": net_comm - tds
                        })
    
    # Display
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No data found. Check your dates or partner selection.")

