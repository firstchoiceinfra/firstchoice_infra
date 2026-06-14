import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# स्टाइलिंग
st.markdown("""<style>
    .a4-container { background: white; padding: 40px; border-radius: 20px; border: 3px solid #b8860b; color: #1e293b; }
    .header-box { text-align: center; border-bottom: 4px double #1e3a8a; padding-bottom: 20px; }
    .comp-name { color: #b8860b; font-size: 40px; font-weight: 900; text-transform: uppercase; }
</style>""", unsafe_allow_html=True)

# सिलेक्शन
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")

# कैलकुलेशन फ़ंक्शन
def generate_commission_data(partner, s_date, e_date):
    rows = []
    s_no = 1
    p_profile = exec_data_root.get(partner, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if info.get('executive_name', '').lower() == partner.lower() and info.get('status', '').lower() == 'booked':
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
                                "S.No.": s_no, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, 
                                "Received Amt": pmt['amt'], "Date": pmt['date'], "Gross": gross, 
                                "Discount": disc_amt, "Net Comm": net_comm, "TDS (2%)": net_comm * 0.02, 
                                "Net In Hand": net_comm - (net_comm * 0.02)
                            })
                            s_no += 1
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# बटन लॉजिक
if st.button("🚀 Generate Multi-Color Statement"):
    st.session_state.df_view = generate_commission_data(search_exec, start, end)

# डिस्प्ले लॉजिक
if 'df_view' in st.session_state and not st.session_state.df_view.empty:
    df = st.session_state.df_view
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown("<div class='header-box'><h1 class='comp-name'>FIRSTCHOICE INFRA</h1><p><i>Symbol Of Trust...</i></p></div>", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    
    # टोटल्स (की-एरर से बचने के लिए सीधा कॉल)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

