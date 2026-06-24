import streamlit as st
import pandas as pd
import datetime

# --- 1. Security & Setup ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted")
    st.stop()

# --- 2. Safe Mauza Finder (No Errors) ---
def get_mauza_safe(p_info):
    # यह चेक करेगा कि p_info एक डिक्शनरी है
    if isinstance(p_info, dict):
        for k, v in p_info.items():
            if str(k).lower() == 'mauza':
                return str(v)
    return "N/A"

# --- 3. UI Filters ---
st.title("📊 Executive Commission Statement")
# ... (बाकी सिलेक्ट और डेट रेंज कोड रखें) ...

if st.button("🚀 Generate Systematic Statement"):
    rows = []
    # सुरक्षित लूप
    for p_name, p_info in db_data.items():
        # पक्का Mauza (Z) चेक
        mauza = get_mauza_safe(p_info)
        
        # प्लॉट का डेटा सुरक्षित तरीके से निकालें
        plots = p_info.get('plots', {}) if isinstance(p_info, dict) else {}
        
        for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                # यहाँ डेटा जोड़ें
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, 
                    "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                    "Received": float(info.get('token_amount', 0)), 
                    "Date": info.get('booking_date', '2026-06-08'),
                    "Gross": 0, "Discount": 0, "Net Comm": 0, "TDS": 0, "In Hand": 0
                })

    if rows:
        df = pd.DataFrame(rows)
        st.table(df) # टेबल यहाँ साफ़ दिखेगी
        st.session_state.final_df = df

