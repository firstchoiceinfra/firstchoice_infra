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
    senior_name = col_a2.text_input("👨‍💼 Senior Chain Head Name", key="form_senior_name")
    exec_mobile = col_a1.text_input("📱 10-Digit Mobile Number (Account Password) *", max_chars=10, key="form_exec_mobile")
    st.caption("⚠️ *Note: The Executive Name will serve as their Login User ID, and the Mobile Number will be their Login Password.*")

    st.markdown("#### 💰 Global Master Commission Engine Configuration")
    st.info("💡 The system will automatically deploy either Percentage or Fixed Cash profiles matching individual project layout settings.")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.markdown("<h5 style='color: #0d9488;'>📈 Channel 1: Percentage-Based Rule (% Master Rate)</h5>", unsafe_allow_html=True)
        exec_pct = st.number_input("Executive Split (%)", min_value=0.0, max_value=100.0, step=0.1, key="ep")
        senior_pct = st.number_input("Senior Split (%)", min_value=0.0, max_value=100.0, step=0.1, key="sp")
    with col_c2:
        st.markdown("<h5 style='color: #b45309;'>💵 Channel 2: Fixed Cash Rule (Fixed Amount Rate)</h5>", unsafe_allow_html=True)
        exec_rs = st.number_input("Executive Payout (Fixed ₹)", min_value=0.0, step=500.0, key="er")
        senior_rs = st.number_input("Senior Payout (Fixed ₹)", min_value=0.0, step=500.0, key="sr")

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
            if 'executives' not in st.session_state.db_projects:
                st.session_state.db_projects['executives'] = {}
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
                st.success("🎉 Associate registry updated successfully!")
                clear_edit_fields()
                st.rerun()

