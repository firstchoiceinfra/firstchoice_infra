import streamlit as st
import streamlit.components.v1 as components
import database
import pandas as pd
import base64
import os
import re

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")
database.init_db()
db_data = st.session_state.db_projects

# 🔎 पार्टनर मैनेजमेंट के डेटाबेस से सीधा डेटा उठाने का सबसे मजबूत तरीका
exec_data_root = {}
for key in ['executives', 'db_executives', 'partners', 'db_partners', 'associates']:
    if key in st.session_state and isinstance(st.session_state[key], dict) and len(st.session_state[key]) > 0:
        exec_data_root = st.session_state[key]
        break

if not exec_data_root and isinstance(db_data, dict):
    for k, v in db_data.items():
        if str(k).strip().lower() in ['executives', 'executive', 'partners', 'partner', 'associates']:
            if isinstance(v, dict) and len(v) > 0:
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

# 🛠️ दो नामों को आपस में स्मार्ट तरीके से मैच करने वाला फ़ंक्शन (शॉर्ट नाम और फुल नाम को मिलाएगा)
def names_match(n1, n2):
    c1 = re.sub(r'[^a-z0-9]', '', str(n1).lower())
    c2 = re.sub(r'[^a-z0-9]', '', str(n2).lower())
    if not c1 or not c2:
        return False
    if c1 == c2 or c1 in c2 or c2 in c1:
        return True
    w1 = [w for w in re.split(r'[^a-z0-9]', str(n1).lower()) if len(w) > 2]
    w2 = [w for w in re.split(r'[^a-z0-9]', str(n2).lower()) if len(w) > 2]
    if w1 and w2 and w1[0] == w2[0]:
        return True
    return False

# 🛠️ पूरी डाउनलाइन (सीनियर -> जूनियर -> सब-जूनियर) की चेन खोजने वाला स्कैनर
def get_downline_team(target_user, exec_data):
    team = set()
    queue = [str(target_user).strip().lower()]
    all_execs = list(exec_data.keys())
    
    while queue:
        curr = queue.pop(0)
        for k in all_execs:
            v = exec_data[k]
            if isinstance(v, dict):
                sp = ""
                for key in ['sponsor', 'sponsor_name', 'Sponsor', 'Sponsor Name', 'upline', 'Upline']:
                    if key in v:
                        sp = str(v[key]).strip().lower()
                        break
                if sp and (names_match(sp, curr) or names_match(curr, sp)):
                    k_low = str(k).strip().lower()
                    if k_low not in team and k_low != str(target_user).strip().lower():
                        team.add(k_low)
                        queue.append(k_low)
    return team

# 🛠️ कट-टू-कट डिफरेंस कमीशन कैलकुलेटर
def get_diff_pct(target_user, plot_exec, exec_data):
    target_pct = 0.0
    target_low = str(target_user).strip().lower()
    for k, v in exec_data.items():
        if names_match(k, target_low) or names_match(target_low, k):
            for key, val in v.items():
                if str(key).strip().lower() in ['percentage_exec', 'percentage', 'pct', 'commission']:
                    target_pct = safe_float(val)
                    break
            break
            
    if names_match(target_user, plot_exec) or names_match(plot_exec, target_user):
        return target_pct
        
    curr = str(plot_exec).strip().lower()
    child_of_target = None
    visited = set()
    
    while curr and curr not in visited:
        visited.add(curr)
        curr_sponsor = ""
        for k, v in exec_data.items():
            if names_match(k, curr) or names_match(curr, k):
                for key, val in v.items():
                    if str(key).strip().lower() in ['sponsor', 'sponsor_name', 'sponsor name', 'upline']:
                        curr_sponsor = str(val).strip().lower()
                        break
                break
                
        if not curr_sponsor:
            break
        if names_match(curr_sponsor, target_low) or names_match(target_low, curr_sponsor):
            child_of_target = curr
            break
        curr = curr_sponsor
        
    if child_of_target:
        child_pct = 0.0
        for k, v in exec_data.items():
            if names_match(k, child_of_target) or names_match(child_of_target, k):
                for key, val in v.items():
                    if str(key).strip().lower() in ['percentage_exec', 'percentage', 'pct', 'commission']:
                        child_pct = safe_float(val)
                        break
                break
        return max(0.0, target_pct - child_pct)
    else:
        plot_exec_pct = 0.0
        for k, v in exec_data.items():
            if names_match(k, plot_exec) or names_match(plot_exec, k):
                for key, val in v.items():
                    if str(key).strip().lower() in ['percentage_exec', 'percentage', 'pct', 'commission']:
                        plot_exec_pct = safe_float(val)
                        break
                break
        return max(0.0, target_pct - plot_exec_pct)

# 3. SECURITY LOGIC
st.markdown('<div class="no-print">', unsafe_allow_html=True)

user_role = str(st.session_state.get('role', '')).strip().lower()
logged_in_user = str(st.session_state.get('username', '')).strip()

is_admin = (user_role == 'admin' or logged_in_user.lower() == 'admin' or (not user_role and not logged_in_user))

if is_admin:
    st.success(f"👑 **Admin Panel:** Active (Connected to Partner Management: Loaded {len(exec_data_root)} Partners)")
    all_execs = list(exec_data_root.keys())
    search_exec = st.selectbox("🔎 Select Business Partner", all_execs)
else:
    target_low = logged_in_user.lower()
    my_downline = get_downline_team(target_low, exec_data_root)
    
    allowed_options = [logged_in_user]
    for k in exec_data_root.keys():
        if str(k).strip().lower() in my_downline and str(k).strip().lower() != target_low:
            allowed_options.append(str(k))
            
    st.info(f"🔒 **Executive View:** Logged in as **{logged_in_user}**")
    if allowed_options:
        search_exec = st.selectbox("🔎 Select Business Partner (Your Team Only)", allowed_options)
    else:
        search_exec = logged_in_user

comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation Logic
if btn_generate and search_exec: 
    rows = []
    count = 1
    target_low = str(search_exec).strip().lower()
    selected_user_downline = get_downline_team(target_low, exec_data_root)
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
                sp_name = ""
                for key, val in info.items():
                    k_l = str(key).strip().lower()
                    if k_l in ['executivename', 'executive', 'execname', 'partnername', 'executive_name']:
                        ex_name = str(val).strip().lower()
                    elif k_l in ['sponsorname', 'sponsor', 'upline', 'sponsor_name']:
                        sp_name = str(val).strip().lower()
                
                is_self = names_match(ex_name, target_low) or names_match(target_low, ex_name)
                
                is_in_downline = False
                for dl_member in selected_user_downline:
                    if names_match(ex_name, dl_member) or names_match(dl_member, ex_name):
                        is_in_downline = True
                        break
                        
                is_group = is_in_downline or names_match(sp_name, target_low) or names_match(target_low, sp_name)
                
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
                    
                    applicable_pct = get_diff_pct(search_exec, ex_name, exec_data_root)
                    
                    if is_self:
                        entry_label = "Self"
                    else:
                        orig_seller_name = str(ex_name).title()
                        for k in exec_data_root.keys():
                            if names_match(k, ex_name) or names_match(ex_name, k):
                                orig_seller_name = str(k)
                                break
                        entry_label = f"Group ({orig_seller_name})"
                    
                    for pmt in payments:
                        amt = safe_float(pmt['amt'])
                        if amt > 0:
                            gross = (amt * applicable_pct) / 100
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

