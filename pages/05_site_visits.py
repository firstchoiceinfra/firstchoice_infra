import streamlit as st
import database
import datetime
import pandas as pd
import base64
import io
from PIL import Image

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Site Visits")

# --- 2. Security Interceptor Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

# --- 3. Database Initialization ---
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
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; }}
.visit-card {{ background-color: #ffffff; border-left: 4px solid {p_color}; padding: 15px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); margin-bottom: 15px; }}
div[data-testid="stForm"] {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 25px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📸 Associate Site Visit Verification Desk</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 30px;'>Real-Time Compressed Logs, Selfie Verifications & 6-Month Data Retention Guard</p>", unsafe_allow_html=True)

# Initialize site visit storage list node if absent from global registry strings
if 'site_visits' not in st.session_state.db_projects:
    st.session_state.db_projects['site_visits'] = []

# ====================================================================
# 🛡️ SYSTEM AUTOMATION: 6-Month (180 Days) Auto-Cleanup Policy
# ====================================================================
logged_visits = st.session_state.db_projects.get('site_visits', [])
today_date = datetime.date.today()
retention_threshold = today_date - datetime.timedelta(days=180)
retention_triggered = False

for visit in logged_visits:
    if isinstance(visit, dict) and visit.get('photo_base64') != "":
        try:
            v_date = datetime.datetime.strptime(visit.get('visit_date'), "%Y-%m-%d").date()
            if v_date < retention_threshold:
                visit['photo_base64'] = "" # Permanently delete photo to free cloud storage
                visit['photo_status'] = "Purged automatically via 6-Month Cloud Retention Policy"
                retention_triggered = True
        except:
            pass

if retention_triggered:
    database.save_db_data()
# ====================================================================

# Fetching list of available layout projects
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

if not project_names:
    st.warning("⚠️ No active blueprints configured in cloud data registries. Please map layout profiles via Admin Desk first.")
    st.stop()

# Fetch active executive user directory
executives_root = db_data.get('executives', {})
active_exec_list = sorted([k for k, v in executives_root.items() if isinstance(v, dict)])

# --- Main Log Submission Form ---
st.markdown("### 🗺️ Record New Client Site Inspection Tour")
with st.form("site_visit_submission_form"):
    
    st.markdown("#### 📍 Layout Specification & Date Details")
    col_l1, col_l2 = st.columns(2)
    visit_project = col_l1.selectbox("🏢 Select Layout Target Project Blueprint", project_names)
    visit_date = col_l2.date_input("📅 Date of Site Tour Inspection", datetime.date.today())
    
    st.markdown("#### 👤 Team Attribution & Hierarchy Details")
    col_t1, col_t2 = st.columns(2)
    
    if st.session_state.get('user_role', 'executive') == 'executive':
        logged_exec_name = st.session_state.get('current_user_name', 'Direct')
        col_t2.text_input("Executive Account Holder Name", value=logged_exec_name, disabled=True)
        final_exec = logged_exec_name
        
        exec_profile = executives_root.get(logged_exec_name, {})
        senior_head_val = exec_profile.get('senior_name', 'Direct / Admin')
        senior_name = col_t1.text_input("Authorized Senior Chain Head", value=senior_head_val, disabled=True)
    else:
        final_exec = col_t2.selectbox("Select Reporting Executive Account", ["Admin / Direct"] + active_exec_list)
        senior_name = col_t1.text_input("Enter Senior Chain Head Name / Designation", placeholder="e.g., Senior Channel Lead")

    st.markdown("#### 👥 Client Records & Mandatory Media Attributions")
    col_c1, col_c2 = st.columns([1.1, 0.9])
    
    customer_name = col_c1.text_input("👤 Prospective Client / Lead Full Name *")
    uploaded_photo = col_c2.file_uploader("📷 Upload Site Visit Verification Selfie / Photo", type=["jpg", "jpeg", "png"])
    st.caption("ℹ️ *Selfie mandate checklist: Compressed natively to preserve cloud server database optimization thresholds.*")
    
    st.write("")
    submit_visit = st.form_submit_button("🔒 Secure and Log Attendance Record Entry", use_container_width=True)
    
    if submit_visit:
        if customer_name.strip() == "":
            st.error("🚨 Validation Failure: Please specify a valid Client / Lead Identity String to map entries!")
        elif uploaded_photo is None:
            st.error("🚨 Compliance Failure: Uploading a verification site selfie is mandatory to validate entries!")
        else:
            try:
                # 🌟 SYSTEM AUTOMATION: Live Smart Image Compressor Engine 🌟
                raw_image = Image.open(uploaded_photo)
                if raw_image.mode in ("RGBA", "P"):
                    raw_image = raw_image.convert("RGB")
                
                # Rescale image downscaling to optimal desktop/mobile standard dimensions
                raw_image.thumbnail((800, 800))
                
                # Write back into compressed stream buffer arrays
                compressed_buffer = io.BytesIO()
                raw_image.save(compressed_buffer, format="JPEG", quality=40) # Drastically scales down memory footprints
                compressed_bytes = compressed_buffer.getvalue()
                
                base64_encoded_img = base64.b64encode(compressed_bytes).decode("utf-8")
                image_data_url = f"data:image/jpeg;base64,{base64_encoded_img}"
                
                new_visit_node = {
                    "visit_id": f"VISIT-{int(datetime.datetime.now().timestamp())}",
                    "project_name": visit_project,
                    "visit_date": str(visit_date),
                    "executive_name": final_exec,
                    "senior_name": senior_name.strip() if hasattr(senior_name, 'strip') else senior_name,
                    "customer_name": customer_name.strip(),
                    "photo_base64": image_data_url,
                    "photo_status": "Active (Compressed)",
                    "timestamp": str(datetime.datetime.now())
                }
                
                st.session_state.db_projects['site_visits'].append(new_visit_node)
                
                with st.spinner("Compressing and uploading attendance structures..."):
                    if database.save_db_data():
                        st.success(f"🎉 Success! Compressed site visit safely secured under reference code {new_visit_node['visit_id']}!")
                        st.rerun()
            except Exception as err:
                st.error(f"🚨 Media Processing Failure: Structural extraction on file failed. Error details: {str(err)}")


# --- Live Site Visit Registry Logs Dashboard ---
st.markdown("<br><hr>", unsafe_allow_html=True)
st.markdown("### 📋 Historic Site Visit Registry & Selfie Gallery Tracking Dashboard")

if not logged_visits:
    st.info("ℹ️ No historical site inspection registries logged inside central storage nodes.")
else:
    if st.session_state.get('user_role', 'executive') == 'executive':
        logged_exec_name = st.session_state.get('current_user_name', 'Direct')
        filtered_visits = [v for v in logged_visits if isinstance(v, dict) and v.get('executive_name') == logged_exec_name]
    else:
        filtered_visits = [v for v in logged_visits if isinstance(v, dict)]
        
    if not filtered_visits:
        st.caption("No site visits registered under your executive profile parameters yet.")
    else:
        # Show latest entries first
        display_list = list(filtered_visits)
        display_list.reverse()
        
        for idx, visit in enumerate(display_list):
            with st.container():
                st.markdown(f"""
                <div class="visit-card">
                    <span style="font-size: 14px; font-weight: bold; color: {p_color};">🏢 Project: {visit.get('project_name')}</span>
                    <span style="float: right; font-size:12px; background-color:#e2e8f0; padding:2px 8px; border-radius:4px; font-weight:600; color:#334155;">📅 Tour Date: {visit.get('visit_date')}</span>
                    <br><span style="font-size: 12px; color:#475569; font-weight:500;">👤 <b>Prospective Client:</b> {visit.get('customer_name')}</span>
                    <br><span style="font-size: 11px; color:#64748b;">👨‍💼 Executive: {visit.get('executive_name')} | 👴 Reporting Senior Head: {visit.get('senior_name')}</span>
                </div>
                """, unsafe_allow_html=True)
                
                col_d1, col_d2 = st.columns([0.3, 0.7])
                
                with col_d1:
                    img_str = visit.get('photo_base64','')
                    if img_str:
                        st.image(img_str, caption="Verified Selfie Frame Map", use_container_width=True)
                    else:
                        # If image was deleted by the 6-month retention cleanup script
                        status_msg = visit.get('photo_status', "No verification photo attached.")
                        st.warning(f"⏳ {status_msg}")
                        
                with col_d2:
                    st.write("")
                    st.write("")
                    st.caption(f"**Ledger Transaction Sync Reference ID:** `{visit.get('visit_id')}`")
                    st.caption(f"**System Encoded Timestamp Registry ID:** {visit.get('timestamp')}")
                    
                st.markdown("<div style='margin-bottom: 20px; border-bottom: 1px dashed #cbd5e1;'></div>", unsafe_allow_html=True)
