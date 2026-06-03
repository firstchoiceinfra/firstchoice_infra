import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# 1. सिक्योरिटी चेक (अब यह बिल्कुल सही 'user_role' पकड़ेगा)
current_role = str(st.session_state.get("user_role", "")).lower()

if not current_role:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) से लॉगिन करें!")
    st.stop()

if current_role not in ["admin", "executive"]:
    st.error("🔒 यह पेज केवल एडमिन और एग्जीक्यूटिव के लिए है!")
    st.stop()

# डेटा स्टोरेज
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

# 2. फोटो कंप्रेसर (ताकि सर्वर का स्पेस न भरे)
def compress_image(image_file):
    if image_file is None:
        return "No Photo ❌"
    try:
        img = Image.open(image_file)
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=50) 
        return "Photo Saved 📸"
    except Exception as e:
        return "Error ❌"

st.title("🏗️ Site Visits Dashboard")
st.write(f"👤 Logged in as: **{current_role.upper()}**")

with st.expander("➕ Add New Site Visit (यहाँ से डेटा डालें)", expanded=True):
    with st.form("visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name (ग्राहक का नाम) *")
            visit_date = st.date_input("Visit Date", datetime.today())
        with col2:
            executive_name = st.text_input("Executive Name (विजिट करवाने वाले का नाम) *")
            project_name = st.selectbox("Project Visited", ["First Choice City 2", "First Choice City 3", "Sai Samruddhi (Cement Road)", "Other"])
        
        st.markdown("---")
        st.write("**Customer Selfie / Photo 📷 (कस्टमर के साथ सेल्फी)**")
        selfie_photo = st.camera_input("Take a Live Selfie (कैमरे से लें)") 
        gallery_photo = st.file_uploader("या गैलरी से अपलोड करें", type=['jpg', 'jpeg', 'png'])
        
        submitted = st.form_submit_button("Save Record")
        
        if submitted:
            if customer_name and executive_name:
                photo_to_save = selfie_photo if selfie_photo else gallery_photo
                photo_status = compress_image(photo_to_save)
                
                st.session_state.site_visits.append({
                    "Date": visit_date.strftime("%d-%m-%Y"),
                    "Customer": customer_name,
                    "Project": project_name,
                    "Executive": executive_name,
                    "Uploaded_By_Role": current_role, # यह फ़िल्टर करने के काम आएगा
                    "Photo": photo_status
                })
                st.success("✅ Record and Photo Saved Successfully!")
            else:
                st.error("⚠️ Please fill all required fields (*)")

st.divider()
st.subheader("📋 Records")

# 3. स्मार्ट फ़िल्टर (एडमिन सब देखेगा, एग्जीक्यूटिव सिर्फ अपना)
if st.session_state.site_visits:
    df = pd.DataFrame(st.session_state.site_visits)
    
    if current_role == "admin":
        st.write("👀 **Admin View:** आप सभी एग्जीक्यूटिव की विजिट देख रहे हैं।")
        st.dataframe(df.drop(columns=["Uploaded_By_Role"]), use_container_width=True)
    else:
        st.write("👀 **Executive View:** आप सिर्फ एग्जीक्यूटिव टीम की विजिट देख रहे हैं।")
        filtered_df = df[df["Uploaded_By_Role"] == "executive"]
        
        if not filtered_df.empty:
            st.dataframe(filtered_df.drop(columns=["Uploaded_By_Role"]), use_container_width=True)
        else:
            st.info("आपकी अभी तक कोई साइट विजिट दर्ज नहीं है।")
else:
    st.info("अभी तक कोई रिकॉर्ड नहीं है।")
