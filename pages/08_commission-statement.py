import streamlit as st
import pandas as pd
import re
import datetime

# --- 1. Security & Helpers ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 2. Database Sync & Deep Search Mauza ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

def find_mauza(data):
    # अब यह सिर्फ 'Mauza' को ही सर्च करेगा (Case-insensitive)
    for k, v in data.items():
        if k.lower() == 'mauza': return str(v)
    return "N/A"

# --- 3. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

# --- 4. Logic Engine ---
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauza = find_mauza(p_info)
            plots = p_info['plots']
            
            for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # यहाँ कैलकुलेशन और फिल्टरिंग वही है जो हमने फाइनल की थी
                    amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                    
                    rows.append({
                        "S.No.": len(rows)+1,
                        "Customer": info.get('customer_name', 'N/A'),
                        "Plot": str(pid).upper(),
                        "Mauza": mauza,
                        "Received": amt,
                        "Date": info.get('booking_date', 'N/A'),
                        "Gross": 0.0, "Disc": 0.0, "Net": 0.0, "TDS": 0.0, "In Hand": 0.0
                    })
    
    if rows:
        df = pd.DataFrame(rows)
        # टोटल रो को अलग से बनाना ताकि एरर न आए
        st.table(df) # st.table एकदम फिक्स्ड चौड़ाई वाली टेबल दिखाता है
        
        # Grand Totals
        st.write("---")
        st.subheader("GRAND TOTALS")
        totals = df.sum(numeric_only=True)
        st.table(pd.DataFrame(totals).transpose())
    else:
        st.warning("कोई डेटा नहीं मिला।")

