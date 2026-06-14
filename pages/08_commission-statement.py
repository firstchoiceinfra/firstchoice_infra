import streamlit as st
import database
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. Premium Styling
st.markdown("""<style>
    .a4-page { background: white; padding: 40px; border: 3px solid #b8860b; color: black; max-width: 800px; margin: auto; border-radius: 15px; }
    .header-sect { text-align: center; border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
    .btn-row { display: flex; gap: 20px; justify-content: center; margin-top: 30px; }
    @media print { .no-print { display: none !important; } }
</style>""", unsafe_allow_html=True)

# 3. Inputs
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")

# 4. Calculation
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
                            rows.append({"Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, "TDS (2%)": net_comm * 0.02, "Net In Hand": net_comm - (net_comm * 0.02)})
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display Logic
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header-sect'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; font-weight:bold;'>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</div>", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    cols = st.columns(4)
    cols[0].metric("Gross", f"₹{df['Gross'].sum():,.2f}")
    cols[1].metric("Discount", f"₹{df['Discount'].sum():,.2f}")
    cols[2].metric("TDS", f"₹{df['TDS (2%)'].sum():,.2f}")
    cols[3].metric("Net Pay", f"₹{df['Net In Hand'].sum():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # Buttons
    st.markdown(f"""
        <div class="btn-row no-print">
            <button onclick="window.print()" style="padding: 15px 30px; background: #1e3a8a; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                🖨️ Print / Save as PDF
            </button>
            <a href="https://wa.me/?text=FIRSTCHOICE INFRA Commission Summary for {meta['exec']}: Net Pay ₹{df['Net In Hand'].sum():,.2f}" target="_blank" style="text-decoration:none;">
                <button style="padding: 15px 30px; background: #25d366; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                    💬 Send Summary to WhatsApp
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

