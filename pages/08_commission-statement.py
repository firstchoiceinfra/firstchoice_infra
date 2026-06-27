import streamlit as st

st.title("Test Page")
st.write("अगर यह पेज दिख रहा है, तो आपका कोडिंग एनवायरनमेंट सही है।")

# अब धीरे-धीरे हम डेटाबेस वाला हिस्सा जोड़ेंगे
if 'db_projects' in st.session_state:
    st.success("डेटाबेस लोड है!")
else:
    st.error("डेटाबेस लोड नहीं है।")

