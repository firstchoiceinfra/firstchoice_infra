import streamlit as st
import pandas as pd
import datetime

# ... (Security & Logic वही रखें जो काम कर रहा है) ...

# --- 4. Print Layout (Systematic A4 Fix) ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Statement"):
        # CSS को फिक्स किया ताकि टेबल कटे नहीं
        html = f"""
        <style>
            @media print {{
                body {{ width: 100%; }}
                .report-table {{ width: 100% !important; table-layout: fixed; font-size: 10px; }}
            }}
            .report-table {{ width: 100%; border-collapse: collapse; font-family: Arial; }}
            .report-table th, .report-table td {{ border: 1px solid #000; padding: 4px; text-align: center; word-wrap: break-word; }}
        </style>
        <div style="font-family: Arial; padding: 20px; border: 1px solid #000; max-width: 800px; margin: auto;">
            <center>
                <h1>FIRSTCHOICE INFRA</h1>
                <p><i>Symbol Of Trust...</i></p>
                <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                <hr>
                <h2>Executive Commission Statement</h2>
            </center>
            <p><b>Partner:</b> {search_exec} &nbsp;&nbsp;&nbsp; <b>Period:</b> {start_d} to {end_d}</p>
            
            <table class="report-table">
                <thead>
                    <tr>
                        <th>S.No.</th><th>Mauza</th><th>Project</th><th>Plot</th><th>Customer</th>
                        <th>Received</th><th>Date</th><th>Gross</th><th>Discount</th><th>Net</th><th>TDS</th><th>In Hand</th>
                    </tr>
                </thead>
                <tbody>
                    {"".join([f"<tr><td>{r['S.No.']}</td><td>{r['Mauza']}</td><td>{r['Project']}</td><td>{r['Plot']}</td><td>{r['Customer']}</td><td>{r['Received']}</td><td>{r['Date']}</td><td>{r['Gross']}</td><td>{r['Discount']}</td><td>{r['Net']}</td><td>{r['TDS']}</td><td>{r['In Hand']}</td></tr>" for r in st.session_state.final_df.to_dict('records')])}
                </tbody>
            </table>
        </div>
        <script>window.print();</script>
        """
        st.components.v1.html(html, height=800)

