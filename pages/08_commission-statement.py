import streamlit as st
import pandas as pd
import datetime

# --- 1. Partner Management Page Sync (Fix) ---
def get_sync_data():
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    
    # अब यह Partner Management वाले डेटा को प्राथमिकता देगा
    # अगर ex में 'name' नाम की की (key) है, तो उसे यूज़ करेंगे
    partner_list = []
    if isinstance(ex, dict):
        for val in ex.values():
            if isinstance(val, dict) and 'name' in val:
                partner_list.append(val['name'])
    
    return db, sorted(partner_list)

db_data, partner_list = get_sync_data()

# --- 2. UI ---
st.title("📊 Executive Commission Statement")

if not partner_list:
    st.error("Partner Management पेज में डेटा नहीं मिल रहा है।")
    st.stop()

search_exec = st.selectbox("👤 Select Partner", options=partner_list)
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

# --- 3. Generate Logic (वही जो काम कर रहा है) ---
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
        mauza = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza'), "N/A")
        plots = p_info.get('plots', {})
        
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        for pid, info in plot_items:
            if isinstance(info, dict) and info.get('executive_name') == search_exec:
                amt = float(info.get('token_amount', 0))
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, 
                    "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                    "Received": amt, "Date": info.get('booking_date', '2026-06-08'),
                    "Gross": amt*0.1, "Discount": amt*0.02, "Net Comm": amt*0.08, 
                    "TDS": amt*0.002, "In Hand": amt*0.078
                })

    if rows:
        st.session_state.final_df = pd.DataFrame(rows)
        st.table(st.session_state.final_df)
    else:
        st.warning("इस पार्टनर के लिए कोई बुकिंग नहीं है।")

