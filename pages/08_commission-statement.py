import streamlit as st
import database
import pandas as pd
import datetime

# Page setup
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# मल्टी-कलर प्रीमियम स्टाइलिंग (A4 Print Ready)
st.markdown("""<style>
    .a4-page { background: white; padding: 40px; border-radius: 15px; border: 2px solid #b8860b; color: black; max-width: 800px; margin: auto; }
    .header-sect { text-align: center; border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
    .btn-container { display: flex; gap: 20px; justify-content: center; margin-top: 20px; }
    @media print { .no-print { display: none !important; } }
</style>""", unsafe_allow_html=True)

# ... (आपका कैलकुलेशन और डिस्प्ले लॉजिक वही रहेगा) ...

# फाइनल रेंडरिंग पार्ट
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    
    st.markdown("<div class='a4-page' id='print-area'>", unsafe_allow_html=True)
    # 1. कंपनी हेडर
    st.markdown("""<div class='header-sect'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    # 2. स्टेटमेंट टाइटल और डिटेल्स
    st.markdown("<h2 style='text-align:center;'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"**Partner:** {search_exec} | **Period:** {start} to {end}", unsafe_allow_html=True)
    
    # 3. टेबल
    st.dataframe(df, use_container_width=True)
    
    # 4. फाइनेंशियल समरी
    cols = st.columns(4)
    cols[0].metric("Gross", f"₹{df['Gross'].sum():,.2f}")
    cols[1].metric("Discount", f"₹{df['Discount'].sum():,.2f}")
    cols[2].metric("TDS", f"₹{df['TDS (2%)'].sum():,.2f}")
    cols[3].metric("Net Pay", f"₹{df['Net In Hand'].sum():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # 5. एक्शन बटन्स (जो सीधे PDF में बदलेंगे)
    st.markdown("<div class='no-print' style='text-align:center; margin-top:30px;'>", unsafe_allow_html=True)
    st.info("💡 प्रो-टिप: 'Print/Save as PDF' दबाएं और फाइल को PDF के रूप में सेव करें। इसे आप किसी भी WhatsApp पर 'Document' की तरह भेज सकते हैं।")
    
    if st.button("🖨️ Save as A4 PDF"):
        st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

