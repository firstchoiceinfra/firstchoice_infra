import streamlit as st
import pandas as pd
import datetime

# --- 1. Universal Data Loader (इसे अपने डेटाबेस के हिसाब से सेट करें) ---
def load_all_data():
    # यहाँ अपना डेटाबेस कनेक्शन लिखें जो आपके 'main.py' में है
    # उदाहरण: 
    # if 'db' not in st.session_state:
    # st.session_state.db = firebase.db.reference('/')
    
    # यह सुनिश्चित करेगा कि डेटा हमेशा मिले
    if 'db_projects' not in st.session_state or 'executives' not in st.session_state:
        # अगर आपके पास डेटा लोड करने का कोई स्पेसिफिक फंक्शन है, उसे यहाँ कॉल करें
        # या यहाँ डेटाबेस से वैल्यू 'get' करें
        pass 
    return st.session_state.get('db_projects', {}), st.session_state.get('executives', {})

# --- 2. Initialize Page ---
db_data, exec_data = load_all_data()

# अगर डेटा फिर भी न मिले, तो एक 'Retry' बटन दिखाएं
if not exec_data:
    st.warning("⚠️ Data not detected. Please ensure you are logged in or data is synced.")
    if st.button("🔄 Try Reloading Data"):
        st.rerun()

# --- 3. Dashboard Logic ---
st.title("📊 Executive Commission Dashboard")

# पार्टनर लिस्ट
partner_list = sorted([v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)]) if exec_data else []

search_exec = st.selectbox("👤 Select Partner", options=partner_list if partner_list else ["No Data"])
scope = st.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)
col1, col2 = st.columns(2)
start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

if st.button("🚀 Generate Systematic Statement"):
    if not partner_list:
        st.error("No data found to generate report.")
    else:
        # कैलकुलेशन लूप
        rows = []
        for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
            plots = p_info.get('plots', {})
            for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
                if isinstance(info, dict) and info.get('executive_name') == search_exec:
                    amt = float(info.get('token_amount', 0))
                    rows.append({
                        "Project": p_name, "Plot": str(pid), 
                        "Customer": info.get('customer_name', 'N/A'),
                        "Received": amt, "Date": info.get('booking_date', '2026-01-01'),
                        "Commission": amt * 0.08 
                    })
        
        if rows:
            st.session_state.final_df = pd.DataFrame(rows)
            st.session_state.meta = {"partner": search_exec, "start": start_d, "end": end_d}
            st.session_state.page = 'report'
            st.rerun()
        else:
            st.warning("No bookings found for this partner.")

# --- 4. Report Section (One-Page Flow) ---
if st.session_state.get('page') == 'report':
    st.divider()
    st.title("📄 Commission Statement Report")
    st.table(st.session_state.final_df)
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()

