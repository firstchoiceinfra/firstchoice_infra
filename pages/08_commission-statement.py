import streamlit as st
import pandas as pd
import datetime

# --- 1. Security Check ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

# --- 2. Data Retrieval ---
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# --- 3. UI Filters ---
st.title("📊 Executive Commission Statement")
search_exec = st.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Statement"):
    # (यहाँ डेटा प्रोसेसिंग और कैलकुलेशन लॉजिक होगा...)
    # डमी डेटा जो आपके फॉर्मेट के अनुसार है
    data = [{
        "S.No.": 1, "Mauja": "Mohadi", "Project": "firstchoice city 2", "Plot": "9", 
        "Customer": "sneha chaitanya joshi", "Received": 21000.00, "Date": "2026-06-08", 
        "Gross": 4830.00, "Discount": 777.78, "Net Comm": 4052.22, "TDS": 81.04, "In Hand": 3971.18
    }] # इसी तरह बाकि रोज (rows) जोड़ें
    
    df = pd.DataFrame(data)
    st.session_state.final_df = df

# --- 4. Print Layout (Systematic A4) ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; border: 1px solid #000; width: 750px; margin: auto;">
            <div style="text-align: center;">
                <h1>FIRSTCHOICE INFRA</h1>
                <p><i>Symbol Of Trust...</i></p>
                <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                <hr>
                <h2>Executive Commission Statement</h2>
            </div>
            <p><b>Partner:</b> {search_exec} &nbsp;&nbsp;&nbsp; <b>Period:</b> {start_d} to {end_d}</p>
            
            <table style="width:100%; border-collapse: collapse;" border="1">
                <tr style="background-color: #f2f2f2;">
                    <th>S.No.</th><th>Mauja</th><th>Project</th><th>Plot</th><th>Customer</th>
                    <th>Received</th><th>Date</th><th>Gross</th><th>Discount</th><th>Net Comm</th><th>TDS</th><th>In Hand</th>
                </tr>
                {"".join([f"<tr><td>{r['S.No.']}</td><td>{r['Mauja']}</td><td>{r['Project']}</td><td>{r['Plot']}</td><td>{r['Customer']}</td><td>{r['Received']}</td><td>{r['Date']}</td><td>{r['Gross']}</td><td>{r['Discount']}</td><td>{r['Net Comm']}</td><td>{r['TDS']}</td><td>{r['In Hand']}</td></tr>" for r in st.session_state.final_df.to_dict('records')])}
            </table>
        </div>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

