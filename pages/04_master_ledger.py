import streamlit as st
import database
import datetime
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Ledger")

# --- 2. Security Check (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 Security Alert: You do not have permission to access the Master Ledger Panel!")
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
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
div[data-testid="stMetric"] div[data-testid="stMetricLabel"] {{ font-size: 13px !important; font-weight: 600 !important; color: #475569 !important; }}
div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{ font-size: 20px !important; font-weight: 800 !important; color: #0f172a !important; }}
</style>
""", unsafe_allow_html=True)

# 🛠️ Safe Float Function
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return float(default)
        return float(val)
    except: return float(default)

st.markdown("<h1 style='text-align: center;'>🏦 Central Master Ledger (Live Cashflow)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #475569;'>Real-time Audit of all Booking Advances & EMI Collections across all Projects</p>", unsafe_allow_html=True)

# --- Ledger Filter Engine ---
st.markdown("### 🔍 Generate Collection Report")
col_d1, col_d2 = st.columns(2)
start_date = col_d1.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = col_d2.date_input("📅 End Date", datetime.date.today())

if st.button("📊 Fetch Master Collection Records", use_container_width=True):
    ledger_rows = []
    
    # 🎯 NEW: Overall Business Trackers
    overall_total_business = 0.0
    overall_total_pending = 0.0
    overall_total_collected = 0.0
   
    project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]
   
    with st.spinner("Scanning entire database for tokens, EMIs and overall business health..."):
        for p_name in project_names:
            p_info = db_data[p_name]
            p_plots = p_info.get('plots', {})
           
            if isinstance(p_plots, list):
                p_plots = {str(idx): p for idx, p in enumerate(p_plots) if p is not None}
               
            for plot_id, plot_info in p_plots.items():
                if isinstance(plot_info, dict) and str(plot_info.get('status', '')).strip().lower() == 'booked':
                    
                    # --- 🌟 OVERALL BUSINESS CALCULATOR (All Time) ---
                    plot_area = safe_float(plot_info.get('plot_area', plot_info.get('area', 0.0)))
                    rate_per_sqft = safe_float(plot_info.get('selling_rate', 0.0))
                    
                    if rate_per_sqft > 100000:
                        total_deal_value = rate_per_sqft
                    elif plot_area > 0 and rate_per_sqft > 0:
                        total_deal_value = plot_area * rate_per_sqft
                    else:
                        total_deal_value = rate_per_sqft # Fallback
                        
                    token_amt_overall = safe_float(plot_info.get('token_amount', 0.0))
                    partial_payments_overall = plot_info.get('partial_payments', [])
                    total_emi_paid_overall = sum(safe_float(pmt.get('amount', 0.0)) for pmt in partial_payments_overall)
                    
                    total_paid_overall = token_amt_overall + total_emi_paid_overall
                    net_pending_overall = max(0.0, total_deal_value - total_paid_overall)
                    
                    if total_deal_value > 0:
                        overall_total_business += total_deal_value
                        overall_total_collected += total_paid_overall
                        overall_total_pending += net_pending_overall
                    # ---------------------------------------------------

                    cust_name = str(plot_info.get('customer_name', 'N/A')).title()
                    exec_name = str(plot_info.get('executive_name', 'Direct')).title()
                   
                    # 1️⃣ SCAN TOKEN AMOUNT (Date Filtered)
                    b_date_str = str(plot_info.get('booking_date', plot_info.get('receipt_date', ''))).strip()
                    b_date_obj = datetime.date.today()
                    if b_date_str:
                        try: b_date_obj = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                        except:
                            try: b_date_obj = datetime.datetime.strptime(b_date_str, "%d-%m-%Y").date()
                            except: pass
                   
                    if start_date <= b_date_obj <= end_date:
                        token_amt = safe_float(plot_info.get('token_amount', plot_info.get('received_amount', 0.0)))
                        if token_amt > 0:
                            ledger_rows.append({
                                "Date": b_date_obj.strftime("%d-%m-%Y"),
                                "Project": p_name,
                                "Plot No.": plot_id,
                                "Client Name": cust_name,
                                "Payment Type": "Booking Advance (Token)",
                                "Payment Mode": plot_info.get('payment_mode', 'N/A'),
                                "Executive": exec_name,
                                "Amount (₹)": token_amt
                            })
                           
                    # 2️⃣ SCAN EMI / PARTIAL PAYMENTS (Date Filtered)
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
                                ledger_rows.append({
                                    "Date": pmt_date_obj.strftime("%d-%m-%Y"),
                                    "Project": p_name,
                                    "Plot No.": plot_id,
                                    "Client Name": cust_name,
                                    "Payment Type": str(pmt.get('remarks', 'Installment Payment')),
                                    "Payment Mode": str(pmt.get('mode', 'N/A')),
                                    "Executive": exec_name,
                                    "Amount (₹)": emi_amt
                                })
                               
    # --- Report Generation & Dashboard UI ---
    st.write("---")
    
    # 🌟 NEW OVERALL BUSINESS DASHBOARD
    st.markdown("### 🏢 Overall Company Portfolio (All Time)")
    c_b1, c_b2, c_b3 = st.columns(3)
    c_b1.metric("💼 Total Business Volume", f"₹ {overall_total_business:,.2f}")
    c_b2.metric("✅ Total Amount Received", f"₹ {overall_total_collected:,.2f}")
    
    # Red color for pending balance to make it stand out
    st.markdown(f"""
        <style>
        div[data-testid="stMetric"]:nth-of-type(3) div[data-testid="stMetricValue"] {{
            color: #dc2626 !important; 
        }}
        </style>
    """, unsafe_allow_html=True)
    c_b3.metric("⚠️ Total Pending Balance", f"₹ {overall_total_pending:,.2f}")

    st.markdown(f"### 📅 Collection Report ({start_date.strftime('%d %b %Y')} to {end_date.strftime('%d %b %Y')})")
    
    if ledger_rows:
        df_ledger = pd.DataFrame(ledger_rows)
       
        # Calculate totals dynamically for the selected date range
        total_revenue = df_ledger['Amount (₹)'].sum()
        total_token_revenue = df_ledger[df_ledger['Payment Type'] == 'Booking Advance (Token)']['Amount (₹)'].sum()
        total_emi_revenue = df_ledger[df_ledger['Payment Type'] != 'Booking Advance (Token)']['Amount (₹)'].sum()
       
        # Formatting for beautiful display
        df_display = df_ledger.copy()
        df_display['Amount (₹)'] = df_display['Amount (₹)'].apply(lambda x: f"₹ {x:,.2f}")
       
        # Top Metrics Row
        c_m1, c_m2, c_m3, c_m4 = st.columns(4)
        c_m1.metric("Transactions in Range", f"{len(df_ledger)} Entries")
        c_m2.metric("Tokens in Range", f"₹ {total_token_revenue:,.2f}")
        c_m3.metric("EMIs in Range", f"₹ {total_emi_revenue:,.2f}")
        c_m4.metric("🏆 Revenue in Range", f"₹ {total_revenue:,.2f}")
       
        st.markdown("<br>", unsafe_allow_html=True)
       
        # The Master Data Table
        st.dataframe(df_display, use_container_width=True, hide_index=True)
       
        # WhatsApp/Excel Export
        csv_data = df_ledger.to_csv(index=False).encode('utf-8-sig')
        st.write("---")
        st.download_button(
            label="📥 Export Complete Master Ledger (Print / Excel)",
            data=csv_data,
            file_name=f"FC_Infra_Master_Ledger_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.info("🔍 No cash collection records found for the selected date range. Try expanding the dates.")

