import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re
from datetime import datetime

# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================
st.set_page_config(layout="wide", page_title="Commission Statement", initial_sidebar_state="collapsed")

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file: 
            return base64.b64encode(img_file.read()).decode()
    return ""

def safe_float(val):
    try: 
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else 0.0
    except: 
        return 0.0

def clean_txt(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

def parse_date(date_str):
    if not date_str or str(date_str).strip() in ['', 'NaT', 'nan', 'None']:
        return None
    try: 
        dt = pd.to_datetime(str(date_str), format='mixed', dayfirst=True, errors='coerce')
        if pd.isna(dt):
            return None
        return dt.date()
    except: 
        return None

# ==========================================
# 3. CSS & PRINT LAYOUT
# ==========================================
st.markdown("""<style>
    @media print {
        @page { margin: 10mm; size: A4 portrait; }
        [data-testid="stSidebar"], .stAppHeader, .no-print, div.stButton, div[data-testid="stSelectbox"] { display: none !important; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        body, .stApp { background: white !important; color: black !important; }
    }
    .filter-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
    .statement-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    .header-table { width: 100%; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }
    .header-table td { vertical-align: middle; }
    .company-name { font-size: 28px; font-weight: bold; color: #000; text-transform: uppercase; margin: 0; text-align: center; }
    .slogan { font-size: 14px; font-style: italic; margin: 5px 0; text-align: center; }
    .address { font-size: 12px; margin: 0; text-align: center; }
    .info-section { display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px; font-weight: bold; }
    
    .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 8px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
    .data-table td:nth-child(2), .data-table td:nth-child(3), .data-table td:nth-child(4) { text-align: left; }
    
    .data-table tbody tr:last-child td { 
        font-weight: 900 !important; 
        background-color: #e0e0e0 !important; 
        font-size: 14px; 
        border-top: 2px solid #000; 
        border-bottom: 2px solid #000; 
    }
</style>""", unsafe_allow_html=True)

# ==========================================
# 4. SYNC DATA FROM MASTER DATABASE
# ==========================================
db_projects = st.session_state.get('db_projects', {})

partner_db = {}
for key in ['executives', 'db_executives', 'partners', 'associates']:
    if key in st.session_state and isinstance(st.session_state[key], dict) and st.session_state[key]:
        partner_db = st.session_state[key]
        break

if not partner_db and isinstance(db_projects, dict):
    for k, v in db_projects.items():
        if str(k).strip().lower() in ['executives', 'executive', 'partners', 'associates']:
            if isinstance(v, dict): 
                partner_db = v; break

parents_tree = {}  
partner_rates = {}  
real_names = {}

# 🔥 DEEP SCANNER FOR PARTNER DATA (Fixes 0.00 Commission)
for key_id, info in partner_db.items():
    if isinstance(info, dict):
        exec_name, sponsor_name = key_id, ""
        pct_val = 0.0
        
        for k, v in info.items():
            kl = clean_txt(k)
            if kl in ['name', 'executivename', 'partnername', 'fullname', 'executive']: 
                exec_name = str(v)
            elif kl in ['sponsor', 'sponsorname', 'upline', 'sponsor_name']: 
                sponsor_name = str(v)
            # यहाँ सभी संभावित कमीशन नाम जोड़े गए हैं
            elif kl in ['percentage', 'commission', 'pct', 'percentageexec', 'percentage_exec', 'comm', 'rate', 'mycommission']: 
                pct_val = safe_float(v)
        
        c_exec = clean_txt(exec_name)
        if c_exec:
            partner_rates[c_exec] = pct_val
            real_names[c_exec] = exec_name
            if sponsor_name: parents_tree[c_exec] = clean_txt(sponsor_name)

def is_downline(boss, seller):
    curr = seller
    visited = set()
    while curr and curr in parents_tree:
        if curr in visited: break
        visited.add(curr)
        parent = parents_tree[curr]
        if parent == boss: return True
        curr = parent
    return False

def get_diff_rate(boss, seller, boss_pct):
    if not seller or boss == seller: return boss_pct
    curr = seller
    path = [curr]
    visited = set()
    while curr and curr in parents_tree:
        if curr in visited: break
        visited.add(curr)
        parent = parents_tree[curr]
        if parent == boss:
            immediate_junior = path[-1]
            return max(0.0, boss_pct - partner_rates.get(immediate_junior, 0.0))
        path.append(parent)
        curr = parent
    return max(0.0, boss_pct - partner_rates.get(seller, 0.0))

def resolve_clean_id(raw_name):
    c_raw = clean_txt(raw_name)
    if not c_raw: return ""
    if c_raw in partner_rates: return c_raw
    for c_id in partner_rates.keys():
        if c_raw in c_id or c_id in c_raw: return c_id
    return c_raw

# ==========================================
# 5. TOP UI: FILTERS & SELECTION
# ==========================================
st.markdown('<div class="no-print filter-box">', unsafe_allow_html=True)
st.subheader("📊 Executive Commission Generator")

exec_options = list(real_names.values())

if exec_options:
    search_exec = st.selectbox("👤 Select Executive", options=exec_options, index=0)
else:
    st.warning("⚠️ सिस्टम में कोई एग्जीक्यूटिव नहीं मिला।")
    search_exec = None

col1, col2, col3 = st.columns(3)
with col1:
    comm_type = st.radio("📑 Statement Type", ["Self", "Group", "All (Self + Group)"])
with col2:
    start_date = st.date_input("📅 Start Date", pd.to_datetime("today").replace(month=1, day=1))
with col3:
    end_date = st.date_input("📅 End Date", pd.to_datetime("today"))

btn_get_statement = st.button("🚀 Get Statement", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. PROCESS STATEMENT DATA
# ==========================================
if btn_get_statement and search_exec:
    rows = []
    count = 1
    target_clean = clean_txt(search_exec)
    boss_pct = partner_rates.get(target_clean, 0.0)
    
    # Mauja Fallback Mapping
    mauja_mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for proj_name, p_info in db_projects.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            b_rate = safe_float(p_info.get('base_rate', 650))
            
            # 🔥 FETCH MAUJA FROM INVENTORY
            mauja_name = ""
            for mk in ['mauja', 'Mauja', 'location', 'village']:
                if mk in p_info: mauja_name = str(p_info[mk])
            if not mauja_name:
                mauja_name = mauja_mapping.get(str(proj_name).lower().strip(), "N/A")
            
            plots_data = p_info['plots']
            if isinstance(plots_data, dict): plot_loop = plots_data.items()
            elif isinstance(plots_data, list): plot_loop = enumerate(plots_data)
            else: plot_loop = []
            
            for pid, info in plot_loop:
                if isinstance(info, dict):
                    e_name, cust_name = "", "N/A"
                    tok_amt, tok_date = 0.0, ""
                    c_rate, disc_sqft = b_rate, 0.0
                    
                    for k, v in info.items():
                        kl = clean_txt(k)
                        if kl in ['executivename', 'executive', 'partnername', 'agentname']: e_name = str(v)
                        elif kl in ['customername', 'customer', 'name']: cust_name = str(v)
                        elif kl in ['tokenamount', 'token', 'bookingamount']: tok_amt = safe_float(v)
                        elif kl in ['bookingdate', 'tokendate', 'date']: tok_date = str(v)
                        elif kl in ['companyrate', 'crate']: c_rate = safe_float(v)
                        elif kl in ['discount', 'disc']: disc_sqft = safe_float(v)
                    
                    seller_clean = resolve_clean_id(e_name)
                    is_self = (seller_clean == target_clean)
                    is_group = is_downline(target_clean, seller_clean) if not is_self else False
                                
                    is_valid = (comm_type == "Self" and is_self) or \
                               (comm_type == "Group" and is_group) or \
                               (comm_type == "All (Self + Group)" and (is_self or is_group))
                               
                    if is_valid:
                        payments = [{'amt': tok_amt, 'date': tok_date}]
                        
                        pp_data = info.get('partial_payments', info.get('partialpayments', []))
                        if isinstance(pp_data, dict): pp_data = list(pp_data.values())
                        if isinstance(pp_data, list):
                            for pmt in pp_data:
                                if isinstance(pmt, dict):
                                    p_amt = safe_float(pmt.get('amount', pmt.get('amt', 0)))
                                    p_date = str(pmt.get('date', pmt.get('payment_date', '')))
                                    payments.append({'amt': p_amt, 'date': p_date})
                        
                        if c_rate <= 0: c_rate = 650 
                        diff_pct = get_diff_rate(target_clean, seller_clean, boss_pct)
                        
                        for pmt in payments:
                            amt = safe_float(pmt['amt'])
                            pmt_date_parsed = parse_date(pmt['date'])
                            
                            date_in_range = True
                            if pmt_date_parsed:
                                if pmt_date_parsed < start_date or pmt_date_parsed > end_date:
                                    date_in_range = False
                            
                            if amt > 0 and date_in_range:
                                gross_comm = (amt * diff_pct) / 100
                                disc_amt = (amt / c_rate) * disc_sqft 
                                exact_comm = gross_comm - disc_amt
                                tds = exact_comm * 0.02
                                net_in_hand = exact_comm - tds
