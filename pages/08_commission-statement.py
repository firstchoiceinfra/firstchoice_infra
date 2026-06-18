import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re

# ==========================================
# 1. PAGE SETUP & DATABASE
# ==========================================
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")

try:
    import database
    database.init_db()
except:
    pass

db_data = st.session_state.get('db_projects', {})

# मास्टर डेटा ढूँढना
exec_data_root = {}
for key in ['executives', 'db_executives', 'partners', 'associates']:
    if key in st.session_state and isinstance(st.session_state[key], dict) and st.session_state[key]:
        exec_data_root = st.session_state[key]
        break
if not exec_data_root and isinstance(db_data, dict):
    for k, v in db_data.items():
        if str(k).strip().lower() in ['executives', 'executive', 'partners', 'associates']:
            if isinstance(v, dict): exec_data_root = v
            break

# लोगो
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
        [data-testid="stSidebar"], .stAppHeader, div.stButton, div[data-testid="stSelectbox"], div[role="radiogroup"], .no-print { display: none !important; }
        body, html, .stApp, main { background: white !important; padding: 0 !important; margin: 0 !important; }
        .block-container { padding-top: 0 !important; margin-top: 0 !important; }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 5px 20px; }
    .header { position: relative; text-align: center; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 15px; }
    .title { font-size: 30px; font-weight: bold; margin: 0; color: #000; text-transform: uppercase; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 6px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
    .data-table tr:last-child td { font-weight: 900 !important; background-color: #ffeb3b !important; color: #000 !important; font-size: 15px !important; }
</style>""", unsafe_allow_html=True)

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

# ==========================================
# 3. SMART NAME MATCHING (दमदार और सिंपल)
# ==========================================
def clean_n(name):
    return re.sub(r'[^a-z0-9]', '', str(name).lower())

def is_match(n1, n2):
    s1, s2 = clean_n(n1), clean_n(n2)
    if not s1 or not s2: return False
    if s1 == s2 or s1 in s2 or s2 in s1: return True
    return False

# ==========================================
# 4. BUILD MASTER DATA (बिना किसी कचरे के)
# ==========================================
exec_list = []
for k, v in exec_data_root.items():
    if isinstance(v, dict):
        name, sp, pct = str(k).strip(), "", 0.0
        for key, val in v.items():
            kl = clean_n(key)
            if kl in ['name', 'executivename', 'partnername']: name = str(val).strip()
            elif kl in ['sponsor', 'sponsorname', 'upline']: sp = str(val).strip()
            elif kl in ['percentage', 'pct', 'commission', 'percentageexec']: pct = safe_float(val)
        exec_list.append({'name': name, 'sp': sp, 'pct': pct})

def get_pct(target_name):
    for ex in exec_list:
        if is_match(ex['name'], target_name): return ex['pct']
    return 0.0

# चेन (Network) बनाना
links = []
for ex in exec_list:
    if ex['name'] and ex['sp'] and not is_match(ex['name'], ex['sp']):
        links.append((ex['name'], ex['sp']))

# प्लॉट से भी चेन जोड़ना (ताकि कोई जूनियर छूटे नहीं)
for p_info in db_data.values():
    if isinstance(p_info, dict) and 'plots' in p_info:
        for pid, info in (p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots'])):
            if isinstance(info, dict):
                en, sn = "", ""
                for k, v in info.items():
                    kl = clean_n(k)
                    if kl in ['executivename', 'executive', 'partnername']: en = str(v).strip()
                    elif kl in ['sponsorname', 'sponsor', 'upline']: sn = str(v).strip()
                if en and sn and not is_match(en, sn):
                    links.append((en, sn))

def get_full_team(boss_name):
    team = set()
    queue = [boss_name]
    while queue:
        curr = queue.pop(0)
        for child, parent in links:
            if is_match(parent, curr) and not is_match(child, boss_name) and child not in team:
                team.add(child)
                queue.append(child)
    return team

# ==========================================
# 5. SECURITY LOCK (सिर्फ बॉस के लिए)
# ==========================================
st.markdown('<div class="no-print">', unsafe_allow_html=True)
is_admin = False

for val in st.session_state.values():
    if isinstance(val, str) and any(x in str(val).lower() for x in ['admin', 'boss', 'owner', 'firstchoice']):
        is_admin = True; break

if 'force_unlock' in st.session_state and st.session_state.force_unlock:
    is_admin = True

if not is_admin:
    st.error("🚫 Access Denied! यह पेज सिर्फ एडमिन के लिए है।")
    pwd = st.text_input("Admin PIN (Emergency Unlock)", type="password")
    if st.button("🔓 Unlock Page"):
        if pwd == "1234" or pwd == "admin123":
            st.session_state.force_unlock = True
            st.rerun()
        else: st.error("❌ गलत पिन!")
    st.stop()

st.success("👑 **Admin Panel Active**")
if st.button("🔒 Lock Page"):
    st.session_state.force_unlock = False
    st.rerun()

all_names = [ex['name'] for ex in exec_list if ex['name']]
search_exec = st.selectbox("🔎 Select Business Partner", all_names) if all_names else None
comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start_date, end_date = col1.date_input("Start Date"), col2.date_input("End Date")
btn_gen = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# 6. COMMISSION LOGIC (फ्रेश और कट-टू-कट)
# ==========================================
if btn_gen and search_exec: 
    rows = []
    count = 1
    my_team = get_full_team(search_exec)
    boss_pct = get_pct(search_exec)
    
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for proj_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(proj_name.lower(), "Nagpur"))
            b_rate = safe_float(p_info.get('base_rate', 650))
            
            for pid, info in (p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots'])):
                if isinstance(info, dict):
                    e_name, s_name = "", ""
                    for k, v in info.items():
                        kl = clean_n(k)
                        if kl in ['executivename', 'executive']: e_name = str(v).strip()
                        elif kl in ['sponsorname', 'sponsor']: s_name = str(v).strip()
                    
                    is_self = is_match(e_name, search_exec)
                    is_group = False
                    
                    if not is_self:
                        if is_match(s_name, search_exec): is_group = True
                        else:
                            for member in my_team:
                                if is_match(e_name, member) or is_match(s_name, member):
                                    is_group = True; break
                    
                    is_valid = (comm_type == "Self" and is_self) or (comm_type == "Group" and is_group) or (comm_type == "All (Self + Group)" and (is_self or is_group))
                    
                    if is_valid:
                        payments = [{'amt': safe_float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                        pp_data = info.get('partial_payments', [])
                        if isinstance(pp_data, dict): pp_data = pp_data.values()
                        payments.extend([{'amt': safe_float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in pp_data if isinstance(pmt, dict)])
                        
                        c_rate = safe_float(info.get('company_rate'))
                        if c_rate <= 0: c_rate = b_rate
                        if c_rate <= 0: c_rate = 650 
                        disc_sqft = safe_float(info.get('discount', 0))
                        
                        # 🎯 डायरेक्ट डिफरेंस कैलकुलेशन
                        diff_pct = boss_pct
                        if not is_self:
                            # अगर ग्रुप का है, तो जिसने बेचा है उसका % माइनस करो
                            child_pct = get_pct(e_name)
                            diff_pct = max(0.0, boss_pct - child_pct)
                        
                        entry_type = "Self" if is_self else f"Group ({e_name.title()})"
                        
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
# 7. DISPLAY FINAL STATEMENT
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

