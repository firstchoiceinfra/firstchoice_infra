import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import re
import datetime

st.set_page_config(layout="wide", page_title="FC Infra - Master Commission Statement")

# --- Security: Only Admin ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted to Administrator Only.")
    st.stop()

# --- Functions ---
def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- Sync Data ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
real_names = {clean_txt(k): v.get('name', k) for k, v in exec_data.items()}

# --- UI Filters ---
search_exec = st.selectbox("👤 Select Executive", options=sorted(list(real_names.values())))
comm_type = st.radio("📑 Scope", ["Self", "Group", "All (Self + Group)"], horizontal=True)
col1, col2 = st.columns(2)
start_date = col1.date_input("Start Date", datetime.date(2020, 1, 1))
end_date = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Full Statement"):
    rows = []
    target_clean = clean_txt(search_exec)
    boss_pct = partner_rates.get(target_clean, 0.0)
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = str(p_info.get('mauja', 'N/A'))
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # Calculations
                    amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                    
                    # Commission Logic
                    diff_pct = boss_pct - partner_rates.get(clean_txt(info.get('executive_name', '')), 0.0)
                    gross = (amt * diff_pct) / 100
                    disc = safe_float(info.get('discount', 0))
                    net_comm = max(0, gross - disc)
                    tds = net_comm * 0.02
                    
                    rows.append({
                        "S.No.": len(rows) + 1,
                        "Customer": info.get('customer_name', 'N/A'),
                        "Plot": str(pid).upper(),
                        "Mauja": mauja,
                        "Received": amt,
                        "Date": info.get('booking_date', 'N/A'),
                        "Gross Comm": gross,
                        "Discount": disc,
                        "Net Comm": net_comm,
                        "TDS (2%)": tds,
                        "In Hand": net_comm - tds
                    })
    
    df = pd.DataFrame(rows)
    # Add Total Row
    if not df.empty:
        totals = df.sum(numeric_only=True)
        totals['S.No.'] = 'TOTAL'
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
        
    st.dataframe(df, use_container_width=True)
    st.session_state.final_df = df

if 'final_df' in st.session_state:
    if st.button("🖨️ Print Final Statement"):
        st.write(st.session_state.final_df.to_html(classes='data-table'))

