import streamlit as st
import pandas as pd
import datetime

# --- 1. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted")
    st.stop()

# --- 2. Normalized Data Reader (सभी पेजों के लिए एक ही लॉजिक) ---
def get_safe_data():
    db_data = st.session_state.get('db_projects', {})
    exec_data = db_data.get('executives', {})
    return db_data, exec_data

def get_clean(s): return "".join(filter(str.isalnum, str(s).lower()))

# --- 3. UI Filters ---
st.title("📊 Executive Commission Statement")
db_data, exec_data = get_safe_data()

search_exec = st.selectbox("👤 Select Partner", sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

# --- 4. Core Logic (No Error Logic) ---
if st.button("🚀 Generate Systematic Statement"):
    rows = []
    target = get_clean(search_exec)
    
    # पक्का सिंक: पेरेंट ट्री
    parents = {get_clean(k): get_clean(v.get('senior_name', '')) for k, v in exec_data.items()}
    
    def get_downlines(boss):
        res = []
        for c, p in parents.items():
            if p == boss:
                res.append(c)
                res.extend(get_downlines(c))
        return list(set(res))
    
    downlines = get_downlines(target)

    for p_name, p_info in db_data.items():
        # पक्का Mauza (Z) सर्च
        mauza = next((str(v) for k, v in p_info.items() if k.lower() in ['mauza', 'mauja']), "N/A")
        
        # पक्का Plot सर्च (Dict हो या List, दोनों हैंडल करेगा)
        plots = p_info.get('plots', {})
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        
        for pid, info in plot_items:
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                seller = get_clean(info.get('executive_name', ''))
                
                # स्कोप फिल्टर
                match = (scope=="Self" and seller==target) or (scope=="Group" and seller in downlines) or (scope=="All" and (seller==target or seller in downlines))
                
                if match:
                    amt = float(info.get('token_amount', 0))
                    b_date = pd.to_datetime(str(info.get('booking_date', '2020-01-01'))).date()
                    if start_d <= b_date <= end_d:
                        rows.append({
                            "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, "Plot": str(pid),
                            "Customer": info.get('customer_name', 'N/A'), "Received": amt, "Date": b_date,
                            "Gross": amt*0.1, "Discount": amt*0.02, "Net Comm": amt*0.08, "TDS": amt*0.002, "In Hand": amt*0.078
                        })

    if rows:
        df = pd.DataFrame(rows)
        st.session_state.final_df = df
        st.table(df)
    else:
        st.warning("No data found for this selection.")

# --- 5. Print Layout (Fixed A4) ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        html = f"""
        <style>
            .ftable {{ width:100%; border-collapse:collapse; font-family:Arial; }}
            .ftable th, .ftable td {{ border:1px solid #000; padding:5px; text-align:center; font-size:12px; }}
        </style>
        <div style="width:750px; margin:auto; padding:20px; border:1px solid #000;">
            <center><h1>FIRSTCHOICE INFRA</h1><p>Symbol Of Trust...</p></center>
            <p><b>Partner:</b> {search_exec} | <b>Period:</b> {start_d} to {end_d}</p>
            {st.session_state.final_df.to_html(classes='ftable', index=False)}
        </div>
        <script>window.print();</script>"""
        st.components.v1.html(html, height=800)

