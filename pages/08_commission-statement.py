
import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(page_title="Commission Statement", layout="wide")

# डेटाबेस सिंक
database.init_db()
db_data = st.session_state.db_projects

st.title("📊 Advanced Statement & Payout Ledger")

# यहाँ अपना 'Generate' वाला पूरा बटन का लॉजिक रखें
if st.button("🔍 Generate Comprehensive Ledger"):
    # सुनिश्चित करें कि यहाँ जो 'for' लूप है, उसके अंत में आप सारी इंडेंटेशन सही कर रहे हैं
    statement_rows = [] 
    
    # [यहाँ अपना लूपिंग कोड रखें]
    
    # यह हिस्सा सबसे महत्वपूर्ण है, यहाँ गलती न हो:
    if 'statement_rows' in locals() and statement_rows:
        df = pd.DataFrame(statement_rows)
        st.dataframe(df, use_container_width=True)
        # कैलकुलेशन
        t_net = df['Net Payout (₹)'].sum()
        st.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
    else:
        st.info("डेटा नहीं मिला।")
