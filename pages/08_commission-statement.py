import streamlit as st
import streamlit.components.v1 as components # <--- यह लाइन छूट गई थी, अब जोड़ दी गई है!
import pandas as pd
import base64
import os
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")

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

logo_base64 = get_image_base64("logo.jpg")
logo_html = f"<img src='data:image/jpeg;base64,{logo_base64}' style='position:absolute; top:0px; left:15px; width:130px; height:auto; mix-blend-mode: multiply;'/>" if logo_base64 else ""

# 2. CSS 
st.markdown("""<style>
    .block-container { padding-top: 2rem !important; margin-top: 0px !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    [data-testid="stHeader"], div[class^="viewerBadge"], #Manage-app { display: none !important; }
    @media print {
        @page { margin-top: 0mm !important; margin-bottom: 5mm !important; }
        [data-testid="stHeader"], [data-testid="stSidebar"], .stAppHeader { display: none !important; }
        [data-testid="stSelectbox"], [data-testid="stHorizontalBlock"], div.stButton, div[role="radiogroup"], .no-print { display: none !important; }
        body, html, .stApp, main { background: white !important; padding: 0 !important; margin: 0 !important; }
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 5px 20px; }
    .header { position: relative; text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 15px; }
    .title { font-size: 30px; font-weight: bold; margin: 0; color: #000; text-transform: uppercase; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 6px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
    .data-table tr:last-child td { font-weight: 900 !important; background-color: #ffeb3b !important; color: #000 !important; font-size: 15px !important; padding: 12px 6px !important; border-top: 3px solid #000 !important; border-bottom: 3px solid #000 !important; }
</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

# 🛠️ सबसे स्मार्ट और सुरक्षित नाम मैचिंग (Token Subset)
def is_same_person(n1, n2):
    s1 = re.sub(r'[^a-z0-9\s]', '', str(n1).lower()).strip()
    s2 = re.sub(r'[^a-z0-9\s]', '', str(n2).lower()).strip()
    if not s1 or not s2: return False
    if s1 == s2: return True
    w1 = set(s1.split())
    w2 = set(s2.split())
    if not w1 or not w2: return False
    if w1.issubset(w2) or w2.issubset(w1): return True
    return False

# 🛠️ पार्ट 1: पूरा मास्टर डेटा लोड करना
exec_list = []
for k, v in exec_data_root.items():
    if isinstance(v, dict):
        name = ""
        sp = ""
        pct = 0.0
        for key, val in v.items():
            kl = str(key).strip().lower()
            if kl in ['name', 'executivename', 'partnername', 'fullname']: name = str(val).strip()
            elif kl in ['sponsor', 'sponsorname', 'upline', 'sponsor_name']: sp = str(val).strip()
            elif kl in ['percentage', 'percentageexec', 'pct', 'commission', 'commissionpercentage']: pct = safe_float(val)
        if not name: name = str(k).strip()
        exec_list.append({'name': name, 'sp': sp, 'pct': pct})

def resolve_name(raw_name):
    if not raw_name: return ""
    raw_str = str(raw_name).strip()
    for ex in exec_list:
        if raw_str.lower() == ex['name'].lower(): return ex['name']
    for ex in exec_list:
        if is_same_person(raw_str, ex['name']): return ex['name']
    return raw_str

# 🛠️ पार्ट 2: असीमित गहराई (Infinite Depth) वाली मास्टर चेन बनाना
links = set()
# पार्टनर मैनेजमेंट से चेन जोड़ें
for ex in exec_list:
    if ex['name'] and ex['sp'] and not is_same_person(ex['name'], ex['sp']):
        links.add((resolve_name(ex['name']), resolve_name(ex['sp'])))

# प्लॉट बुकिंग से भी चेन जोड़ें (ताकि कोई जूनियर छूटे नहीं)
for p_info in db_data.values():
    if isinstance(p_info, dict) and 'plots' in p_info:
        plots = p_info['plots']
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        for pid, info in plot_items:
            if isinstance(info, dict):
                ex_n, sp_n = "", ""
                for key, val in info.items():
                    kl = str(key).strip().lower()
                    if kl in ['executivename', 'executive', 'execname', 'partnername']: ex_n = str(val).strip()
                    elif kl in ['sponsorname', 'sponsor', 'upline', 'sponsor_name

