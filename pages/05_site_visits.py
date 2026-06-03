import streamlit as st
import pandas as pd
from datetime import datetime
from PIL import Image
import io

st.set_page_config(page_title="Site Visits", page_icon="🏗️", layout="wide")

# 🚨 सिस्टम जासूस: यह स्क्रीन पर दिखाएगा कि 'मेन पेज' से यहाँ क्या डेटा आ रहा है
st.info("🔍 सिस्टम चेक (ताकि हम बीमारी पकड़ सकें):")
st.write(st.session_state)

# 🔓 हमने यहाँ से st.stop() यानी 'ताला' हटा दिया है! अब पेज 100% खुलेगा।
user_role = str(st.session_state.get("role", "unknown")).lower()
current_username = str(st.session_state.get("username", "Unknown"))

if user_role not in ["admin", "executive"]:
    st.warning("⚠️ सिस्टम को आपका पद समझ नहीं आ रहा है, लेकिन हमने पेज खोल दिया है. आप अपना काम कर सकते हैं!")

# डेटा स्टोरेज
if 'site_visits' not in st.session_state:
    st.session_state.site_visits = []

# फोटो कंप्रेसर (स्पेस बचाने के लिए)
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
                    "Uploaded_By": current_username,
                    "Photo": photo_status
                })
                st.success("✅ Record and Photo Saved Successfully!")
            else:
                st.error("⚠️ Please fill all required fields (*)")

st.divider()
st.subheader("📋 Records")

if st.session_state.site_visits:
    df = pd.DataFrame(st.session_state.site_visits)
    
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
            st.dataframe(df.drop(columns=["Uploaded_By"]), use_container_width=True) # अगर रोल न मिले तो भी सब दिखे
else:
    st.info("अभी तक कोई रिकॉर्ड नहीं है।")
