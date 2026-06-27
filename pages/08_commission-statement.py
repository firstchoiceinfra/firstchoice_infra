import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# 1. डेटाबेस लोड करें
if 'db_projects' not in st.session_state:
    database.init_db()

db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

st.title("📊 Master Commission Statement")

# 2. पार्टनर सिलेक्शन
partner_names = sorted(list(set([str(v.get('name', k)).strip() for k, v in exec_data.items() if isinstance(v, dict)])))
search_exec = st.selectbox("👤 पार्टनर चुनें", partner_names)
scope = st.radio("📑 स्कोप", ["Self", "Group"], horizontal=True)

# 3. टीम ढूँढने का फंक्शन (पूरी चेन)
def get_all_team_members(target, exec_dict):
    team = [target.lower()]
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            # स्पॉन्सर ढूँढें
            sponsor = str(v.get('sponsor', v.get('upline', v.get('description', '')))).split('|')[-1].strip().lower()
            if sponsor == target.lower():
                name = str(v.get('name', k)).strip().lower()
                team.append(name)
                team.extend(get_all_team_members(name, exec_dict))
    return list(set(team))

if st.button("🚀 रिपोर्ट जनरेट करें"):
    valid_team = get_all_team_members(search_exec, exec_data) if scope == "Group" else [search_exec.lower()]
    rows = []

    # 4. डेटा छानना (Deep Scan)
    for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict):
                    # बुकिंग में पार्टनर का नाम ढूँढें (जो भी Key हो)
                    exec_in_booking = str(info.get('executive_name', info.get('partner', ''))).strip().lower()
                    
                    if exec_in_booking in valid_team:
                        amt = float(info.get('token_amount', 0))
                        rows.append({
                            "Member": exec_in_booking.upper(), 
                            "Customer": info.get('customer_name', 'N/A'),
                            "Amount": amt
                        })
    
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.error("❌ कोई डेटा नहीं मिला।")
        st.write("सर्च टीम:", valid_team)

