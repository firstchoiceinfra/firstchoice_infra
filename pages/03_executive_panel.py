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

# --- 3. Cloud Database Integration ---
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# --- ✨ PROFESSIONAL BRANDING HEADER ---
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

# --- Theme & CSS ---
st.markdown("""
<style>
.stApp { background-image: url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"); background-attachment: fixed; background-size: cover; }
.block-container { background-color: rgba(255, 255, 255, 0.92) !important; padding: 2rem !important; border-radius: 20px; }
h1, h2 { color: #1e3a8a !important; font-weight: 800; }
.stButton>button { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white !important; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def safe_float(val, default=0.0):
    try: return float(val) if val else default
    except: return default

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
        curr = str(exec_data_root.get(curr_key_actual, {}).get('senior_name', '')).strip()
        if not curr or curr.lower() == 'direct': break
    if curr and curr.lower() == senior_key.lower():
        child_actual = next((k for k in exec_data_root.keys() if k.lower() == child_of_senior.lower()), None)
        if child_actual:
            profile = exec_data_root.get(child_actual, {})
            return float(profile.get('percentage_exec', 0.0)), float(profile.get('rupees_exec', 0.0)), child_actual
    return 0.0, 0.0, None

# --- UI & Ledger Engine ---
st.markdown("<h1 style='text-align: center;'>👑 Executive & Master Commission Panel</h1>", unsafe_allow_html=True)
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_clean_list)
start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.date_input("📅 End Date", datetime.date.today())
comm_filter = st.radio("🎯 View Type:", ["All (Self + Team)", "⭐ Self", "👥 Team"], horizontal=True)

if st.button("🔍 Generate Comprehensive Ledger"):
    search_exec_clean = str(search_exec).strip().lower()
    all_downlines_lower = [d.lower() for d in get_all_downlines(search_exec_clean)]
    statement_rows = []
    project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data)]
    
    for p_name in project_names:
        p_info = db_data[p_name]
        for plot_id, plot_info in p_info.get('plots', {}).items():
            if isinstance(plot_info, dict) and str(plot_info.get('status', '')).lower() == 'booked':
                plot_exec = str(plot_info.get('executive_name', '')).strip().lower()
                is_direct = (plot_exec == search_exec_clean)
                is_downline = (plot_exec in all_downlines_lower)
                
                if (comm_filter == "⭐ Self" and not is_direct) or (comm_filter == "👥 Team" and not is_downline): continue
                if is_direct or is_downline:
                    sr_profile = exec_data_root[search_exec]
                    sr_pct = safe_float(sr_profile.get('percentage_exec', 0.0))
                    # ... [यहाँ अपना पिछला पूरा डेटा लूपिंग लॉजिक पेस्ट करें] ...
                    # (लूप पूरा होने के बाद नीचे वाला ब्लॉक लगाएं)

    if statement_rows:
        df_statement = pd.DataFrame(statement_rows)
        # 1. हेडर
        print_commission_header(search_exec, start_date, end_date)
        # 2. टेबल
        st.dataframe(df_statement, use_container_width=True, hide_index=True)
        # 3. कैलकुलेशन
        t_gross = df_statement['Gross (₹)'].sum()
        t_tds = df_statement['TDS (₹)'].sum()
        t_net = df_statement['Net Payout (₹)'].sum()
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
        c2.metric("Total TDS Deduction", f"₹ {t_tds:,.2f}")
        c3.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
        # 4. बटन
        c_b1, c_b2 = st.columns(2)
        csv = df_statement.to_csv(index=False).encode('utf-8-sig')
        c_b1.download_button("🖨️ Download Statement (Excel)", csv, "Commission.csv", "text/csv", use_container_width=True)
        wa_url = f"https://wa.me/?text=Statement for {search_exec}: Net Pay: ₹{t_net:,.0f}"
        c_b2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)

