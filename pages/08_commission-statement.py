import streamlit as st
import pandas as pd
import re
import datetime
import base64
import os

# --- 1. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 2. Data Sync & Logic ---
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

# --- 3. UI ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
c1, c2 = st.columns(2)
start_d, end_d = c1.date_input("Start Date", datetime.date(2020, 1, 1)), c2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = str(p_info.get('mauja', p_info.get('Mauja', 'N/A')))
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # Date & Seller Check
                    b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    if start_d <= b_date <= end_d and ((scope=="Self" and seller==target_clean) or (scope=="Group" and seller in all_downlines) or (scope=="All")):
                        amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                        gross = (amt * (partner_rates.get(target_clean, 0) - partner_rates.get(seller, 0))) / 100
                        disc = amt * (safe_float(info.get('discount', 0)) / 100)
                        net = max(0, gross - disc)
                        rows.append({"S.No.": len(rows)+1, "Customer": info.get('customer_name', 'N/A'), "Plot": str(pid).upper(), "Mauja": mauja, "Received": amt, "Date": b_date, "Gross": gross, "Disc": disc, "Net": net, "TDS": net*0.02, "In Hand": net*0.98})

    if rows:
        df = pd.DataFrame(rows)
        # TOTALS (अलग से कैलकुलेट करके, डेटाफ्रेम में बिना गड़बड़ किए)
        totals = df.sum(numeric_only=True)
        st.dataframe(df, use_container_width=True)
        st.session_state.final_df = df
        st.session_state.totals = totals
    else: st.warning("कोई डेटा नहीं मिला।")

# --- 4. A4 Print Engine ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print A4 Statement"):
        logo = base64.b64encode(open('logo.jpg', 'rb').read()).decode() if os.path.exists('logo.jpg') else ""
        html = f"""
        <div style='width: 100%; max-width: 800px; margin: auto; font-family: sans-serif; border: 1px solid #ccc; padding: 20px;'>
            <div style='display: flex; align-items: center; border-bottom: 2px solid #000; padding-bottom: 10px;'>
                <img src='data:image/jpeg;base64,{logo}' width='80'>
                <div style='margin-left: 20px; text-align: center; flex-grow: 1;'>
                    <h1 style='margin:0;'>FIRSTCHOICE INFRA</h1>
                    <p style='margin:0; font-weight:bold;'>Symbol Of Trust</p>
                    <p style='margin:0;'>Plot No. 06, Shop No.106, Motilal Nagar, Nagpur-440034</p>
                </div>
            </div>
            <div style='display: flex; justify-content: space-between; margin: 20px 0;'>
                <b>Partner: {search_exec}</b>
                <b>Period: {start_d} To {end_d}</b>
            </div>
            {st.session_state.final_df.to_html(index=False, classes='table table-bordered')}
            <div style='margin-top:20px; font-weight:bold;'>TOTALS: {st.session_state.totals.to_dict()}</div>
        </div>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

