import streamlit as st
import database

# 1. डेटा को फोर्स लोड करें (अगर सेशन खाली है)
if 'db_projects' not in st.session_state:
    database.init_db()

# 2. डेटा एक्सेस करने का सबसे सुरक्षित तरीका
db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

# 3. पार्टनर नाम निकालने का लॉजिक
partner_list = []
if isinstance(executives, dict):
    # अगर पार्टनर मैनेजमेंट में डेटा है
    partner_list = sorted([v.get('name', k) for k, v in executives.items() if isinstance(v, dict)])
else:
    # अगर सीधे डिक्शनरी नहीं है तो इन्वेंटरी डैशबोर्ड से पार्टनर ढूंढें
    partners = set()
    for proj in db_projects.values():
        if isinstance(proj, dict) and 'plots' in proj:
            for plot in (proj['plots'].values() if isinstance(proj['plots'], dict) else proj['plots']):
                if isinstance(plot, dict) and 'executive_name' in plot:
                    partners.add(plot['executive_name'])
    partner_list = sorted(list(partners))

# --- UI ---
st.title("📊 Executive Commission Dashboard")

if not partner_list:
    st.warning("No partners found. Please check 'Partner Management'.")
else:
    search_exec = st.selectbox("👤 Select Partner", options=partner_list)
    # ... बाकी का कोड

