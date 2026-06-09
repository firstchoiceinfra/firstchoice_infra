import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

def apply_premium_theme():
    p_color = db_data.get('_app_settings', {}).get('primary_color', "#1e3a8a")
    st.markdown(f"""<style>
        .invoice-container {{ background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border-top: 15px solid {p_color}; }}
        .header-title {{ text-align: center; color: {p_color}; font-size: 36px; font-weight: 800; margin-bottom: 0px; }}
        .slogan {{ text-align: center; color: #64748b; font-style: italic; margin-bottom: 25px; }}
        .partner-info {{ display: flex; justify-content: space-between; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; margin-bottom: 20px; }}
        .action-bar {{ display: flex; gap: 20px; justify-content: center; margin-top: 30px; padding: 20px; background: #f8fafc; border-radius: 15px; }}
        .stButton>button {{ border-radius: 50px !important; padding: 10px 25px !important; font-weight: bold; transition: 0.3s; }}
    </style>""", unsafe_allow_html=True)

apply_premium_theme()

exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
c1, c2 = st.columns(2)
start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = c2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Premium Statement", use_container_width=True):
    rows = []
    s_no = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    comp_rate = float(info.get('company_rate', p_info.get('base_rate', 700)))
                    discount_sqft = float(info.get('discount', 0))
                    
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            disc_amt = (pmt['amt'] * (discount_sqft / comp_rate)) if comp_rate > 0 else 0
                            net_comm = max(0, gross - disc_amt)
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            rows.append({
                                "S.No.": s_no, "Customer": info.get('customer_name'), "Plot": pid, 
                                "Received Amt": pmt['amt'], "Date": pmt['date'], "Gross": gross, 
                                "Discount": disc_amt, "Net Comm": net_comm, "TDS (2%)": tds, "Net In Hand": in_hand
                            })
                            s_no += 1
    
    if rows:
        df = pd.DataFrame(rows)
        # इनवॉइस बॉक्स शुरू
        st.markdown("<div class='invoice-container'>", unsafe_allow_html=True)
        st.markdown("<h1 class='header-title'>Firstchoice Infra</h1>", unsafe_allow_html=True)
        st.markdown("<p class='slogan'>Symbol of Trust</p>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
        st.markdown(f"<div class='partner-info'><span><b>Partner:</b> {search_exec}</span> <span><b>Period:</b> {start} to {end}</span></div>", unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        
        # टोटल टेबल (नीचे में टोटल)
        totals = pd.DataFrame({
            "Metric": ["Gross Total", "Discount Total", "Net Comm Total", "TDS Total", "FINAL PAYOUT"],
            "Amount (₹)": [df['Gross'].sum(), df['Discount'].sum(), df['Net Comm'].sum(), df['TDS (2%)'].sum(), df['Net In Hand'].sum()]
        })
        st.table(totals)
        
        # प्रीमियम एक्शन बार
        st.markdown("<div class='action-bar'>", unsafe_allow_html=True)
        c_a, c_b = st.columns(2)
        if c_a.button("🖨️ Print Statement"): st.write("Opening Print Layout...")
        if c_b.button("💬 Send to WhatsApp"): st.write("Redirecting to WhatsApp...")
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.info("कोई रिकॉर्ड नहीं मिला।")
