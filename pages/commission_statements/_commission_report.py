import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("📄 Final Commission Report")

# 1. Check if data exists
if 'final_df' not in st.session_state:
    st.error("No data generated! Please go back to the Dashboard and generate data first.")
    if st.button("⬅️ Back to Dashboard"):
        st.switch_page("pages/08_commission-statement.py") # अपने फाइल का सही पाथ दें
else:
    df = st.session_state.final_df
    meta = st.session_state.meta_data
    
    st.subheader(f"Partner: {meta['partner']} | Period: {meta['start']} to {meta['end']}")
    
    # 2. Display the table
    st.table(df)
    
    # 3. Print Engine
    if st.button("🖨️ Print to A4"):
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial; padding: 20px; }}
                    .report-table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
                    .report-table th, .report-table td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
                    h1 {{ text-align: center; }}
                </style>
            </head>
            <body>
                <h1>FIRSTCHOICE INFRA</h1>
                <p><i>Symbol Of Trust...</i></p>
                <hr>
                <h3>Executive Commission Statement</h3>
                <p><b>Partner:</b> {meta['partner']} &nbsp;&nbsp; <b>Period:</b> {meta['start']} to {meta['end']}</p>
                {df.to_html(classes='report-table', index=False)}
            </body>
        </html>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

