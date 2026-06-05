import streamlit as st
import database
import pandas as pd
import datetime
import base64
from PIL import Image
import io

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Site Visits Tracker")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

# Initialize site visits database array if it doesn't exist
if 'site_visits_log' not in db_data:
    db_data['site_visits_log'] = []

# ==========================================
# 🎨 CLEAN CSS THEME
# ==========================================
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
if '_app_settings' in db_data:
    bg_url = db_data['_app_settings'].get('bg_url', bg_url)

st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: rgba(255, 255, 255, 0.0) !important; backdrop-filter: none !important; -webkit-backdrop-filter: none !important; padding: 2rem !important; }}
.form-box {{ background-color: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.1); border-top: 5px solid #1e3a8a; }}
.history-box {{ background-color: #ffffff; padding: 20px; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.1); border-top: 5px solid #3b82f6; }}
h2, h3 {{ color: #1e3a8a !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white !important; font-weight: bold; border-radius: 8px; transition: all 0.3s; }}
.stButton>button:hover {{ transform: scale(1.02); }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; background-color: white; padding: 10px; border-radius: 10px;'>📍 Log, Monitor, and Track Client Site Visits</h2><br>", unsafe_allow_html=True)

# Fetch active projects
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]
if not project_names:
    project_names = ["No Projects Available"]

# ==========================================
# 📱 SPLIT LAYOUT: FORM (Left) & HISTORY (Right)
# ==========================================
col_form, col_history = st.columns([1, 1.2])

with col_form:
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown("### 📝 Add New Site Visit")
    
    with st.form("site_visit_form", clear_on_submit=True):
        c_name = st.text_input("👤 Client Full Name *")
        
        # 🔒 Executive will enter the full number here
        c_phone = st.text_input("📱 Client Mobile Number * (Hidden after save)")
        
        c1, c2 = st.columns(2)
        v_date = c1.date_input("📆 Date of Visit", datetime.date.today())
        v_proj = c2.selectbox("🏢 Project Visited", project_names)
        
        c3, c4 = st.columns(2)
        
        # Auto-fill Executive Name
        logged_in_name = st.session_state.get('current_user_name', '')
        if st.session_state.get('user_role', 'executive') == 'executive':
            exec_name = c3.text_input("👨‍💼 Assigned Executive Name *", value=logged_in_name, disabled=True)
        else:
            exec_name = c3.text_input("👨‍💼 Assigned Executive Name *", value=logged_in_name)
            
        interest = c4.selectbox("📊 Client Interest Level", ["High (Hot)", "Medium (Warm)", "Low (Cold)", "Not Interested"])
        
        remarks = st.text_area("📝 Executive Remarks / Feedback")
        
        st.markdown("📸 **Upload Site Visit Photo (Auto-Compress)**")
        uploaded_photo = st.file_uploader("Choose a photo (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
        
        submit_btn = st.form_submit_button("💾 Save Visit Record Permanently", use_container_width=True)
        
        if submit_btn:
            if not c_name.strip() or not c_phone.strip() or not exec_name.strip():
                st.error("🚨 Please fill Client Name, Mobile Number, and Executive Name!")
            else:
                photo_b64 = ""
                if uploaded_photo is not None:
                    try:
                        # 🚀 SMART COMPRESSION ENGINE
                        img = Image.open(uploaded_photo)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        img.thumbnail((800, 800))
                        
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", optimize=True, quality=60)
                        
                        photo_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    except Exception as e:
                        st.error(f"Error processing image: {e}")
                
                # Saving the REAL phone number in database
                visit_record = {
                    "visit_date": str(v_date),
                    "client_name": c_name.strip(),
                    "phone": c_phone.strip(), 
                    "project": v_proj,
                    "executive": exec_name.strip(),
                    "interest": interest,
                    "remarks": remarks.strip(),
                    "date_logged": str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                    "photo_data": photo_b64
                }
                
                db_data['site_visits_log'].append(visit_record)
                if database.save_db_data():
                    st.success("🎉 Site Visit Successfully Logged! Data is secured.")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_history:
    st.markdown('<div class="history-box">', unsafe_allow_html=True)
    st.markdown("### 📋 Recent Site Visits & Photos")
    
    visits = db_data.get('site_visits_log', [])
    
    if not visits:
        st.info("ℹ️ No site visits have been logged yet.")
    else:
        # 🔒 STRICT ADMIN LOCK FOR EXCEL DOWNLOAD (With Clean Format)
        if st.session_state.get('user_role', 'executive') == 'admin':
            df_export = pd.DataFrame(visits)
            
            # Cleaning up the photo_data column so Excel doesn't break
            if 'photo_data' in df_export.columns:
                df_export['photo_data'] = df_export['photo_data'].apply(lambda x: "Yes (View in System)" if x else "No Photo")
            
            # Renaming columns for a clean, professional Excel Sheet
            df_export = df_export.rename(columns={
                'visit_date': 'Visit Date',
                'client_name': 'Client Name',
                'phone': 'Contact Number',
                'project': 'Project Visited',
                'executive': 'Assigned Executive',
                'interest': 'Interest Level',
                'remarks': 'Feedback / Remarks',
                'photo_data': 'Photo Attached?',
                'date_logged': 'System Entry Time'
            })
            
            # Reordering columns so Contact Number and Name come first
            cols_order = ['Visit Date', 'Client Name', 'Contact Number', 'Project Visited', 'Assigned Executive', 'Interest Level', 'Feedback / Remarks', 'Photo Attached?', 'System Entry Time']
            existing_cols = [col for col in cols_order if col in df_export.columns]
            df_export = df_export[existing_cols]
                
            csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
            st.download_button("🖨️ Download Clean Excel Report (Admin Only)", data=csv_data, file_name=f"FC_Infra_Site_Visits_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
            st.write("---")
        
        # 🟢 DISPLAY HISTORY TO EVERYONE (With MASKED Phone Numbers)
        for i, v in enumerate(reversed(visits)):
            icon = "🔥" if "High" in v['interest'] else "⭐" if "Medium" in v['interest'] else "❄️"
            
            # 🛡️ PHONE NUMBER MASKING LOGIC FOR DISPLAY
            raw_phone = str(v.get('phone', ''))
            if len(raw_phone) >= 6:
                masked_phone = "******" + raw_phone[-4:] # Shows only last 4 digits (e.g. ******9876)
            else:
                masked_phone = "🔒 Hidden"

            with st.expander(f"{icon} {v['visit_date']} | {v['client_name']} ({v['project']})"):
                sc1, sc2 = st.columns([1.5, 1])
                
                with sc1:
                    # Showing Masked Phone Number on Screen
                    st.write(f"**📱 Mobile:** `{masked_phone}`")
                    st.write(f"**👨‍💼 Executive:** {v['executive']}")
                    st.write(f"**📊 Interest:** {v['interest']}")
                    st.write(f"**📝 Remarks:** {v['remarks']}")
                    st.caption(f"Logged on: {v.get('date_logged', 'N/A')}")
                
                with sc2:
                    if v.get('photo_data'):
                        try:
                            img_bytes = base64.b64decode(v['photo_data'])
                            st.image(img_bytes, caption="📸 Site Photo", use_column_width=True)
                        except:
                            st.error("Image broken")
                    else:
                        st.warning("🚫 No Photo Attached")
                        
    st.markdown('</div>', unsafe_allow_html=True)

