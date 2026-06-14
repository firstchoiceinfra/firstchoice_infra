import streamlit as st
import database
import pandas as pd
import datetime

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS - प्रिंट के लिए सबसे बेस्ट सेटिंग
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton { display: none !important; }
        
        /* ये सेटिंग्स पेज को हिलने की आजादी देंगी */
        html, body {
            height: auto !important;
            overflow: visible !important;
        }
        
        .a4-page { 
            display: block !important; 
            width: 100% !important; 
            margin: 0 !important; 
            padding: 10px !important;
            position: relative !important; /* absolute से हटाकर relative किया */
            height: auto !important;
        }
    }
</style>""", unsafe_allow_html=True)

# 3. Inputs (प्रिंट में नहीं दिखेंगे)
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Full Commission Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation
if btn_generate:
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            db_mauja = p_info.get('mauja', '')
            mauja = db_mauja if db_mauja and db_mauja.lower() != project_name.lower() else mapping.get(project_name.lower(), "Nagpur")
            
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
                                "S.No.": count, "Mauja": mauja, "Project": project_name, 
                                "Customer": info.get('customer_name', 'N/A'), "Plot": pid, 
                                "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, 
                                "Discount": disc_amt, "TDS": net_comm * 0.02, "Net In Hand": net_comm - (net_comm * 0.02)
                            })
                            count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    st.markdown(f"""<div style='text-align:center;'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p style='font-size:12px;'><i>Symbol Of Trust... | Plot No. 06, Shop No.106, Motilal Nagar, Nagpur-440034</i></p>
        <h2 style='margin-top:10px;'>Business Partner Commission Statement</h2>
        <p><b>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</b></p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    
    st.markdown(f"""
        <div class="summary-box">
            Gross Total: ₹{df['Gross'].sum():,.2f} &nbsp;|&nbsp; Net In Hand: ₹{df['Net In Hand'].sum():,.2f}
        </div>
        </div>
    """, unsafe_allow_html=True)

    # 6. Buttons
    st.markdown(f"""
        <div class="no-print" style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding: 15px 30px; background: #1e3a8a; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                🖨️ Final Print
            </button>
        </div>
    """, unsafe_allow_html=True)

