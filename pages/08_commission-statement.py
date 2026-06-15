import streamlit as st
import database
import pandas as pd

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS 
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton { display: none !important; }
        .a4-container { width: 100% !important; margin: 0 !important; }
    }
    .a4-container { background: white; color: black; max-width: 900px; margin: auto; padding: 30px; border: 1px solid #ccc; }
    .header { text-align: center; border-bottom: 2px solid #b8860b; padding-bottom: 10px; }
    .title { color: #b8860b; font-size: 24px; font-weight: bold; margin: 0; }
    .info-sect { display: flex; justify-content: space-between; margin-top: 20px; font-weight: bold; }
    .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 11px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 6px; text-align: left; }
    .data-table th { background-color: #eee; }
    .summary-box { margin-top: 20px; padding: 15px; border: 2px solid #1e3a8a; background: #f0f4f8; }
</style>""", unsafe_allow_html=True)

# 3. Inputs
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Full Official Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation (Improved Logic)
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
            
            plots = p_info['plots']
            # डिक्शनरी या लिस्ट दोनों को संभालने के लिए
            plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                # एग्जीक्यूटिव का नाम मैच करना
                if str(info.get('executive_name', '')).strip().lower() == str(search_exec).strip().lower():
                    
                    # हर बुकिंग में कम से कम बुकिंग अमाउंट तो होगा ही
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    # अगर एक्स्ट्रा भुगतान हैं, तो उन्हें जोड़ें
                    if 'partial_payments' in info and isinstance(info['partial_payments'], list):
                        payments.extend([{'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in info['partial_payments']])
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            tds = gross * 0.02
                            net = gross - tds
                            rows.append({
                                "S.No.": count, "Mauja": mauja, "Project": project_name, 
                                "Customer": info.get('customer_name', 'N/A'), "Plot": pid, 
                                "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, 
                                "TDS": tds, "Net": net
                            })
                            count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        <p class='title'>FIRSTCHOICE INFRA</p>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:11px;'>Plot No. 06, Shop No.106, Motilal Nagar, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center;'>Executive Commission Statement</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-sect'><span>Partner: {meta['exec']}</span><span>Period: {meta['start']} to {meta['end']}</span></div>", unsafe_allow_html=True)
    
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    
    st.markdown(f"""<div class='summary-box'>
        <p>Gross Total: ₹{df['Gross'].sum():,.2f} | TDS Total: ₹{df['TDS'].sum():,.2f}</p>
        <hr><p><strong>Net Amount Payable: ₹{df['Net'].sum():,.2f}</strong></p>
    </div></div>""", unsafe_allow_html=True)
    
    st.markdown('<div class="no-print" style="text-align:center; margin-top:20px;"><button onclick="window.print()" style="padding:10px 20px; background:#1e3a8a; color:white; border:none; border-radius:5px;">🖨️ Print Final Statement</button></div>', unsafe_allow_html=True)

