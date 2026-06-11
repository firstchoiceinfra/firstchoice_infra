import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Firstchoice Infra - Payout")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रीमियम स्टाइलिंग
st.markdown("""<style>
    .premium-container { background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.1); border: 2px solid #b8860b; color: #333; }
    .comp-name { text-align: center; color: #b8860b; font-size: 45px; font-weight: 900; text-transform: uppercase; margin: 0; }
    .comp-slogan { text-align: center; color: #1e3a8a; font-size: 18px; font-style: italic; margin-bottom: 20px; }
    .title-heading { text-align: center; background: #1e3a8a; color: white; padding: 10px; border-radius: 5px; margin-top: 20px; }
    .info-bar { display: flex; justify-content: space-between; padding: 15px; background: #f1f5f9; border-radius: 10px; margin: 20px 0; font-weight: bold; }
</style>""", unsafe_allow_html=True)

search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🚀 Generate Elite Statement"):
    # (आपका कैलकुलेशन लॉजिक यहाँ सुरक्षित है...)
    # [कैलकुलेशन लॉजिक यहाँ वैसा ही रहेगा...]
    # मान लेते हैं कि 'df' और 'rows' तैयार हैं...
    
    if 'rows' in locals() and rows:
        st.session_state.df_statement = pd.DataFrame(rows)

if 'df_statement' in st.session_state and st.session_state.df_statement is not None:
    df = st.session_state.df_statement
    
    st.markdown("<div class='premium-container'>", unsafe_allow_html=True)
    # हेडर एरिया
    st.markdown("<h1 class='comp-name'>FIRSTCHOICE INFRA</h1>", unsafe_allow_html=True)
    st.markdown("<p class='comp-slogan'>Symbol Of Trust...</p>", unsafe_allow_html=True)
    st.markdown("<h2 class='title-heading'>Business Partner Commission Statement</h2>", unsafe_allow_html=True)
    
    # पार्टनर और डेट डिटेल्स
    st.markdown(f"""<div class='info-bar'>
        <span>Partner Name: {search_exec}</span>
        <span>Period: {start} to {end}</span>
    </div>""", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True)
    
    # टोटल सेक्शन
    st.markdown("### 📊 Financial Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gross Total", f"₹ {df['Gross'].sum():,.2f}")
    c2.metric("Discount Total", f"₹ {df['Discount'].sum():,.2f}")
    c3.metric("TDS Total", f"₹ {df['TDS (2%)'].sum():,.2f}")
    c4.metric("Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
    
    # प्रिंट और व्हाट्सएप (फिक्स्ड)
    st.markdown("<br><hr>", unsafe_allow_html=True)
    col_p, col_w = st.columns(2)
    
    # प्रिंट बटन - ब्राउज़र का प्रिंट डायलॉग खोलेगा
    col_p.markdown("""<button onclick="window.print()" style="width:100%; padding:15px; background:#1e3a8a; color:white; border-radius:10px; border:none; font-weight:bold;">🖨️ Print Statement</button>""", unsafe_allow_html=True)
    
    # व्हाट्सएप बटन - डायरेक्ट मैसेज
    wa_msg = f"Statement for {search_exec}: Gross ₹{df['Gross'].sum():,.2f}, Net Pay ₹{df['Net In Hand'].sum():,.2f}"
    wa_link = f"https://wa.me/?text={wa_msg.replace(' ', '%20')}"
    col_w.markdown(f'<a href="{wa_link}" target="_blank"><button style="width:100%; padding:15px; background:#25d366; color:white; border-radius:10px; border:none; font-weight:bold;">💬 Send to WhatsApp</button></a>', unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

