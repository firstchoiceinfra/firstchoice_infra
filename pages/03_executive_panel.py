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

# --- ✨ PROFESSIONAL HEADER FUNCTION ---
def print_commission_header(exec_name, start_date, end_date):
    st.markdown(f"""
    <div style="border: 4px solid #b8860b; padding: 20px; border-radius: 15px; background: #fdfaf6; margin-bottom: 25px; text-align: center; box-shadow: 0px 5px 15px rgba(0,0,0,0.2);">
        <h1 style="margin: 0; color: #8b4513; font-size: 35px;">Firstchoice Infra</h1>
        <p style="margin: 0; font-style: italic; color: #555; font-size: 16px;">Symbol Of Trust...</p>
        <hr style="border-top: 2px solid #b8860b; margin: 10px 0;">
        <p style="margin: 0; font-size: 14px; font-weight: bold;">📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
        <h2 style="margin-top: 15px; color: #b8860b; text-decoration: underline;">Commission for Executive</h2>
        <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">
            Executive: {exec_name} | Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Global Theme Synchronization Logic
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255, 255, 255, 0.92)"

if '_app_settings' in db_data:
    global_settings = db_data['_app_settings']
    bg_url = global_settings.get('bg_url', bg_url)
    p_color = global_settings.get('primary_color', p_color)
    s_color = global_settings.get('secondary_color', s_color)
    c_bg = global_settings.get('card_bg', c_bg)

st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: {c_bg} !important; padding: 1.5rem 2.5rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 1.5rem; margin-bottom: 1.5rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
.ledger-box {{ background-color: #ffffff; border-left: 4px solid {p_color}; padding: 10px 15px !important; border-radius: 8px; box-shadow: 0px 2px 5px rgba(0,0,0,0.05); margin-bottom: 8px !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{ font-size: 11px !important; font-weight: 600 !important; color: #475569 !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ font-size: 14px !important; font-weight: 700 !important; color: #0f172a !important; }}
div.row-widget.stRadio > div {{ flex-direction:row; background-color: #f1f5f9; padding: 10px; border-radius: 10px; justify-content: center; }}
</style>
""", unsafe_allow_html=True)

# 🛠️ Safe Float & Hierarchy Builder
def safe_float(val, default=0.0):
    try: return float(val) if val else default
    except: return default

if 'executives' not in db_data: db_data['executives'] = {}
exec_data_root = db_data['executives']

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
            jr_pct = safe_float(child_profile.get('percentage_exec', 0.0))
            jr_rs = safe_float(child_profile.get('rupees_exec', 0.0))
            return jr_pct, jr_rs, child_actual
    return 0.0, 0.0, None

def prepare_edit(ex_name, details):
    st.session_state['form_exec_name'] = ex_name
    st.session_state['form_senior_name'] = details.get('senior_name', '')
    st.session_state['form_exec_mobile'] = details.get('mobile', '')
    st.session_state['ep'] = safe_float(details.get('percentage_exec', 0.0))
    st.session_state['er'] = safe_float(details.get('rupees_exec', 0.0))
    st.session_state['edit_mode_active'] = True
    st.session_state['old_edit_name'] = ex_name

def clear_edit_fields():
    for k in ['form_exec_name', 'form_senior_name', 'form_exec_mobile', 'ep', 'er', 'edit_mode_active', 'old_edit_name']:
        st.session_state.pop(k, None)

st.markdown("<h1 style='text-align: center;'>👑 Executive & Master Commission Panel</h1>", unsafe_allow_html=True)

