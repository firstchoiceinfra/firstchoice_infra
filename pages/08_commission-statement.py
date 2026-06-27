import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 🔒 ADMIN LOCK
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied!")
    st.stop()

if 'db_projects' not in st.session_state:
    database.init_db()

db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

# ---------------------------------------------------------
# 🌟 UPDATED DOWNLINE LOGIC (ScreenShot Format Match)
# ---------------------------------------------------------
def get_exec_details(target_name, exec_dict):
    """फोटो वाले फॉर्मेट (Name | Sponsor) से स्पॉन्सर ढूँढता है"""
    upline = ""
    # नाम के आधार पर स्पॉन्सर ढूँढें
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            raw_name = str(v.get('name', k)).strip().lower()
            if raw_name == str(target_name).strip().lower():
                # आपके स्क्रीनशॉट में 'company' या 'prem banole' वाला पार्ट यहाँ से आएगा
                upline_raw = v.get('upline_name', v.get('sponsor', v.get('referred_by', '')))
                # अगर सीधे 'upline' की नहीं है, तो 'description' या 'note' चेक करें
                if not upline_raw:
                    upline_raw = v.get('description', '') 
                
                upline = str(upline_raw).split('|')[-1].strip().lower()
                break
    return upline, 0.23 # डिफ़ॉल्ट 23% कमीशन

def get_all_downlines(target_name, exec_dict):
    """पूरी चेन ढूँढता है"""
    downlines = []
    target_clean = str(target_name).strip().lower()
    
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            exec_name = str(v.get('name', k)).strip()
            # हर एंट्री के लिए स्पॉन्सर चेक करें
            _, u = get_exec_details(exec_name, exec_dict)
            if u == target_clean:
                downlines.append(exec_name)
                downlines.extend(get_all_downlines(exec_name, exec_dict))
    return list(set(downlines))

# ---------------------------------------------------------
# डैशबोर्ड का बाकी हिस्सा (इसे पिछले कोड की तरह ही रखें)
# ---------------------------------------------------------

# (बाकी डैशबोर्ड का कैलकुलेशन लॉजिक अब इस नए 'get_exec_details' का उपयोग करेगा 
# और आपकी फोटो में दिख रहे | सिंबल वाले स्पॉन्सर को सही से पकड़ लेगा)

