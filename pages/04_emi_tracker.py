import streamlit as st
import database
import datetime
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - EMI Ledger")

# --- 2. Security Interceptor Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

# --- 3. Database Initialization ---
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
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; }}
.emi-badge {{ background-color: #f1f5f9; border-left: 4px solid {p_color}; padding: 10px 15px; border-radius: 6px; font-weight: bold; margin-bottom: 15px; }}
div[data-testid="stForm"] {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; }}
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

st.markdown("<h1 style='text-align: center;'>📈 Customer EMI & Partial Payment Desk</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 30px;'>Autonomous Collection Tracking, Balance Audits & Automated Reminders</p>", unsafe_allow_html=True)

# Fetching available projects list
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

if not project_names:
    st.warning("⚠️ No active projects found in registry. Initialize blueprints first.")
    st.stop()

# --- Dropdown Selectors ---
col_s1, col_s2 = st.columns(2)
selected_project = col_s1.selectbox("🏢 Select Layout Blueprint Project", project_names)

project_plots = db_data[selected_project].get('plots', {})
if isinstance(project_plots, list):
    project_plots = {str(idx): p for idx, p in enumerate(project_plots) if p is not None}

# Filtering only Booked plots for installment tracking
booked_plots_list = [p_id for p_id, p_info in project_plots.items() if isinstance(p_info, dict) and p_info.get('status') == 'Booked']

if not booked_plots_list:
    st.info("ℹ️ No active booked plot nodes found in this project to map installments.")
    st.stop()

selected_plot = col_s2.selectbox("🎯 Select Active Booked Plot Number", sorted(booked_plots_list, key=lambda x: int(x) if x.isdigit() else 9999))

# Fetch target customer data node safely
plot_data = project_plots[selected_plot]
customer_name = plot_data.get('customer_name', 'N/A')

# 🎯 गड़बड़ी यहाँ ठीक की है: Total Plot Value सही से निकालना (Area x Rate)
plot_area = safe_float(plot_data.get('plot_area', plot_data.get('area', 1116.23)))
s_rate = safe_float(plot_data.get('selling_rate', 0.0))

if 0 < s_rate < 10000: # मतलब यह पर-स्क्वायर-फीट का रेट है (जैसे 686)
    total_cost = s_rate * plot_area
else:
    total_cost = s_rate if s_rate > 0 else safe_float(plot_data.get('total_value', 191000.0))

token_paid = safe_float(plot_data.get('token_amount', plot_data.get('received_amount', 0.0)))

# Initialize partial payment registry array if not present inside the dataset
if 'partial_payments' not in plot_data:
    plot_data['partial_payments'] = []

partial_payments_list = plot_data.get('partial_payments', [])

# Dynamic accounting calculators
total_partial_paid = sum(safe_float(pmt.get('amount', 0.0)) for pmt in partial_payments_list)
total_overall_paid = token_paid + total_partial_paid
net_outstanding_balance = max(0.0, total_cost - total_overall_paid)

# --- Real-Time Customer Account Summary Card ---
st.markdown("### 👤 Account Profile Summary")
st.markdown(f"""
<div class="emi-badge">
    <span style="font-size: 15px; color:{p_color};">Client Identity: {customer_name} | Plot Reference: P-{selected_plot}</span><br>
    <span style="font-size: 12px; color:#64748b; font-weight:500;">Project: {selected_project} | Contact String: {plot_data.get('phone','N/A')}</span>
</div>
""", unsafe_allow_html=True)

c_m1, c_m2, c_m3, c_m4 = st.columns(4)
c_m1.metric("Gross Deal Value", f"₹ {total_cost:,.2f}")
c_m2.metric("Initial Advance Token", f"₹ {token_paid:,.2f}")
c_m3.metric("Total Installments Paid", f"₹ {total_partial_paid:,.2f}", delta=f"Overall Paid: ₹{total_overall_paid:,.2f}")
c_m4.metric("🏆 Net Outstanding Due", f"₹ {net_outstanding_balance:,.2f}", delta="Remaining Balance", delta_color="inverse")

# --- Form Section Layout Split ---
col_f1, col_f2 = st.columns([1.1, 0.9])

with col_f1:
    st.markdown("### 💳 Log New Installment / Partial Payment")
    with st.form("partial_payment_form"):
        col_p1, col_p2 = st.columns(2)
        paid_amt = col_p1.number_input("Collected Installment Amount (₹) *", min_value=0.0, step=5000.0, key="input_paid_amt")
        pmt_date = col_p2.date_input("Date of Receipt Collection", key="input_pmt_date")
       
        col_p3, col_p4 = st.columns(2)
        pmt_mode = col_p3.selectbox("Payment Channel Mode", ["Online/UPI", "Cash", "Cheque", "RTGS/NEFT"], key="input_pmt_mode")
        inst_ref = col_p4.text_input("Transaction ID / Instrument Ref No.", key="input_inst_ref")
       
        remarks = st.text_input("Accountant Remarks / Notes", placeholder="e.g., Third Installment Received", key="input_remarks")
       
        submit_payment = st.form_submit_button("💾 Save Payment Entry & Adjust Ledger Balance", use_container_width=True)
       
        if submit_payment:
            if paid_amt <= 0:
                st.error("🚨 Accounting Failure: Collected installment amount must be greater than zero!")
            elif paid_amt > net_outstanding_balance:
                st.error(f"🚨 Limit Violation: Entered amount exceeds the remaining net outstanding due of ₹{net_outstanding_balance:,.2f}!")
            else:
                new_receipt = {
                    "receipt_no": f"REC-{selected_project[:3].upper()}-{selected_plot}-{len(partial_payments_list)+1}",
                    "amount": paid_amt,
                    "date": str(pmt_date.strftime("%d-%m-%Y")),
                    "mode": pmt_mode,
                    "reference": inst_ref.strip() if inst_ref.strip() else "N/A",
                    "remarks": remarks.strip() if remarks.strip() else "Installment Payment"
                }
               
                plot_data['partial_payments'].append(new_receipt)
                
                with st.spinner("Updating central accounting records..."):
                    if database.save_db_data():
                        st.success(f"🎉 Success! Installment of ₹{paid_amt:,.2f} safely authorized and logged!")
                        st.invalidate_pages() if hasattr(st, "invalidate_pages") else None
                        st.rerun()

with col_f2:
    st.markdown("### 🔔 Automated EMI Reminders Engine")
    st.markdown("<div style='background-color:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:20px;'>", unsafe_allow_html=True)
   
    # Formulate localized dynamic message strings
    reminder_text = (
        f"Dear {customer_name},\n\n"
        f"This is a friendly payment reminder from Firstchoice Infra regarding your plot booking P-{selected_plot} "
        f"in our project '{selected_project}'.\n\n"
        f"Summary Details:\n"
        f"- Total Plot Cost: ₹{total_cost:,.2f}\n"
        f"- Total Amount Paid: ₹{total_overall_paid:,.2f}\n"
        f"- Net Outstanding Balance Due: ₹{net_outstanding_balance:,.2f}\n\n"
        f"Kindly arrange for the installment payment clearance at your earliest convenience. "
        f"Ignore if already settled. Thank you!\n\n"
        f"Warm regards,\n"
        f"Accounts Desk\n"
        f"Firstchoice Infra, Nagpur"
    )
   
    st.caption("Copy this auto-calculated string directly to send to the client via WhatsApp/SMS notification channels:")
    st.text_area("Live Notification Template", value=reminder_text, height=220, disabled=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- Comprehensive Live Payment Ledger Table ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📄 Real-Time Payment History Ledger Breakdown")

history_rows = []
history_rows.append({
    "Receipt ID": "REC-TOKEN-01",
    "Payment Category": "Initial Booking Advance",
    "Collection Date": plot_data.get('receipt_date', plot_data.get('booking_date', 'N/A')),
    "Payment Mode": plot_data.get('payment_mode', 'N/A'),
    "Instrument Ref": plot_data.get('transaction_id', 'N/A'),
    "Amount Deposited (₹)": token_paid,
    "Account Status": "Cleared"
})

for pmt in partial_payments_list:
    history_rows.append({
        "Receipt ID": pmt.get('receipt_no', 'N/A'),
        "Payment Category": pmt.get('remarks', 'Installment Payment'),
        "Collection Date": pmt.get('date', 'N/A'),
        "Payment Mode": pmt.get('mode', 'N/A'),
        "Instrument Ref": pmt.get('reference', 'N/A'),
        "Amount Deposited (₹)": safe_float(pmt.get('amount', 0.0)),
        "Account Status": "Cleared"
    })

df_ledger = pd.DataFrame(history_rows)
st.dataframe(df_ledger, use_container_width=True, hide_index=True)

# --- Printable File Download Operations ---
st.write("---")
csv_ledger_data = df_ledger.to_csv(index=False).encode('utf-8-sig')

st.download_button(
    label="📥 Export & Print Complete Ledger Statement (Share via WhatsApp)",
    data=csv_ledger_data,
    file_name=f"Ledger_Statement_{str(customer_name).replace(' ', '_')}_Plot_{selected_plot}.csv",
    mime="text/csv",
    use_container_width=True
)

