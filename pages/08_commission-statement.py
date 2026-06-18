import streamlit as st
import pandas as pd
import datetime

# 1. डेटा सिंक का पक्का तरीका
db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# 2. UI - सारे फिल्टर एक साथ
st.title("📊 Commission Statement")
c1, c2 = st.columns(2)
search_exec = c1.selectbox("👤 Select Partner", options=sorted(list(exec_data.keys())))
scope = c2.radio("📑 Scope", ["Self", "Group", "All"], horizontal=True)

d1, d2 = st.columns(2)
start_d = d1.date_input("📅 Start Date", datetime.date(2020, 1, 1))
end_d = d2.date_input("📅 End Date", datetime.date.today())

if st.button("🚀 Generate Statement"):
    rows = []
    # यहाँ से डेटा प्रोसेस हो रहा है
    for p_name, p_info in db_data.items():
        # Mauza (Z) ढूँढने का पक्का लॉजिक
        mauza = next((str(v) for k, v in p_info.items() if k.lower() == 'mauza'), "N/A")
        
        # प्लॉट का डेटा
        plots = p_info.get('plots', {})
        for pid, info in (plots.items() if isinstance(plots, dict) else enumerate(plots)):
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                # (यहाँ आपकी कैलकुलेशन Logic रहेगी)
                # ...
                rows.append({
                    "S.No.": len(rows)+1, "Customer": info.get('customer_name', 'N/A'),
                    "Plot": str(pid), "Mauza": mauza, "Received": 10000, 
                    "Date": "2026-06-18", "Gross": 500, "Disc": 50, "Net": 450, "TDS": 9, "In Hand": 441
                })

    if rows:
        df = pd.DataFrame(rows)
        # TOTAL को अलग से दिखाना है ताकि टेबल न बिगड़े
        st.table(df)
        
        # Grand Total Calculation
        total_data = df.sum(numeric_only=True)
        st.write("---")
        st.subheader("GRAND TOTALS")
        st.table(pd.DataFrame(total_data).transpose())
        
        st.session_state.final_df = df
        st.session_state.totals = total_data

# 3. प्रोफेशनल प्रिंट लेआउट
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Final A4"):
        # यहाँ साफ़ HTML रेंडरिंग है
        html = f"""
        <style>
            .ftable {{ width: 100%; border-collapse: collapse; font-family: Arial; }}
            .ftable th, .ftable td {{ border: 1px solid #000; padding: 8px; text-align: center; }}
        </style>
        <h2>FIRSTCHOICE INFRA</h2>
        <p>Commission Report: {search_exec}</p>
        {st.session_state.final_df.to_html(classes='ftable', index=False)}
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

