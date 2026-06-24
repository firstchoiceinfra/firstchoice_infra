import streamlit as st
import pandas as pd
import datetime

# --- 1. Master Sync: Inventory & Partner Management ---
def get_sync_data():
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {}) # Partner Management data
    return db, ex

db_data, exec_data = get_sync_data()

# --- 2. UI ---
st.title("📊 Executive Commission Statement")
# Partner Management से नाम उठाएं
partner_names = [val.get('name', k) for k, val in exec_data.items() if isinstance(val, dict)]
search_exec = st.selectbox("👤 Select Partner", options=sorted(partner_names))

# --- 3. Generate Logic (Difference Commission) ---
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    
    # सिलेक्टेड पार्टनर का कमीशन % और सीनियर का नाम निकालें
    target_partner = next((v for v in exec_data.values() if v.get('name') == search_exec), {})
    my_pct = float(target_partner.get('percentage_exec', 0))
    senior_name = target_partner.get('senior_name', '')

    for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
        mauza = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza'), "N/A")
        plots = p_info.get('plots', {})
        
        for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
            if isinstance(info, dict) and info.get('executive_name') == search_exec:
                # कमीशन कैलकुलेशन (Difference logic)
                amt = float(info.get('token_amount', 0))
                # यहाँ आप अपना difference का लॉजिक लगा सकते हैं
                gross = (amt * my_pct) / 100 
                
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, 
                    "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                    "Received": amt, "Date": info.get('booking_date', '2026-06-08'),
                    "Gross": gross, "Discount": 0, "Net Comm": gross, 
                    "TDS": gross * 0.02, "In Hand": gross * 0.98
                })

    if rows:
        st.session_state.final_df = pd.DataFrame(rows)
        st.table(st.session_state.final_df)
    else:
        st.warning("इस पार्टनर का कोई बुकिंग डेटा नहीं मिला।")

