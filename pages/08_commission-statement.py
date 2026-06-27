import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# ==========================================import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

if 'db_projects' not in st.session_state:
    try:
        database.init_db()
    except Exception as e:
        st.error("डेटाबेस लोड करने में समस्या: " + str(e))

db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

partner_list = []
if isinstance(executives, dict) and executives:
    partner_list = sorted([v.get('name', k) for k, v in executives.items() if isinstance(v, dict)])
else:
    partners = set()
    for proj in db_projects.values():
        if isinstance(proj, dict) and 'plots' in proj:
            for plot in (proj['plots'].values() if isinstance(proj['plots'], dict) else proj['plots']):
                if isinstance(plot, dict) and 'executive_name' in plot:
                    partners.add(plot['executive_name'])
    partner_list = sorted(list(partners))

if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

if st.session_state.page == 'dashboard':
    st.title("📊 Executive Commission Dashboard")

    if not partner_list:
        st.warning("⚠️ No partners found. Please check 'Partner Management' or ensure bookings exist.")
    else:
        search_exec = st.selectbox("👤 Select Partner", options=partner_list)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        scope = st.radio("📑 Commission Scope", ["Self", "Group", "All"], horizontal=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
        end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Generate Systematic Statement", use_container_width=True):
            rows = []
            
            for p_name, p_info in db_projects.items() if isinstance(db_projects, dict) else {}:
                if isinstance(p_info, dict) and p_name not in ['executives', '_app_settings']:
                    mauja = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza' or str(k).lower() == 'mauja'), "N/A")
                    plots = p_info.get('plots', {})
                    
                    plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
                    
                    for pid, info in plot_items:
                        if isinstance(info, dict) and info.get('executive_name') == search_exec:
                            b_date_str = info.get('booking_date', '1900-01-01')
                            try:
                                b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                            except:
                                b_date = start_d 
                                
                            if start_d <= b_date <= end_d:
                                amt = float(info.get('token_amount', 0))
                                
                                gross = amt * 0.23        
                                discount = amt * 0.037    
                                net_comm = gross - discount
                                tds = net_comm * 0.02
                                in_hand = net_comm - tds
                                
                                rows.append({
                                    "S.No.": len(rows) + 1, 
                                    "Mauja": str(mauja).capitalize(), 
                                    "Project": str(p_name), 
                                    "Plot": str(pid), 
                                    "Customer": str(info.get('customer_name', 'N/A')).title(),
                                    "Received": amt, 
                                    "Date": b_date_str,
                                    "Gross": gross, 
                                    "Discount": discount, 
                                    "Net Comm": net_comm, 
                                    "TDS": tds, 
                                    "In Hand": in_hand
                                })
            
            if rows:
                df = pd.DataFrame(rows)
                
                total_row = {
                    "S.No.": "TOTAL", 
                    "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
                    "Received": df["Received"].sum(),
                    "Gross": df["Gross"].sum(),
                    "Discount": df["Discount"].sum(),
                    "Net Comm": df["Net Comm"].sum(),
                    "TDS": df["TDS"].sum(),
                    "In Hand": df["In Hand"].sum()
                }
                
                for col in ["Received", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]:
                    df[col] = df[col].apply(lambda x: f"{float(x):.2f}")
                    total_row[col] = f"{float(total_row[col]):.2f}"
                
                df.loc[len(df)] = total_row
                
                st.session_state.final_df = df
                st.session_state.meta_data = {
                    "partner": search_exec, 
                    "scope": scope, 
                    "start": start_d, 
                    "end": end_d
                }
                st.session_state.page = 'report' 
                st.rerun()
            else:
                st.error("❌ इस पार्टनर और चुनी गई तारीखों के बीच कोई बुकिंग डेटा नहीं मिला!")

elif st.session_state.page == 'report':
    
    st.title("📄 Executive Commission Statement")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if 'final_df' in st.session_state:
        meta = st.session_state.meta_data
        df = st.session_state.final_df
        
        st.dataframe(df, use_container_width=True)
        
        if st.button("🖨️ Print Statement (PDF Format)", type="primary"):
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #000; padding: 15px; font-size: 13px; }}
                    .header-section {{ text-align: center; margin-bottom: 25px; }}
                    .header-section h1 {{ margin: 0; font-size: 28px; font-weight: bold; letter-spacing: 1px; color: #000; }}
                    .header-section p {{ margin: 4px 0; font-size: 14px; }}
                    .tagline {{ font-style: italic; font-weight: bold; }}
                    .title-box {{ font-weight: bold; font-size: 18px; text-decoration: underline; text-align: center; margin: 20px 0; }}
                    .info-section {{ margin-bottom: 15px; font-size: 14px; line-height: 1.6; }}
                    .table-container {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
                    .table-container th, .table-container td {{ border: 1px solid #000; padding: 5px; text-align: center; }}
                    .table-container th {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header-section">
                    <h1>FIRSTCHOICE INFRA</h1>
                    <p class="tagline">Symbol Of Trust...</p>
                    <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                </div>
                
                <div class="title-box">Executive Commission Statement</div>
                
                <div class="info-section">
                    <b>Partner:</b> {meta['partner']} <br>
                    <b>Scope:</b> {meta['scope']} <br>
                    <b>Period:</b> {meta['start']} to {meta['end']}
                </div>
                
                {df.to_html(classes='table-container', index=False)}
                
            </body>
            </html>
            <script>window.print();</script>
            """
            st.components.v1.html(html, height=800)
    else:
        st.error("No data found!")
        st.session_state.page = 'dashboard'


# 1. डेटाबेस इनिशियलाइज़ेशन (डेटा हमेशा लोड होगा)
# ==========================================
if 'db_projects' not in st.session_state:
    try:
        database.init_db()
    except Exception as e:
        st.error("डेटाबेस लोड करने में समस्या: " + str(e))

db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

# पार्टनर की लिस्ट बनाना
partner_list = []
if isinstance(executives, dict) and executives:
    partner_list = sorted([v.get('name', k) for k, v in executives.items() if isinstance(v, dict)])
else:
    # अगर executives डिक्शनरी काम न करे, तो बुकिंग्स से नाम ढूँढें
    partners = set()
    for proj in db_projects.values():
        if isinstance(proj, dict) and 'plots' in proj:
            for plot in (proj['plots'].values() if isinstance(proj['plots'], dict) else proj['plots']):
                if isinstance(plot, dict) and 'executive_name' in plot:
                    partners.add(plot['executive_name'])
    partner_list = sorted(list(partners))

# ==========================================
# 2. पेज नेविगेशन स्टेट 
# ==========================================
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# ==========================================
# 🌟 DASHBOARD PAGE (इनपुट और सिलेक्शन)
# ==========================================
if st.session_state.page == 'dashboard':
    st.title("📊 Executive Commission Dashboard")

    if not partner_list:
        st.warning("⚠️ No partners found. Please check 'Partner Management' or ensure bookings exist.")
    else:
        # पार्टनर सिलेक्शन
        search_exec = st.selectbox("👤 Select Partner", options=partner_list)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # स्कोप सिलेक्शन
        scope = st.radio("📑 Commission Scope", ["Self", "Group", "All"], horizontal=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # डेट सिलेक्शन
        col1, col2 = st.columns(2)
        start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
        end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

        st.markdown("<br>", unsafe_allow_html=True)

        # जनरेट बटन और कैलकुलेशन
        if st.button("🚀 Generate Systematic Statement", use_container_width=True):
            rows = []
            
            for p_name, p_info in db_projects.items() if isinstance(db_projects, dict) else {}:
                if isinstance(p_info, dict) and p_name not in ['executives', '_app_settings']:
                    mauja = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza' or str(k).lower() == 'mauja'), "N/A")
                    plots = p_info.get('plots', {})
                    
                    plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
                    
                    for pid, info in plot_items:
                        if isinstance(info, dict) and info.get('executive_name') == search_exec:
                            # डेट फ़िल्टर (बुकिंग डेट चेक करें)
                            b_date_str = info.get('booking_date', '1900-01-01')
                            try:
                                b_date = datetime.datetime.strptime(b_date_str, "%Y-%m-%d").date()
                            except:
                                b_date = start_d # अगर डेट गलत है तो डिफ़ॉल्ट मान लें
                                
                            if start_d <= b_date <= end_d:
                                amt = float(info.get('token_amount', 0))
                                
                                # --- कमीशन लॉजिक (PDF के अनुसार डमी कैलकुलेशन) ---
                                gross = amt * 0.23        
                                discount = amt * 0.037    
                                net_comm = gross - discount
                                tds = net_comm * 0.02
                                in_hand = net_comm - tds
                                
                                rows.append({
                                    "S.No.": len(rows) + 1, 
                                    "Mauja": str(mauja).capitalize(), 
                                    "Project": str(p_name), 
                                    "Plot": str(pid), 
                                    "Customer": str(info.get('customer_name', 'N/A')).title(),
                                    "Received": amt, 
                                    "Date": b_date_str,
                                    "Gross": gross, 
                                    "Discount": discount, 
                                    "Net Comm": net_comm, 
                                    "TDS": tds, 
                                    "In Hand": in_hand
                                })
            
            if rows:
                df = pd.DataFrame(rows)
                
                # TOTAL कैलकुलेशन
                total_row = {
                    "S.No.": "TOTAL", 
                    "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
                    "Received": df["Received"].sum(),
                    "Gross": df["Gross"].sum(),
                    "Discount": df["Discount"].sum(),
                    "Net Comm": df["Net Comm"].sum(),
                    "TDS": df["TDS"].sum(),
                    "In Hand": df["In Hand"].sum()
                }
                
                # राउंड ऑफ और फॉर्मेटिंग (2 डेसिमल तक)
                for col in ["Received", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]:
                    df[col] = df[col].apply(lambda x: f"{float(x):.2f}")
                    total_row[col] = f"{float(total_row[col]):.2f}"
                
                # टोटल रो (Row) जोड़ना
                df.loc[len(df)] = total_row
                
                # सेशन स्टेट में डेटा सेव करना
                st.session_state.final_df = df
                st.session_state.meta_data = {
                    "partner": search_exec, 
                    "scope": scope, 
                    "start": start_d, 
                    "end": end_d
                }
                st.session_state.page = 'report' 
                st.rerun()
            else:
                st.error("❌ इस पार्टनर और चुनी गई तारीखों के बीच कोई बुकिंग डेटा नहीं मिला!")

# ==========================================
# 📄 REPORT PAGE (PDF Format Style)
# ==========================================
elif st.session_state.page == 'report':
    
    st.title("📄 Executive Commission Statement")
    
    # वापस जाने का बटन
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if 'final_df' in st.session_state:
        meta = st.session_state.meta_data
        df = st.session_state.final_df
        
        st.dataframe(df, use_container_width=True)
        
        # पीडीएफ जैसा प्रिंट बटन
        if st.button("🖨️ Print Statement (PDF Format)", type="primary"):
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #000; padding: 15px; font-size: 13px; }}
                    .header-section {{ text-align: center; margin-bottom: 25px; }}
                    .header-section h1 {{ margin
