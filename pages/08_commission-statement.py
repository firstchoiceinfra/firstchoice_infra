import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re

# ==========================================
# 1. PAGE SETUP & MASTER DATABASE CONNECT
# ==========================================
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")

try:
    import database
    database.init_db()
except:
    pass

db_data = st.session_state.get('db_projects', {})

# 🔎 पार्टनर मैनेजमेंट (Partner Management) के ओरिजिनल डेटाबेस को खोजना
partner_db = {}
for key in ['executives', 'db_executives', 'partners', 'associates']:
    if key in st.session_state and isinstance(st.session_state[key], dict) and st.session_state[key]:
        partner_db = st.session_state[key]
        break

if not partner_db and isinstance(db_data, dict):
    for k, v in db_data.items():
        if str(k).strip().lower() in ['executives', 'executive', 'partners', 'associates']:
            if isinstance(v, dict): 
                partner_db = v
                break

# लोगो फंक्शन
def get_image_base64(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    return ""
logo_html = f"<img src='data:image/jpeg;base64,{get_image_base64('logo.jpg')}' style='position:absolute; top:0px; left:15px; width:130px; mix-blend-mode: multiply;'/>"

# ==========================================
# 2. CSS & PRINT FORMATTING
# ==========================================
st.markdown("""<style>
    .block-container { padding-top: 2rem !important; padding-bottom: 1rem !important; max-width: 100% !important; }
    [data-testid="stHeader"], #Manage-app { display: none !important; }
    @media print {
        @page { margin-top: 0mm !important; margin-bottom: 5mm !important; }
        [data-testid="stSidebar"], .stAppHeader, div.stButton, div[data-testid="stSelectbox"], div[role="radiogroup"], .no-print, details { display: none !important; }
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

def clean_txt(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower()).strip()

# स्मार्ट नाम मैचिंग सेंसर (टोकन और स्पेस की गलतियां सुधारेगा)
def is_same_name(n1, n2):
    s1, s2 = clean_txt(n1), clean_txt(n2)
    if not s1 or not s2: return False
    if s1 == s2 or s1 in s2 or s2 in s1: return True
    w1, w2 = set(str(n1).lower().split()), set(str(n2).lower().split())
    if w1 and w2 and (w1.issubset(w2) or w2.issubset(w1)): return True
    return False

# ==========================================
# 3. PARTNER MANAGEMENT DATA EXTRACTION
# ==========================================
p_management_tree = {} # सीनियर-जूनियर मैपिंग
p_percentages = {} # किसका कितना % है

for key_id, info_dict in partner_db.items():
    if isinstance(info_dict, dict):
        exec_name = str(key_id).strip()
        sponsor_name = ""
        pct_val = 0.0
        
        for k, v in info_dict.items():
            kl = clean_txt(k)
            if kl in ['name', 'executivename', 'partnername', 'fullname']: 
                exec_name = str(v).strip()
            elif kl in ['sponsor', 'sponsorname', 'upline', 'sponsor_name']: 
                sponsor_name = str(v).strip()
            elif kl in ['percentage', 'percentageexec', 'percentage_exec', 'pct', 'commission']: 
                pct_val = safe_float(v)
                
        c_exec = clean_txt(exec_name)
        if c_exec:
            p_percentages[c_exec] = pct_val
            if sponsor_name:
                p_management_tree[c_exec] = clean_txt(sponsor_name)

def get_canonical_id(raw_name):
    c_raw = clean_txt(raw_name)
    for c_id in p_percentages.keys():
        if c_raw == c_id or c_raw in c_id or c_id in c_raw:
            return c_id
    return c_raw

# 🛠️ असीमित गहराई (Infinite Downline) खोजने वाला लूप स्कैनर
def build_infinite_downline(target_id):
    downline = set()
    queue = [target_id]
    while queue:
        curr = queue.pop(0)
        for child, parent in p_management_tree.items():
            if parent == curr or is_same_name(parent, curr):
                if child not in downline and child != target_id:
                    downline.add(child)
                    queue.append(child)
    return downline

# 🛠️ सटीक ट्री-बेस्ड डिफरेंस कमीशन कैलकुलेटर
def calculate_differential_pct(target_id, seller_id):
    target_pct = p_percentages.get(target_id, 0.0)
    if target_id == seller_id or not seller_id:
        return target_pct
        
    curr = seller_id
    path = []
    visited = set()
    
    # नीचे से ऊपर सीनियर की तरफ ट्रैक करना
    while curr and curr not in visited and curr != target_id:
        visited.add(curr)
        path.append(curr)
        curr = p_management_tree.get(curr, "")
        
    if curr == target_id and path:
        immediate_junior = path[-1] # टारगेट का ठीक नीचे वाला लिंक पार्टनर
        junior_pct = p_percentages.get(immediate_junior, 0.0)
        return max(0.0, target_pct - junior_pct)
    else:
        seller_pct = p_percentages.get(seller_id, 0.0)
        return max(0.0, target_pct - seller_pct)

# ==========================================
# 4. TOTAL ADMIN SECURITY LOCK
# ==========================================
st.markdown('<div class="no-print">', unsafe_allow_html=True)
is_admin_logged = False

for val in st.session_state.values():
    if isinstance(val, str) and any(x in str(val).lower() for x in ['admin', 'boss', 'owner', 'firstchoice']):
        is_admin_logged = True
        break
if 'force_unlock' in st.session_state and st.session_state.force_unlock:
    is_admin_logged = True

if not is_admin_logged:
    st.error("🚫 Access Denied! यह पेज सुरक्षित है और सिर्फ एडमिन के लिए उपलब्ध है।")
    pwd = st.text_input("Admin PIN (Emergency Unlock)", type="password")
    if st.button("🔓 Unlock Page"):
        if pwd == "1234" or pwd == "admin123":
            st.session_state.force_unlock = True
            st.rerun()
        else: st.error("❌ गलत पिन!")
    st.stop()

st.success("👑 **Admin Panel Active** (पार्टनर मैनेजमेंट से सफलतापूर्वक कनेक्टेड)")
if st.button("🔒 Lock Page"):
    st.session_state.force_unlock = False
    st.rerun()

# ड्रॉपडाउन में दिखाने के लिए ओरिजिनल नाम निकालना
display_names_map = {}
for k, v in partner_db.items():
    if isinstance(v, dict):
        nm = str(k).strip()
        for sub_k, sub_v in v.items():
            if clean_txt(sub_k) in ['name', 'executivename']: nm = str(sub_v).strip()
        display_names_map[clean_txt(nm)] = nm

all_options = list(display_names_map.values())
search_exec = st.selectbox("🔎 Select Business Partner", all_options) if all_options else None
comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start_date, end_date = col1.date_input("Start Date"), col2.date_input("End Date")
btn_gen = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 5. STATEMENT CALCULATION LOGIC
# ==========================================
if btn_gen and search_exec:
    rows = []
    count = 1
    target_id = clean_txt(search_exec)
    
    # लाइव चेन ढूंढना पार्टनर मैनेजमेंट के डेटा से
    full_downline_set = build_infinite_downline(target_id)
    
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for proj_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(proj_name.lower(), "Nagpur"))
            b_rate = safe_float(p_info.get('base_rate', 650))
            
            plots_dict = p_info['plots']
            plot_loop = plots_dict.items() if isinstance(plots_dict, dict) else enumerate(plots_dict)
            
            for pid, info in plot_loop:
                if isinstance(info, dict):
                    e_name, s_name = "", ""
                    for k, v in info.items():
                        kl = clean_txt(k)
                        if kl in ['executivename', 'executive', 'executive_name', 'partnername']: e_name = str(v).strip()
                        elif kl in ['sponsorname', 'sponsor_name', 'sponsor', 'upline']: s_name = str(v).strip()
                    
                    seller_id = clean_txt(e_name)
                    sponsor_id = clean_txt(s_name)
                    
                    is_self = (seller_id == target_id or is_same_name(seller_id, target_id))
                    
                    is_group = False
                    if not is_self:
                        # अगर बेचने वाला या उसका स्पॉन्सर हमारी लाइव पार्टनर ट्री डाउनलाइन में मैच हो जाए
                        if seller_id in full_downline_set or sponsor_id == target_id or sponsor_id in full_downline_set:
                            is_group = True
                        else:
                            for dl_member in full_downline_set:
                                if is_same_name(seller_id, dl_member) or is_same_name(sponsor_id, dl_member):
                                    is_group = True; break
                                    
                    is_valid = (comm_type == "Self" and is_self) or \
                               (comm_type == "Group" and is_group) or \
                               (comm_type == "All (Self + Group)" and (is_self or is_group))
                               
                    if is_valid:
                        payments = [{'amt': safe_float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                        pp_data = info.get('partial_payments', [])
                        if isinstance(pp_data, dict): pp_data = pp_data.values()
                        payments.extend([{'amt': safe_float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in pp_data if isinstance(pmt, dict)])
                        
                        c_rate = safe_float(info.get('company_rate'))
                        if c_rate <= 0: c_rate = b_rate
                        if c_rate <= 0: c_rate = 650 
                        disc_sqft = safe_float(info.get('discount', 0))
                        
                        # 🎯 लाइव डिफरेंस कैलकुलेशन
                        diff_pct = calculate_differential_pct(target_id, seller_id)
                        
                        display_seller_name = display_names_map.get(seller_id, str(e_name).title())
                        entry_type = "Self" if is_self else f"Group ({display_seller_name})"
                        
                        for pmt in payments:
                            amt = safe_float(pmt['amt'])
                            if amt > 0:
                                gross = (amt * diff_pct) / 100
                                disc_amt = (amt / c_rate) * disc_sqft 
                                net_comm = gross - disc_amt
                                tds = net_comm * 0.02
                                in_hand = net_comm - tds
                                
                                rows.append({
                                    "S.No.": count, "Type": entry_type, "Mauja": mauja, "Project": proj_name, "Plot": pid, 
                                    "Customer": info.get('customer_name', 'N/A'), "Received": amt, 
                                    "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, 
                                    "Net Comm": net_comm, "TDS": tds, "In Hand": in_hand
                                })
                                count += 1

    df = pd.DataFrame(rows)
    totals = { "S.No.": "TOTAL", "Type": "", "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
        "Received": df['Received'].sum() if not df.empty else 0, "Gross": df['Gross'].sum() if not df.empty else 0, 
        "Discount": df['Discount'].sum() if not df.empty else 0, "Net Comm": df['Net Comm'].sum() if not df.empty else 0, 
        "TDS": df['TDS'].sum() if not df.empty else 0, "In Hand": df['In Hand'].sum() if not df.empty else 0 }
        
    st.session_state.df_view = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    st.session_state.meta = {"exec": search_exec, "start": start_date, "end": end_date, "type": comm_type}

# ==========================================
# 6. DISPLAY FINAL STATEMENT
# ==========================================
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df, meta = st.session_state.df_view, st.session_state.meta
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        {logo_html}
        <h1 class='title'>FIRSTCHOICE INFRA</h1>
        <p style='margin: 5px 0;'><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px; margin: 0;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>
    <h3 style='text-align:center; margin-top:0;'>Executive Commission Statement</h3>
    <div style='margin-bottom:10px; font-size:13px;'>
        <b>Partner:</b> {meta['exec']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Type:</b> {meta['type']} 
        <span style="float:right;"><b>Period:</b> {meta['start']} to {meta['end']}</span>
    </div>""", unsafe_allow_html=True)
    
    st.markdown(df.to_html(classes='data-table', index=False, float_format="%.2f"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    components.html("""<style>@media print { body { display: none !important; } }</style>
        <div style="text-align:center; margin-top:20px;"><button onclick="window.parent.print()" style="padding:12px 30px; background-color:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:16px;">🖨️ Print Final Document</button></div>
    """, height=80)

