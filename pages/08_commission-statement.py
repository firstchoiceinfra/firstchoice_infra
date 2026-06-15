import streamlit as st
import database
import pandas as pd

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS (प्रोफेशनल और प्रिंट-फ्रेंडली)
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton, .stSelectbox, .stDateInput { display: none !important; }
        .a4-container { width: 100% !important; margin: 0 !important; padding: 10px !important; }
        .data-table { font-size: 9px !important; }
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

# 3. Inputs (प्रिंट में नहीं आएंगे)
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Official Statement")
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
                    amt = float(info.get('token_amount', 0))
                    if amt > 0:
                        gross = (amt * p_pct) / 100
                        tds = gross * 0.02
                        net = gross - tds
                        rows.append({"S.No.": count, "Mauja": mauja, "Project": project_name, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": amt, "Date": info.get('booking_date', ''), "Gross": gross, "TDS": tds, "Net": net})
                        count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Official Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        <p class='title'>FIRSTCHOICE INFRA</p>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:11px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h3 style='text-align:center;'>Executive Commission Statement</h3>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-sect'><span>Partner: {meta['exec']}</span><span>Period: {meta['start']} to {meta['end']}</span></div>", unsafe_allow_html=True)
    
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    
    st.markdown(f"""<div class='summary-box'>
        <p>Gross Amount: ₹{df['Gross'].sum():,.2f}</p>
        <p>TDS Deduction (2%): ₹{df['TDS'].sum():,.2f}</p>
        <hr>
        <p><strong>Net Amount Payable: ₹{df['Net'].sum():,.2f}</strong></p>
    </div></div>""", unsafe_allow_html=True)
    
    st.markdown('<div class="no-print" style="text-align:center; margin-top:20px;"><button onclick="window.print()" style="padding:10px 20px; background:#1e3a8a; color:white; border:none; border-radius:5px;">🖨️ Print Official Document</button></div>', unsafe_allow_html=True)