# Admin section
if user_role == 'admin':
    is_editing = st.session_state.get('edit_mode_active', False)
    st.subheader("✏️ Edit Partner Profile" if is_editing else "🏗️ Add New Partner Account & Assign Slab")
    with st.form("commission_form"):
        col_a1, col_a2 = st.columns(2)
        exec_name = col_a1.text_input("👨‍💼 Executive Full Name (Login ID) *", key="form_exec_name")
        senior_name = col_a2.text_input("👴 Immediate Senior / Upline Name", key="form_senior_name")
        exec_mobile = col_a1.text_input("📱 10-Digit Mobile Number (Account Password) *", max_chars=10, key="form_exec_mobile")
        col_c1, col_c2 = st.columns(2)
        exec_pct = col_c1.number_input("📈 Percentage Slab (%)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        exec_rs = col_c2.number_input("💵 Fixed Payout Slab (₹)", min_value=0.0, step=500.0, key="er")
        
        if is_editing:
            col_btn1, col_btn2 = st.columns(2)
            save_comm = col_btn1.form_submit_button("💾 Update Partner Profile", use_container_width=True)
            if col_btn2.form_submit_button("❌ Cancel", use_container_width=True): clear_edit_fields(); st.rerun()
        else: save_comm = st.form_submit_button("💾 Register Profile & Set Slab", use_container_width=True)
        
        if save_comm:
            exec_clean = exec_name.strip()
            if exec_clean and exec_mobile:
                st.session_state.db_projects['executives'][exec_clean] = {"name": exec_clean, "mobile": exec_mobile.strip(), "senior_name": senior_name.strip() if senior_name.strip() else "Direct", "percentage_exec": exec_pct, "rupees_exec": exec_rs, "last_updated": str(datetime.date.today())}
                if database.save_db_data(): st.success("🎉 Updated!"); clear_edit_fields(); st.rerun()

# Ledger Engine
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📊 Advanced Statement & Payout Ledger")
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
if user_role != 'admin': exec_clean_list = [k for k in exec_clean_list if k.lower() in ([curr_user.lower()] + [d.lower() for d in get_all_downlines(curr_user)])]

if exec_clean_list:
    col_s1, col_s2, col_s3 = st.columns(3)
    search_exec = col_s1.selectbox("🔎 Select Executive", exec_clean_list)
    start_date = col_s2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col_s3.date_input("📅 End Date", datetime.date.today())
    comm_filter = st.radio("🎯 View Type:", ["All (Self + Team)", "⭐ Self", "👥 Team"], horizontal=True)

    if st.button("🔍 Generate Comprehensive Ledger", use_container_width=True):
        search_exec_clean = str(search_exec).strip().lower()
        all_downlines_lower = [d.lower() for d in get_all_downlines(search_exec_clean)]
        statement_rows = []
        s_no = 1
        project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data)]
        for p_name in project_names:
            p_info = db_data[p_name]
            for plot_id, plot_info in p_info.get('plots', {}).items():
                if isinstance(plot_info, dict) and str(plot_info.get('status', '')).lower() == 'booked':
                    plot_exec = str(plot_info.get('executive_name', '')).strip().lower()
                    if (comm_filter == "⭐ Self" and plot_exec != search_exec_clean) or (comm_filter == "👥 Team" and plot_exec not in all_downlines_lower): continue
                    
                    sr_profile = exec_data_root[search_exec]
                    sr_pct = safe_float(sr_profile.get('percentage_exec', 0.0))
                    sr_rs = safe_float(sr_profile.get('rupees_exec', 0.0))
                    
                    # Logic to calculate commission
                    jr_pct_deduction, jr_rs_deduction, _ = get_diff_deduction(plot_info.get('executive_name', ''), search_exec_clean)
                    final_pct = max(0.0, sr_pct - jr_pct_deduction) if plot_exec != search_exec_clean else sr_pct
                    final_rs = max(0.0, sr_rs - jr_rs_deduction) if plot_exec != search_exec_clean else sr_rs
                    
                    for pmt in [{'date_str': str(plot_info.get('booking_date', '')), 'type': 'Booking', 'amt': safe_float(plot_info.get('token_amount', 0.0))}] + [{'date_str': str(p.get('date', '')), 'type': str(p.get('remarks', 'Installment')), 'amt': safe_float(p.get('amount', 0.0))} for p in plot_info.get('partial_payments', [])]:
                        if pmt['amt'] > 0:
                            p_date = datetime.datetime.strptime(pmt['date_str'], "%Y-%m-%d").date() if pmt['date_str'] else datetime.date.today()
                            if start_date <= p_date <= end_date:
                                gross = (pmt['amt'] * final_pct / 100.0) if 'Percentage' in p_info.get('comm_type', '') else (final_rs if pmt['type']=='Booking' else 0)
                                tds = (gross * 2.0) / 100.0
                                statement_rows.append({"S.No.": s_no, "Client": plot_info.get('customer_name', 'N/A'), "Plot": plot_id, "Type": pmt['type'], "Paid": pmt['amt'], "Date": p_date.strftime("%d-%m-%Y"), "Gross (₹)": round(gross, 2), "TDS (₹)": round(tds, 2), "Net Payout (₹)": int(round(gross - tds))})
                                s_no += 1

        if statement_rows:
            df_statement = pd.DataFrame(statement_rows)
            print_commission_header(search_exec, start_date, end_date)
            st.dataframe(df_statement, use_container_width=True, hide_index=True)
            t_gross, t_tds, t_net = df_statement['Gross (₹)'].sum(), df_statement['TDS (₹)'].sum(), df_statement['Net Payout (₹)'].sum()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
            c2.metric("Total TDS Deduction", f"₹ {t_tds:,.2f}")
            c3.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
            c_b1, c_b2 = st.columns(2)
            csv = df_statement.to_csv(index=False).encode('utf-8-sig')
            c_b1.download_button("🖨️ Download Excel", csv, "Statement.csv", "text/csv", use_container_width=True)
            wa_url = f"https://wa.me/?text=Statement for {search_exec}: Net Pay: ₹{t_net:,.0f}"
            c_b2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)
