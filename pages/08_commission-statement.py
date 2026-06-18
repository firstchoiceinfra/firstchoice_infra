import streamlit as st
import pandas as pd
import re
import datetime

# --- Security & Config ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Statement")
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Admin Only.")
    st.stop()

# --- Helpers ---
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

# --- Sync Engine ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
parents_tree = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in exec_data.items()}

def get_downlines(boss_clean):
    res = []
    # पूरे ट्री को बार-बार स्कैन करके डाउनलाइन ढूंढने वाला पक्का इंजन
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_downlines(child))
    return list(set(res))

# --- UI ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

if st.button("🔄 Refresh & Generate"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            plots = p_info.get('plots', {})
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    is_valid = (scope=="Self" and seller==target_clean) or \
                               (scope=="Group" and seller in all_downlines) or \
                               (scope=="All" and (seller==target_clean or seller in all_downlines))
                    
                    if is_valid:
                        amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                        
                        # 🔥 फिक्स्ड कैलकुलेशन: डिस्काउंट को पहले परसेंटेज में बदलें
                        # मान लिया कि डिस्काउंट 'रुपये प्रति स्क्वेयर फीट' में है
                        raw_disc = safe_float(info.get('discount', 0))
                        company_rate = safe_float(info.get('company_rate', 650)) # अगर रेट न हो तो 650
                        
                        # डिस्काउंट % = (डिस्काउंट / कंपनी रेट) * 100
                        disc_percent = (raw_disc / company_rate) * 100 if company_rate > 0 else 0
                        disc_amt = amt * (disc_percent / 100)
                        
                        # कमीशन लॉजिक
                        boss_pct = partner_rates.get(target_clean, 0.0)
                        seller_pct = partner_rates.get(seller, 0.0)
                        diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                        
                        gross = (amt * diff_pct) / 100
                        net_comm = max(0, gross - disc_amt)
                        tds = net_comm * 0.02
                        
                        rows.append({
                            "Customer": info.get('customer_name', 'N/A'),
                            "Plot": str(pid).upper(),
                            "Mauja": p_info.get('mauja', 'N/A'),
                            "Received": amt,
                            "Gross": gross,
                            "Disc Amt": disc_amt,
                            "Net Comm": net_comm,
                            "TDS": tds,
                            "In Hand": net_comm - tds
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        # Totals
        summary = df.sum(numeric_only=True)
        st.write("### Grand Totals", summary)
    else:
        st.warning("कोई डेटा नहीं मिला।")

