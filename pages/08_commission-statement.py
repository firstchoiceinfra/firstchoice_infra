import streamlit as st

st.title("🔍 Data Debugger")

# यह कोड आपको बताएगा कि आपकी session_state में क्या-क्या है
st.write("### Current Session State Keys:")
st.write(list(st.session_state.keys()))

if 'executives' in st.session_state:
    st.success("✅ 'executives' key found!")
    st.write(st.session_state['executives'])
else:
    st.error("❌ 'executives' key is MISSING!")

if 'db_projects' in st.session_state:
    st.success("✅ 'db_projects' key found!")
else:
    st.error("❌ 'db_projects' key is MISSING!")

