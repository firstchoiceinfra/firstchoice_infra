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
.history-box {{ background-color: #ffffff; padding: 25px; border-radius: 15px; box-shadow: 0px 10px 25px rgba(0,0,0,0.1); border-top: 5px solid #3b82f6; }}
h2, h3 {{ color: #1e3a8a !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white !important; font-weight: bold; border-radius: 8px; transition: all 0.3s; border: none; }}
.stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); }}
div[data-testid="stDataFrame"] {{ border: 1px solid #e2e8f0; border-radius: 10px; overflow: hidden; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h2 style='text-align: center; background-color: white; padding: 15px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);'>📍 Log & Monitor Client Site Visits</h2><br>", unsafe_allow_html=True)

# Fetch active projects
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]
if not project_names:
    project_names = ["No Projects Available"]

# ==========================================
# 📱 SPLIT LAYOUT: FORM (Left) & HISTORY TABLE (Right)
# ==========================================
col_form, col_history = st.columns([1, 1.8])

with col_form:
    st.markdown('<div class="form-box">', unsafe_allow_html=True)
    st.markdown("### 📝 Add New Site Visit")
    
    with st.form("site_visit_form", clear_on_submit=True):
        c_name = st.text_input("👤 Client Full Name *")
        c_phone = st.text_input("📱 Client Mobile Number * (Hidden after save)")
        
        c1, c2 = st.columns(2)
        v_date = c1.date_input("📆 Date of Visit", datetime.date.today())
        v_proj = c2.selectbox("🏢 Project Visited", project_names)
        
        logged_in_name = st.session_state.get('current_user_name', '')
        is_admin = st.session_state.get('user_role', 'executive') == 'admin'
        
        if is_admin:
            exec_name = st.text_input("👨‍💼 Assigned Executive", value=logged_in_name)
        else:
            exec_name = st.text_input("👨‍💼 Assigned Executive", value=logged_in_name, disabled=True)
            
        interest = st.selectbox("📊 Client Interest Level", ["High (Hot)", "Medium (Warm)", "Low (Cold)", "Not Interested"])
        remarks = st.text_area("📝 Executive Remarks / Feedback")
        
        st.markdown("📸 **Upload Site Visit Photo**")
        uploaded_photo = st.file_uploader("Choose a photo (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
        
        submit_btn = st.form_submit_button("💾 Save Visit Record", use_container_width=True)
        
        if submit_btn:
            if not c_name.strip() or not c_phone.strip() or not exec_name.strip():
                st.error("🚨 Please fill Client Name, Mobile Number, and Executive Name!")
            else:
                photo_b64 = ""
                if uploaded_photo is not None:
                    try:
                        img = Image.open(uploaded_photo)
                        if img.mode != 'RGB': img = img.convert('RGB')
                        img.thumbnail((800, 800))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", optimize=True, quality=60)
                        photo_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    except Exception as e:
                        st.error(f"Error processing image: {e}")
                
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
                    st.success("🎉 Site Visit Successfully Logged!")
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_history:
    st.markdown('<div class="history-box">', unsafe_allow_html=True)
    st.markdown("### 📋 Site Visits Statement & Ledger")
    
    visits = db_data.get('site_visits_log', [])
    
    if not visits:
        st.info("ℹ️ No site visits have been logged yet.")
    else:
        # 🚀 AUTO-DATA NORMALIZER
        normalized_visits = []
        for v in reversed(visits):
            nv = {}
            nv['Date'] = v.get('visit_date', v.get('Date', ''))
            nv['Client Name'] = v.get('client_name', v.get('Client Name', ''))
            nv['Contact Number'] = str(v.get('phone', v.get('Contact Number', '')))
            nv['Project'] = v.get('project', v.get('Project', ''))
            nv['Executive'] = v.get('executive', v.get('Executive', ''))
            nv['Interest'] = v.get('interest', v.get('Interest', ''))
            nv['Remarks'] = v.get('remarks', v.get('Remarks', ''))
            nv['System_Entry'] = v.get('date_logged', v.get('System_Entry', ''))
            nv['photo_data'] = v.get('photo_data', '')
            normalized_visits.append(nv)
            
        df_visits = pd.DataFrame(normalized_visits)
        is_admin = st.session_state.get('user_role', 'executive') == 'admin'
        
        df_display = df_visits.copy()
        
        # 🛡️ PHONE MASKING LOGIC FOR SCREEN DISPLAY
        if not is_admin:
            df_display['Contact Number'] = df_display['Contact Number'].apply(
                lambda x: "******" + str(x)[-4:] if len(str(x)) >= 6 else "🔒 Hidden"
            )
            
        display_cols = ['Date', 'Client Name', 'Contact Number', 'Project', 'Executive', 'Interest', 'Remarks']
        df_display = df_display[[c for c in display_cols if c in df_display.columns]]
        
        # 📊 RENDER TABLE
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # 🖨️ ADMIN ONLY EXCEL DOWNLOAD
        if is_admin:
            st.write("---")
            df_export = df_visits.copy()
            
            df_export['Contact Number'] = df_export['Contact Number'].apply(lambda x: f" {x}")
            
            if 'photo_data' in df_export.columns:
                df_export['Photo Status'] = df_export['photo_data'].apply(lambda x: "Attached in System" if x else "No Photo")
                df_export = df_export.drop(columns=['photo_data'])
            
            export_cols = ['Date', 'Client Name', 'Contact Number', 'Project', 'Executive', 'Interest', 'Remarks', 'Photo Status', 'System_Entry']
            df_export = df_export[[c for c in export_cols if c in df_export.columns]]
            
            csv_data = df_export.to_csv(index=False).encode('utf-8-sig')
            
            c_btn1, c_btn2 = st.columns([1, 2])
            with c_btn1:
                st.download_button("🖨️ Download Clean Excel Sheet", data=csv_data, file_name=f"Site_Visits_{datetime.date.today()}.csv", mime="text/csv", use_container_width=True)
                st.caption("*(Only Admin can see this button and real numbers)*")

        # 📸 PHOTO GALLERY
        st.write("")
        with st.expander("📸 View Attached Site Photos"):
            photos_found = False
            p_cols = st.columns(3)
            p_idx = 0
            for nv in normalized_visits:
                if nv.get('photo_data'):
                    photos_found = True
                    with p_cols[p_idx % 3]:
                        try:
                            img_bytes = base64.b64decode(nv['photo_data'])
                            st.image(img_bytes, caption=f"{nv['Client Name']} ({nv['Date']})", use_column_width=True)
                        except: pass
                    p_idx += 1
            if not photos_found:
                st.info("No photos have been attached to any visits yet.")
                
    st.markdown('</div>', unsafe_allow_html=True)
