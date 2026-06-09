import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रीमियम मल्टी-कलर थीम
st.markdown("""<style>
    .premium-card { background: linear-gradient(135deg, #ffffff 0%, #fdfbf7 100%); padding: 40px; border-radius: 25px; border: 2px solid #b8860b; box-shadow: 0 15px 35px rgba(184,134,11,0.2); }
    .comp-name { text-align: center; color: #b8860b; font-size: 48px; font-weight: 900; letter-spacing: 3px; text-transform: uppercase; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
    .comp-slogan { text-align: center; color: #1e3a8a; font-size: 20px; font-style: italic; margin-bottom: 20px; border-bottom: 3px double #b8860b; padding-bottom: 15px; }
    
    /* मल्टी-कलर बटन्स */
    div.stButton > button:first-child { background: linear-gradient(45deg, #1e3a8a, #3b82f6) !important; color: white !important; border: none !important; }
    .btn-print { background: linear-gradient(45deg, #b8860b, #d4af37) !important; color: white !important; }
    .btn-whatsapp { background: linear-gradient(45deg, #25d366, #128c7e) !important; color: white !important; }
</style>""", unsafe_allow_html=True)

# (बाकी आपका कैलकुलेशन लॉजिक यहाँ वैसा ही रहेगा)

if rows:
    # प्रीमियम इनवॉइस व्यू
    st.markdown("<div class='premium-card'>", unsafe_allow_html=True)
    st.markdown("<h1 class='comp-name'>FIRSTCHOICE INFRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='comp-slogan'>Symbol Of Trust...</p>", unsafe_allow_html=True)
    
    # ... (आपका टेबल और टोटल्स कोड) ...
    
    # प्रीमियम कलर्ड एक्शन बार
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🖨️ Print Statement", key="print_btn"): 
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    with col_b:
        if st.button("💬 Send to WhatsApp", key="wa_btn"): 
            st.write("Redirecting to WhatsApp...")
    st.markdown("</div>", unsafe_allow_html=True)