# --- Live Statement Ledger Engine ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("📊 Executive Commission Statement (Live Ledger Dashboard)")
exec_data_root = db_data.get('executives', {})
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if exec_clean_list:
    col_s1, col_s2, col_s3 = st.columns(3)
    search_exec = col_s1.selectbox("🔎 Select Executive", exec_clean_list)
    start_date = col_s2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
    end_date = col_s3.date_input("📅 End Date", datetime.date.today())

    if st.button("🔍 Generate Real-Time Statement", use_container_width=True):
        ex_profile = exec_data_root[search_exec]
        ex_pct = safe_float(ex_profile.get('percentage_exec', 23.0)) 
        ex_rs = safe_float(ex_profile.get('rupees_exec', 0.0))
        statement_rows = []
        s_no = 1
        
        search_exec_clean = str(search_exec).strip().lower()
       
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
                    
                    if plot_status == 'booked' and plot_exec == search_exec_clean:
                        
                        # 1️⃣ नेट कमीशन % निकालें 
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
                            net_comm_pct = max(0.0, ex_pct - disc_pct_reduction)
                        else:
                            net_comm_pct = ex_pct

                        # 2️⃣ एडवांस टोकन की एंट्री स्कैन करें
                        b_date_str = str(plot_info.get('booking_date', plot_info.get('receipt_date', ''))).strip()
                        b_date = datetime.date.today()
                        if b_date_str:
                            try: b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                            except:
                                try: b_date = datetime.datetime.strptime(b_date_str, "%d-%m-%Y").date()
                                except: pass
                           
                        if start_date <= b_date <= end_date:
                            token_amt = safe_float(plot_info.get('token_amount', plot_info.get('received_amount', 0.0)))
                            if token_amt > 0:
                                if "Percentage" in p_mode: 
                                    gross_comm = (token_amt * net_comm_pct) / 100.0 
                                else: 
                                    gross_comm = ex_rs
                                   
                                tds_amt = (gross_comm * 2.0) / 100.0
                                net_comm = gross_comm - tds_amt
                               
                                statement_rows.append({
                                    "S.No.": s_no, 
                                    "Client Name": str(plot_info.get('customer_name', 'N/A')).title(),
                                    "Project (Location)": f"{p_name} ({p_mauza})",
                                    "Plot No.": plot_id,
                                    "Payment Type": "Booking Token", 
                                    "Area (Sq.Ft)": round(plot_area, 2),
                                    "Paid Amt (₹)": f"{token_amt:,.0f}",
                                    "Payment Date": b_date.strftime("%d-%m-%Y"),
                                    "Net Comm %": f"{net_comm_pct:.1f} %",
                                    "Gross Comm (₹)": round(gross_comm, 2), 
                                    "2% TDS (₹)": round(tds_amt, 2), 
                                    "Net Payout (₹)": int(round(net_comm))
                                })
                                s_no += 1
                        
                        # 3️⃣ 🎯 EMI (Partial Payments) की एंट्री स्कैन करें
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
                                if emi_amt > 0:
                                    if "Percentage" in p_mode: 
                                        gross_comm = (emi_amt * net_comm_pct) / 100.0 
                                    else: 
                                        gross_comm = 0 
                                       
                                    tds_amt = (gross_comm * 2.0) / 100.0
                                    net_comm = gross_comm - tds_amt
                                   
                                    statement_rows.append({
                                        "S.No.": s_no, 
                                        "Client Name": str(plot_info.get('customer_name', 'N/A')).title(),
                                        "Project (Location)": f"{p_name} ({p_mauza})",
                                        "Plot No.": plot_id,
                                        "Payment Type": str(pmt.get('remarks', 'Installment Payment')), 
                                        "Area (Sq.Ft)": round(plot_area, 2),
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
            c_sum1, c_sum2, c_sum3, c_sum4 = st.columns(4)
            c_sum1.metric("Total Transactions", f"{len(df_statement)} Entries")
            c_sum2.metric("Total Gross Commission", f"₹ {df_statement['Gross Comm (₹)'].sum():,.2f}")
            c_sum3.metric("Total TDS Deduction (2%)", f"₹ {df_statement['2% TDS (₹)'].sum():,.2f}")
            c_sum4.metric("🏆 Net Payable Commission", f"₹ {df_statement['Net Payout (₹)'].sum():,.2f}")
           
            csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 Export Statement File (Print / Share on WhatsApp)", csv_data, f"Statement_{search_exec}.csv", "text/csv", use_container_width=True)
        else:
            st.info(f"🔍 '{search_exec}' के लिए {start_date.strftime('%d-%m-%Y')} से {end_date.strftime('%d-%m-%Y')} के बीच कोई बुकिंग या EMI रिकॉर्ड नहीं मिला।")

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
                <br><span style="font-size: 11px; color: #64748b;">👴 <b>Senior Chain Head:</b> {p_details.get('senior_name','N/A')} | 📅 Updated: {p_details.get('last_updated','N/A')}</span>
            </div>
            """, unsafe_allow_html=True)
           
            c_m1, c_m2, c_m3, c_m4, c_m5, c_m6 = st.columns([1.0, 1.0, 1.1, 1.1, 0.7, 0.7])
            c_m1.metric("Exec %", f"{p_details.get('percentage_exec', 0)} %")
            c_m2.metric("Senior %", f"{p_details.get('percentage_senior', 0)} %")
            c_m3.metric("Exec ₹ (Fixed)", f"₹ {p_details.get('rupees_exec', 0)}")
            c_m4.metric("Senior ₹ (Fixed)", f"₹ {p_details.get('rupees_senior', 0)}")
           
            with c_m5:
                st.button("✏️ Edit", key=f"edit_{ex_name}", use_container_width=True, on_click=prepare_edit, args=(ex_name, p_details))
            with c_m6:
                if st.button("🗑️ Delete", key=f"del_{ex_name}", use_container_width=True):
                    st.session_state.db_projects['executives'].pop(ex_name, None)
                    database.save_db_data()
                    st.success(f"Partner Account '{ex_name}' successfully removed!")
                    st.rerun()
            st.markdown("<div style='margin-bottom: 12px; border-bottom: 1px dashed #e2e8f0;'></div>", unsafe_allow_html=True)
