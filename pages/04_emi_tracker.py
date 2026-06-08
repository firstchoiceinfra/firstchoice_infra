import streamlit as st
import pandas as pd
import database
import datetime
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - EMI & Pending Dues Tracker")

# --- 2. Security Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

curr_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# --- 3. Database Sync ---
database.init_db()
db_data = st.session_state.db_projects

# ====================================================================
# 🎨 Premium UI & Glassmorphism Theme
# ====================================================================
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
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 1.5rem; margin-bottom: 1.5rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 900; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 8px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{ font-size: 12px !important; font-weight: 700 !important; color: #475569 !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ font-size: 20px !important; font-weight: 800 !important; color: #b91c1c !important; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>💸 Live EMI & Pending Recovery Tracker</h1>", unsafe_allow_html=True)

# 🛠️ Safe Float Function
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return float(default)
        return float(val)
    except: return float(default)

# 🚀 SMART HIERARCHY BUILDER 
exec_data_root = db_data.get('executives', {})

def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data_root.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name))
    return list(set(downlines))

# =========================================================
# 📊 DATA EXTRACTION ENGINE (WITH SMART AUTO-CALCULATOR)
# =========================================================
all_downlines_lower = [d.lower() for d in get_all_downlines(curr_user)]

pending_records = []
payment_map = {} 
all_booked_map = {} 

total_company_pending = 0.0
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

for p_name in project_names:
    p_info = db_data[p_name]
    p_plots = p_info.get('plots', {})
    
    if isinstance(p_plots, list):
        p_plots = {str(idx): p for idx, p in enumerate(p_plots) if p is not None}
        
    for plot_id, plot_info in p_plots.items():
        if isinstance(plot_info, dict):
            status = str(plot_info.get('status', '')).strip().lower()
            plot_exec = str(plot_info.get('executive_name', '')).strip().lower()
            
            if status == 'booked':
                # 🎯 AUTO-CALCULATOR LOGIC START
                plot_area = safe_float(plot_info.get('plot_area', plot_info.get('area', 0.0)))
                rate_per_sqft = safe_float(plot_info.get('selling_rate', 0.0))
                
                if rate_per_sqft > 100000:
                    total_deal_value = rate_per_sqft
                else:
                    total_deal_value = plot_area * rate_per_sqft
                
                if total_deal_value <= 0:
                    continue 
                # 🎯 AUTO-CALCULATOR LOGIC END

                customer = str(plot_info.get('customer_name', 'N/A')).title()
                booked_str = plot_info.get('booked_plots_str', plot_id)
                token_slip = str(plot_info.get('token_slip_no', 'N/A'))
                
                token_amt = safe_float(plot_info.get('token_amount', 0.0))
                partial_payments = plot_info.get('partial_payments', [])
                total_emi_paid = sum(safe_float(pmt.get('amount', 0.0)) for pmt in partial_payments)
                
                total_paid = token_amt + total_emi_paid
                net_pending = total_deal_value - total_paid

                full_key = f"{p_name} | P-{booked_str} | {customer}"
                all_booked_map[full_key] = {'proj': p_name, 'plot': plot_id, 'curr_slip': token_slip}
                
                opt_key = f"{p_name} | P-{booked_str} | {customer} (Total Paid: ₹{total_paid:,.0f} | Due: ₹{net_pending:,.0f})"
                payment_map[opt_key] = {'proj': p_name, 'plot': plot_id}
                
                is_authorized = False
                if user_role == 'admin':
                    is_authorized = True
                elif plot_exec == curr_user.lower() or plot_exec in all_downlines_lower:
                    is_authorized = True
                
                if is_authorized and total_deal_value > 0 and net_pending > 0:
                    total_company_pending += net_pending
                    
                    b_date = plot_info.get('booking_date', plot_info.get('receipt_date', 'N/A'))
                    phone = str(plot_info.get('phone', ''))
                    
                    wa_phone = phone.replace(' ', '').replace('+', '').strip()
                    if len(wa_phone) == 10: wa_phone = "91" + wa_phone
                    wa_msg = f"🌟 *FirstChoice Infra - Payment Reminder* 🌟\n\nDear *{customer}*,\nThis is a gentle reminder regarding the pending payment for your Plot *P-{booked_str}* in *{p_name}*.\n\n🔹 *Total Value:* ₹ {total_deal_value:,.2f}\n✅ *Amount Paid:* ₹ {total_paid:,.2f}\n⚠️ *Pending Due:* ₹ {net_pending:,.2f}\n\nKindly clear the pending dues at the earliest. Thank you!\n\nRegards,\n*FC Infra Team*"
                    wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(wa_msg)}"
                    
                    pending_records.append({
                        "Project": p_name,
                        "Plot(s)": f"P-{booked_str}",
                        "Client Name": customer,
                        "Executive": str(plot_info.get('executive_name', 'Direct')).title(),
                        "Total Value (₹)": total_deal_value,
                        "Token/Down Pmt (₹)": token_amt,
                        "Token Slip No": token_slip,
                        "Total Paid (₹)": total_paid,
                        "🚨 Net Pending (₹)": net_pending,
                        "WhatsApp": wa_url
                    })

