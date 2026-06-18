import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Helper Functions ---
def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 3. Sync Engine ---
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

# --- 4. UI ---
st.title("📊 Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

if st.button("🚀 Generate"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # 🔥 फिक्स्ड मौजा सिंक (Case-Insensitive)
            mauja = "N/A"
            for key in p_info.keys():
                if key.lower() == 'mauja' or key.lower() == 'mauza':
                    mauja = str(p_info[key])
                    break
            
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
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
                        disc_amt = amt * (safe_float(info.get('discount', 0)) / 100)
                        net = max(0, gross - disc_amt)
                        
                        rows.append({
                            "Customer": info.get('customer_name', 'N/A'),
                            "Plot": str(pid), "Mauja": mauja, "Received": amt,
                            "Gross": gross, "Disc": disc_amt, "Net": net, "TDS": net * 0.02
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("कोई डेटा नहीं मिला।")

