import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# ... (Security और Database वाला हिस्सा वही रखें जो मैंने पहले दिया था) ...

if st.button("🚀 Generate PDF-Format Statement"):
    # ... (डेटा प्रोसेसिंग वाला हिस्सा वही रखें) ...
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # 🖨️ यह वाला कोड ब्राउज़र की हर पाबंदी को तोड़ देगा
        st.markdown("""
        <script>
        function openPrintWindow() {
            var printWin = window.open('', '_blank', 'width=800,height=600');
            printWin.document.write('<html><head><title>Statement</title></head><body>');
            printWin.document.write('<h1>Commission Statement</h1>');
            printWin.document.write(document.querySelector('[data-testid="stDataFrame"]').outerHTML);
            printWin.document.write('</body></html>');
            printWin.document.close();
            printWin.focus();
            setTimeout(function(){ printWin.print(); }, 500);
        }
        </script>
        <button onclick="openPrintWindow()" style="padding:15px 30px; font-size:16px; background:#1e3a8a; color:white; border:none; border-radius:8px; cursor:pointer;">
            🖨️ Click to Print Statement
        </button>
        """, unsafe_allow_html=True)

