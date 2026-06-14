import streamlit as st
import database
import pandas as pd
import datetime

# Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# मल्टी-कलर स्टाइलिंग
st.markdown("""<style>
    .a4-page { background: white; padding: 40px; border: 3px solid #b8860b; color: black; max-width: 800px; margin: auto; }
    .header-sect { text-align: center; border-bottom: 3px double #1e3a8a; padding-bottom: 10px; margin-bottom: 20px; }
    .no-print { margin-top: 30px; }
    @media print { .no-print { display: none !important; } }
</style>""", unsafe_allow_html=True)

# सिलेक्शन इनपुट
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")

# जनरेट बटन
if st.button("🚀 Generate Multi-Color Statement"):
    # ... (कैलकुलेशन लॉजिक यहाँ वही रहेगा) ...
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# स्टेटमेंट रेंडरिंग
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-page'>", unsafe_allow_html=True)
    # हेडर
    st.markdown(f"""<div class='header-sect'>
        <h1 style='color:#b8860b; margin:0;'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("<h2>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    st.markdown(f"**Partner:** {meta['exec']} | **Period:** {meta['start']} to {meta['end']}", unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)
    
    # समरी
    cols = st.columns(4)
    cols[0].metric("Gross", f"₹{df['Gross'].sum():,.2f}")
    cols[1].metric("Discount", f"₹{df['Discount'].sum():,.2f}")
    cols[2].metric("TDS", f"₹{df['TDS (2%)'].sum():,.2f}")
    cols[3].metric("Net Pay", f"₹{df['Net In Hand'].sum():,.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

    # यहाँ लगानी है वो बटन वाली लाइन (HTML कोड)
    st.markdown(f"""
        <div style="display: flex; gap: 20px; justify-content: center;" class="no-print">
            <button onclick="window.print()" style="padding: 15px 30px; background: #1e3a8a; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                🖨️ Print / Save as PDF
            </button>
            
            <a href="https://wa.me/?text=FIRSTCHOICE INFRA - Commission Summary%0APartner: {meta['exec']}%0ANet Payout: ₹{df['Net In Hand'].sum():,.2f}" target="_blank">
                <button style="padding: 15px 30px; background: #25d366; color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer;">
                    💬 Send Summary to WhatsApp
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)

