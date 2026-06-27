import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 SECURITY: सिर्फ एडमिन देख सकता है
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

if 'db_projects' not in st.session_state:
    database.init_db()

db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

st.title("📊 Executive Commission Dashboard")

# 1. पार्टनर लिस्ट (Case Insensitive)
partner_names = sorted(list(set([str(v.get('name', k)).strip() for k, v in exec_data.items() if isinstance(v, dict)])))

if partner_names:
    search_exec = st.selectbox("👤 Select Partner", options=partner_names)
    scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
    start_d = st.date_input("📅 Start Date", datetime.date(2025, 6, 20))
    end_d = st.date_input("📅 End Date", datetime.date(2026, 6, 24))

    if st.button("🚀 Generate Statement"):
        rows = []
        
        # --- पूरी बुकिंग्स स्कैन करना ---
        found_any = False
        for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
            if isinstance(p_info, dict) and 'plots' in p_info:
                for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                    if isinstance(info, dict):
                        # नाम का मिलान - केस इनसेंसिटिव
                        exec_name_in_booking = str(info.get('executive_name', '')).strip().lower()
                        
                        # अगर बुकिंग का नाम 'parikshit rumale' जैसा कुछ भी है
                        if exec_name_in_booking == search_exec.lower():
                            # अमाउंट निकालना
                            amt = float(info.get('token_amount', 0))
                            rows.append({"Project": p_name, "Customer": info.get('customer_name', 'N/A'), "Amount": amt})
                            found_any = True
        
        if found_any:
            df = pd.DataFrame(rows)
            st.success("✅ डेटा मिल गया!")
            st.dataframe(df)
        else:
            # 💡 DEBUG: अगर फिर भी नहीं मिल रहा, तो यह लाइन आपको दिखाएगी कि बुकिंग में नाम क्या सेव है
            st.error("❌ कोई डेटा नहीं मिला।")
            st.info("डेटाबेस में बुकिंग का नाम और आपका सिलेक्शन मैच नहीं हो रहा।")

