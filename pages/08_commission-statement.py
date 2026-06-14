import streamlit as st
import database
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS (प्रिंट के लिए सुपर-क्लीन सेटिंग)
st.markdown("""<style>
    @media print {
        .no-print { display: none !important; }
        .a4-page { width: 100% !important; margin: 0 !important; }
    }
    .a4-page { background: white; padding: 20px; color: black; max-width: 800px; margin: auto; }
    .header-sect { text-align: center; border-bottom: 2px solid #b8860b; padding-bottom: 10px; }
    .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .data-table th, .data-table td { border: 1px solid #333; padding: 8px; text-align: left; font-size: 12px; }
    .data-table th { background-color: #eee; }
</style>""", unsafe_allow_html=True)

# 3. Inputs
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation
if btn_generate:
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
                            rows.append({"Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, "TDS": net_comm * 0.02, "Net": net_comm - (net_comm * 0.02)})
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. डिस्प्ले
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header-sect'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p style='font-size:14px;'><i>Symbol Of Trust... | Plot No. 06, Shop No.106, Motilal Nagar, Nagpur-440034</i></p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown(f"<h3 style='text-align:center;'>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</h3>", unsafe_allow_html=True)
    
    # यहाँ टेबल का HTML वर्जन है जो प्रिंट में कभी नहीं कटेगा
    html_str = df.to_html(classes='data-table', index=False)
    st.markdown(html_str, unsafe_allow_html=True)
    
    st.markdown(f"""
        <div style="margin-top:20px; font-weight:bold;">
            Gross Total: ₹{df['Gross'].sum():,.2f} | Net Total: ₹{df['Net'].sum():,.2f}
        </div>
        </div>
    """, unsafe_allow_html=True)

    # 6. बटन्स
    st.markdown(f"""
        <div class="no-print" style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding: 15px 30px; background: #1e3a8a; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                🖨️ Print Commission Statement
            </button>
            <a href="https://wa.me/?text=FIRSTCHOICE INFRA - Commission Summary for {meta['exec']}: Net Payout ₹{df['Net'].sum():,.2f}" target="_blank" style="text-decoration: none; margin-left: 20px;">
                <button style="padding: 15px 30px; background: #25d366; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                    💬 Send Summary to WhatsApp
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

