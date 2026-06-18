import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Page & Security ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Commission Statement")

if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Master Sync Engine (Fixing the Blank Page & Data Sync) ---
# यह सीधा st.session_state से डेटा उठा रहा है जैसा कि आपके बाकी पेजों में है
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# Hierarchy logic
partner_rates = {clean_txt(k): safe_float(v.get('percentage_exec', 0)) for k, v in exec_data.items()}
parents_tree = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in exec_data.items()}

def get_downlines(boss_clean):
    res = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_downlines(child))
    return list(set(res))

# --- 3. UI Filters ---
st.title("📊 Master Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

c1, c2 = st.columns(2)
start_d = c1.date_input("Start Date", datetime.date(2020, 1, 1))
end_d = c2.date_input("End Date", datetime.date.today())

# --- 4. Main Calculation Loop ---
if st.button("🚀 Generate Full Statement"):
    target_clean = clean_txt(search_exec)
    all_downlines = get_downlines(target_clean)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # मौजा सिंक: आपके इन्वेंटरी डैशबोर्ड से मौजा Key उठा रहे हैं
            mauja = str(p_info.get('mauja', 'N/A'))
            plots = p_info['plots']
            if isinstance(plots, list): plots = {str(i): p for i, p in enumerate(plots) if p}
            
            for pid, info in plots.items():
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = clean_txt(info.get('executive_name', ''))
                    
                    is_valid = (scope=="Self" and seller==target_clean) or \
                               (scope=="Group" and seller in all_downlines) or \
                               (scope=="All" and (seller==target_clean or seller in all_downlines))
                    
                    if is_valid:
                        # Amounts
                        amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                        
                        # Calculation Logic (डिस्काउंट का परसेंटेज फिक्स)
                        boss_pct = partner_rates.get(target_clean, 0.0)
                        seller_pct = partner_rates.get(seller, 0.0)
                        diff_pct = boss_pct - seller_pct if seller != target_clean else boss_pct
                        
                        gross = (amt * diff_pct) / 100
                        
                        # Discount % logic (जैसा आपने बोला था)
                        raw_disc_percent = safe_float(info.get('discount', 0)) 
                        disc_amt = amt * (raw_disc_percent / 100)
                        
                        net_comm = max(0, gross - disc_amt)
                        
                        rows.append({
                            "Customer": info.get('customer_name', 'N/A'),
                            "Plot": str(pid).upper(),
                            "Mauja": mauja,
                            "Received": amt,
                            "Gross Comm": gross,
                            "Disc Amt": disc_amt,
                            "Net Comm": net_comm,
                            "TDS": net_comm * 0.02,
                            "In Hand": net_comm * 0.98
                        })
    
    if rows:
        df = pd.DataFrame(rows)
        # TOTAL ROW
        summary = df.sum(numeric_only=True)
        summary['Customer'] = 'GRAND TOTAL'
        df = pd.concat([df, pd.DataFrame([summary])], ignore_index=True)
        
        st.dataframe(df, use_container_width=True)
        st.session_state.final_df = df
    else:
        st.warning("No records found for this executive/team.")

# --- 5. Print Logic ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print System Statement"):
        html = f"""<div style='font-family:sans-serif;'>
            <h2>FIRSTCHOICE INFRA</h2>
            <p>Commission Report for {search_exec}</p>
            {st.session_state.final_df.to_html(index=False)}
            <script>window.print();</script>
        </div>"""
        st.components.v1.html(html, height=800)

