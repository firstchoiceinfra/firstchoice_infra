import streamlit as st
import pandas as pd
import datetime
import database

# 1. डेटा लोड और इनिशियलाइज़ेशन
if 'db_projects' not in st.session_state:
    database.init_db()

db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

partner_list = []
if isinstance(executives, dict):
    partner_list = sorted([v.get('name', k) for k, v in executives.items() if isinstance(v, dict)])
else:
    partners = set()
    for proj in db_projects.values():
        if isinstance(proj, dict) and 'plots' in proj:
            for plot in (proj['plots'].values() if isinstance(proj['plots'], dict) else proj['plots']):
                if isinstance(plot, dict) and 'executive_name' in plot:
                    partners.add(plot['executive_name'])
    partner_list = sorted(list(partners))

# 2. पेज स्टेट मैनेजमेंट (Dashboard vs Report स्विच करने के लिए)
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# ==========================================
# 🌟 DASHBOARD PAGE (यहाँ आप सेलेक्ट करेंगे)
# ==========================================
if st.session_state.page == 'dashboard':
    st.title("📊 Executive Commission Dashboard")

    if not partner_list:
        st.warning("No partners found. Please check 'Partner Management'.")
    else:
        # पार्टनर ड्रॉपडाउन
        search_exec = st.selectbox("👤 Select Partner", options=partner_list)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # एक्टिव बटन्स (Self, Group, All)
        scope = st.radio("📑 Commission Scope", ["Self", "Group", "All"], horizontal=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # डेट सिलेक्शन
        col1, col2 = st.columns(2)
        start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
        end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

        st.markdown("<br>", unsafe_allow_html=True)

        # जनरेट बटन
        if st.button("🚀 Generate Systematic Statement", use_container_width=True):
            rows = []
            # डेटा कैलकुलेशन लूप
            for p_name, p_info in db_projects.items() if isinstance(db_projects, dict) else {}:
                if isinstance(p_info, dict) and p_name not in ['executives', '_app_settings']:
                    mauza = next((str(v) for k, v in p_info.items() if str(k).lower() == 'mauza'), "N/A")
                    plots = p_info.get('plots', {})
                    
                    plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
                    
                    for pid, info in plot_items:
                        if isinstance(info, dict) and info.get('executive_name') == search_exec:
                            amt = float(info.get('token_amount', 0))
                            # यहाँ आपका कमीशन लॉजिक है (Gross, TDS, In Hand)
                            rows.append({
                                "S.No.": len(rows)+1, 
                                "Mauza": mauza, 
                                "Project": p_name, 
                                "Plot": str(pid), 
                                "Customer": info.get('customer_name', 'N/A'),
                                "Received": amt, 
                                "Date": info.get('booking_date', 'N/A'),
                                "Gross": amt * 0.1, 
                                "Discount": amt * 0.02, 
                                "Net Comm": amt * 0.08, 
                                "TDS": amt * 0.002, 
                                "In Hand": amt * 0.078
                            })
            
            if rows:
                st.session_state.final_df = pd.DataFrame(rows)
                # मेटाडेटा सेव कर रहे हैं ताकि रिपोर्ट पेज पर दिखे
                st.session_state.meta_data = {
                    "partner": search_exec, 
                    "scope": scope, 
                    "start": start_d, 
                    "end": end_d
                }
                st.session_state.page = 'report' # पेज बदलें
                st.rerun()
            else:
                st.error("❌ इस पार्टनर, डेट और स्कोप के लिए कोई बुकिंग डेटा नहीं मिला!")

# ==========================================
# 📄 REPORT PAGE (यहाँ जनरेट होने के बाद टेबल दिखेगी)
# ==========================================
elif st.session_state.page == 'report':
    st.title("📄 Executive Commission Statement")
    
    # डैशबोर्ड पर वापस जाने का बटन
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if 'final_df' in st.session_state:
        meta = st.session_state.meta_data
        
        # पार्टनर और स्कोप की जानकारी दिखाएं
        st.info(f"**Partner:** {meta['partner']} | **Scope:** {meta['scope']} | **Period:** {meta['start']} to {meta['end']}")
        
        # टेबल रेंडर करें
        st.dataframe(st.session_state.final_df, use_container_width=True)
        
        # प्रिंट बटन (HTML फॉर्मेट)
        if st.button("🖨️ Print to A4"):
            html = f"""
            <div style="font-family: Arial; padding: 20px; border: 1px solid #000; width: 100%; margin: auto; position: relative;">
                <div style="position: absolute; top: 20px; right: 20px; font-weight: bold; font-size: 18px; color: #1e3a8a;">
                    FIRSTCHOICE INFRA
                </div>
                <center>
                    <h2 style="color: #1e3a8a; margin-bottom: 5px;">COMMISSION STATEMENT</h2>
                    <p style="margin-top: 0;"><i>Symbol Of Trust...</i></p>
                </center>
                <hr>
                <p><b>Partner Name:</b> {meta['partner']} <br>
                <b>Commission Scope:</b> {meta['scope']} <br>
                <b>Statement Period:</b> {meta['start']} to {meta['end']}</p>
                {st.session_state.final_df.to_html(classes='table', index=False, border=1)}
            </div>
            <script>window.print();</script>
            """
            st.components.v1.html(html, height=800)
    else:
        st.error("No data found!")
        st.session_state.page = 'dashboard'

