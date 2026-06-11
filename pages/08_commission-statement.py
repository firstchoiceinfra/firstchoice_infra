import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# CSS स्टाइलिंग
st.markdown("""<style>
    .premium-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border-top: 15px solid #1e3a8a; }
    .stButton>button { border-radius: 8px !important; font-weight: bold !important; width: 100%; }
</style>""", unsafe_allow_html=True)

search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Elite Statement", use_container_width=True):
    # (कैलकुलेशन लॉजिक यहाँ आपका पहले वाला ही है...)
    # [कैलकुलेशन कोड यहाँ रखें]
    
    # कैलकुलेशन के बाद का हिस्सा (यह बटन के अंदर ही रहेगा)
    if 'df' in locals():
        st.markdown("<div class='premium-container'>", unsafe_allow_html=True)
        # ... (कंपनी हेडर और टेबल यहाँ रखें) ...
        
        # बटन का सही लॉजिक
        c1, c2 = st.columns(2)
        
        # प्रिंट बटन (JS के जरिए)
        if c1.button("🖨️ Print Statement"):
            st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            st.toast("प्रिंट डायलॉग खुल रहा है...")
            
        # व्हाट्सएप बटन (लिंक के जरिए)
        if c2.button("💬 Send to WhatsApp"):
            msg = f"Hello {search_exec}, here is your commission statement from Firstchoice Infra."
            wa_link = f"https://wa.me/?text={msg}"
            st.markdown(f'<a href="{wa_link}" target="_blank">👉 Click here to open WhatsApp</a>', unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

