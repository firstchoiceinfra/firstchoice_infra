import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Commission Statement", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("📊 Advanced Statement & Payout Ledger")

# 1. एग्जीक्यूटिव लिस्ट चेक करें
exec_clean_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
if not exec_clean_list:
    st.error("🚨 डेटाबेस में कोई एग्जीक्यूटिव नहीं मिला। क्या आपने Partner Management में एग्जीक्यूटिव ऐड किए हैं?")
    st.stop()

# 2. इनपुट फिल्टर्स
col1, col2, col3 = st.columns(3)
search_exec = col1.selectbox("🔎 Select Executive", exec_clean_list)
start_date = col2.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = col3.date_input("📅 End Date", datetime.date.today())

# 3. जनरेट बटन
if st.button("🔍 Generate Ledger"):
    statement_rows = []
    # यहाँ आपका लूपिंग लॉजिक जो 'statement_rows' को भरता है
    # (जो पहले काम कर रहा था, उसे यहाँ पेस्ट करें)
    
    # --- DEBUGGING: चेक करें कि डेटा मिल रहा है या नहीं ---
    if not statement_rows:
        st.warning(f"⚠️ {search_exec} के लिए इस तारीख के बीच कोई 'Booked' बुकिंग नहीं मिली।")
    else:
        df = pd.DataFrame(statement_rows)
        st.success(f"🎉 {len(df)} रिकॉर्ड मिले!")
        st.dataframe(df, use_container_width=True)
        
        # टोटल कैलकुलेशन
        t_net = df['Net Payout (₹)'].sum()
        st.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
        
        # WhatsApp बटन
        wa_url = f"https://wa.me/?text=Commission Report: Net Pay ₹{t_net:,.0f}"
        st.markdown(f'<a href="{wa_url}" target="_blank" style="padding:10px; background:#25D366; color:white; border-radius:5px; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)

