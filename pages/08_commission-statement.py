
import streamlit as st
import pandas as pd
import datetime

# --- 1. Master Sync Function (जो सभी पेजों के डेटा को संभालेगा) ---
def get_safe_data():
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    return db, ex

def clean_txt(s): return "".join(filter(str.isalnum, str(s).lower()))

# --- 2. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted")
    st.stop()

st.title("📊 Executive Commission Statement")
db, ex = get_safe_data()

# --- 3. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(ex.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    target = clean_txt(search_exec)
    rows = []
    
    # पेरेंट ट्री (Group के लिए)
    parents = {clean_txt(k): clean_txt(v.get('senior_name', '')) for k, v in ex.items()}
    def get_downlines(boss):
        res = []
        for c, p in parents.items():
            if p == boss:
                res.append(c); res.extend(get_downlines(c))
        return list(set(res))
    
    downlines = get_downlines(target)

    # डेटा लूप - सुरक्षित (Safe Access)
    for p_name, p_info in db.items():
        if not isinstance(p_info, dict): continue
        
        # 'Mauza' (Z) सर्च - केस इनसेंसिटिव
        mauza = next((str(v) for k, v in p_info.items() if k.lower() == 'mauza'), "N/A")
        plots = p_info.get('plots', {})
        
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        for pid, info in plot_items:
            if not isinstance(info, dict) or str(info.get('status', '')).lower() != 'booked': continue
            
            seller = clean_txt(info.get('executive_name', ''))
            match = (scope=="Self" and seller==target) or (scope=="Group" and seller in downlines) or (scope=="All" and (seller==target or seller in downlines))
            
            if match:
                amt = float(info.get('token_amount', 0))
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, "Plot": str(pid),
                    "Customer": info.get('customer_name', 'N/A'), "Received": amt, 
                    "Date": info.get('booking_date', '2026-06-08'), "Gross": amt*0.1, 
                    "Discount": amt*0.02, "Net Comm": amt*0.08, "TDS": amt*0.002, "In Hand": amt*0.078
                })

    if rows:
        st.session_state.final_df = pd.DataFrame(rows)
        st.table(st.session_state.final_df)
    else:
        st.warning("No records found.")

# --- 4. Print & PDF Layout ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Systematic Statement"):
        st.components.v1.html(f"""
        <div style="font-family:Arial; width:100%; max-width:800px; margin:auto; border:1px solid #000; padding:20px;">
            <center><h1>FIRSTCHOICE INFRA</h1><p>Symbol Of Trust...</p></center>
            <hr>
            <h3>Executive Commission Statement</h3>
            <p><b>Partner:</b> {search_exec} | <b>Period:</b> {start_d} to {end_d}</p>
            {st.session_state.final_df.to_html(classes='table', index=False)}
        </div>
        <script>window.print();</script>""", height=800)
