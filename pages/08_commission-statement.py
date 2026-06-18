import streamlit as st
import pandas as pd
import re
import datetime
import base64
import os

# --- 1. Security & Helpers ---
if st.session_state.get('user_role', '').lower() != 'admin':
    st.error("🚨 Access Restricted: Admin Only.")
    st.stop()

def clean_txt(s): return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()
def safe_float(val):
    try: return float(re.sub(r'[^\d.]', '', str(val)))
    except: return 0.0

# --- 2. Calculation (वही जो सही काम कर रही है) ---
db_data = st.session_state.get('db_projects', {})
# ... (यहाँ आपका वही पुराना वाला कैलकुलेशन लॉजिक रहेगा जो सही चल रहा है) ...

# --- 3. PRINT ENGINE (Systematic Styling) ---
if 'final_df' in st.session_state:
    if st.button("🖨️ Print Systematic Statement"):
        logo = base64.b64encode(open('logo.jpg', 'rb').read()).decode() if os.path.exists('logo.jpg') else ""
        
        # यहाँ 'घुसड़-घुसड़' रोकने के लिए टेबल को प्रॉपर CSS दी है
        html_content = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    .header {{ display: flex; align-items: center; border-bottom: 2px solid #333; padding-bottom: 10px; }}
                    .logo {{ width: 80px; margin-right: 20px; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th {{ background-color: #f2f2f2; border: 1px solid #000; padding: 10px; text-align: left; }}
                    td {{ border: 1px solid #000; padding: 8px; text-align: right; }}
                    .total-row {{ font-weight: bold; background-color: #ddd; }}
                </style>
            </head>
            <body>
                <div class='header'>
                    <img src='data:image/jpeg;base64,{logo}' class='logo'>
                    <div>
                        <h1 style='margin:0;'>FIRSTCHOICE INFRA</h1>
                        <p style='margin:0;'>Symbol Of Trust | Nagpur</p>
                    </div>
                </div>
                <h3>Partner: {search_exec} | Statement Period: {start_d} to {end_d}</h3>
                {st.session_state.final_df.to_html(index=False, classes='table')}
                <script>
                    window.onload = function() {{ window.print(); }}
                </script>
            </body>
        </html>
        """
        st.components.v1.html(html_content, height=800)

