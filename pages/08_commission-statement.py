import streamlit as st
import pandas as pd
import re
import datetime
import base64
import os

# --- 1. Security & Config ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 2. Database & Tree Sync ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
# सीनियर ट्री
parents_tree = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in exec_data.items()}

def get_downlines(boss_clean):
    res = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_downlines(child))
    return list(set(res))

# --- 3. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d, end_d = col1.date_input("Start Date", datetime.date(2020, 1, 1)), col2.date_input("End Date", datetime.date.today())

# --- 4. Strict Filter Engine ---
if st.button("🚀 Generate Filtered Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = str(p_info.get('mauja', p_info.get('Mauja', 'N/A')))
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # यहाँ हो रहा है असल फिल्टरिंग
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    # लॉजिक: क्या यह पार्टनर इस प्लॉट का हक़दार है?
                    is_match = False
                    if scope == "Self" and seller == target_clean: is_match = True
                    elif scope == "Group" and seller in all_downlines: is_match = True
                    elif scope == "All" and (seller == target_clean or seller in all_downlines): is_match = True
                    
                    if is_match:
                        b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                        if start_d <= b_date <= end_d:
                            amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                            
                            gross = (amt * (partner_rates.get(target_clean, 0) - partner_rates.get(seller, 0))) / 100
                            disc = amt * (safe_float(info.get('discount', 0)) / 100)
                            net = max(0, gross - disc)
                            
                            rows.append({"S.No.": len(rows)+1, "Customer": info.get('customer_name', 'N/A'), "Plot": str(pid).upper(), "Mauja": mauja, "Received": amt, "Date": b_date, "Gross": gross, "Disc": disc, "Net": net, "TDS": net*0.02, "In Hand": net*0.98})

    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.session_state.final_df = df
        # टोटल कैलकुलेशन
        st.write("### Grand Totals")
        st.write(df.sum(numeric_only=True))
    else:
        st.warning("इस पार्टनर का कोई डेटा नहीं मिला।")

# --- 5. Print Layout ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Systematic A4"):
        logo = base64.b64encode(open('logo.jpg', 'rb').read()).decode() if os.path.exists('logo.jpg') else ""
        html = f"""<div style='font-family: Arial; padding: 20px;'>
            <div style='display:flex; align-items:center; border-bottom:2px solid #000;'>
                <img src='data:image/jpeg;base64,{logo}' width='80'>
                <div style='text-align:center; flex-grow:1;'><h1>FIRSTCHOICE INFRA</h1><p>Symbol Of Trust</p></div>
            </div>
            <h3>Partner: {search_exec} ({scope}) | Date: {start_d} to {end_d}</h3>
            {st.session_state.final_df.to_html(index=False, classes='table')}
            <script>window.print();</script>
        </div>"""
        st.components.v1.html(html, height=800)

