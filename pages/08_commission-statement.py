import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Page & Security Setup ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Commission Statement")

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Helper Functions ---
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

# --- 3. Sync Database ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
parents_tree = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in exec_data.items()}

def get_downlines(boss_clean):
    res = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_downlines(child))
    return list(set(res))

# --- 4. UI Layout ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

# 🎯 DATE FILTERS
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2020, 1, 1))
end_d = col2.date_input("📅 End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', 'N/A')
            plots = p_info.get('plots', {})
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # Check Date Range
                    b_date_str = str(info.get('booking_date', datetime.date.today()))
                    b_date = pd.to_datetime(b_date_str).date()
                    
                    if start_d <= b_date <= end_d:
                        seller = clean_txt(info.get('executive_name', ''))
                        is_valid = (scope=="Self" and seller==target_clean) or \
                                   (scope=="Group" and seller in all_downlines) or \
                                   (scope=="All" and (seller==target_clean or seller in all_downlines))
                        
                        if is_valid:
                            amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                            boss_pct = partner_rates.get(target_clean, 0.0)
                            seller_pct = partner_rates.get(seller, 0.0)
                            diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                            
                            gross = (amt * diff_pct) / 100
                            raw_disc = safe_float(info.get('discount', 0))
                            company_rate = safe_float(info.get('company_rate', 650))
                            disc_amt = amt * ((raw_disc / company_rate) * 100 / 100) if company_rate > 0 else 0
                            
                            net_comm = max(0, gross - disc_amt)
                            
                            rows.append({
                                "Customer": info.get('customer_name', 'N/A'),
                                "Plot": str(pid).upper(),
                                "Mauja": mauja,
                                "Received": amt,
                                "Date": b_date,
                                "Gross": gross,
                                "Disc": disc_amt,
                                "Net Comm": net_comm,
                                "TDS": net_comm * 0.02,
                                "In Hand": net_comm * 0.98
                            })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.session_state.temp_df = df
    else:
        st.warning("No records found for this period.")

# --- 5. Print Button ---
if 'temp_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        st.markdown(st.session_state.temp_df.to_html(classes='table'), unsafe_allow_html=True)
        st.write('<script>window.print();</script>', unsafe_allow_html=True)

