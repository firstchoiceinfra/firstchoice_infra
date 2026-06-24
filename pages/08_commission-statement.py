import streamlit as st
import pandas as pd
import datetime

# 1. पूरी तरह सुरक्षित डेटा सिंक (AttributeError का खात्मा)
def get_sync_data():
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    
    # अगर ex खाली है, तो db से नाम निकालो (सुरक्षित तरीके से)
    if not ex and isinstance(db, dict):
        ex = {}
        for p_name, p in db.items():
            if isinstance(p, dict) and 'plots' in p:
                plots = p['plots']
                # प्लॉट अगर डिक्शनरी है तो ठीक, वरना खाली मान लो
                plot_values = plots.values() if isinstance(plots, dict) else []
                for info in plot_values:
                    if isinstance(info, dict) and 'executive_name' in info:
                        ex[info['executive_name']] = {'name': info['executive_name']}
    return db, ex

db_data, exec_data = get_sync_data()

# 2. UI
st.title("📊 Executive Commission Statement")
# पार्टनर लिस्ट में अब "No options" की जगह नाम आएंगे
partner_list = sorted(list(exec_data.keys()))
search_exec = st.selectbox("👤 Select Partner", options=partner_list if partner_list else ["Data Empty"])

scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

# 3. Generate Logic
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    # सुरक्षित डेटा लूप
    for p_name, p_info in db_data.items() if isinstance(db_data, dict) else []:
        if not isinstance(p_info, dict): continue
        
        # Mauza (Z) सुरक्षित सर्च
        mauza = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza'), "N/A")
        
        plots = p_info.get('plots', {})
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        
        for pid, info in plot_items:
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                # यहाँ आपका 12 कॉलम वाला लॉजिक...
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, 
                    "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                    "Received": float(info.get('token_amount', 0)), 
                    "Date": info.get('booking_date', '2026-06-08'),
                    "Gross": 0, "Discount": 0, "Net Comm": 0, "TDS": 0, "In Hand": 0
                })

    if rows:
        st.session_state.final_df = pd.DataFrame(rows)
        st.table(st.session_state.final_df)
    else:
        st.warning("कोई रिकॉर्ड नहीं मिला।")

