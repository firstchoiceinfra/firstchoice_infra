import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# मल्टी-कलर प्रीमियम स्टाइलिंग
st.markdown("""<style>
    .a4-container { background: linear-gradient(135deg, #ffffff 0%, #f0f4f8 100%); padding: 40px; border-radius: 20px; border: 3px solid #b8860b; color: #1e293b; }
    .header-box { text-align: center; border-bottom: 4px double #1e3a8a; padding-bottom: 20px; }
    .comp-name { color: #b8860b; font-size: 48px; font-weight: 900; text-transform: uppercase; margin: 0; }
    .slogan { color: #1e3a8a; font-size: 18px; font-style: italic; font-weight: 600; }
    .btn-group { display: flex; gap: 15px; justify-content: center; margin-top: 30px; }
    @media print { .no-print { display: none; } .a4-container { border: none; } }
</style>""", unsafe_allow_html=True)

search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")

if st.button("🚀 Generate Multi-Color Statement"):
    # (आपका कैलकुलेशन लॉजिक यहाँ वैसा ही रहेगा...)
    # [कैलकुलेशन लॉजिक...]
    st.session_state.df_view = pd.DataFrame(rows)

if 'df_view' in st.session_state:
    df = st.session_state.df_view
    
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    # प्रीमियम हेडर
    st.markdown(f"""<div class='header-box'>
        <h1 class='comp-name'>FIRSTCHOICE INFRA</h1>
        <p class='slogan'>Symbol Of Trust...</p>
        <p>📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; justify-content:space-between; font-weight:bold;'><span>Partner: {search_exec}</span> <span>Period: {start} to {end}</span></div>", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    # फाइनेंशियल समरी (मल्टी-कलर)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
    
    # बटन्स (नो-प्रिंट क्लास)
    st.markdown("<div class='no-print btn-group'>", unsafe_allow_html=True)
    if st.button("🖨️ Print as PDF"): st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    wa_msg = f"FIRSTCHOICE INFRA%0AStatement for {search_exec}%0AGross: ₹{df['Gross'].sum():,.2f}%0ANet Pay: ₹{df['Net In Hand'].sum():,.2f}"
    st.markdown(f'<a href="https://wa.me/?text={wa_msg}" target="_blank"><button style="padding:15px 30px; background:#25d366; color:white; border:none; border-radius:10px; font-weight:bold;">💬 Send to WhatsApp</button></a>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

