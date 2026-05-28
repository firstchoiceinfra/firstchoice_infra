import streamlit as st

st.set_page_config(page_title="Firstchoice ERP", layout="wide")

st.title("🏢 Firstchoice Infra ERP System")
st.markdown("---")

st.subheader("सिस्टम डैशबोर्ड")
st.write("स्वागत है! कृपया नीचे दिए गए विकल्पों में से किसी एक को चुनें:")

col1, col2 = st.columns(2)

with col1:
    if st.button("📊 डैशबोर्ड देखें"):
        st.switch_page("pages/01_Dashboard.py")

with col2:
    if st.button("📝 नई बुकिंग करें"):
        st.switch_page("pages/02_Booking.py")

st.markdown("---")
st.caption("Firstchoice Infra © 2026 - अधिकृत उपयोग के लिए")