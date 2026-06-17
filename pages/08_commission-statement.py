import streamlit as st
import streamlit.components.v1 as components
import database
import pandas as pd
import base64
import os

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# लोगो फंक्शन
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

LOGO_FILE = "logo.jpg" 
logo_base64 = get_image_base64(LOGO_FILE)
logo_html = f"<img src='data:image/jpeg;base64,{logo_base64}' style='position:absolute; top:0px; left:15px; width:130px; height:auto; mix-blend-mode: multiply;'/>" if logo_base64 else ""

# 2. CSS 
st.markdown("""<style>
    .block-container { padding-top: 0rem !important; margin-top: -60px !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    [data-testid="stHeader"] { display: none !important; height: 0 !important; }

    div[class^="viewerBadge"], div[class*="viewerBadge"], #viewerBadge_container__1QSob, a[href*="streamlit.io/cloud"], #Manage-app { 
        display: none !important; visibility: hidden !important; opacity: 0 !important; height: 0 !important; width: 0 !important;
    }

    @media print {
        @page { margin-top: 0mm !important; margin-bottom: 5mm !important; }
        [data-testid="stHeader"], [data-testid="stDecoration"], header, .stAppHeader, [data-testid="stSidebar"], [data-testid="stToolbar"] { display: none !important; }
        [data-testid="stSelectbox"], [data-testid="stHorizontalBlock"], div.stButton, div[role="radiogroup"], div.stInfo, .no-print { display: none !important; }
        body, html, .stApp, main { background: white !important; padding: 0 !important; margin: 0 !important; }
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
        .a4-container { display: block !important; width: 100% !important; position: absolute !important; top: 0 !important; left: 0 !important; margin: 0 !important; padding: 0 !important; border: none !important; }
    }
    
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 5px 20px; }
    .header { position: relative; text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 15px; }
    .title { font-size: 30px; font-weight: bold; margin: 0; color: #000; text-transform: uppercase; }
    
    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 6px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
    
    /* TOTAL वाली लाइन एकदम डार्क और हाईलाइटेड */
    .data-table tr:last-child td { 
        font-weight: 900 !important; 
        background-color: #ffeb3b !important; 
        color: #000 !important; 
        font-size: 15px !important; 
        padding: 12px 6px !important; 
        border-top: 3px solid #000 !important; 
        border-bottom: 3px solid #000 !important; 
    }
</style>""", unsafe_allow_html=True)

# डाउनलाइन निकालने का फंक्शन
def get_downline_team(target_user, exec_data):
    team = set()
    queue = [str(target_user).strip().lower()]
    while queue:
        curr = queue.pop(0)
        for k, v in exec_data.items():
            if isinstance(v, dict):
                sp = str(v.get('sponsor', v.get('sponsor_name', ''))).strip().lower()
                if sp == curr:
                    sub_exec = str(k).strip().lower()
                    if sub_exec not in team:
                        team.add(sub_exec)
                        queue.append(sub_exec)
    return team

# 3. SMART SECURITY LOGIC (अब एडमिन ब्लॉक नहीं होगा)
st.markdown('<div class="no-print">', unsafe_allow_html=True)

# सेशन स्टेट से डेटा लें
raw_role = st.session_state.get('role', '') 
raw_user = st.session_state.get('username', '')

user_role = str(raw_role).strip().lower()
logged_in_user = str(raw_user).strip()

# एडमिन पहचानने का स्मार्ट तरीका
is_admin = (user_role == 'admin' or logged_in_user.lower() == 'admin' or (not raw_role and not raw_user))

if is_admin:
    # अगर एडमिन है, तो पूरी कंपनी के लोग दिखेंगे
    st.info("👑 **Admin View:** Welcome Boss! Viewing all Partners.")
    all_execs = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
    search_exec = st.selectbox("🔎 Select Business Partner", all_execs)
else:
    # अगर कोई एग्जीक्यूटिव है, तो सिर्फ उसकी डाउनलाइन टीम दिखेगी
    st.info(f"🔒 **Secure View:** Logged in as **{logged_in_user}** (Showing your team only)")
    my_downline = get_downline_team(logged_in_user, exec_data_root)
    allowed_options = [k for k in exec_data_root.keys() if str(k).strip().lower() == logged_in_user.lower() or str(k).strip().lower() in my_downline]
    
    if allowed_options:
        search_exec = st.selectbox("🔎 Select Business Partner", allowed_options)
    else:
        st.warning(f"No business data found for '{logged_in_user}'.")
        search_exec = None

comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

# 4. Calculation Logic
if btn_generate and search_exec: 
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = safe_float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    selected_user_downline = get_downline_team(search_exec, exec_data_root)
    
    for project_name, p_info in

