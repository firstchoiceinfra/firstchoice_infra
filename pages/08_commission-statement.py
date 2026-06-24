import streamlit as st
import pandas as pd
import datetime

# --- 1. Security ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted")
    st.stop()

# --- 2. Data Retrieval ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# --- 3. UI Filters ---
st.title("📊 Executive Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    rows = []
    # डेटा फेचिंग लूप (सिंक के साथ)
    for p_name, p_info in db_data.items():
        # पक्का Mauza सर्च (Z वाली स्पेलिंग)
        mauza = next((str(v) for k, v in p_info.items() if k.lower() == 'mauza'), "N/A")
        
        plots = p_info.get('plots', {})
        for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                # यहाँ कैलकुलेशन Logic
                amt = float(info.get('token_amount', 0))
                # 12 कॉलम्स का फिक्स्ड स्ट्रक्चर
                rows.append({
                    "S.No.": len(rows)+1, "Mauza": mauza, "Project": p_name, 
                    "Plot": str(pid), "Customer": info.get('customer_name', 'N/A'),
                    "Received": amt, "Date": info.get('booking_date', '2026-06-08'),
                    "Gross": amt*0.1, "Discount": amt*0.02, "Net Comm": amt*0.08, 
                    "TDS": amt*0.002, "In Hand": amt*0.078
                })

    df = pd.DataFrame(rows)
    st.session_state.final_df = df
    st.table(df) # टेबल को यहाँ दिखा दिया

# --- 4. Print Logic (A4 Perfect) ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        df_html = st.session_state.final_df.to_html(index=False, classes='table table-bordered')
        html = f"""
        <div style="font-family: Arial; padding: 20px; border: 1px solid #000; max-width: 800px; margin: auto;">
            <center>
                <h1>FIRSTCHOICE INFRA</h1>
                <p><i>Symbol Of Trust...</i></p>
                <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                <hr>
                <h2>Executive Commission Statement</h2>
            </center>
            <p><b>Partner:</b> {search_exec} &nbsp; <b>Period:</b> {start_d} to {end_d}</p>
            {df_html}
        </div>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

