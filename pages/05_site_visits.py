import streamlit as st
import database
import datetime
import pandas as pd
from PIL import Image
import io
import base64

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Site Visits Tracker")

# --- 2. Security Check (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

# --- 3. Cloud Database Integration ---
database.init_db()
db_data = st.session_state.db_projects

# Global Theme Synchronization Logic
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255, 255, 255, 0.92)"

if '_app_settings' in db_data:
    global_settings = db_data['_app_settings']
    bg_url = global_settings.get('bg_url', bg_url)
    p_color = global_settings.get('primary_color', p_color)
    s_color = global_settings.get('secondary_color', s_color)
    c_bg = global_settings.get('card_bg', c_bg)

st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
div[data-testid="stForm"] {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🚗 Site Visits Tracker Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #475569;'>Log, Monitor, and Track Client Site Visits Permanently</p>", unsafe_allow_html=True)

# 🛠️ Database Setup for Site Visits
if 'site_visits' not in db_data:
    db_data['site_visits'] = []

# Fetch active projects and executives for dropdowns
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]
exec_data_root = db_data.get('executives', {})
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]

if not project_names:
    project_names = ["No Projects Available"]
if not exec_list:
    exec_list = ["Direct Sale"]

# --- Layout: Split into Form (Left) and Data Table (Right) ---
col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown("### 📝 Add New Site Visit")
    with st.form("site_visit_form"):
        c_name = st.text_input("👤 Client Full Name *")
        c_mobile = st.text_input("📱 Client Mobile Number *", max_chars=10)
        
        c_p1, c_p2 = st.columns(2)
        v_date = c_p1.date_input("📅 Date of Visit")
        v_project = c_p2.selectbox("🏢 Project Visited", project_names)
        
        c_e1, c_e2 = st.columns(2)
        v_exec = c_e1.selectbox("👨‍💼 Assigned Executive", exec_list)
        v_status = c_e2.selectbox("📊 Client Interest Level", ["High (Hot)", "Medium (Warm)", "Low (Cold)", "Not Interested", "Booked"])
        
        # 🚀 नया फोटो अपलोडर
        v_photo = st.file_uploader("📸 Upload Site Visit Photo (Auto-Compress)", type=["jpg", "jpeg", "png"])
        
        v_remarks = st.text_input("📝 Executive Remarks / Feedback")
        
        submit_visit = st.form_submit_button("💾 Save Visit Record Permanently", use_container_width=True)
        
        if submit_visit:
            if c_name.strip() == "" or c_mobile.strip() == "":
                st.error("🚨 Client Name and Mobile Number are mandatory fields!")
            else:
                photo_b64 = ""
                # 🚀 Auto-Compression Engine
                if v_photo is not None:
                    try:
                        img = Image.open(v_photo)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.thumbnail((800, 800)) # इमेज का साइज छोटा करना
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=50, optimize=True) # 50% क्वालिटी कंप्रेस करना
                        photo_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                    except Exception as e:
                        st.warning("⚠️ Photo upload failed, but saving the visit record.")

                new_visit = {
                    "Date": str(v_date.strftime("%d-%m-%Y")),
                    "Client Name": c_name.strip().title(),
                    "Mobile Number": c_mobile.strip(),
                    "Project": v_project,
                    "Executive": v_exec,
                    "Status": v_status,
                    "Photo": photo_b64, # कंप्रेस की हुई फोटो का कोड यहाँ सेव होगा
                    "Remarks": v_remarks.strip() if v_remarks.strip() else "N/A",
                    "Timestamp": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                }
                
                # Appending to Database
                db_data['site_visits'].insert(0, new_visit)
                
                with st.spinner("Compressing Photo & Locking data into cloud..."):
                    if database.save_db_data():
                        st.success(f"🎉 Success! Site visit for {c_name} has been permanently saved with compressed photo.")
                        st.rerun()

with col2:
    st.markdown("### 📋 Recent Site Visits History")
    
    visits_list = db_data.get('site_visits', [])
    
    if not visits_list:
        st.info("ℹ️ No site visits have been logged yet.")
    else:
        # टेबल को शानदार दिखाने के लिए डेटा सेट करना
        history_rows = []
        for v in visits_list:
            photo_status = "📸 Attached" if len(v.get('Photo', '')) > 50 else "❌ No"
            history_rows.append({
                "Date": v.get("Date", ""),
                "Client Name": v.get("Client Name", ""),
                "Mobile No.": v.get("Mobile Number", ""),
                "Project": v.get("Project", ""),
                "Exec.": v.get("Executive", ""),
                "Status": v.get("Status", ""),
                "Photo": photo_status,
                "Remarks": v.get("Remarks", "")
            })
            
        df_visits = pd.DataFrame(history_rows)
        
        # Display DataFrame
        st.dataframe(df_visits, use_container_width=True, hide_index=True)
        
        st.write("---")
        # Download Button
        csv_data = df_visits.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Export Site Visits Data (Excel/CSV)",
            data=csv_data,
            file_name=f"Site_Visits_Report_{datetime.date.today()}.csv",
            mime="text/csv",
            use_container_width=True
        )
