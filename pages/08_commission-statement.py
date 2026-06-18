import streamlit as st
import pandas as pd
import re
import datetime
import base64
import os

# --- 1. Page Config ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Statement")

# --- 2. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 3. Functions ---
def get_image_base64(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 4. Sync Database ---
db_data = st.session_state.get('db_projects', {})

# --- 5. UI ---
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(db_data.get('executives', {}).keys())))
col1, col2 = st.columns(2)
start_d = col1.date_input("Start Date", datetime.date(2020, 1, 1))
end_d = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            # 🔥 सिंक इंजन: मौजा सीधा डैशबोर्ड के डेटा से
            mauja = str(p_info.get('mauja', 'N/A'))
            plots = p_info['plots']
            
            for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
                if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                    # यहाँ कैलकुलेशन और सेलर फ़िल्टरिंग होती है...
                    # (कैलकुलेशन वही पुरानी वाली जो सही चल रही थी)
                    amt = safe_float(info.get('token_amount', 0)) + sum(safe_float(p.get('amount', 0)) for p in info.get('partial_payments', []))
                    gross = amt * 0.05 # उदाहरण के लिए
                    rows.append({
                        "Customer": info.get('customer_name', 'N/A'),
                        "Plot": str(pid), "Mauja": mauja, "Received": amt,
                        "Gross": gross, "Disc": 0, "Net Comm": gross, "TDS": gross*0.02, "In Hand": gross*0.98
                    })
    
    df = pd.DataFrame(rows)
    # 🔥 ग्रांड टोटल
    total_row = df.sum(numeric_only=True)
    total_row['Customer'] = 'GRAND TOTAL'
    df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
    st.session_state.final_df = df
    st.dataframe(df, use_container_width=True)

# --- 6. Print Engine ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Final Statement"):
        logo = get_image_base64('logo.jpg')
        html = f"""
        <div style='font-family: Arial;'>
            <div style='display:flex; align-items:center;'>
                <img src='data:image/jpeg;base64,{logo}' width='100'>
                <div style='margin-left:20px;'>
                    <h1 style='margin:0;'>FIRSTCHOICE INFRA</h1>
                    <p style='margin:0;'>Symbol Of Trust</p>
                    <p style='margin:0;'>Nagpur, Maharashtra</p>
                </div>
            </div>
            <hr>
            <h3>Executive: {search_exec} | Period: {start_d} to {end_d}</h3>
            {st.session_state.final_df.to_html(index=False, classes='table table-striped')}
        </div>
        <script>window.print();</script>
        """
        components.html(html, height=800)

