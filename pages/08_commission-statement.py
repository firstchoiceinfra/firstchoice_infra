import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रोफेशनल हेडर
def print_commission_header(exec_name, start, end):
    st.markdown(f"""
    <div style="border: 4px solid #b8860b; padding: 20px; border-radius: 15px; background: #fdfaf6; text-align: center;">
        <h1>Firstchoice Infra</h1>
        <p>📍 Plot No. 06, Shop No.106, Motilal Nagar, Nagpur</p>
        <hr>
        <h2>Executive Commission Statement</h2>
        <p><b>Executive:</b> {exec_name} | <b>Period:</b> {start.strftime('%d-%m-%Y')} to {end.strftime('%d-%m-%Y')}</p>
    </div>
    """, unsafe_allow_html=True)

# [यहाँ अपना 'Live Statement Ledger Engine' वाला पूरा लूपिंग कोड पेस्ट करें]

if st.button("🔍 Generate Comprehensive Ledger", use_container_width=True):
    # (आपका पुराना लूप जो statement_rows बनाता है)
    
    if 'statement_rows' in locals() and statement_rows:
        df = pd.DataFrame(statement_rows)
        print_commission_header(search_exec, start_date, end_date)
        st.dataframe(df, use_container_width=True)
        
        # ऑटो-कैलकुलेशन
        t_gross = df['Gross (₹)'].sum()
        t_tds = df['TDS (₹)'].sum()
        t_net = df['Net Payout (₹)'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
        c2.metric("Total TDS Deduction", f"₹ {t_tds:,.2f}")
        c3.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
        
        # बटन
        cb1, cb2 = st.columns(2)
        csv = df.to_csv(index=False).encode('utf-8-sig')
        cb1.download_button("📥 Download Excel", csv, "Statement.csv", "text/csv", use_container_width=True)
        wa_url = f"https://wa.me/?text=Commission Report for {search_exec}: Net Pay: ₹{t_net:,.0f}"
        cb2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)
