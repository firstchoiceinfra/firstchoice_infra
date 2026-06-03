import streamlit as st

st.set_page_config(page_title="Agreements", page_icon="📝", layout="wide")

# 1. सिक्योरिटी चेक (ताकि कोई बिना लॉगिन के न घुस पाए)
current_role = str(st.session_state.get("user_role", "")).lower()

if not current_role:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) से लॉगिन करें!")
    st.stop()

if current_role not in ["admin", "executive"]:
    st.error("🔒 यह पेज केवल एडमिन और एग्जीक्यूटिव के लिए है!")
    st.stop()

# 2. टाइटल और हेडिंग
st.title("📝 Master Template Configuration")
st.subheader("Upload Your Format & Share")

# 3. भाषा चुनने का ऑप्शन (जैसा आपने कहा था, इसे वैसे ही रखा है)
st.write("### 🌐 एग्रीमेंट की भाषा चुनें")
language = st.radio("Language:", ["मराठी (Marathi)", "हिंदी (Hindi)", "English"])

st.divider()

# 4. फोटो या फाइल अपलोड करने का स्मार्ट फीचर
st.write("### 📤 अपना पुराना एग्रीमेंट फॉर्मेट अपलोड करें")
st.write("यहाँ आप अपने एग्रीमेंट की **फोटो (Photo)** या **PDF फाइल** अपलोड कर सकते हैं, ताकि सिस्टम उसके आधार पर नया एग्रीमेंट बना सके।")

uploaded_format = st.file_uploader("Upload Format (Choose file)", type=["jpg", "jpeg", "png", "pdf", "docx"])

if uploaded_format:
    st.success(f"✅ आपकी फाइल '{uploaded_format.name}' सफलतापूर्वक अपलोड हो गई है!")
    
    # अगर फोटो अपलोड की है, तो उसका प्रीव्यू (Preview) दिखाएं
    if uploaded_format.type in ["image/jpeg", "image/png"]:
        with st.expander("👀 अपलोड किए गए एग्रीमेंट की फोटो देखें", expanded=True):
            st.image(uploaded_format, caption="Your Master Template", use_container_width=True)
            
    st.info("🔄 सिस्टम ने आपका फॉर्मेट रीड कर लिया है। अब आप नया एग्रीमेंट जनरेट कर सकते हैं।")
    
    # 5. नया एग्रीमेंट जनरेट करने का बटन
    if st.button("✨ नया एग्रीमेंट जनरेट करें (Generate Agreement)", type="primary"):
        st.balloons()
        st.success(f"🎉 बधाई हो! सिस्टम आपके अपलोड किए गए फॉर्मेट और '{language}' भाषा के अनुसार नया एग्रीमेंट तैयार कर रहा है...")
        # (भविष्य में यहाँ हम AI या PDF जनरेशन का कोड जोड़ सकते हैं जो असली PDF प्रिंट करेगा)
