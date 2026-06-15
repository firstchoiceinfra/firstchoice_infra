import streamlit as st
import database
import pandas as pd

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS (प्रिंट के लिए फाइनल सेटिंग)
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton, .stSelectbox, .stDateInput { 
            display: none !important; 
        }
        /* यह सेटिंग पेज को ऊपर-नीचे होने और पूरा डेटा लेने की आजादी देगी */
        body, html { height: auto !important; overflow: visible !important; }
        .a4-page { 
            display: block !important; 
            width: 100% !important; 
            margin: 0 !important; 
            padding: 10px !important;
            height: auto !important; 
            overflow: visible !important;
            page-break-after: always; /* पेज ज्यादा होने पर अपने आप ब्रेक होगा */
        }
        .data-table { width: 100% !important; border-collapse: collapse; }
        tr { page-break-inside: avoid !important; } /* रो को कटने से बचाएगा */
    }
    .a4-page { background: white; padding: 20px; color: black; max-width: 900px; margin: auto; }
    .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    .data-table th, .data-table td { border: 1px solid #333; padding: 6px; text-align: left; font-size: 10px; }
    .data-table th { background-color: #eee; }
    .summary-box { margin-top: 20px; padding: 10px; border: 2px solid #b8860b; font-weight: bold; }
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
                    payments = [{'type': 'Booking', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    payments.extend([{'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in info.get('partial_payments', [])])
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            rows.append({"S.No.": count, "Mauja": mauja, "Project": project_name, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, "Net In Hand": gross * 0.98})
                            count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    st.markdown(f"<h3>FIRSTCHOICE INFRA</h3><p>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</p>", unsafe_allow_html=True)
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>Gross Total: ₹{df['Gross'].sum():,.2f} | Net Total: ₹{df['Net In Hand'].sum():,.2f}</div></div>", unsafe_allow_html=True)

    # 6. Buttons
    st.markdown('<div class="no-print" style="text-align:center;"><button onclick="window.print()">🖨️ Print as PDF</button></div>', unsafe_allow_html=True)

