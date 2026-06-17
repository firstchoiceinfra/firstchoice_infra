import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import base64
import os
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")

# (अगर आपके database.py में init_db है, तो उसे कॉल करें)
try:
    import database
    database.init_db()
except:
    pass

db_data = st.session_state.get('db_projects', {})

# 🔎 डेटाबेस की गहराई से Executives को निकालना
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
            elif isinstance(v, list):
                exec_data_root = {str(i): item for i, item in enumerate(v) if isinstance(item, dict)}
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

def clean_str(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())

# 🛠️ पार्ट 1: डेटाबेस के अंदर से असली नाम और स्पॉन्सर निकालना (ID को इग्नोर करके)
parsed_execs = {}
for k, v in exec_data_root.items():
    if isinstance(v, dict):
        name = ""
        sp = ""
        pct = 0.0
        for key, val in v.items():
            kl = clean_str(key)
            if kl in ['name', 'executivename', 'partnername', 'fullname']: 
                name = str(val).strip()
            elif kl in ['sponsor', 'sponsorname', 'upline']: 
                sp = str(val).strip()
            elif kl in ['percentage', 'percentageexec', 'pct', 'commission', 'commissionpercentage']: 
                pct = safe_float(val)
                
        if not name: 
            name = str(k).strip()
            
        parsed_execs[name] = {
            'name': name,
            'c_name': clean_str(name),
            'sp': sp,
            'c_sp': clean_str(sp),
            'pct': pct
        }

# 🛠️ पार्ट 2: डाउनलाइन ढूँढने वाला सुपर-स्कैनर
def get_team(target_c_name, parsed_data):
    team = set()
    queue = [target_c_name]
    while queue:
        curr = queue.pop(0)
        if not curr: continue
        for k, v in parsed_data.items():
            csp = v['c_sp']
            cnm = v['c_name']
            # अगर करेंट पर्सन स्पॉन्सर के नाम में मैच हो जाए
            if csp and (curr in csp or csp in curr):
                if cnm not in team and cnm != target_c_name:
                    team.add(cnm)
                    queue.append(cnm)
    return team

# 🛠️ पार्ट 3: कट-टू-कट डिफरेंस कमीशन कैलकुलेटर
def get_diff(target_c, plot_c, parsed_data):
    t_pct = 0.0
    p_pct = 0.0
    for v in parsed_data.values():
        if target_c == v['c_name'] or target_c in v['c_name'] or v['c_name'] in target_c: 
            t_pct = v['pct']
        if plot_c == v['c_name'] or plot_c in v['c_name'] or v['c_name'] in plot_c: 
            p_pct = v['pct']

    if not plot_c or target_c == plot_c or plot_c in target_c or target_c in plot_c:
        return t_pct

    curr = plot_c
    visited = set()
    child_pct = 0.0

    while curr and curr not in visited:
        visited.add(curr)
        found_parent = False
        for v in parsed_data.values():
            if v['c_name'] == curr or curr in v['c_name']:
                csp = v['c_sp']
                if csp:
                    if target_c == csp or target_c in csp or csp in target_c:
                        child_pct = v['pct']
                        return max(0.0, t_pct - child_pct)
                    else:
                        curr = csp
                        found_parent = True
                        break
        if not found_parent:
            break
            
    return max(0.0, t_pct - p_pct)

# 3. 100% SECURE LOGIN LOGIC
st.markdown('<div class="no-print">', unsafe_allow_html=True)

user_role = str(st.session_state.get('role', '')).strip().lower()
logged_in_user = str(st.session_state.get('username', '')).strip()
c_logged = clean_str(logged_in_user)

is_admin = (user_role == 'admin' or c_logged == 'admin')

if not c_logged and not is_admin:
    st.error("🚫 **Access Denied (सुरक्षा लॉक):** कोई लॉगिन सेशन डेटा नहीं मिला। कृपया मुख्य लॉगिन पेज से आएं।")
    st.stop()

if is_admin:
    st.success(f"👑 **Admin Panel:** Active (Connected to Database - {len(parsed_execs)} Partners Found)")
    all_execs = [v['name'] for v in parsed_execs.values()]
    search_exec = st.selectbox("🔎 Select Business Partner", all_execs)
else:
    st.info(f"🔒 **Executive View:** Logged in as **{logged_in_user}**")
    my_team = get_team(c_logged, parsed_execs)
    
    allowed_options = []
    for v in parsed_execs.values():
        if v['c_name'] == c_logged or v['c_name'] in my_team:
            allowed_options.append(v['name'])
            
    if not allowed_options:
        allowed_options = [logged_in_user]
        
    search_exec = st.selectbox("🔎 Select Business Partner (Your Team Only)", allowed_options)

comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation Logic
if btn_generate and search_exec: 
    rows = []
    count = 1
    target_c = clean_str(search_exec)
    selected_downline = get_team(target_c, parsed_execs)
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            base_rate_from_db = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                
                ex_name = ""
                for key, val in info.items():
                    kl = clean_str(key)
                    if kl in ['executivename', 'executive', 'execname', 'partnername']:
                        ex_name = str(val).strip()
                        
                plot_c = clean_str(ex_name)
                
                is_self = False
                if target_c == plot_c or plot_c in target_c or target_c in plot_c:
                    is_self = True
                
                is_group = False
                if not is_self:
                    for dl in selected_downline:
                        if dl == plot_c or plot_c in dl or dl in plot_c:
                            is_group = True
                            break
                
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
                    
                    # 🎯 डिफरेंस लागू
                    diff_pct = get_diff(target_c, plot_c, parsed_execs)
                    
                    if is_self:
                        entry_label = "Self"
                    else:
                        orig_name = str(ex_name).title()
                        for v in parsed_execs.values():
                            if v['c_name'] == plot_c or plot_c in v['c_name']:
                                orig_name = v['name']
                                break
                        entry_label = f"Group ({orig_name})"
                    
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
    
    # 6. Active Print Button
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

