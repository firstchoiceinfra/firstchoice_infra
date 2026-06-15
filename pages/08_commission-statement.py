import streamlit as st
import database
import pandas as pd

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS - यहाँ मैंने प्रिंट की सेटिंग को एकदम 'लॉक' कर दिया है
st.markdown("""<style>
    /* प्रिंट के समय ये चीजें पक्का नहीं दिखेंगी */
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton, .stSelectbox, .stDateInput { 
            display: none !important; 
        }
        body { background: white !important; }
        .a4-container { 
            display: block !important; 
            width: 100% !important; 
            margin: 0 !important; 
            padding: 10px !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
        }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 20px; }
    .header { text-align: center; border-bottom: 2px solid #b8860b; padding-bottom: 10px; }
    .title { color: #b8860b; font-size: 22px; font-weight: bold; margin: 0; }
    .data-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 10px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 5px; text-align: left; }
    .data-table th { background-color: #eee; }
    .summary-box { margin-top: 15px; padding: 10px; border: 2px solid #1e3a8a; font-size: 12px; }
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
            
            comp_rate = float(p_info.get('base_rate', 700))
            
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('executive_name', '')).strip().lower() == str(search_exec).strip().lower():
                    amt = float(info.get('token_amount', 0))
                    discount_sqft = float(info.get('discount', 0))
                    if amt > 0:
                        gross = (amt * p_pct) / 100
                        disc_amt = (amt * (discount_sqft / comp_rate)) if comp_rate > 0 else 0
                        tds = (gross - disc_amt) * 0.02
                        net = (gross - disc_amt) - tds
                        rows.append({"S.No.": count, "Mauja": mauja, "Project": project_name, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": amt, "Date": info.get('booking_date', ''), "Gross": gross, "Discount": disc_amt, "TDS": tds, "Net": net})
                        count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'><p class='title'>FIRSTCHOICE INFRA</p><p><i>Symbol Of Trust...</i></p></div>
        <h3 style='text-align:center;'>Executive Commission Statement</h3>
        <p><b>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</b></p>""", unsafe_allow_html=True)
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    st.markdown(f"<div class='summary-box'>Gross Total: ₹{df['Gross'].sum():,.2f} | Discount Total: ₹{df['Discount'].sum():,.2f} | TDS: ₹{df['TDS'].sum():,.2f} | <b>Net Pay: ₹{df['Net'].sum():,.2f}</b></div></div>", unsafe_allow_html=True)

    # 6. Buttons
    st.markdown('<div class="no-print" style="text-align:center; margin-top:20px;"><button onclick="window.print()" style="padding:10px 20px;">🖨️ Print as PDF</button></div>', unsafe_allow_html=True)

