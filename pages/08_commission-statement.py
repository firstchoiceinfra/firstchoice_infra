import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# CSS स्टाइलिंग
st.markdown("""<style>
    .premium-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border-top: 15px solid #1e3a8a; }
    .stButton>button { background: linear-gradient(45deg, #1e3a8a, #3b82f6); color: white; border-radius: 10px; font-weight: bold; width: 100%; }
</style>""", unsafe_allow_html=True)

# सिलेक्शन
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

# बटन का लॉजिक - अब 'df' को session_state में स्टोर करेंगे
if st.button("🚀 Generate Elite Statement"):
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
        st.session_state.df_statement = pd.DataFrame(rows)
    else:
        st.session_state.df_statement = None
        st.info("कोई बुकिंग रिकॉर्ड नहीं मिला।")

# स्टेटमेंट दिखाने का लॉजिक (बटन से बाहर)
if 'df_statement' in st.session_state and st.session_state.df_statement is not None:
    df = st.session_state.df_statement
    st.markdown("<div class='premium-container'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; color:#b8860b;'>FIRSTCHOICE INFRA</h1><p style='text-align:center; font-style:italic;'>Symbol Of Trust...</p>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    
    # टोटल और एक्शन बार
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("🏆 Net Payout", f"₹ {df['Net In Hand'].sum():,.2f}")
    
    b1, b2 = st.columns(2)
    if b1.button("🖨️ Print Statement"): st.write("Print mode enabled...")
    if b2.button("💬 Send to WhatsApp"): st.write("WhatsApp redirecting...")
    st.markdown("</div>", unsafe_allow_html=True)

