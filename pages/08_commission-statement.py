import streamlit as st
import database
import pandas as pd
import urllib.parse
import datetime

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects

# प्रोफेशनल हेडर
def print_commission_header(exec_name, start, end):
    st.markdown(f"""
    <div style="border: 4px solid #b8860b; padding: 20px; border-radius: 15px; background: #fdfaf6; text-align: center;">
        <h1>Firstchoice Infra</h1>
        <h2>Executive Commission Statement</h2>
        <p><b>Executive:</b> {exec_name} | <b>Period:</b> {start.strftime('%d-%m-%Y')} to {end.strftime('%d-%m-%Y')}</p>
    </div>
    """, unsafe_allow_html=True)

# [यहाँ अपना पूरा Ledger Engine लूप कोड पेस्ट करें]
# (जो आपने पहले इस्तेमाल किया था, वही यहाँ काम करेगा)

# अंत में यह जोड़ें:
if 'statement_rows' in locals() and statement_rows:
    df = pd.DataFrame(statement_rows)
    print_commission_header(search_exec, start_date, end_date)
    st.dataframe(df, use_container_width=True)
    
    t_gross = df['Gross (₹)'].sum()
    t_net = df['Net Payout (₹)'].sum()
    
    c1, c2 = st.columns(2)
    c1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
    c2.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
    
    # बटन्स
    cb1, cb2 = st.columns(2)
    csv = df.to_csv(index=False).encode('utf-8-sig')
    cb1.download_button("📥 Download Excel", csv, "Commission.csv", "text/csv")
    wa_url = f"https://wa.me/?text=Report for {search_exec}: Net Pay: ₹{t_net:,.0f}"
    cb2.markdown(f'<a href="{wa_url}" target="_blank" style="padding:10px; background:#25D366; color:white; border-radius:5px; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)
