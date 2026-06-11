import streamlit as st
import database
import pandas as pd
import datetime

# Page configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# PREMIUM A4 PRINT CSS
st.markdown("""<style>
    @media print {
        .no-print { display: none !important; }
        .a4-page { width: 210mm; margin: auto; padding: 20px; background: white; color: black; }
    }
    .a4-page { background: white; padding: 50px; border: 1px solid #ccc; max-width: 800px; margin: auto; color: black; }
    .header-section { text-align: center; border-bottom: 2px solid #b8860b; padding-bottom: 20px; margin-bottom: 20px; }
    .company-name { font-size: 32px; font-weight: 900; color: #b8860b; margin: 0; }
    .slogan { font-style: italic; color: #1e3a8a; }
    .info-row { display: flex; justify-content: space-between; margin: 20px 0; font-weight: bold; }
    .summary-box { background: #f8fafc; padding: 15px; border: 1px solid #ddd; margin-top: 20px; }
</style>""", unsafe_allow_html=True)

# सिलेक्शन लॉजिक (आपका पुराना ही)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")

if st.button("🚀 Generate Elite Statement"):
    # ... (आपका कैलकुलेशन लॉजिक यहाँ रखें) ...
    # मान लेते हैं कि 'df' तैयार है
    st.session_state.df_view = df 

# स्टेटमेंट डिस्प्ले (A4 स्टाइल में)
if 'df_view' in st.session_state:
    df = st.session_state.df_view
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    # कंपनी लेटरहेड
    st.markdown("<div class='header-section'><h1 class='company-name'>FIRSTCHOICE INFRA</h1><p class='slogan'>Symbol Of Trust...</p><p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p></div>", unsafe_allow_html=True)
    
    st.markdown("<h2>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"<div class='info-row'><span>Partner: {search_exec}</span> <span>Period: {start} to {end}</span></div>", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    # फाइनल समरी
    st.markdown("<div class='summary-box'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Final Net Pay", f"₹ {df['Net In Hand'].sum():,.2f}")
    st.markdown("</div></div>", unsafe_allow_html=True)
    
    # एक्शन बटन्स
    st.markdown("<div class='no-print' style='text-align:center; margin-top:20px;'>", unsafe_allow_html=True)
    if st.button("🖨️ Print as A4"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    
    st.info("WhatsApp के लिए 'Print as A4' दबाएं, फिर 'Save as PDF' चुनें और उस फाइल को भेजें। यही सबसे प्रोफेशनल तरीका है।")
    st.markdown("</div>", unsafe_allow_html=True)

