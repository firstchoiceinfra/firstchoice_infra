import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Security & Page Setup ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Helper Functions ---
def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 3. Database Sync ---
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

# --- 4. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

# डेट रेंज फिल्टर्स
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2020, 1, 1))
end_d = col2.date_input("📅 End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # मौजा सिंक
            mauja = "N/A"
            for key in p_info.keys():
                if key.lower() in ['mauja', 'mauza']: mauja = str(p_info[key])
            
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    # लॉजिक चेक
                    is_valid = (scope=="Self" and seller==target_clean) or \
                               (scope=="Group" and seller in all_downlines) or \
                               (scope=="All" and (seller==target_clean or seller in all_downlines))
                    
                    if is_valid:
                        payments = [{'amt': safe_float(info.get('token_amount', 0)), 'date': info.get('booking_date', '2020-01-01')}]
                        for pmt in info.get('partial_payments', []):
                            payments.append({'amt': safe_float(pmt.get('amount', 0)), 'date': pmt.get('date', '2020-01-01')})
                        
                        for i, pmt in enumerate(payments):
                            pmt_date = pd.to_datetime(pmt['date']).date()
                            if start_d <= pmt_date <= end_d and pmt['amt'] > 0:
                                # कैलकुलेशन
                                boss_pct = partner_rates.get(target_clean, 0.0)
                                seller_pct = partner_rates.get(seller, 0.0)
                                diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                                
                                gross = (pmt['amt'] * diff_pct) / 100
                                raw_disc = safe_float(info.get('discount', 0))
                                disc_amt = pmt['amt'] * (raw_disc / 100)
                                net = max(0, gross - disc_amt)
                                tds = net * 0.02
                                
                                rows.append({
                                    "S.No.": len(rows) + 1,
                                    "Customer": info.get('customer_name', 'N/A'),
                                    "Plot": str(pid).upper(),
                                    "Mauja": mauja,
                                    "Received": pmt['amt'],
                                    "Date": pmt_date,
                                    "Gross": gross,
                                    "Disc": disc_amt,
                                    "Net": net,
                                    "TDS": tds,
                                    "In Hand": net - tds
                                })
    
    if rows:
        df = pd.DataFrame(rows)
        # टोटल रो कैलकुलेशन
        totals = df.sum(numeric_only=True)
        totals['S.No.'] = 'TOTAL'
        totals['Customer'] = '-'
        totals['Plot'] = '-'
        totals['Mauja'] = '-'
        totals['Date'] = '-'
        
        df_final = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
        st.dataframe(df_final, use_container_width=True)
        st.session_state.final_df = df_final
    else:
        st.warning("कोई डेटा नहीं मिला।")

if 'final_df' in st.session_state:
    if st.button("🖨️ Print Systematic Statement"):
        st.markdown(st.session_state.final_df.to_html(classes='table'), unsafe_allow_html=True)
        st.write('<script>window.print();</script>', unsafe_allow_html=True)

