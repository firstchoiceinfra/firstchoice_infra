
import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# मल्टी-कलर प्रीमियम स्टाइलिंग
st.markdown("""<style>
    .a4-container { background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 100%); padding: 40px; border-radius: 25px; border: 3px solid #b8860b; color: #1e293b; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }
    .header-box { text-align: center; border-bottom: 4px double #1e3a8a; padding-bottom: 20px; margin-bottom: 25px; }
    .comp-name { color: #b8860b; font-size: 45px; font-weight: 900; text-transform: uppercase; margin: 0; }
    .comp-slogan { color: #1e3a8a; font-size: 18px; font-style: italic; font-weight: 600; }
    .partner-info { display: flex; justify-content: space-between; padding: 15px; background: #eef2ff; border-radius: 10px; font-weight: bold; margin-bottom: 20px; }
    .btn-row { display: flex; gap: 20px; justify-content: center; margin-top: 30px; }
    @media print { .no-print { display: none !important; } }
</style>""", unsafe_allow_html=True)

# सिलेक्शन
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start = col1.date_input("Start Date")
end = col2.date_input("End Date")

if st.button("🚀 Generate Multi-Color Statement"):
    rows = []
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if info.get('executive_name', '').lower() == search_exec.lower() and info.get('status', '').lower() == 'booked':
                    comp_rate = float(info.get('company_rate', p_info.get('base_rate', 700)))
                    discount_sqft = float(info.get('discount', 0))
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    payments.extend([{'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in info.get('partial_payments', [])])
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            disc_amt = (pmt['amt'] * (discount_sqft / comp_rate)) if comp_rate > 0 else 0
                            net_comm = max(0, gross - disc_amt)
                            rows.append({
                                "Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": pmt['amt'], 
                                "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, 
                                "TDS (2%)": net_comm * 0.02, "Net In Hand": net_comm - (net_comm * 0.02)
                            })
    st.session_state.df_view = pd.DataFrame(rows) if rows else None

# स्टेटमेंट रेंडरिंग
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    
    # कंपनी हेडर
    st.markdown(f"""<div class='header-box'>
        <h1 class='comp-name'>FIRSTCHOICE INFRA</h1>
        <p class='comp-slogan'>Symbol Of Trust...</p>
        <p>📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='partner-info'><span>Partner: {search_exec}</span> <span>Period: {start} to {end}</span></div>", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    # फाइनेंशियल समरी
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
    
    # एक्शन बटन्स (no-print)
    st.markdown("<div class='no-print btn-row'>", unsafe_allow_html=True)
    if st.button("🖨️ Print Statement"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    msg = f"Commission Summary for {search_exec}: Net Payout ₹{df['Net In Hand'].sum():,.2f}"
    st.markdown(f'<a href="https://wa.me/?text={msg}" target="_blank"><button style="padding:15px 30px; background:#25d366; color:white; border:none; border-radius:10px; font-weight:bold;">💬 Send Summary to WhatsApp</button></a>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

