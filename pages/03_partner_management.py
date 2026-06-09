import streamlit as st
import database
import datetime

st.set_page_config(page_title="Partner Management", layout="wide")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

st.title("🏗️ Partner Management & Slab Registry")

# [यहाँ अपना पूरा Admin Only वाला कोड पेस्ट करें - पार्टनर जोड़ने और एडिट/डिलीट करने वाला]

# मास्टर स्लैब रजिस्ट्री ग्रिड
st.markdown("<br><hr><h4>📋 Master Slab Registry</h4>", unsafe_allow_html=True)
for ex_name, p_details in {k: v for k, v in exec_data_root.items() if isinstance(v, dict)}.items():
    st.markdown(f"**Name:** {ex_name} | **Senior:** {p_details.get('senior_name')} | **Slab:** {p_details.get('percentage_exec')}%")
    # यहाँ एडिट और डिलीट बटन रखें
