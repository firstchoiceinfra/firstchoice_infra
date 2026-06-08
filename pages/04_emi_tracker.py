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
# 📊 DATA EXTRACTION ENGINE (Find Pending Dues)
# =========================================================
all_downlines_lower = [d.lower() for d in get_all_downlines(curr_user)]

pending_records = []
payment_map = {} # Admin Payment System Mapping
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
                is_authorized = False
                if user_role == 'admin':
                    is_authorized = True
                elif plot_exec == curr_user.lower() or plot_exec in all_downlines_lower:
                    is_authorized = True
                
                if is_authorized:
                    selling_rate = safe_float(plot_info.get('selling_rate', 0.0))
                    
                    if selling_rate <= 0:
                        continue
                        
                    token_amt = safe_float(plot_info.get('token_amount', 0.0))
                    
                    partial_payments = plot_info.get('partial_payments', [])
                    total_emi_paid = sum(safe_float(pmt.get('amount', 0.0)) for pmt in partial_payments)
                    
                    total_paid = token_amt + total_emi_paid
                    net_pending = selling_rate - total_paid
                    
                    if net_pending > 0:
                        total_company_pending += net_pending
                        
                        b_date = plot_info.get('booking_date', plot_info.get('receipt_date', 'N/A'))
                        customer = str(plot_info.get('customer_name', 'N/A')).title()
                        phone = str(plot_info.get('phone', ''))
                        booked_str = plot_info.get('booked_plots_str', plot_id)
                        
                        # Store in map for Admin Payment Form
                        opt_key = f"{p_name} | P-{booked_str} | {customer} (Due: ₹{net_pending:,.0f})"
                        payment_map[opt_key] = {'proj': p_name, 'plot': plot_id}
                        
                        # WhatsApp Link
                        wa_phone = phone.replace(' ', '').replace('+', '').strip()
                        if len(wa_phone) == 10: wa_phone = "91" + wa_phone
                        wa_msg = f"🌟 *FirstChoice Infra - Payment Reminder* 🌟\n\nDear *{customer}*,\nThis is a gentle reminder regarding the pending payment for your Plot *P-{booked_str}* in *{p_name}*.\n\n🔹 *Total Value:* ₹ {selling_rate:,.2f}\n✅ *Amount Paid:* ₹ {total_paid:,.2f}\n⚠️ *Pending Due:* ₹ {net_pending:,.2f}\n\nKindly clear the pending dues at the earliest. Thank you!\n\nRegards,\n*FC Infra Team*"
                        wa_url = f"https://wa.me/{wa_phone}?text={urllib.parse.quote(wa_msg)}"
                        
                        pending_records.append({
                            "Project": p_name,
                            "Plot(s)": f"P-{booked_str}",
                            "Booking Date": b_date,
                            "Client Name": customer,
                            "Contact": phone,
                            "Executive": str(plot_info.get('executive_name', 'Direct')).title(),
                            "Total Value (₹)": selling_rate,
                            "Down Payment/Token (₹)": token_amt,
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
    curr_cols = ["Total Value (₹)", "Down Payment/Token (₹)", "Total Paid (₹)", "🚨 Net Pending (₹)"]
    for c in curr_cols:
        df_display[c] = df_display[c].apply(lambda x: f"₹ {x:,.0f}")
        
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
    st.write("<br>", unsafe_allow_html=True)
    
    clean_csv = df_pending.drop(columns=['WhatsApp']).to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Download Pending Report (Excel)", clean_csv, "Pending_EMI_Report.csv", "text/csv")

else:
    st.success("🎉 Great News! There are no pending dues in your authorized network.")
    st.balloons()

# =========================================================
# 🔒 NEW: SECURE PAYMENT REGISTRATION DESK (ADMIN ONLY)
# =========================================================
st.markdown("<br><hr>", unsafe_allow_html=True)
st.subheader("💳 EMI Payment Registration Desk")

if user_role == 'admin':
    if pending_records:
        st.info("💡 Select the client's account below to securely register their new EMI payment.")
        with st.form("admin_emi_payment_form"):
            selected_key = st.selectbox("📌 Select Pending Account:", list(payment_map.keys()))
            
            col_p1, col_p2, col_p3 = st.columns(3)
            pay_amt = col_p1.number_input("💸 Received Amount (₹)", min_value=1.0, step=500.0)
            pay_date = col_p2.date_input("📅 Date of Receipt", datetime.date.today())
            pay_mode = col_p3.selectbox("🏪 Payment Mode", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
            
            pay_remarks = st.text_input("📝 Remarks / Transaction ID (Optional)")
            
            submit_pay = st.form_submit_button("✅ Register Payment & Update Ledger", use_container_width=True)
            
            if submit_pay:
                target_proj = payment_map[selected_key]['proj']
                target_plot = payment_map[selected_key]['plot']
                
                new_pmt = {
                    "date": str(pay_date),
                    "amount": pay_amt,
                    "mode": pay_mode,
                    "remarks": pay_remarks if pay_remarks.strip() != "" else "Installment Payment"
                }
                
                # Check and append new payment safely
                if 'partial_payments' not in st.session_state.db_projects[target_proj]['plots'][target_plot]:
                    st.session_state.db_projects[target_proj]['plots'][target_plot]['partial_payments'] = []
                    
                st.session_state.db_projects[target_proj]['plots'][target_plot]['partial_payments'].append(new_pmt)
                
                if database.save_db_data():
                    st.success("🎉 Success! The payment has been securely added to the Master Ledger.")
                    st.rerun()
else:
    # एग्जीक्यूटिव के लिए स्ट्रिक्ट लॉक मैसेज
    st.error("🔒 **ACTION RESTRICTED: ADMINISTRATIVE RIGHTS REQUIRED**")
    st.info("💡 Executives are authorized to view pending dues and send reminders only. You cannot add or modify EMI payments. Please direct the client to the Admin Desk for payment clearance.")

