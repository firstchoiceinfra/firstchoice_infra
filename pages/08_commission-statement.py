import streamlit as st
import pandas as pd
import re
import datetime
import base64
import os

# --- 1. Page & Security Setup ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Helper Functions ---
def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

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
# 🔥 बटन वापस जोड़ दिया गया है
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2020, 1, 1))
end_d = col2.date_input("📅 End Date", datetime.date.today())

# --- 5. Calculation Logic ---
if st.button("🚀 Generate Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # 🔥 सिंक इंजन: मौजा इन्वेंटरी से
            mauja = str(p_info.get('mauja', 'N/A'))
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                    
                    if start_d <= b_date <= end_d:
                        seller = clean_txt(info.get('executive_name', ''))
                        is_valid = (scope=="Self" and seller==target_clean) or \
                                   (scope=="Group" and seller in all_downlines) or \
                                   (scope=="All" and (seller==target_clean or seller in all_downlines))
                        
                        if is_valid:
                            amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                            
                            # कमीशन और डिस्काउंट कैलकुलेशन
                            boss_pct = partner_rates.get(target_clean, 0.0)
                            seller_pct = partner_rates.get(seller, 0.0)
                            diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                            
                            gross = (amt * diff_pct) / 100
                            raw_disc = safe_float(info.get('discount', 0))
                            company_rate = safe_float(info.get('company_rate', 650))
                            # परसेंटेज वाला डिस्काउंट फिक्स
                            disc_amt = amt * (raw_disc / 100) 
                            
                            net_comm = max(0, gross - disc_amt)
                            rows.append({
                                "Customer": info.get('customer_name', 'N/A'),
                                "Plot": str(pid).upper(),
                                "Mauja": mauja,
                                "Received": amt,
                                "Gross": gross,
                                "Disc": disc_amt,
                                "Net Comm": net_comm,
                                "TDS": net_comm * 0.02,
                                "In Hand": net_comm * 0.98
                            })
    
    if rows:
        df = pd.DataFrame(rows)
        # Grand Total
        totals = df.sum(numeric_only=True)
        totals['Customer'] = 'GRAND TOTAL'
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
        
        st.dataframe(df, use_container_width=True)
        st.session_state.final_df = df
    else:
        st.warning("No data found for this selection.")

# --- 6. Print Button ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Final Statement"):
        logo = get_image_base64('logo.jpg')
        html = f"""
        <div style='font-family: Arial;'>
            <div style='display:flex; align-items:center;'>
                <img src='data:image/jpeg;base64,{logo}' width='80'>
                <div style='margin-left:15px;'>
                    <h2 style='margin:0;'>FIRSTCHOICE INFRA</h2>
                    <p style='margin:0;'>Symbol Of Trust | Nagpur, Maharashtra</p>
                </div>
            </div>
            <hr>
            <h3>Partner: {search_exec} | From: {start_d} To: {end_d}</h3>
            {st.session_state.final_df.to_html(index=False, classes='table')}
        </div>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

