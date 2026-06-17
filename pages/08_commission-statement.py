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

# स्मार्ट तरीके से executives का डेटा ढूँढना
exec_data_root = {}
for k, v in db_data.items():
    if str(k).strip().lower() == 'executives':
        exec_data_root = v
        break

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
    .block-container { padding-top: 2rem !important; margin-top: 0px !important; padding-bottom: 1rem !important; max-width: 100% !important; }
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

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

# 🛠️ स्मार्ट ट्री बिल्डर (स्पेलिंग की गलतियों को इग्नोर करके चेन जोड़ेगा)
def build_exec_tree(exec_data):
    norm_data = {}
    for k, v in exec_data.items():
        if isinstance(v, dict):
            sp = ""
            pct = 0.0
            for key, val in v.items():
                k_low = str(key).strip().lower()
                # स्पॉन्सर का नाम किसी भी तरह लिखा हो, यह पकड़ लेगा
                if k_low in ['sponsor', 'sponsor_name', 'sponsor name']:
                    sp = str(val).strip().lower()
                # परसेंटेज किसी भी तरह लिखा हो, यह पकड़ लेगा
                elif k_low in ['percentage_exec', 'percentage', 'pct', 'commission']:
                    pct = safe_float(val)
            
            norm_data[str(k).strip().lower()] = {
                'name': str(k),
                'sponsor': sp,
                'pct': pct
            }
    return norm_data

# 🛠️ पूरी डाउनलाइन ढूँढने वाला स्कैनर (रमेश -> दिनेश -> अतुल)
def get_downline_set(target_norm, norm_data):
    team = set()
    queue = [target_norm]
    while queue:
        curr = queue.pop(0)
        for k, v in norm_data.items():
            if v['sponsor'] == curr and k not in team:
                team.add(k)
                queue.append(k)
    return team

# 🛠️ असली डिफरेंस कमीशन कैलकुलेटर
def get_diff_pct(target_norm, plot_exec_norm, norm_data):
    target_pct = norm_data.get(target_norm, {}).get('pct', 0.0)
    if target_norm == plot_exec_norm:
        return target_pct
    
    curr = plot_exec_norm
    child_of_target = None
    visited = set()
    
    # चेन में नीचे से ऊपर की तरफ जाना (अतुल -> दिनेश -> रमेश)
    while curr and curr in norm_data and curr != target_norm:
        visited.add(curr)
        sp = norm_data[curr]['sponsor']
        if sp == target_norm:
            child_of_target = curr
            break
        if sp in visited or not sp:
            break
        curr = sp
        
    if child_of_target:
        child_pct = norm_data.get(child_of_target, {}).get('pct', 0.0)
        return max(0.0, target_pct - child_pct)
    else:
        plot_exec_pct = norm_data.get(plot_exec_norm, {}).get('pct', 0.0)
        return max(0.0, target_pct - plot_exec_pct)

# 3. 100% BULLETPROOF AUTOMATIC SECURITY LOGIC
st.markdown('<div class="no-print">', unsafe_allow_html=True)

logged_in_user = ""
user_role = ""

for k, v in st.session_state.items():
    k_low = str(k).lower()
    if k_low in ['role', 'user_role', 'access', 'type'] and isinstance(v, str):
        user_role = v.strip().lower()
    if k_low in ['username', 'user', 'logged_in_user', 'name', 'current_user'] and isinstance(v, str):
        logged_in_user = v.strip()

norm_exec_data = build_exec_tree(exec_data_root)
all_exec_names = list(norm_exec_data.keys())

if not logged_in_user:
    for k, v in st.session_state.items():
        if isinstance(v, str):
            v_clean = v.strip().lower()
            if v_clean in all_exec_names:
                logged_in_user = v.strip()
            elif v_clean == 'admin':
                user_role = 'admin'
                logged_in_user = 'Admin'

is_admin = (user_role == 'admin' or logged_in_user.lower() == 'admin')

if not logged_in_user and not is_admin:
    st.error("🚫 **Access Denied (सुरक्षा लॉक):** कोई लॉगिन सेशन डेटा नहीं मिला। कृपया मुख्य लॉगिन पेज से आएं।")
    st.stop()

if is_admin:
    st.success("👑 **Admin Panel:** लॉग-इन: **Boss (Admin)** - सभी का एक्सेस चालू है।")
    all_execs = [v['name'] for v in norm_exec_data.values()]
    search_exec = st.selectbox("🔎 Select Business Partner", all_execs)
else:
    st.info(f"🔒 **Executive View:** लॉग-इन आईडी - **{logged_in_user}** (आपका और आपकी पूरी टीम का एक्सेस)")
    target_norm = logged_in_user.lower()
    my_downline = get_downline_set(target_norm, norm_exec_data)
    
    allowed_options = []
    for k, v in norm_exec_data.items():
        if k == target_norm or k in my_downline:
            allowed_options.append(v['name'])
            
    if allowed_options:
        search_exec = st.selectbox("🔎 Select Business Partner (Your Team Only)", allowed_options)
    else:
        st.error("डेटाबेस में आपके नाम का कोई रिकॉर्ड नहीं मिला।")
        search_exec = None

comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation Logic
if btn_generate and search_exec: 
    rows = []
    count = 1
    target_norm = str(search_exec).strip().lower()
    
    # सिलेक्ट किए गए पार्टनर की डाउनलाइन ढूँढना
    selected_user_downline = get_downline_set(target_norm, norm_exec_data)
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            base_rate_from_db = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                
                # प्लॉट डेटा से स्पॉन्सर और एग्जीक्यूटिव का नाम निकालना
                ex_name = ""
                sp_name = ""
                for key, val in info.items():
                    k_low = str(key).strip().lower()
                    if k_low in ['executive_name', 'executive', 'exec_name']:
                        ex_name = str(val).strip().lower()
                    elif k_low in ['sponsor_name', 'sponsor']:
                        sp_name = str(val).strip().lower()
                
                exec_in_db = ex_name
                sponsor_in_db = sp_name
                
                is_self = (exec_in_db == target_norm)
                # अगर प्लॉट बेचने वाला डाउनलाइन में है, या प्लॉट का डायरेक्ट स्पॉन्सर टारगेट यूजर है
                is_group = (exec_in_db in selected_user_downline) or (sponsor_in_db == target_norm)
                
                is_valid = False
                if comm_type == "Self": is_valid = is_self
                elif comm_type == "Group": is_valid = is_group
                else: is_valid = is_self or is_group
                
                if is_valid:
                    payments = [{'amt': safe_float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    pp_data = info.get('partial_payments', [])
                    if isinstance(pp_data, dict): pp_list = pp_data.values()
                    else: pp_list = pp_data
                    payments.extend([{'amt': safe_float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in pp_list if isinstance(pmt, dict)])
                    
                    comp_rate = safe_float(info.get('company_rate'))
                    if comp_rate <= 0: comp_rate = base_rate_from_db
                    if comp_rate <= 0: comp_rate = 650 
                    discount_sqft = safe_float(info.get('discount', 0))
                    
                    # 🎯 'डिफरेंस कमीशन' लागू
                    applicable_pct = get_diff_pct(target_norm, exec_in_db, norm_exec_data)
                    
                    # टेबल में बेचने वाले का नाम दिखाने का लेबल
                    if is_self:
                        entry_label = "Self"
                    else:
                        orig_seller_name = norm_exec_data.get(exec_in_db, {}).get('name', exec_in_db.title())
                        if not orig_seller_name:
                            orig_seller_name = "Team
