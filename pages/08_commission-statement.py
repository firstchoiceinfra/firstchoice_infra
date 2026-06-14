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
    .a4-page { background: white; padding: 40px; border-radius: 20px; border: 2px solid #b8860b; color: black; max-width: 800px; margin: auto; }
</style>""", unsafe_allow_html=True)

# 1. इनपुट कंट्रोल्स (ये सबसे ऊपर रहेंगे)
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Business Partner", exec_list)
c1, c2 = st.columns(2)
start = c1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = c2.date_input("End Date", datetime.date.today())

# 2. बटन लॉजिक
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
    
    # डेटा को session_state में डाल दिया
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta_data = {"exec": search_exec, "start": start, "end": end}

# 3. रेंडरिंग (यह चेक करता है कि क्या डेटा मौजूद है)
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta_data
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align:center; color:#b8860b;'>FIRSTCHOICE INFRA</h1><p style='text-align:center;'><i>Symbol Of Trust...</i></p>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>Business Partner Commission Statement</h3>", unsafe_allow_html=True)
    st.markdown(f"**Partner:** {meta['exec']} &nbsp;&nbsp; **Period:** {meta['start']} to {meta['end']}", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    # Totals
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Net Payout", f"₹ {df['Net In Hand'].sum():,.2f}")
    
    if st.button("🖨️ Print / Save as PDF"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

