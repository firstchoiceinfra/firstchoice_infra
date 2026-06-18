import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re
import datetime

# ==========================================
# 1. PAGE CONFIGURATION & STRICT SECURITY
# ==========================================
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

# SECURITY LAYER: सिर्फ Admin को एक्सेस देने के लिए
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

# एडमिन रोल चेक (अगर एडमिन नहीं है तो एरर देकर रोक दो)
if st.session_state.get('user_role', 'executive').lower() != 'admin':
    st.error("🚨 ACCESS DENIED: This page is restricted to Administrative Personnel only.")
    st.stop()

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file: 
            return base64.b64encode(img_file.read()).decode()
    return ""

def safe_float(val, default=0.0):
    try: 
        if val is None or str(val).strip() == "": return float(default)
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else float(default)
    except: 
        return float(default)

def clean_txt(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

def parse_date(date_str):
    if not date_str or str(date_str).strip() in ['', 'NaT', 'nan', 'None']: return None
    try: 
        dt = pd.to_datetime(str(date_str), format='mixed', dayfirst=True, errors='coerce')
        return None if pd.isna(dt) else dt.date()
    except: return None

# ==========================================
# 3. GLOBAL THEME & PRINT CSS
# ==========================================
database_module_exists = True
try: import database; database.init_db()
except: database_module_exists = False

db_data = st.session_state.get('db_projects', {})
settings = db_data.get('_app_settings', {})
bg_url = settings.get('bg_url', "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop")
p_color = settings.get('primary_color', "#1e3a8a")
s_color = settings.get('secondary_color', "#3b82f6")
c_bg = settings.get('card_bg', "rgba(255, 255, 255, 0.92)")

st.markdown(f"""<style>
    .stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
    .block-container {{ background-color: {c_bg} !important; padding: 2rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 1.5rem; margin-bottom: 1.5rem; }}
    h1, h2, h3 {{ color: {p_color} !important; font-weight: 900; }}
    @media print {{
        @page {{ margin: 10mm; size: A4 landscape; }}
        [data-testid="stSidebar"], .stAppHeader, .no-print, div.stButton, div[data-testid="stSelectbox"], form {{ display: none !important; }}
        .block-container {{ background: white !important; padding: 0 !important; box-shadow: none !important; }}
        body, .stApp {{ background: white !important; color: black !important; }}
    }}
    .filter-box {{ background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid {p_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .statement-container {{ background: white; color: black; max-width: 100%; margin: auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
    .header-table {{ width: 100%; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
    .header-table td {{ vertical-align: middle; }}
    .company-name {{ font-size: 28px; font-weight: bold; color: #000; text-transform: uppercase; margin: 0; text-align: center; }}
    .slogan {{ font-size: 14px; font-style: italic; margin: 5px 0; text-align: center; color: #333; }}
    .address {{ font-size: 12px; margin: 0; text-align: center; color: #333; }}
    .info-section {{ display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #000; }}
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 11px; color: #000; }}
    .data-table th, .data-table td {{ border: 1px solid #000; padding: 6px; text-align: center; }}
    .data-table th {{ background-color: #f0f0f0; font-weight: bold; }}
    .data-table td:nth-child(2), .data-table td:nth-child(4), .data-table td:nth-child(5) {{ text-align: left; }}
    .data-table tbody tr:last-child td {{ font-weight: 900 !important; background-color: #e0e0e0 !important; font-size: 13px; border-top: 2px solid #000; border-bottom: 2px solid #000; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 4. MASTER DATA EXTRACTION
# ==========================================
parents_tree = {}  
partner_rates = {}  
real_names = {}

exec_data = db_data.get('executives', {})
for ex_name, details in exec_data.items():
    if isinstance(details, dict):
        name = details.get('name', ex_name).strip()
        senior = str(details.get('senior_name', '')).replace('Direct', '').strip()
        pct = safe_float(details.get('percentage_exec', 0.0))
        
        c_name = clean_txt(name)
        if c_name:
            partner_rates[c_name] = pct
            real_names[c_name] = name
            c_senior = clean_txt(senior)
            if c_senior and c_senior != c_name: 
                parents_tree[c_name] = c_senior

def get_all_downlines_recursive(boss_clean):
    downlines = []
    for child, parent in parents_tree.items():
        if parent == boss_clean:
            downlines.append(child)
            downlines.extend(get_all_downlines_recursive(child))
    return list(set(downlines))

def get_diff_rate(boss_clean, seller_clean, boss_pct):
    if not seller_clean or boss_clean == seller_clean: return boss_pct
    curr = seller_clean
    path = [curr]
    visited = set()
    while curr and curr in parents_tree:
        if curr in visited: break
        visited.add(curr)
        parent = parents_tree[curr]
        if parent == boss_clean:
            immediate_junior = path[-1]
            return max(0.0, boss_pct - partner_rates.get(immediate_junior, 0.0))
        path.append(parent)
        curr = parent
    return max(0.0, boss_pct - partner_rates.get(seller_clean, 0.0))

def resolve_clean_id(raw_name):
    c_raw = clean_txt(raw_name)
    if not c_raw: return ""
    if c_raw in partner_rates: return c_raw
    for c_id in partner_rates.keys():
        if c_raw in c_id or c_id in c_raw: return c_id
    return c_raw

# ==========================================
# 5. UI & CALCULATION ENGINE
# ==========================================
st.markdown("<h1 style='text-align: center;'>📊 Master Commission Statement (Admin Only)</h1>", unsafe_allow_html=True)
st.markdown('<div class="no-print filter-box">', unsafe_allow_html=True)

exec_options = sorted(list(real_names.values()))
search_exec = st.selectbox("👤 Select Business Partner / Executive", options=exec_options) if exec_options else None

col1, col2, col3 = st.columns(3)
with

