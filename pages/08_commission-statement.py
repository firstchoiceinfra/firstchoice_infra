import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")

# (डेटाबेस इनिशियलाइज़ेशन)
try:
    import database
    database.init_db()
except:
    pass

db_data = st.session_state.get('db_projects', {})

# 🔎 डेटाबेस से Executives का मास्टर डेटा निकालना
exec_data_root = {}
for key in ['executives', 'db_executives', 'partners', 'associates']:
    if key in st.session_state and isinstance(st.session_state[key], dict) and st.session_state[key]:
        exec_data_root = st.session_state[key]
        break

if not exec_data_root and isinstance(db_data, dict):
    for k, v in db_data.items():
        if str(k).strip().lower() in ['executives', 'executive', 'partners', 'associates']:
            if isinstance(v, dict):
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
        font-weight: 900 !important; background-color: #ffeb3b !important; color: #000 !important; 
        font-size: 15px !important; padding: 12px 6px !important; border-top: 3px solid #000 !important; border-bottom: 3px solid #000 !important; 
    }
</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

def clean_str(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

def names_match(n1, n2):
    c1, c2 = clean_str(n1), clean_str(n2)
    if not c1 or not c2: return False
    return c1 == c2 or c1 in c2 or c2 in c1

# 🛠️ पार्ट 1: डेटाबेस पार्सिंग
parsed_execs = {}
for k, v in exec_data_root.items():
    if isinstance(v, dict):
        name, sp, pct = "", "", 0.0
        for key, val in v.items():
            kl = clean_str(key)
            if kl in ['name', 'executivename', 'partnername', 'fullname']: name = str(val).strip()
            elif kl in ['sponsor', 'sponsorname', 'upline']: sp = str(val).strip()
            elif kl in ['percentage', 'percentageexec', 'pct', 'commission', 'commissionpercentage']: pct = safe_float(val)
        if not name: name = str(k).strip()
        parsed_execs[clean_str(name)] = {'name': name, 'c_name': clean_str(name), 'sp': sp, 'c_sp': clean_str(sp), 'pct': pct}

# 🛠️ पार्ट 2: A -> B -> C पूरी चेन ढूँढने वाला सुपर-स्कैनर
def get_full_downline(target_c_name, parsed_data):
    team = set()
    queue = [target_c_name]
    while queue:
        curr = queue.pop(0)
        if not curr: continue
        for k, v in parsed_data.items():
            csp = v['c_sp']
            cnm = v['c_name']
            if csp and names_match(csp, curr):
                if cnm not in team and not names_match(cnm, target_c_name):
                    team.add(cnm)
                    queue.append(cnm) 
    return team

# 🛠️ पार्ट 3: कट-टू-कट डिफरेंस कमीशन कैलकुलेटर
def get_diff_commission(target_c, plot_c, parsed_data):
    t_pct = parsed_data.get(target_c, {}).get('pct', 0.0)
    if not plot_c or names_match(target_c, plot_c): return t_pct

    curr = plot_c
    visited = set()
    child_of_target = None

    while curr and curr not in visited:
        visited.add(curr)
        curr_sp = ""

