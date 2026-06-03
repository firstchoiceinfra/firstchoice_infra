import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# 1. सिक्योरिटी और लॉगिन चेक
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 कृपया पहले मुख्य पेज (Main Page) से लॉगिन करें!")
    st.stop()

user_role = str(st.session_state.get("role", "")).lower()
current_username = str(st.session_state.get("username", "Unknown")) # बैकएंड में यूजर को पहचानने के लिए

if user_role not in ["admin", "executive"]:
    st.error("🔒 यह पेज केवल एडमिन और एग्जीक्यूटिव के लिए है!")
    st.stop()

# डेटा स्टोरेज
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

# 2. इमेज कंप्रेसर फंक्शन (ताकि स्पेस न भरे)
def compress_image(image_file):
    if image_file is None:
        return "No Photo ❌"
    try:
        img = Image.open(image_file)
        if img.mode in ("RGBA", "P"): 
            img = img.convert("RGB")
        # फोटो की साइज़ छोटी करना
        img.thumbnail((800, 800)) 
        buf = io.BytesIO()
        # क्वालिटी 50% तक कम करके सेव करना (KB में)
        img.save(buf, format="JPEG", quality=50) 
        return "Photo Saved 📸"
    except Exception as e:
        return "Error ❌"

st.title("🏗️ Site Visits Dashboard")

with st.expander("➕ Add New Site Visit (यहाँ से डेटा डालें)", expanded=True):
    with st.form("visit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Customer Name (ग्राहक का नाम) *")
            visit_date = st.date_input("Visit Date", datetime.today())
        with col2:
            executive_name = st.text_input("Executive Name (विजिट करवाने वाले का नाम) *")
            project_name = st.selectbox("Project Visited", ["First Choice City 2", "First Choice City 3", "Sai Samruddhi", "Other"])
        
        st.markdown("---")
        st.write("**Customer Selfie / Photo 📷 (कस्टमर के साथ सेल्फी)**")
        # एग्जीक्यूटिव डायरेक्ट मोबाइल से सेल्फी ले सकते हैं
        selfie_photo = st.camera_input("Take a Live Selfie") 
        gallery_photo = st.file_uploader("या गैलरी से अपलोड करें", type=['jpg', 'jpeg', 'png'])
        
        submitted = st.form_submit_button("Save Record")
        
        if submitted:
            if customer_name and executive_name:
                # फोटो कंप्रेस करें
                photo_to_save = selfie_photo if selfie_photo else gallery_photo
                photo_status = compress_image(photo_to_save)
                
                st.session_state.site_visits.append({
                    "Date": visit_date.strftime("%d-%m-%Y"),
                    "Customer": customer_name,
                    "Project": project_name,
                    "Executive": executive_name,
                    "Uploaded_By": current_username, # यह सिस्टम को बताएगा कि किसने अपलोड किया
                    "Photo": photo_status
                })
                st.success("✅ Record and Photo Saved Successfully!")
            else:
                st.error("⚠️ Please fill all required fields (*)")

st.divider()
st.subheader("📋 Records")

if st.session_state.site_visits:
    df = pd.DataFrame(st.session_state.site_visits)
    
    # 3. स्मार्ट फ़िल्टर (एडमिन सब देखेगा, एग्जीक्यूटिव सिर्फ अपना)
    if user_role == "admin":
        st.write("👀 **Admin View:** आप सभी एग्जीक्यूटिव की विजिट देख रहे हैं।")
        st.dataframe(df.drop(columns=["Uploaded_By"]), use_container_width=True)
    else:
        st.write(f"👀 **Executive View:** आप सिर्फ अपनी टीम की विजिट देख रहे हैं।")
        filtered_df = df[df["Uploaded_By"] == current_username]
        
        if not filtered_df.empty:
            st.dataframe(filtered_df.drop(columns=["Uploaded_By"]), use_container_width=True)
        else:
            st.info("आपकी अभी तक कोई साइट विजिट दर्ज नहीं है।")
else:
    st.info("अभी तक कोई रिकॉर्ड नहीं है।")
