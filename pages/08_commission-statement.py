import streamlit as st
import pandas as pd
import database

st.set_page_config(layout="wide")

# डेटाबेस लोड
if 'db_projects' not in st.session_state:
    database.init_db()

db_data = st.session_state.get('db_projects', {})
exec_data = db_data.get('executives', {})

# नाम को साफ़ करने वाला फंक्शन (सबसे जरूरी)
def clean_name(name):
    return "".join(str(name).lower().split())

# टीम की पूरी चेन निकालने वाला फंक्शन
def get_team_chain(target_name, exec_dict):
    target_clean = clean_name(target_name)
    team = [target_clean]
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            # स्पॉन्सर का नाम ढूँढें और साफ़ करें
            s = str(v.get('sponsor', v.get('upline', ''))).split('|')[-1]
            if clean_name(s) == target_clean:
                team.append(clean_name(v.get('name', k)))
                team.extend(get_team_chain(v.get('name', k), exec_dict))
    return list(set(team))

st.title("📊 Master Commission Statement (Debug Mode)")
partner_names = sorted(list(set([str(v.get('name', k)).strip() for k, v in exec_data.items() if isinstance(v, dict)])))
search_exec = st.selectbox("👤 पार्टनर चुनें", partner_names)
scope = st.radio("📑 स्कोप", ["Self", "Group"], horizontal=True)

if st.button("🚀 रिपोर्ट जनरेट करें"):
    valid_team = get_team_chain(search_exec, exec_data) if scope == "Group" else [clean_name(search_exec)]
    st.write(f"🔍 सिस्टम इन नामों को ढूँढ रहा है: {valid_team}")
    
    rows = []
    for p_name, p_info in db_data.items() if isinstance(db_data, dict) else {}:
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                if isinstance(info, dict):
                    # बुकिंग वाले नाम को भी साफ़ करें
                    booked_by = clean_name(info.get('executive_name', info.get('partner', '')))
                    
                    if booked_by in valid_team:
                        amt = float(info.get('token_amount', 0))
                        rows.append({"Team Member": booked_by, "Project": p_name, "Amount": amt})
    
    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.error("❌ कोई डेटा नहीं मिला।")
        st.info("प्रो टिप: अगर '🔍 सिस्टम इन नामों को ढूँढ रहा है' में सही नाम है, लेकिन डेटा नहीं आ रहा, तो इसका मतलब है कि बुकिंग के अंदर 'executive_name' वाली Key ही खाली है।")

