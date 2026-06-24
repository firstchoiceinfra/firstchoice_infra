import streamlit as st
import pandas as pd
import datetime

# --- 1. Master Sync: डेटाबेस को सीधे खींचने वाला सबसे पक्का फंक्शन ---
@st.cache_resource
def get_data_from_db():
    # यह फंक्शन सीधे डेटाबेस से डेटा उठाएगा
    db = st.session_state.get('db_projects', {})
    ex = st.session_state.get('executives', {})
    return db, ex

# --- 2. डेटा को लोड करें (यहीं से पार्टनर की लिस्ट बनेगी) ---
db_data, exec_data = get_data_from_db()

# अगर exec_data (Partner Management) खाली है, तो Inventory Dashboard से नाम निकालो
if not exec_data and db_data:
    partner_names = set()
    for p in db_data.values():
        if isinstance(p, dict) and 'plots' in p:
            for info in (p['plots'].values() if isinstance(p['plots'], dict) else p['plots']):
                if isinstance(info, dict) and 'executive_name' in info:
                    partner_names.add(info['executive_name'])
    partner_list = sorted(list(partner_names))
else:
    partner_list = sorted([v.get('name', k) for k, v in exec_data.items() if isinstance(v, dict)])

st.title("📊 Executive Commission Dashboard")

if not partner_list:
    st.error("❌ डेटा नहीं मिल रहा है।")
    st.info("प्रो टिप: 'Partner Management' पेज पर जाएं, एक पार्टनर का नाम एडिट करें और 'Save' बटन दबाएं। इससे डेटा रिफ्रेश होकर यहाँ दिखने लगेगा।")
else:
    # अब पार्टनर के नाम यहाँ पक्का दिखेंगे
    search_exec = st.selectbox("👤 Select Partner", options=partner_list)
    # ... (बाकी डैशबोर्ड का काम)

