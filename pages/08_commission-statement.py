import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रीमियम थीम और स्टाइलिंग
st.markdown("""<style>
    .premium-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border-top: 15px solid #1e3a8a; }
    .comp-name { text-align: center; color: #b8860b; font-size: 40px; font-weight: 900; text-transform: uppercase; }
    .comp-slogan { text-align: center; color: #1e3a8a; font-size: 16px; font-style: italic; margin-bottom: 20px; border-bottom: 2px solid #b8860b; padding-bottom: 10px; }
    .address { text-align: center; font-size: 13px; color: #4b5563; margin-bottom: 30px; }
    .stButton>button { border-radius: 8px !important; font-weight: bold !important; }
</style>""", unsafe_allow_html=True)

exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Business Partner", exec_list)
c1, c2 = st.columns(2)
start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = c2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Elite Statement", use_container_width=True):
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
        # प्रीमियम इनवॉइस व्यू
        st.markdown("<div class='premium-container'>", unsafe_allow_html=True)
        st.markdown("<h1 class='comp-name'>FIRSTCHOICE INFRA</h1>", unsafe_allow_html=True)
        st.markdown("<p class='comp-slogan'>Symbol Of Trust...</p>", unsafe_allow_html=True)
        st.markdown("<p class='address'>📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align:center;'>Business Partner Commission Statement</h3>", unsafe_allow_html=True)
        st.markdown(f"<b>Partner:</b> {search_exec} &nbsp;&nbsp;&nbsp; <b>Period:</b> {start} to {end}", unsafe_allow_html=True)
        
        st.dataframe(df, use_container_width=True)
        
        # टोटल्स
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
        c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
        c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
        c4.metric("🏆 Net Payout", f"₹ {df['Net In Hand'].sum():,.2f}")
        
        # प्रीमियम बटन्स
        st.markdown("<div style='display:flex; gap:20px; justify-content:center; margin-top:30px;'>", unsafe_allow_html=True)
        if st.button("🖨️ Print Statement"): st.write("Printer ready...")
        if st.button("💬 Send to WhatsApp"): st.write("Redirecting to WhatsApp...")
        st.markdown("</div></div>", unsafe_allow_html=True)
    else:
        st.info("कोई बुकिंग रिकॉर्ड नहीं मिला।")

