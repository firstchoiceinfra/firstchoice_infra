import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

def apply_premium_theme():
    p_color = db_data.get('_app_settings', {}).get('primary_color', "#1e3a8a")
    st.markdown(f"""<style>
        .invoice-box {{ background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.1); border-top: 10px solid {p_color}; }}
        h1 {{ color: {p_color} !important; text-align: center; }}
        .header-info {{ font-size: 16px; color: #334155; margin-bottom: 20px; }}
        .total-box {{ background: #f8fafc; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }}
    </style>""", unsafe_allow_html=True)

apply_premium_theme()

st.title("Firstchoice Infra")
st.markdown("<h3 style='text-align:center;'>Business Partner Commission Statement</h3>", unsafe_allow_html=True)

exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
c1, c2 = st.columns(2)
start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = c2.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Premium Statement", use_container_width=True):
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
                    
                    payments = [{'type': 'Booking Token', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            # कैलकुलेशन
                            gross = (pmt['amt'] * p_pct) / 100
                            disc_amt = (pmt['amt'] * (discount_sqft / comp_rate)) if comp_rate > 0 else 0
                            net_comm = max(0, gross - disc_amt)
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            
                            rows.append({
                                "S.No.": s_no, "Customer": info.get('customer_name'), "Plot": pid, 
                                "Mauza": p_info.get('mauza', 'N/A'), "Received Amt": pmt['amt'], 
                                "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, 
                                "Net Comm": net_comm, "TDS (2%)": tds, "Net In Hand": in_hand
                            })
                            s_no += 1
    
    if rows:
        df = pd.DataFrame(rows)
        # हेडर इंफॉर्मेशन
        st.markdown(f"<div class='invoice-box'><p class='header-info'><b>Partner:</b> {search_exec} <br><b>Period:</b> {start} to {end}</p>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True)
        
        # टोटल कैलकुलेशन बॉक्स
        st.markdown("<div class='total-box'>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
        c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
        c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
        c4.metric("🏆 Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
        st.markdown("</div></div>", unsafe_allow_html=True)
        
        # प्रिंट और व्हाट्सएप बटन
        b1, b2 = st.columns(2)
        if b1.button("🖨️ Print Statement"): st.write("Generating Print View...")
        if b2.button("💬 Send to WhatsApp"): st.write("Opening WhatsApp...")
    else:
        st.info("कोई बुकिंग रिकॉर्ड नहीं मिला।")

