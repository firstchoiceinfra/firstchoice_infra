import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रिंट के लिए अल्टीमेट CSS (साइडबार और बटन हटा देगा, मल्टी-पेज सपोर्ट)
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, .stButton, .stSelectbox, .stDateInput { display: none !important; }
        .a4-page { width: 100% !important; margin: 0 !important; padding: 10px !important; border: none !important; }
        @page { size: A4; margin: 15mm; }
    }
    .a4-page { background: white; padding: 40px; border: 2px solid #b8860b; color: black; max-width: 800px; margin: auto; }
    .header-sect { text-align: center; border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
</style>""", unsafe_allow_html=True)

# इनपुट (no-print क्लास ताकि ये प्रिंट में न आएं)
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
if st.button("🚀 Generate Multi-Color Statement"):
    # (आपका कैलकुलेशन लॉजिक वही रहेगा...)
    # [कैलकुलेशन लॉजिक...]
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}
st.markdown('</div>', unsafe_allow_html=True)

# रेंडरिंग
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    # हेडर
    st.markdown(f"""<div class='header-sect'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='text-align:center; font-weight:bold;'>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</div>", unsafe_allow_html=True)
    
    # टेबल (डेटा ज्यादा होने पर अपने आप दूसरे पेज पर जाएगी)
    st.table(df) 
    
    # समरी
    cols = st.columns(4)
    cols[0].metric("Gross", f"₹{df['Gross'].sum():,.2f}")
    cols[1].metric("Discount", f"₹{df['Discount'].sum():,.2f}")
    cols[2].metric("TDS", f"₹{df['TDS (2%)'].sum():,.2f}")
    cols[3].metric("Net Pay", f"₹{df['Net In Hand'].sum():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # प्रिंट बटन
    st.markdown(f"""
        <div class="no-print" style="text-align:center; margin-top:30px;">
            <button onclick="window.print()" style="padding: 15px 30px; background: #1e3a8a; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                🖨️ Print A4 Statement
            </button>
        </div>
    """, unsafe_allow_html=True)

