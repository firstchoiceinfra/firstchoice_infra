import streamlit as st

# यह आपके सिस्टम का एक डेमो है कि कमीशन का गणित कैसे काम करेगा
st.subheader("💰 Executive Commission Tracker")

# 1. डेटा जो मास्टर लेजर/इन्वेंटरी से ऑटोमेटिक आएगा (आपकी वैल्यू के अनुसार)
plot_base_price = 191000.00 # प्लॉट की कुल कीमत
commission_rate = 20.0 # एग्जीक्यूटिव का फिक्स कमीशन (%)
discount_given = 14000.00 # एग्जीक्यूटिव द्वारा दिया गया डिस्काउंट

# 2. असली गणित (बिल्कुल पारदर्शी तरीके से)
# नियम: पहले प्लॉट की कीमत में से डिस्काउंट माइनस होगा, फिर बचे हुए अमाउंट (Net Value) पर 20% कमीशन निकलेगा।
# (या अगर आपके यहाँ नियम है कि डिस्काउंट सीधा एग्जीक्यूटिव के कमीशन से कटता है, तो आप मुझे बताइएगा, हम वो फॉर्मूला लगा देंगे)

net_plot_value = plot_base_price - discount_given
final_commission = (net_plot_value * commission_rate) / 100

# 3. एग्जीक्यूटिव को स्क्रीन पर एकदम साफ़-साफ़ हिसाब दिखाना (ताकि कोई कन्फ्यूजन न हो)
st.markdown("### 📊 Commission Breakdown (कमीशन का पूरा हिसाब)")

col1, col2, col3 = st.columns(3)
col1.metric("Total Plot Value (प्लॉट की कीमत)", f"₹ {plot_base_price:,.2f}")
col2.metric(f"Discount Given (छूट)", f"- ₹ {discount_given:,.2f}")
col3.metric("Net Plot Value (बचा हुआ अमाउंट)", f"₹ {net_plot_value:,.2f}")

st.divider()

col4, col5 = st.columns(2)
col4.info(f"**Commission Rate:** {commission_rate}%")
col5.success(f"💸 **Your Final Commission:** ₹ {final_commission:,.2f}")

# 4. सिस्टम को समझने के लिए बैकएंड लॉग
st.write("---")
with st.expander("🔍 Calculation Proof (सिस्टम ने कैसे गिना)"):
    st.code(f"""
    1. Base Price: {plot_base_price}
    2. Minus Discount: -{discount_given}
    3. Net Value = {net_plot_value}
    4. Commission = {net_plot_value} x {commission_rate}% = {final_commission}
    """, language="text")
