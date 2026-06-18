import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re
import datetime

# ==========================================
# 1. PAGE CONFIGURATION & SECURITY
# ==========================================
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
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
        @page {{ margin: 10mm; size: A4 portrait; }}
        [data-testid="stSidebar"], .stAppHeader, .no-print, div.stButton, div[data-testid="stSelectbox"], form {{ display: none !important; }}
        .block-container {{ background: white !important; padding: 0 !important; box-shadow: none !important; }}
        body, .stApp {{ background: white !important; color: black !important; }}
    }}
    .filter-box {{ background-color: #ffffff; padding: 20px; border-radius: 12px; border-left: 5px solid {p_color}; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 20px; }}
    .statement-container {{ background: white; color: black; max-width: 1000px; margin: auto; padding: 20px; border: 1px solid #eee; box-shadow: 0 0 15px rgba(0,0,0,0.1); }}
    .header-table {{ width: 100%; margin-bottom: 20px; border-bottom: 2px solid #000; padding-bottom: 10px; }}
    .header-table td {{ vertical-align: middle; }}
    .company-name {{ font-size: 28px; font-weight: bold; color: #000; text-transform: uppercase; margin: 0; text-align: center; }}
    .slogan {{ font-size: 14px; font-style: italic; margin: 5px 0; text-align: center; color: #333; }}
    .address {{ font-size: 12px; margin: 0; text-align: center; color: #333; }}
    .info-section {{ display: flex; justify-content: space-between; margin-bottom: 15px; font-size: 14px; font-weight: bold; color: #000; }}
    
    .data-table {{ width: 100%; border-collapse: collapse; font-size: 11px; color: #000; }}
    .data-table th, .data-table td {{ border: 1px solid #000; padding: 6px; text-align: right; }}
    .data-table th {{ background-color: #f0f0f0; text-align: center; font-weight: bold; }}
    .data-table td:nth-child(2), .data-table td:nth-child(3), .data-table td:nth-child(4) {{ text-align: left; }}
    .data-table tbody tr:last-child td {{ font-weight: 900 !important; background-color: #e0e0e0 !important; font-size: 13px; border-top: 2px solid #000; border-bottom: 2px solid #000; }}
</style>""", unsafe_allow_html=True)

# ==========================================
# 4. MASTER DATA EXTRACTION (From Partner Management)
# ==========================================
parents_tree = {}  
partner_rates = {}  
real_names = {}

# 100% Accurate fetching from 'executives' dict directly
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
            if clean_txt(senior): 
                parents_tree[c_name] = clean_txt(senior)

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

# ==========================================
# 5. UI: EXECUTIVE FILTER DESK
# ==========================================
st.markdown("<h1 style='text-align: center;'>📊 Master Commission Statement</h1>", unsafe_allow_html=True)
st.markdown('<div class="no-print filter-box">', unsafe_allow_html=True)

exec_options = sorted(list(real_names.values()))

if exec_options:
    search_exec = st.selectbox("👤 Select Business Partner / Executive", options=exec_options, index=0)
else:
    st.warning("⚠️ No executives found in Partner Management registry.")
    search_exec = None

col1, col2, col3 = st.columns(3)
with col1:
    comm_type = st.radio("📑 Statement Scope", ["Self", "Group", "All (Self + Group)"])
with col2:
    start_date = st.date_input("📅 Start Date", datetime.date(2020, 1, 1))
with col3:
    end_date = st.date_input("📅 End Date", datetime.date.today())

btn_get_statement = st.button("🚀 Generate Financial Statement", type="primary", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. COMMISSION CALCULATION ENGINE
# ==========================================
if btn_get_statement and search_exec:
    rows = []
    count = 1
    target_clean = clean_txt(search_exec)
    
    # ⚠️ लाइन 167 यहाँ पूरी तरह से सुरक्षित और सही है
    boss_pct = partner_rates.get(target_clean, 0.0)
    
    # Iterate through all projects in the Master Ledger
    project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]
    
    for p_name in project_names:
        p_info = db_data[p_name]
        p_plots = p_info.get('plots', {})
        b_rate = safe_float(p_info.get('base_rate', 650.0))
        
        # Smart Mauja Extraction
        mauja_name = str(p_info.get('mauja', p_info.get('location', 'N/A'))).strip()
        
        # Handle List vs Dict compatibility
        if isinstance(p_plots, list):
            p_plots = {str(idx): p for idx, p in enumerate(p_plots) if p is not None}
            
        for plot_id, info in p_plots.items():
            if isinstance(info, dict) and str(info.get('status', '')).lower() == 'booked':
                
                # Executive Identity
                seller_raw = str(info.get('executive_name', '')).strip()
                seller_clean = clean_txt(seller_raw)
                
                # Hierarchy Check
                is_self = (seller_clean == target_clean)
                is_group = is_downline(target_clean, seller_clean) if not is_self else False
                            
                is_valid = (comm_type == "Self" and is_self) or \
                           (comm_type == "Group" and is_group) or \
                           (comm_type == "All (Self + Group)" and (is_self or is_group))
                           
                if is_valid:
                    cust_name = str(info.get('customer_name', 'N/A')).title()
                    c_rate = safe_float(info.get('company_rate', b_rate))
                    if c_rate <= 0: c_rate = 650.0 
                    disc_sqft = safe_float(info.get('discount', 0.0))
                    
                    diff_pct = get_diff_rate(target_clean, seller_clean, boss_pct)
                    
                    # 1. Collect Token Payment
                    payments = []
                    tok_amt = safe_float(info.get('token_amount', info.get('received_amount', 0.0)))
                    tok_date = str(info.get('receipt_date', info.get('booking_date', '')))
                    if tok_amt > 0:
                        payments.append({'amt': tok_amt, 'date': tok_date})
                        
                    # 2. Collect EMI Payments (Partial Payments List)
                    partial_payments = info.get('partial_payments', [])
                    for pmt in partial_payments:
                        p_amt = safe_float(pmt.get('amount', 0.0))
                        p_date = str(pmt.get('date', ''))
                        if p_amt > 0:
                            payments.append({'amt': p_amt, 'date': p_date})
                    
                    # 3. Process Payments through Date Filter & Math
                    for pmt in payments:
                        amt = pmt['amt']
                        pmt_date_parsed = parse_date(pmt['date'])
                        
                        date_in_range = True
                        if pmt_date_parsed:
                            if pmt_date_parsed < start_date or pmt_date_parsed > end_date:
                                date_in_range = False
                        
                        if amt > 0 and date_in_range:
                            gross_comm = (amt * diff_pct) / 100
                            disc_amt = (amt / c_rate) * disc_sqft 
                            exact_comm = max(0.0, gross_comm - disc_amt)
                            tds = exact_comm * 0.02
                            net_in_hand = exact_comm - tds
                            
                            rows.append({
                                "S.No.": count,
                                "Customer Name": cust_name,
                                "Plot No.": str(plot_id).upper(),
                                "Mauja": mauja_name.title(),
                                "Received Amount": amt,
                                "Received Date": pmt_date_parsed.strftime('%d-%m-%Y') if pmt_date_parsed else 'N/A',
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
            "S.No.": "TOTAL", "Customer Name": "", "Plot No.": "", "Mauja": "",
            "Received Amount": df['Received Amount'].sum(), "Received Date": "", 
            "Gross Commission": df['Gross Commission'].sum(), "Discount": df['Discount'].sum(), 
            "Exact Commission": df['Exact Commission'].sum(), "TDS (2%)": df['TDS (2%)'].sum(), 
            "Net In Hand": df['Net In Hand'].sum()
        }
        df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    else:
        st.error(f"⚠️ No payment records found for {search_exec} within the selected date range.")

    st.session_state.statement_data = df
    st.session_state.statement_meta = {"exec": search_exec, "start": start_date, "end": end_date, "type": comm_type}

# ==========================================
# 7. PRINTABLE STATEMENT RENDERER
# ==========================================
if 'statement_data' in st.session_state and not st.session_state.statement_data.empty:
    df = st.session_state.statement_data
    meta = st.session_state.statement_meta
    
    logo_b64 = get_image_base64('logo.jpg')
    img_tag = f"<img src='data:image/jpeg;base64,{logo_b64}' width='120'/>" if logo_b64 else "<b>[LOGO]</b>"
    
    # Important: HTML string starts without indentation to prevent markdown code-block issues
    html_string = f"""<div class='statement-container'>
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
<div>Executive Partner: <span style='color: #1e3a8a;'>{meta['exec']}</span> ({meta['type']})</div>
<div>Statement Period: <span style='color: #1e3a8a;'>{meta['start'].strftime('%d %b %Y')} to {meta['end'].strftime('%d %b %Y')}</span></div>
</div>
{df.to_html(classes='data-table', index=False, float_format="%.2f")}
</div>"""

    st.markdown(html_string, unsafe_allow_html=True)
    
    components.html("""
        <style>@media print { body { display: none !important; } }</style>
        <div style="text-align:center; margin-top:30px;" class="no-print">
            <button onclick="window.parent.print()" style="padding:14px 35px; background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px; box-shadow: 0px 6px 15px rgba(59, 130, 246, 0.4);">
                🖨️ Print Final Statement
            </button>
        </div>
    """, height=100)
