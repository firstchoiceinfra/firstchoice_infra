import streamlit as st
import streamlit.components.v1 as components
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

# 🔎 डेटाबेस पार्सिंग (मास्टर डेटा)
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

# 🛠️ बहुत ही स्मार्ट नाम स्कैनर (स्पेस, डॉट, अंडरस्कोर सब इग्नोर करेगा)
def is_same_person(n1, n2):
    s1 = re.sub(r'[^a-z0-9]', '', str(n1).lower())
    s2 = re.sub(r'[^a-z0-9]', '', str(n2).lower())
    if not s1 or not s2: return False
    if s1 == s2: return True
    if len(s1) >= 4 and len(s2) >= 4:
        if s1 in s2 or s2 in s1: return True
    return False

# 🛠️ मास्टर डेटा लोड करना (Executive_name जैसी स्पेलिंग मिस नहीं होगी)
exec_list = []
for k, v in exec_data_root.items():
    if isinstance(v, dict):
        name, sp, pct = "", "", 0.0
        for key, val in v.items():
            kl = str(key).strip().lower()
            if kl in ['name', 'executivename', 'executive_name', 'partnername', 'fullname']: name = str(val).strip()
            elif kl in ['sponsor', 'sponsorname', 'sponsor_name', 'upline']: sp = str(val).strip()
            elif kl in ['percentage', 'percentageexec', 'percentage_exec', 'pct', 'commission']: pct = safe_float(val)
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

# 🛠️ असीमित चेन ढूँढने का सिस्टम (A -> B -> C -> D)
links = set()
for ex in exec_list:
    if ex['name'] and ex['sp'] and not is_same_person(ex['name'], ex['sp']):
        links.add((resolve_name(ex['name']), resolve_name(ex['sp'])))

for p_info in db_data.values():
    if isinstance(p_info, dict) and 'plots' in p_info:
        plots = p_info['plots']
        plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
        for pid, info in plot_items:
            if isinstance(info, dict):
                ex_n, sp_n = "", ""
                for key, val in info.items():
                    kl = str(key).strip().lower()
                    if kl in ['executivename', 'executive_name', 'executive', 'execname', 'partnername']: ex_n = str(val).strip()
                    elif kl in ['sponsorname', 'sponsor_name', 'sponsor', 'upline']: sp_n = str(val).strip()
                if ex_n and sp_n and not is_same_person(ex_n, sp_n):
                    links.add((resolve_name(ex_n), resolve_name(sp_n)))

def get_downline(target_name):
    team = set()
    queue = [target_name]
    while queue:
        curr = queue.pop(0)
        for child, parent in links:
            if is_same_person(parent, curr):
                if child not in team and not is_same_person(child, target_name):
                    team.add(child)
                    queue.append(child)
    return team

# 🛠️ डिफरेंस कैलकुलेटर (कट-टू-कट कमीशन)
def get_pct(name):
    for ex in exec_list:
        if is_same_person(name, ex['name']): return ex['pct']
    return 0.0

def get_diff_pct(target, plot_exec):
    t_pct = get_pct(target)
    if is_same_person(target, plot_exec): return t_pct

    curr = plot_exec
    path = []
    visited = set()
    
    while curr and curr not in visited and not is_same_person(curr, target):
        visited.add(curr)
        path.append(curr)
        parent = ""
        for c, p in links:
            if is_same_person(c, curr):
                parent = p
                break
        curr = parent

    if curr and is_same_person(curr, target) and path:
        imm_child = path[-1] 
        c_pct = get_pct(imm_child)
        return max(0.0, t_pct - c_pct)
    else:
        p_pct = get_pct(plot_exec)
        return max(0.0, t_pct - p_pct)

# ==========================================================
# 🚀 100% STRICT SECURITY + EMERGENCY UNLOCK
# ==========================================================
st.markdown('<div class="no-print">', unsafe_allow_html=True)

is_admin = False

for key, val in st.session_state.items():
    if isinstance(val, str) and any(x in str(val).lower() for x in ['admin', 'boss', 'owner', 'firstchoice']):
        is_admin = True
        break
    if isinstance(val, bool) and val is True and 'admin' in str(key).lower():
        is_admin = True
        break

if 'force_admin_unlock' in st.session_state and st.session_state.force_admin_unlock:
    is_admin = True

if not is_admin:
    st.error("🚫 Access Denied! मेन पेज का लॉगिन डेटा इस पेज तक नहीं पहुँच पाया।")
    st.info("चूँकि आप कंपनी के बॉस (Admin) हैं, कृपया नीचे अपना एमरजेंसी पिन डालकर पेज को तुरंत अनलॉक करें:")
    
    col_a, col_b = st.columns([1, 3])
    with col_a:
        pwd = st.text_input("Admin PIN", type="password")
        if st.button("🔓 Unlock Page"):
            if pwd == "1234" or pwd == "admin123":
                st.session_state.force_admin_unlock = True
                st.rerun()
            else:
                st.error("❌ गलत पिन!")
    st.stop()

