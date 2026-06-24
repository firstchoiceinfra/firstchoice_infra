import streamlit as st
import pandas as pd
import datetime
import base64
import os

# --- 1. Security & Setup ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Master Sync Logic ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# Partner Registry
def get_clean_name(name): return "".join(filter(str.isalnum, str(name).lower()))

# Partner Tree for Downline Sync
parents_tree = {}
for ex_name, details in exec_data.items():
    if isinstance(details, dict):
        senior = get_clean_name(details.get('senior_name', ''))
        child = get_clean_name(details.get('name', ex_name))
        if senior and senior != child:
            parents_tree[child] = senior

# Recursive Downline Engine
def get_all_downlines(boss_clean):
    res = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            res.append(child)
            res.extend(get_all_downlines(child))
    return list(set(res))

# --- 3. UI Filters ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

col1, col2 = st.columns(2)
start_d = col1.date_input("Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Corrected Statement"):
    target_clean = get_clean_name(search_exec)
    all_downlines = get_all_downlines(target_clean)
    rows = []
    
    # --- 4. Strict Sync Engine ---
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauza = str(p_info.get('mauja', 'N/A'))
            plots = p_info['plots']
            
            for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = get_clean_name(info.get('executive_name', ''))
                    
                    # Exact Filter Logic
                    match = False
                    if scope == "Self" and seller == target_clean: match = True
                    elif scope == "Group" and seller in all_downlines: match = True
                    elif scope == "All" and (seller == target_clean or seller in all_downlines): match = True
                    
                    if match:
                        # Date Validation
                        b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                        if start_d <= b_date <= end_d:
                            # Calculation
                            amt = float(info.get('token_amount', 0))
                            rows.append({
                                "S.No.": len(rows)+1, "Customer": info.get('customer_name', 'N/A'),
                                "Plot": str(pid), "Mauza": mauza, "Received": amt, "Date": b_date,
                                "Gross": amt*0.1, "Disc": amt*0.02, "Net": amt*0.08, "TDS": amt*0.002, "In Hand": amt*0.078
                            })

    if rows:
        df = pd.DataFrame(rows)
        st.table(df)
        st.session_state.final_df = df
    else:
        st.warning("No data found for this selection.")

# --- 5. Professional Print ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Systematic Statement"):
        st.components.v1.html(f"""
        <div style='font-family:Arial; padding:40px;'>
            <center><h1>FIRSTCHOICE INFRA</h1><p>Symbol Of Trust...</p></center>
            <p>Partner: {search_exec} | Date: {start_d} to {end_d}</p>
            {st.session_state.final_df.to_html(classes='table', index=False)}
            <script>window.print();</script>
        </div>""", height=800)

