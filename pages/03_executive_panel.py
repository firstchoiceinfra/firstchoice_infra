import streamlit as st
import database
import datetime
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Channel")

# --- 2. Security Check (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 Security Alert: You do not have permission to access the Commission Panel!")
    st.stop()

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
.ledger-box {{ background-color: #ffffff; border-left: 4px solid {p_color}; padding: 6px 12px !important; border-radius: 6px; box-shadow: 0px 1px 3px rgba(0,0,0,0.05); margin-bottom: 4px !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{ font-size: 11px !important; font-weight: 600 !important; color: #475569 !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ font-size: 14px !important; font-weight: 700 !important; color: #0f172a !important; }}
</style>
""", unsafe_allow_html=True)

# 🛠️ Safe Float Function
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return float(default)
        return float(val)
    except:
        return float(default)

# 🚀 SMART HIERARCHY BUILDER (For Inventory Dashboard Privacy & Permissions)
if 'executives' not in db_data:
    db_data['executives'] = {}

exec_data_root = db_data['executives']
team_hierarchy = {}
for ex_name, ex_details in exec_data_root.items():
    s_name = str(ex_details.get('senior_name', '')).strip()
    if s_name and s_name.lower() != "direct" and s_name != "":
        if s_name not in team_hierarchy:
            team_hierarchy[s_name] = []
        team_hierarchy[s_name].append(ex_name)

# Save hierarchy to cloud so Inventory Dashboard can read it
db_data['team_hierarchy'] = team_hierarchy

# --- Dynamic Safe-Edit Callback Engine ---
def prepare_edit(ex_name, details):
    st.session_state['form_exec_name'] = ex_name
    st.session_state['form_senior_name'] = details.get('senior_name', '')
    st.session_state['form_exec_mobile'] = details.get('mobile', '')
    st.session_state['ep'] = safe_float(details.get('percentage_exec', 0.0))
    st.session_state['sp'] = safe_float(details.get('percentage_senior', 0.0))
    st.session_state['er'] = safe_float(details.get('rupees_exec', 0.0))
    st.session_state['sr'] = safe_float(details.get('rupees_senior', 0.0))
    st.session_state['edit_mode_active'] = True
    st.session_state['old_edit_name'] = ex_name

def clear_edit_fields():
    for k in ['form_exec_name', 'form_senior_name', 'form_exec_mobile', 'ep', 'sp', 'er', 'sr', 'edit_mode_active', 'old_edit_name']:
        st.session_state.pop(k, None)

st.markdown("<h1 style='text-align: center;'>👑 Executive & Commission Channel Panel</h1>", unsafe_allow_html=True)

# --- Main Setup Profile Form ---
is_editing = st.session_state.get('edit_mode_active', False)
st.subheader("✏️ Edit Partner Profile & Commissions (Update Mode)" if is_editing else "🏗️ Add New Partner Account & Commission Structure")

with st.form("commission_form"):
    st.markdown("#### 👤 Associate Personal Credentials")
    col_a1, col_a2 = st.columns(2)
    exec_name = col_a1.text_input("👨‍💼 Executive Full Name (Login ID) *", key="form_exec_name")
    senior_name = col_a2.text_input("👨‍💼 Senior Chain Head Name (Upline)", key="form_senior_name")
    exec_mobile = col_a1.text_input("📱 10-Digit Mobile Number (Account Password) *", max_chars=10, key="form_exec_mobile")
    st.caption("⚠️ *Note: The Executive Name will serve as their Login User ID, and the Mobile Number will be their Login Password.*")

    st.markdown("#### 💰 Global Master Commission Engine Configuration")
    st.info("💡 Direct Sale: What they earn on their own sale. Team Sale (Senior Split): What goes to their Senior when they sell.")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("<h5 style='color: #0d9488;'>📈 Channel 1: Percentage-Based Rule (%)</h5>", unsafe_allow_html=True)
        exec_pct = st.number_input("Executive Split (Self Sale %)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        senior_pct = st.number_input("Senior Split (Difference % to Upline)", min_value=0.0, max_value=100.0, step=0.1, key="sp")
    with col_c2:
        st.markdown("<h5 style='color: #b45309;'>💵 Channel 2: Fixed Cash Rule (Fixed ₹)</h5>", unsafe_allow_html=True)
        exec_rs = st.number_input("Executive Payout (Self Sale Fixed ₹)", min_value=0.0, step=500.0, key="er")
        senior_rs = st.number_input("Senior Payout (Difference Fixed ₹ to Upline)", min_value=0.0, step=500.0, key="sr")

    st.write("")
    if is_editing:
        col_btn1, col_btn2 = st.columns(2)
        save_comm = col_btn1.form_submit_button("💾 Update Partner Profile", use_container_width=True)
        if col_btn2.form_submit_button("❌ Cancel / Abort", use_container_width=True):
            clear_edit_fields()
            st.rerun()
    else:
        save_comm = st.form_submit_button("💾 Register Profile & Activate Credentials", use_container_width=True)

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
                "percentage_exec": exec_pct, "percentage_senior": senior_pct,
                "rupees_exec": exec_rs, "rupees_senior": senior_rs,
                "last_updated": str(datetime.date.today())
            }
            if database.save_db_data():
                st.success("🎉 Associate registry & Team Hierarchy updated successfully!")
                clear_edit_fields()
                st.rerun()

# --- Live Statement Ledger Engine (With Downline Difference Logic) ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📊 Master Commission Statement (Self + Team Business)")
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if exec_clean_list:
    col_s1, col_s2, col_s3 = st.columns(3)
    search_exec = col_s1.selectbox("🔎 Select Executive", exec_clean_list)
    start_date = col_s2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col_s3.date_input("📅 End Date", datetime.date.today())

    if st.button("🔍 Generate Real-Time Agency Statement", use_container_width=True):
        search_exec_clean = str(search_exec).strip().lower()
        
        # 🔗 FIND ALL DIRECT DOWNLINES FOR DIFFERENCE COMMISSION
        downline_keys = [k for k, v in exec_data_root.items() if str(v.get('senior_name', '')).strip().lower() == search_exec_clean]
        downline_keys_lower = [k.lower() for k in downline_keys]
        
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
                        # 🎯 Check if sale is by Self OR Downline
                        is_direct = (plot_exec == search_exec_clean)
                        is_downline = (plot_exec in downline_keys_lower)
                        
                        if is_direct or is_downline:
                            
                            # --- DETERMINE COMMISSION RATES BASED ON SALE TYPE ---
                            if is_direct:
                                busi_type = "⭐ Direct Sale"
                                ex_profile = exec_data_root[search_exec]
                                base_pct = safe_float(ex_profile.get('percentage_exec', 0.0))
                                base_rs = safe_float(ex_profile.get('rupees_exec', 0.0))
                            else:
                                dl_actual_key = next(k for k in downline_keys if k.lower() == plot_exec)
                                dl_profile = exec_data_root[dl_actual_key]
                                busi_type = f"👥 Team Sale ({dl_actual_key})"
                                # Difference comm comes from Downline's 'Senior Split'
                                base_pct = safe_float(dl_profile.get('percentage_senior', 0.0))
                                base_rs = safe_float(dl_profile.get('rupees_senior', 0.0))

                            # 1️⃣ Net Commission % Calculation
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
                                net_comm_pct = max(0.0, base_pct - disc_pct_reduction)
                            else:
                                net_comm_pct = base_pct

                            # 2️⃣ Scan Booking Token
                            b_date_str = str(plot_info.get('booking_date', plot_info.get('receipt_date', ''))).strip()
                            b_date = datetime.date.today()
                            if b_date_str:
                                try: b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                                except:
                                    try: b_date = datetime.datetime.strptime(b_date_str, "%d-%m-%Y").date()
                                    except: pass
                               
                            if start_date <= b_date <= end_date:
                                token_amt = safe_float(plot_info.get('token_amount', plot_info.get('received_amount', 0.0)))
                                if token_amt > 0 and (base_pct > 0 or base_rs > 0): # Only add if comm > 0
                                    if "Percentage" in p_mode:
                                        gross_comm = (token_amt * net_comm_pct) / 100.0
                                    else:
                                        gross_comm = base_rs
                                       
                                    tds_amt = (gross_comm * 2.0) / 100.0
                                    net_comm = gross_comm - tds_amt
                                   
                                    statement_rows.append({
                                        "S.No.": s_no,
                                        "Sale Origin": busi_type,
                                        "Client Name": str(plot_info.get('customer_name', 'N/A')).title(),
                                        "Project (Location)": f"{p_name} ({p_mauza})",
                                        "Plot No.": plot_id,
                                        "Payment Type": "Booking Token",
                                        "Paid Amt (₹)": f"{token_amt:,.0f}",
                                        "Payment Date": b_date.strftime("%d-%m-%Y"),
                                        "Net Comm %": f"{net_comm_pct:.1f} %",
                                        "Gross Comm (₹)": round(gross_comm, 2),
                                        "2% TDS (₹)": round(tds_amt, 2),
                                        "Net Payout (₹)": int(round(net_comm))
                                    })
                                    s_no += 1
                           
                            # 3️⃣ Scan EMI (Partial Payments)
                            partial_payments = plot_info.get('partial_payments', [])
                            for pmt in partial_payments:
                                pmt_date_str = str(pmt.get('date', '')).strip()
                                pmt_date_obj = datetime.date.today()
                                if pmt_date_str:
                                    try: pmt_date_obj = datetime.datetime.strptime(pmt_date_str, "%Y-%m-%d").date()
                                    except:
                                        try: pmt_date_obj = datetime.datetime.strptime(pmt_date_str, "%d-%m-%Y").date()
                                        except: pass
                               
                                if start_date <= pmt_date_obj <= end_date:
                                    emi_amt = safe_float(pmt.get('amount', 0.0))
                                    if emi_amt > 0 and (base_pct > 0 or base_rs > 0):
                                        if "Percentage" in p_mode:
                                            gross_comm = (emi_amt * net_comm_pct) / 100.0
                                        else:
                                            gross_comm = 0 # Fixed amount usually given on booking only
                                           
                                        tds_amt = (gross_comm * 2.0) / 100.0
                                        net_comm = gross_comm - tds_amt
                                       
                                        statement_rows.append({
                                            "S.No.": s_no,
                                            "Sale Origin": busi_type,
                                            "Client Name": str(plot_info.get('customer_name', 'N/A')).title(),
                                            "Project (Location)": f"{p_name} ({p_mauza})",
                                            "Plot No.": plot_id,
                                            "Payment Type": str(pmt.get('remarks', 'Installment Payment')),
                                            "Paid Amt (₹)": f"{emi_amt:,.0f}",
                                            "Payment Date": pmt_date_obj.strftime("%d-%m-%Y"),
                                            "Net Comm %": f"{net_comm_pct:.1f} %",
                                            "Gross Comm (₹)": round(gross_comm, 2),
                                            "2% TDS (₹)": round(tds_amt, 2),
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
            c_sum3.metric("Total TDS Deduction", f"₹ {df_statement['2% TDS (₹)'].sum():,.2f}")
            c_sum4.metric("🏆 Grand Net Payable", f"₹ {df_statement['Net Payout (₹)'].sum():,.2f}")
           
            csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Multi-Level Statement File", csv_data, f"MLM_Statement_{search_exec}.csv", "text/csv", use_container_width=True)
        else:
            st.info(f"🔍 '{search_exec}' या उनकी टीम के लिए {start_date.strftime('%d-%m-%Y')} से {end_date.strftime('%d-%m-%Y')} के बीच कोई रिकॉर्ड नहीं मिला।")

# --- Active Partner Registry (6-Column Grid Layout) ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("<h4 style='font-size:16px;'>📋 Current Active Partners & Login Credentials</h4>", unsafe_allow_html=True)
exec_clean_list_view = {k: v for k, v in exec_data_root.items() if isinstance(v, dict) and 'name' in v}

if not exec_clean_list_view:
    st.caption("No registered partners available.")
else:
    for ex_name, p_details in exec_clean_list_view.items():
        with st.container():
            st.markdown(f"""
            <div class="ledger-box">
                <span style="font-size: 13px; font-weight: bold; color: {p_color};">👨‍💼 Partner ID: {ex_name}</span>
                <span style="float: right; background-color: #f1f5f9; padding: 1px 5px; border-radius: 4px; font-size:11px; color: #475569; font-weight: 600;">🔑 Password (Mob): {p_details.get('mobile','N/A')}</span>
                <br><span style="font-size: 11px; color: #64748b;">👴 <b>Senior Upline:</b> {p_details.get('senior_name','N/A')} | 📅 Updated: {p_details.get('last_updated','N/A')}</span>
            </div>
            """, unsafe_allow_html=True)
           
            c_m1, c_m2, c_m3, c_m4, c_m5, c_m6 = st.columns([1.0, 1.0, 1.1, 1.1, 0.7, 0.7])
            c_m1.metric("Self Sale (%)", f"{p_details.get('percentage_exec', 0)} %")
            c_m2.metric("Diff to Upline (%)", f"{p_details.get('percentage_senior', 0)} %")
            c_m3.metric("Self Sale (₹)", f"₹ {p_details.get('rupees_exec', 0)}")
            c_m4.metric("Diff to Upline (₹)", f"₹ {p_details.get('rupees_senior', 0)}")
           
            with c_m5:
                st.button("✏️ Edit", key=f"edit_{ex_name}", use_container_width=True, on_click=prepare_edit, args=(ex_name, p_details))
            with c_m6:
                if st.button("🗑️ Delete", key=f"del_{ex_name}", use_container_width=True):
                    st.session_state.db_projects['executives'].pop(ex_name, None)
                    database.save_db_data()
                    st.success(f"Partner Account '{ex_name}' successfully removed!")
                    st.rerun()
            st.markdown("<div style='margin-bottom: 12px; border-bottom: 1px dashed #e2e8f0;'></div>", unsafe_allow_html=True)

