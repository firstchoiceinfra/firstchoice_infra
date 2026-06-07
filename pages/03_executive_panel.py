import streamlit as st
import database
import datetime
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Channel")

# --- 2. Security Check (Login Check ONLY, Role check applied below) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

# Get Current User Info
curr_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# --- 3. Cloud Database Integration ---
database.init_db()
db_data = st.session_state.db_projects

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
/* Radio button styling */
div.row-widget.stRadio > div {{ flex-direction:row; background-color: #f1f5f9; padding: 10px; border-radius: 10px; justify-content: center; }}
</style>
""", unsafe_allow_html=True)

# 🛠️ Safe Float Function
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return float(default)
        return float(val)
    except: return float(default)

# 🚀 SMART HIERARCHY BUILDER 
if 'executives' not in db_data:
    db_data['executives'] = {}

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
        
        if not curr or curr.lower() == 'direct':
            break

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

# =========================================================
# 🔒 ADMIN ONLY: SETUP & EDIT PARTNER PROFILE
# =========================================================
if user_role == 'admin':
    is_editing = st.session_state.get('edit_mode_active', False)
    st.subheader("✏️ Edit Partner Profile" if is_editing else "🏗️ Add New Partner Account & Assign Slab")

    with st.form("commission_form"):
        st.markdown("#### 👤 Associate Credentials & Hierarchy")
        col_a1, col_a2 = st.columns(2)
        exec_name = col_a1.text_input("👨‍💼 Executive Full Name (Login ID) *", key="form_exec_name")
        senior_name = col_a2.text_input("👴 Immediate Senior / Upline Name", key="form_senior_name")
        exec_mobile = col_a1.text_input("📱 10-Digit Mobile Number (Account Password) *", max_chars=10, key="form_exec_mobile")
        st.caption("⚠️ *System Auto-calculates Difference Commission based on the Senior's slab minus the Junior's slab.*")

        st.markdown("#### 💰 Executive Master Slab (Self Business Target)")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            exec_pct = st.number_input("📈 Percentage Slab (%)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        with col_c2:
            exec_rs = st.number_input("💵 Fixed Payout Slab (₹)", min_value=0.0, step=500.0, key="er")

        st.write("")
        if is_editing:
            col_btn1, col_btn2 = st.columns(2)
            save_comm = col_btn1.form_submit_button("💾 Update Partner Profile", use_container_width=True)
            if col_btn2.form_submit_button("❌ Cancel / Abort", use_container_width=True):
                clear_edit_fields()
                st.rerun()
        else:
            save_comm = st.form_submit_button("💾 Register Profile & Set Slab", use_container_width=True)

        if save_comm:
            if exec_name.strip() == "" or exec_mobile.strip() == "":
                st.error("🚨 Full Name and Mobile Number are mandatory fields!")
            elif len(exec_mobile.strip()) < 10:
                st.error("🚨 Please enter a valid 10-digit mobile number layout!")
            else:
                exec_clean = exec_name.strip()
                if is_editing and 'old_edit_name' in st.session_state:
                    old_name = st.session_state['old_edit_name']
                    if old_name != exec_clean:
                        st.session_state.db_projects['executives'].pop(old_name, None)
               
                st.session_state.db_projects['executives'][exec_clean] = {
                    "name": exec_clean, "mobile": exec_mobile.strip(),
                    "senior_name": senior_name.strip() if senior_name.strip() else "Direct",
                    "percentage_exec": exec_pct, 
                    "rupees_exec": exec_rs,
                    "last_updated": str(datetime.date.today())
                }
                if database.save_db_data():
                    st.success("🎉 Associate registry & Hierarchy Slab updated successfully!")
                    clear_edit_fields()
                    st.rerun()

# =========================================================
# 📊 EVERYONE: LIVE STATEMENT LEDGER ENGINE 
# =========================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📊 Advanced Statement & Payout Ledger")

exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]

if user_role != 'admin':
    allowed_list_lower = [curr_user.lower()] + [d.lower() for d in get_all_downlines(curr_user)]
    exec_clean_list = [k for k in exec_clean_list if k.lower() in allowed_list_lower]

project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if exec_clean_list:
    col_s1, col_s2, col_s3 = st.columns(3)
    search_exec = col_s1.selectbox("🔎 Select Executive for Statement", exec_clean_list)
    start_date = col_s2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col_s3.date_input("📅 End Date", datetime.date.today())

    # 🎯 NEW FEATURE: SMART FILTER RADIO BUTTONS
    comm_filter = st.radio("🎯 Select Commission View Type:", ["All (Self + Team)", "⭐ Self Commission Only", "👥 Team Commission Only"], horizontal=True)

    if st.button("🔍 Generate Comprehensive Ledger", use_container_width=True):
        search_exec_clean = str(search_exec).strip().lower()
        all_downlines_lower = [d.lower() for d in get_all_downlines(search_exec_clean)]
        
        statement_rows = []
        s_no = 1
       
        for p_name in project_names:
            p_info = db_data[p_name]
            p_mode = p_info.get('comm_type', 'Percentage (%)')
            p_mauza = p_info.get('mauza', 'Unknown')
            p_plots = p_info.get('plots', {})
            if isinstance(p_plots, list):
                p_plots = {str(idx): p for idx, p in enumerate(p_plots) if p is not None}
               
            for plot_id, plot_info in p_plots.items():
                if isinstance(plot_info, dict):
                    plot_status = str(plot_info.get('status', '')).strip().lower()
                    plot_exec = str(plot_info.get('executive_name', '')).strip().lower()
                   
                    if plot_status == 'booked':
                        is_direct = (plot_exec == search_exec_clean)
                        is_downline = (plot_exec in all_downlines_lower)

                        # 🚀 APPLYING THE FILTER LOGIC
                        if comm_filter == "⭐ Self Commission Only" and not is_direct:
                            continue
                        if comm_filter == "👥 Team Commission Only" and not is_downline:
                            continue
                        
                        if is_direct or is_downline:
                            
                            sr_profile = exec_data_root[search_exec]
                            sr_pct = safe_float(sr_profile.get('percentage_exec', 0.0))
                            sr_rs = safe_float(sr_profile.get('rupees_exec', 0.0))

                            if is_direct:
                                busi_type = "⭐ Direct Sale"
                                final_calc_pct = sr_pct
                                final_calc_rs = sr_rs
                                display_comm_str = f"{sr_pct}%"
                            else:
                                jr_pct_deduction, jr_rs_deduction, direct_branch_name = get_diff_deduction(plot_info.get('executive_name', ''), search_exec_clean)
                                busi_type = f"👥 Team Sale (Via: {direct_branch_name})"
                                final_calc_pct = max(0.0, sr_pct - jr_pct_deduction)
                                final_calc_rs = max(0.0, sr_rs - jr_rs_deduction)
                                display_comm_str = f"{final_calc_pct}% (Diff)"

                            plot_area = safe_float(plot_info.get('plot_area', plot_info.get('area', 1116.23)))
                            company_rate = safe_float(plot_info.get('company_rate', p_info.get('base_rate', 700.0)))
                            if company_rate <= 0: company_rate = 700.0
                           
                            discount_val = safe_float(plot_info.get('discount', 14.0))
                            if discount_val > 1000:
                                disc_per_sqft = discount_val / plot_area if plot_area > 0 else 0.0
                            else:
                                disc_per_sqft = discount_val
                           
                            if "Percentage" in p_mode:
                                disc_pct_reduction = (disc_per_sqft / company_rate) * 100.0
                                net_comm_pct = max(0.0, final_calc_pct - disc_pct_reduction)
                            else:
                                net_comm_pct = final_calc_pct

                            all_payments = []
                            b_date_str = str(plot_info.get('booking_date', plot_info.get('receipt_date', ''))).strip()
                            token_amt = safe_float(plot_info.get('token_amount', plot_info.get('received_amount', 0.0)))
                            all_payments.append({'date_str': b_date_str, 'type': 'Booking Token', 'amt': token_amt})
                            
                            for pmt in plot_info.get('partial_payments', []):
                                all_payments.append({'date_str': str(pmt.get('date', '')).strip(), 'type': str(pmt.get('remarks', 'Installment Payment')), 'amt': safe_float(pmt.get('amount', 0.0))})

                            for pmt_data in all_payments:
                                p_date = datetime.date.today()
                                if pmt_data['date_str']:
                                    try: p_date = datetime.datetime.strptime(pmt_data['date_str'], "%Y-%m-%d").date()
                                    except:
                                        try: p_date = datetime.datetime.strptime(pmt_data['date_str'], "%d-%m-%Y").date()
                                        except: pass
                               
                                if start_date <= p_date <= end_date:
                                    paid_amt = pmt_data['amt']
                                    if paid_amt > 0 and (final_calc_pct > 0 or final_calc_rs > 0): 
                                        if "Percentage" in p_mode:
                                            gross_comm = (paid_amt * net_comm_pct) / 100.0
                                        else:
                                            gross_comm = final_calc_rs if pmt_data['type'] == 'Booking Token' else 0
                                           
                                        tds_amt = (gross_comm * 2.0) / 100.0
                                        net_comm = gross_comm - tds_amt
                                       
                                        statement_rows.append({
                                            "S.No.": s_no,
                                            "Sale Origin": busi_type,
                                            "Client Name": str(plot_info.get('customer_name', 'N/A')).title(),
                                            "Project (Location)": f"{p_name} ({p_mauza})",
                                            "Plot": plot_id,
                                            "Payment Type": pmt_data['type'],
                                            "Paid Amt (₹)": f"{paid_amt:,.0f}",
                                            "Date": p_date.strftime("%d-%m-%Y"),
                                            "Slab": display_comm_str,
                                            "Gross (₹)": round(gross_comm, 2),
                                            "TDS (₹)": round(tds_amt, 2),
                                            "Net Payout (₹)": int(round(net_comm))
                                        })
                                        s_no += 1
       
        if statement_rows:
            df_statement = pd.DataFrame(statement_rows)
            st.dataframe(df_statement, use_container_width=True, hide_index=True)
            st.write("---")
            
            total_direct = df_statement[df_statement['Sale Origin'] == '⭐ Direct Sale']['Net Payout (₹)'].sum()
            total_team = df_statement[df_statement['Sale Origin'].str.contains('Team')]['Net Payout (₹)'].sum()
            
            c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
            c_sum1.metric("⭐ Total Direct Income", f"₹ {total_direct:,.2f}")
            c_sum2.metric("👥 Total Team Difference", f"₹ {total_team:,.2f}")
            c_sum3.metric("Total TDS Deduction", f"₹ {df_statement['TDS (₹)'].sum():,.2f}")
            c_sum4.metric("🏆 Grand Net Payable", f"₹ {df_statement['Net Payout (₹)'].sum():,.2f}")
           
            csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Difference Statement File", csv_data, f"MLM_Statement_{search_exec}.csv", "text/csv", use_container_width=True)
        else:
            st.info(f"🔍 '{search_exec}' के लिए {start_date.strftime('%d-%m-%Y')} से {end_date.strftime('%d-%m-%Y')} के बीच कोई रिकॉर्ड नहीं मिला।")
else:
    if not exec_clean_list:
        st.info("🚫 You currently have no associated accounts or downlines in the system.")

# =========================================================
# 🔒 ADMIN ONLY: REGISTRY & PASSWORDS GRID
# =========================================================
if user_role == 'admin':
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.markdown("<h4 style='font-size:16px;'>📋 Master Slab Registry & Login Credentials</h4>", unsafe_allow_html=True)
    exec_clean_list_view = {k: v for k, v in exec_data_root.items() if isinstance(v, dict) and 'name' in v}

    if not exec_clean_list_view

