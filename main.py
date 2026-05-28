import streamlit as st

# पेज का सेटअप
st.set_page_config(page_title="Firstchoice Infra")

# टाइटल और हेडर
st.title("🏢 Firstchoice Infra ERP System")
st.markdown("---")

st.subheader("सिस्टम डैशबोर्ड")
st.write("स्वागत है! कृपया नीचे दिए गए विकल्पों में से किसी एक को चुनें:")

# कॉलम बनाना (बटन के लिए)
col1, col2 = st.columns(2)

with col1:
    st.button("📊 डैशबोर्ड (जल्द आ रहा है)")

with col2:
    st.button("📝 नई बुकिंग (जल्द आ रहा है)")

st.markdown("---")
st.caption("Firstchoice Infra © 2026 - अधिकृत उपयोग के लिए")