# =========================================================
# 🎛️ DASHBOARD UI & FILTERS
# =========================================================
if pending_records:
    df_pending = pd.DataFrame(pending_records)
    
    col1, col2, col3 = st.columns(3)
    proj_filter = col1.selectbox("🏢 Filter by Project:", ["All Projects"] + list(df_pending['Project'].unique()))
    exec_filter = col2.selectbox("👨‍💼 Filter by Executive:", ["All Executives"] + list(df_pending['Executive'].unique()))
    
    if proj_filter != "All Projects":
        df_pending = df_pending[df_pending['Project'] == proj_filter]
    if exec_filter != "All Executives":
        df_pending = df_pending[df_pending['Executive'] == exec_filter]
        
    filtered_pending_total = df_pending['🚨 Net Pending (₹)'].sum()
    col3.metric("⚠️ Total Pending Dues (Filtered)", f"₹ {filtered_pending_total:,.2f}")
    
    st.write("---")
    
    df_display = df_pending.copy()
    def make_clickable(link):
        return f'<a target="_blank" href="{link}" style="background-color:#25D366;color:white;padding:5px 10px;border-radius:5px;text-decoration:none;font-size:12px;font-weight:bold;">💬 Send Reminder</a>'
    
    df_display['WhatsApp'] = df_display['WhatsApp'].apply(make_clickable)
    curr_cols = ["Total Value (₹)", "Token/Down Pmt (₹)", "Total Paid (₹)", "🚨 Net Pending (₹)"]
    for c in curr_cols:
        df_display[c] = df_display[c].apply(lambda x: f"₹ {x:,.0f}")
        
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    clean_csv = df_pending.drop(columns=['WhatsApp']).to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download Pending Report (Excel)", clean_csv, "Pending_EMI_Report.csv", "text/csv")

else:
    st.success("🎉 Great News! There are no pending dues showing in the recovery system.")

# =========================================================
# 🔒 SECURE ADMIN DESK (PAYMENT & SLIP UPDATES)
# =========================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("💳 Admin Registration & Billing Desk")

if user_role == 'admin':
    tab1, tab2 = st.tabs(["💸 Register New EMI Payment", "🧾 Update Old Token Slip No."])
    
    with tab1:
        if not payment_map:
            st.info("No booked accounts found in the database yet.")
        else:
            with st.form("admin_emi_payment_form"):
                st.caption("💡 *Note: You can add payments to any booked plot here.*")
                selected_key = st.selectbox("📌 Select Booked Account:", list(payment_map.keys()))
                
                col_p1, col_p2 = st.columns(2)
                pay_amt = col_p1.number_input("💸 Received Amount (₹) *", min_value=1.0, step=500.0)
                pay_date = col_p2.date_input("📅 Date of Receipt", datetime.date.today())
                
                col_p3, col_p4 = st.columns(2)
                pay_mode = col_p3.selectbox("🏪 Payment Mode", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
                slip_no = col_p4.text_input("🧾 Receipt / Slip Number *")
                
                pay_remarks = st.text_input("📝 Remarks / Transaction ID (Optional)")
                
                submit_pay = st.form_submit_button("✅ Register Payment & Update Ledger", use_container_width=True)
                
                if submit_pay:
                    if slip_no.strip() == "":
                        st.error("🚨 Please enter the Slip/Receipt Number!")
                    else:
                        target_proj = payment_map[selected_key]['proj']
                        target_plot = payment_map[selected_key]['plot']
                        
                        new_pmt = {
                            "date": str(pay_date),
                            "amount": pay_amt,
                            "mode": pay_mode,
                            "slip_no": slip_no.strip(),
                            "remarks": pay_remarks if pay_remarks.strip() != "" else "Installment Payment"
                        }
                        
                        # 🛠️ THE FIX: Handle List vs Dict gracefully
                        plots_ref = st.session_state.db_projects[target_proj]['plots']
                        plot_idx = int(target_plot) if isinstance(plots_ref, list) else target_plot
                        
                        if 'partial_payments' not in plots_ref[plot_idx]:
                            plots_ref[plot_idx]['partial_payments'] = []
                            
                        plots_ref[plot_idx]['partial_payments'].append(new_pmt)
                        
                        if database.save_db_data():
                            st.success("🎉 Success! Payment and Slip Number securely added to the Master Ledger.")
                            st.rerun()

    with tab2:
        if not all_booked_map:
            st.info("No bookings found to update.")
        else:
            st.caption("Use this form to add or correct the 'Token Slip Number' for initial down payments that were already registered.")
            with st.form("update_token_slip_form"):
                update_key = st.selectbox("📌 Select Booked Account:", list(all_booked_map.keys()))
                curr_slip_val = all_booked_map[update_key]['curr_slip']
                
                col_u1, col_u2 = st.columns(2)
                col_u1.info(f"**Current Token Slip No:** {curr_slip_val}")
                new_token_slip = col_u2.text_input("📝 Enter New Token Slip Number *")
                
                submit_update = st.form_submit_button("🔄 Update Token Slip", use_container_width=True)
                
                if submit_update:
                    if new_token_slip.strip() == "":
                        st.error("🚨 Please enter a valid Slip Number!")
                    else:
                        target_proj = all_booked_map[update_key]['proj']
                        target_plot = all_booked_map[update_key]['plot']
                        
                        # 🛠️ THE FIX: Handle List vs Dict gracefully
                        plots_ref = st.session_state.db_projects[target_proj]['plots']
                        plot_idx = int(target_plot) if isinstance(plots_ref, list) else target_plot
                        
                        plots_ref[plot_idx]['token_slip_no'] = new_token_slip.strip()
                        
                        if database.save_db_data():
                            st.success("🎉 Success! Initial Token Slip Number updated.")
                            st.rerun()
else:
    st.error("🔒 **ACTION RESTRICTED: ADMINISTRATIVE RIGHTS REQUIRED**")
    st.info("💡 Executives are authorized to view pending dues and send reminders only.")

