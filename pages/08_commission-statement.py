import streamlit as st
import pandas as pd
import datetime

# --- 1. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted")
    st.stop()

# --- 2. Logic ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

def get_clean(s): return "".join(filter(str.isalnum, str(s).lower()))
parents_tree = {get_clean(k): get_clean(v.get('senior_name', '')) for k, v in exec_data.items()}

def get_downlines(boss):
    boss = get_clean(boss)
    res = []
    for child, parent in parents_tree.items():
        if parent == boss:
            res.append(child)
            res.extend(get_downlines(child))
    return list(set(res))

# --- 3. UI ---
st.title("📊 Executive Commission Statement")
search_exec = st.selectbox("Select Partner", sorted(list(exec_data.keys())))
scope = st.radio("Scope", ["Self", "Group", "All"], horizontal=True)
d1, d2 = st.columns(2)
start_d = d1.date_input("Start Date", datetime.date(2024, 6, 6))
end_d = d2.date_input("End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Statement"):
    target = get_clean(search_exec)
    downlines = get_downlines(target)
    rows = []
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauza = next((str(v) for k, v in p_info.items() if k.lower() == 'mauza'), "N/A")
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    seller = get_clean(info.get('executive_name', ''))
                    match = (scope=="Self" and seller==target) or (scope=="Group" and seller in downlines) or (scope=="All" and (seller==target or seller in downlines))
                    
                    if match:
                        amt = float(info.get('token_amount', 0))
                        b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                        if start_d <= b_date <= end_d:
                            rows.append({
                                "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name,
                                "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                                "Received": amt, "Date": b_date, "Gross": amt*0.1,
                                "Discount": amt*0.02, "Net Comm": amt*0.08, "TDS": amt*0.002, "In Hand": amt*0.078
                            })
    
    if rows:
        df = pd.DataFrame(rows)
        st.session_state.final_df = df
        st.table(df) # जेनरेट होते ही टेबल दिखाएं
    else: st.warning("No data found.")

# --- 4. Print Layout ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        html = f"""
        <div style="font-family:Arial; width:800px; margin:auto; padding:20px; border:1px solid #000;">
            <center>
                <h1>FIRSTCHOICE INFRA</h1>
                <p><i>Symbol Of Trust...</i></p>
                <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                <hr>
                <h2>Executive Commission Statement</h2>
            </center>
            <p><b>Partner:</b> {search_exec} &nbsp;&nbsp; <b>Period:</b> {start_d} to {end_d}</p>
            {st.session_state.final_df.to_html(index=False, border=1)}
            <script>window.print();</script>
        </div>"""
        st.components.v1.html(html, height=800)