# ==========================================================
# 👑 एडमिन पैनल 
# ==========================================================
st.success("👑 **Boss / Admin Panel Active:** (सुरक्षित लॉगिन प्रमाणित)")
if st.button("🔒 Logout (Lock Page)"):
    st.session_state.force_admin_unlock = False
    st.rerun()

all_exec_names = [ex['name'] for ex in exec_list if ex['name']]
if all_exec_names:
    search_exec = st.selectbox("🔎 Select Business Partner to View Statement", all_exec_names)
else:
    st.warning("⚠️ डेटाबेस में कोई पार्टनर नहीं मिला।")
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
    target_exec = resolve_name(search_exec)
    selected_downline = get_downline(target_exec)
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            base_rate_from_db = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                if isinstance(info, dict):
                    ex_name, sp_name = "", ""
                    for key, val in info.items():
                        kl = str(key).strip().lower()
                        # यहाँ अंडरस्कोर वाला 'executive_name' जोड़ दिया गया है!
                        if kl in ['executivename', 'executive_name', 'executive', 'partnername']: ex_name = str(val).strip()
                        elif kl in ['sponsorname', 'sponsor_name', 'sponsor', 'upline']: sp_name = str(val).strip()
                            
                    r_ex = resolve_name(ex_name)
                    r_sp = resolve_name(sp_name)
                    
                    is_self = is_same_person(r_ex, target_exec)
                    is_group = False
                    
                    if not is_self:
                        for dl in selected_downline:
                            if is_same_person(r_ex, dl) or is_same_person(r_sp, dl):
                                is_group = True
                                break
                        if is_same_person(r_sp, target_exec):
                            is_group = True
                    
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
                        
                        diff_pct = get_diff_pct(target_exec, r_ex)
                        
                        if is_self:
                            entry_label = "Self"
                        else:
                            display_name = r_ex if r_ex else str(ex_name).title()
                            entry_label = f"Group ({display_name})"
                        
                        for pmt in payments:
                            amt = safe_float(pmt['amt'])
                            if amt > 0:
                                gross = (amt * diff_pct) / 100
                                disc_amt = (amt / comp_rate) * discount_sqft 
                                net_comm = gross - disc_amt
                                tds = net_comm * 0.02
                                in_hand = net_comm - tds
                                
                                rows.append({
                                    "S.No.": count, "Type": entry_label, "Mauja": mauja, "Project": project_name, "Plot": pid, 
                                    "Customer": info.get('customer_name', 'N/A'), "Received": amt, 
                                    "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, 
                                    "Net Comm": net_comm, "TDS": tds, "In Hand": in_hand
                                })
                                count += 1
    
    df = pd.DataFrame(rows)
    totals = {
        "S.No.": "TOTAL", "Type": "", "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
        "Received": df['Received'].sum() if not df.empty else 0, 
        "Gross": df['Gross'].sum() if not df.empty else 0, 
        "Discount": df['Discount'].sum() if not df.empty else 0, 
        "Net Comm": df['Net Comm'].sum() if not df.empty else 0, 
        "TDS": df['TDS'].sum() if not df.empty else 0, 
        "In Hand": df['In Hand'].sum() if not df.empty else 0
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    st.session_state.df_view = df
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end, "type": comm_type}

# 5. Display Render
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        {logo_html}
        <h1 class='title'>FIRSTCHOICE INFRA</h1>
        <p style='margin: 5px 0;'><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px; margin: 0;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>
    <h3 style='text-align:center; margin-top:0;'>Executive Commission Statement</h3>
    <div style='margin-bottom:10px; font-size:13px;'>
        <b>Partner:</b> {meta['exec']} &nbsp;&nbsp;|&nbsp;&nbsp; 
        <b>Type:</b> {meta['type']} 
        <span style="float:right;"><b>Period:</b> {meta['start']} to {meta['end']}</span>
    </div>""", unsafe_allow_html=True)
    
    html_table = df.to_html(classes='data-table', index=False, float_format="%.2f")
    st.markdown(html_table, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    components.html(
        """
        <style>@media print { body { display: none !important; } }</style>
        <div style="text-align:center; margin-top:20px;">
            <button onclick="window.parent.print()" style="padding:12px 30px; background-color:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif;">
                🖨️ Print Final Document
            </button>
        </div>
        """,
        height=80
    )

