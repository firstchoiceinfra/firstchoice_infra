import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Security & Setup ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 2. Database Sync ---
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

# --- 3. UI Filters (सारे एक साथ) ---
st.title("📊 Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

# तारीख के फिल्टर्स (अब वापस आ गए हैं)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2020, 1, 1))
end_d = col2.date_input("📅 End Date", datetime.date.today())

if st.button("🚀 Generate Systematic Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # Mauza (Z वाला) सिंक
            mauza = "N/A"
            for k, v in p_info.items():
                if k.lower() == 'mauza': mauza = str(v)
            
            for pid, info in (p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots'])):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    # डेट और पार्टनर फिल्टर
                    if start_d <= b_date <= end_d:
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
                                "S.No.": len(rows)+1, "Customer": info.get('customer_name', 'N/A'),
                                "Plot": str(pid).upper(), "Mauza": mauza, "Received": amt,
                                "Date": b_date, "Gross": gross, "Disc": disc_amt,
                                "Net": net, "TDS": net * 0.02, "In Hand": net * 0.98
                            })
    
    if rows:
        df = pd.DataFrame(rows)
        # टोटल रो कैलकुलेशन
        st.table(df)
        st.subheader("GRAND TOTALS")
        st.write(df.sum(numeric_only=True))
    else:
        st.warning("कोई डेटा नहीं मिला।")

