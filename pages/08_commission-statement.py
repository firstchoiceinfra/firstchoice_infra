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
    """अमाउंट में से कॉमा (,) और अक्षरों को हटाकर सुरक्षित रूप से नंबर में बदलता है"""
    try: 
        # "1,50,000" या "Rs. 1500" को 150000.0 में कन्वर्ट करेगा
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else 0.0
    except: 
        return 0.0

def clean_txt(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

def parse_date(date_str):
    try: return pd.to_datetime(date_str, format='mixed', dayfirst=True).date()
    except: return None

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
    .statement-container { background: white; color: black; max-width: 900px; margin: auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    .header-table { width: 100%; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }
    .header-table td { vertical-align: middle; }
    .company-name { font-size: 28px; font-weight: bold; color: #000; text-transform: uppercase; margin: 0; text-align: center; }
    .slogan { font-size: 14px; font-style: italic; margin: 5px 0; text-align: center; }
    .address { font-size: 12px; margin: 0; text-align: center; }
    .info-section { display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px; font-weight: bold; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 8px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
    .data-table td:nth-child(2), .data-table td:nth-child(3) { text-align: left; }
    .data-table tr.total-row td { font-weight: 900 !important; background-color: #e0e0e0 !important; font-size: 14px; border-top: 2px solid #000; border-bottom: 2px solid #000; }
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

for key_id, info in partner_db.items():
    if isinstance(info, dict):
        exec_name = info.get('name', info.get('executivename', info.get('partnername', key_id)))
        sponsor_name = info.get('sponsor', info.get('sponsorname', info.get('upline', '')))
        pct_val = safe_float(info.get('percentage', info.get('commission', info.get('pct', 0))))
        
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
    # ⚠️ यहाँ ध्यान दें: Start Date को डिफ़ॉल्ट रूप से इस साल का पहला दिन रखा गया है
    start_date = st.date_input("📅 Start Date", pd.to_datetime("today").replace(month=1, day=1))
with col3:
    end_date = st.date_input("📅 End Date", pd.to_datetime("today"))

btn_get_statement = st.button("🚀 Get Statement", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. PROCESS STATEMENT DATA (🔥 EXHAUSTIVE SCANNER)
# ==========================================
if btn_get_statement and search_exec:
    rows = []
    count = 1
    target_clean = clean_txt(search_exec)
    boss_pct = partner_rates.get(target_clean, 0.0)
    
    for proj_name, p_info in db_projects.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            b_rate = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            if isinstance(plots_data, dict): plot_loop = plots_data.items()
            elif isinstance(plots_data, list): plot_loop = enumerate(plots_data)
            else: plot_loop = []
            
            for pid, info in plot_loop:
                if isinstance(info, dict):
                    e_name, cust_name = "", "N/A"
                    tok_amt, tok_date = 0.0, ""
                    c_rate, disc_sqft = b_rate, 0.0
                    
                    # 🔎 100% Safe Dictionary Scanning (ब्रह्मास्त्र)
                    for k, v in info.items():
                        kl = clean_txt(k)
                        if kl in ['executivename', 'executive', 'partnername', 'agentname']: e_name = str(v)
                        elif kl in ['customername', 'customer']: cust_name = str(v)
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
                        # Add Token Payment
                        payments = [{'amt': tok_amt, 'date': tok_date}]
                        
                        # Add Partial Payments Safely
                        pp_data = info.get('partial_payments', info.get('partialpayments', []))
                        if isinstance(pp_data, dict): pp_data = list(pp_data.values())
                        if isinstance(pp_data, list):
                            for pmt in pp_data:
                                if isinstance(pmt, dict):
                                    # Handle different possible keys for amount/date inside partial payments
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
                                
                                rows.append({
                                    "S.No.": count,
                                    "Customer Name": cust_name.title(),
                                    "Plot No.": str(pid).upper(),
                                    "Received Amount": amt,
                                    "Received Date": pmt['date'],
                                    "Gross Commission": gross_comm,
                                    "Discount": disc_amt,
                                    "Exact Commission": exact_comm,
                                    "TDS (2%)": tds,
                                    "Net In Hand": net_in_hand
                                })
                                count += 1

    df = pd.DataFrame(rows)
    
    if not df.empty:
        totals = {
            "S.No.": "TOTAL", "Customer Name": "", "Plot No.": "", 
            "Received Amount": df['Received Amount'].sum(), "Received Date": "", 
            "Gross Commission": df['Gross Commission'].sum(), "Discount": df['Discount'].sum(), 
            "Exact Commission": df['Exact Commission'].sum(), "TDS (2%)": df['TDS (2%)'].sum(), 
            "Net In Hand": df['Net In Hand'].sum()
        }
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    else:
        st.warning(f"⚠️ {search_exec} के लिए कोई डेटा नहीं मिला। कृपया 'Start Date' को और पुराना (जैसे जनवरी 2025) करके देखें।")

    st.session_state.statement_data = df
    st.session_state.statement_meta = {"exec": search_exec, "start": start_date, "end": end_date}

# ==========================================
# 7. DISPLAY & PRINT STATEMENT
# ==========================================
if 'statement_data' in st.session_state and not st.session_state.statement_data.empty:
    df = st.session_state.statement_data
    meta = st.session_state.statement_meta
    
    logo_b64 = get_image_base64('logo.jpg')
    img_tag = f"<img src='data:image/jpeg;base64,{logo_b64}' width='120'/>" if logo_b64 else "<b>[LOGO]</b>"
    
    st.markdown(f"""
    <div class='statement-container'>
        <table class='header-table'>
            <tr>
                <td style='width: 20%; text-align: left;'>{img_tag}</td>
                <td style='width: 80%; text-align: center;'>
                    <p class='company-name'>FIRSTCHOICE INFRA</p>
                    <p class='slogan'>Symbol Of Trust...</p>
                    <p class='address'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
                </td>
            </tr>
        </table>
        
        <div class='info-section'>
            <div>Executive: <span style='color: #1e3a8a;'>{meta['exec']}</span></div>
            <div>Period: <span style='color: #1e3a8a;'>{meta['start'].strftime('%d %b %Y')} to {meta['end'].strftime('%d %b %Y')}</span></div>
        </div>
        
        {df.to_html(classes='data-table', index=False, float_format="%.2f").replace('<tr>', '<tr class="total-row">') if not df.empty else ""}
    </div>
    """, unsafe_allow_html=True)
    
    components.html("""
        <script>
            const tables = window.parent.document.querySelectorAll('.data-table');
            tables.forEach(table => {
                const rows = table.querySelectorAll('tr');
                if(rows.length > 1) {
                    rows.forEach(r => r.classList.remove('total-row'));
                    rows[rows.length - 1].classList.add('total-row');
                }
            });
        </script>
        
        <style>@media print { body { display: none !important; } }</style>
        <div style="text-align:center; margin-top:30px;" class="no-print">
            <button onclick="window.parent.print()" style="padding:12px 30px; background-color:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:16px; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">
                🖨️ Print Statement
            </button>
        </div>
    """, height=100)
