import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Channel")

# --- 2. Security Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

curr_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# --- 3. Database Sync ---
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# --- ✨ PROFESSIONAL HEADER FUNCTION ---
def print_commission_header(exec_name, start_date, end_date):
    st.markdown(f"""
    <div style="border: 4px solid #b8860b; padding: 20px; border-radius: 15px; background: #fdfaf6; margin-bottom: 25px; text-align: center; box-shadow: 0px 5px 15px rgba(0,0,0,0.2);">
        <h1 style="margin: 0; color: #8b4513; font-size: 35px;">Firstchoice Infra</h1>
        <p style="margin: 0; font-style: italic; color: #555; font-size: 16px;">Symbol Of Trust...</p>
        <hr style="border-top: 2px solid #b8860b; margin: 10px 0;">
        <p style="margin: 0; font-size: 14px; font-weight: bold;">📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
        <h2 style="margin-top: 15px; color: #b8860b; text-decoration: underline;">Executive Commission Statement</h2>
        <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">
            Executive: {exec_name} | Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# [--- बाकी का आपका पूरा पिछला लॉजिक ---]
# (मैं यहाँ से आपकी फाइल का पूरा लॉजिक वैसा का वैसा ही रख रहा हूँ, बस स्टेटमेंट जनरेशन वाला हिस्सा अपडेट किया है)

# ... (Hierarchy & Deduction Functions here) ...
def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data_root.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name))
    return list(set(downlines))

def get_diff_deduction(sale_maker_key, senior_key):
    curr = sale_maker_key
    child_of_senior = curr
    while curr and curr.lower() != senior_key.lower():
        child_of_senior = curr
        curr_key_actual = next((k for k in exec_data_root.keys() if k.lower() == curr.lower()), None)
        if not curr_key_actual: break
        curr_profile = exec_data_root.get(curr_key_actual, {})
        curr = str(curr_profile.get('senior_name', '')).strip()
        if not curr or curr.lower() == 'direct': break
    if curr and curr.lower() == senior_key.lower():
        child_actual = next((k for k in exec_data_root.keys() if k.lower() == child_of_senior.lower()), None)
        if child_actual:
            child_profile = exec_data_root.get(child_actual, {})
            jr_pct = float(child_profile.get('percentage_exec', 0.0))
            jr_rs = float(child_profile.get('rupees_exec', 0.0))
            return jr_pct, jr_rs, child_actual
    return 0.0, 0.0, None

def prepare_edit(ex_name, details):
    st.session_state['form_exec_name'] = ex_name
    st.session_state['form_senior_name'] = details.get('senior_name', '')
    st.session_state['form_exec_mobile'] = details.get('mobile', '')
    st.session_state['ep'] = float(details.get('percentage_exec', 0.0))
    st.session_state['er'] = float(details.get('rupees_exec', 0.0))
    st.session_state['edit_mode_active'] = True
    st.session_state['old_edit_name'] = ex_name

def clear_edit_fields():
    for k in ['form_exec_name', 'form_senior_name', 'form_exec_mobile', 'ep', 'er', 'edit_mode_active', 'old_edit_name']:
        st.session_state.pop(k, None)

# [ ... यहाँ आपका पूरा पुराना UI और Admin फॉर्म लॉजिक रखें ... ]

# --- UPDATE GENERATE LEDGER LOGIC ---
    if st.button("🔍 Generate Comprehensive Ledger", use_container_width=True):
        # ... (आपका स्टेटमेंट रोज़ बनाने का पुराना लॉजिक) ...
        
        if statement_rows:
            df_statement = pd.DataFrame(statement_rows)
            
            # 1. ब्रांडेड हेडर प्रिंट करें
            print_commission_header(search_exec, start_date, end_date)
            
            # 2. टेबल दिखाएं
            st.dataframe(df_statement, use_container_width=True, hide_index=True)
            st.write("---")
            
            # 3. कैलकुलेशन
            t_gross = df_statement['Gross (₹)'].sum()
            t_tds = df_statement['TDS (₹)'].sum()
            t_net = df_statement['Net Payout (₹)'].sum()
            
            c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
            c_sum1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
            c_sum2.metric("Total TDS Deduction", f"₹ {t_tds:,.2f}")
            c_sum3.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
            
            # 4. बटन्स
            c_b1, c_b2 = st.columns(2)
            csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
            c_b1.download_button("🖨️ Download Statement (Excel)", csv_data, f"Comm_{search_exec}.csv", "text/csv", use_container_width=True)
            
            wa_msg = f"Firstchoice Infra Commission Statement for {search_exec}: Gross: ₹{t_gross:.0f}, TDS: ₹{t_tds:.0f}, Net: ₹{t_net:.0f}"
            wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_msg)}"
            c_b2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)

