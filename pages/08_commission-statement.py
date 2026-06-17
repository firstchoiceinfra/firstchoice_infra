import streamlit as st
import streamlit.components.v1 as components
import database
import pandas as pd
import base64
import os

# 1. Page Config
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement", initial_sidebar_state="collapsed")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

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
    .block-container { padding-top: 0rem !important; margin-top: -60px !important; padding-bottom: 1rem !important; max-width: 100% !important; }
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
    
    /* TOTAL वाली लाइन एकदम डार्क और हाईलाइटेड */
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

# डाउनलाइन निकालने का फंक्शन
def get_downline_team(target_user, exec_data):
    team = set()
    queue = [str(target_user).strip().lower()]
    while queue:
        curr = queue.pop(0)
        for k, v in exec_data.items():
            if isinstance(v, dict):
                sp = str(v.get('sponsor', v.get('sponsor_name', ''))).strip().lower()
                if sp == curr:
                    sub_exec = str(k).strip().lower()
                    if sub_exec not in team:
                        team.add(sub_exec)
                        queue.append(sub_exec)
    return team

# 3. 100% BULLETPROOF SECURITY & RECOVERY LOGIC
st.markdown('<div class="no-print">', unsafe_allow_html=True)

# 1. पहले चेक करें कि क्या लॉगिन पेज से डेटा आया है?
logged_in_user = str(st.session_state.get('username', '')).strip()
user_role = str(st.session_state.get('role', '')).strip().lower()

# 2. अगर डेटा नहीं आया (लॉगिन पेज ने नाम नहीं भेजा), तो ब्लॉक करने के बजाय मैनुअल बॉक्स दिखाएं!
if not logged_in_user:
    st.warning("⚠️ सिस्टम को आपका लॉगिन डेटा नहीं मिला। कृपया नीचे अपना नाम या ID डालें:")
    manual_user = st.text_input("Enter your ID / Name (Type 'admin' for full access):", key="manual_login")
    
    if manual_user:
        logged_in_user = manual_user.strip()
        if logged_in_user.lower() == 'admin':
            user_role = 'admin'
        else:
            user_role = 'executive'
    else:
        st.stop() # जब तक नाम नहीं डालेंगे, पेज यहीं रुका रहेगा

# 3. अब चेक करें कि एडमिन है या एग्जीक्यूटिव
if user_role == 'admin' or logged_in_user.lower() == 'admin':
    st.success("👑 **Admin Panel:** सभी पार्टनर्स का एक्सेस चालू है।")
    all_execs = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
    search_exec = st.selectbox("🔎 Select Business Partner", all_execs)
else:
    st.info(f"🔒 **Executive View:** लॉग-इन आईडी - **{logged_in_user}** (सिर्फ आपका और आपकी टीम का डेटा)")
    my_downline = get_downline_team(logged_in_user, exec_data_root)
    allowed_options = [k for k in exec_data_root.keys() if str(k).strip().lower() == logged_in_user.lower() or str(k).strip().lower() in my_downline]
    
    if allowed_options:
        search_exec = st.selectbox("🔎 Select Business Partner (Your Team Only)", allowed_options)
    else:
        st.warning(f"'{logged_in_user}' नाम से डेटाबेस में कोई पार्टनर या टीम नहीं मिली। कृपया सही नाम टाइप करें।")
        search_exec = None

comm_type = st.radio("📊 Select Commission Type", ["Self", "Group", "All (Self + Group)"], horizontal=True)

col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

def safe_float(val):
    try: return float(str(val).strip() or 0)
    except: return 0.0

# 4. Calculation Logic
if btn_generate and search_exec: 
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = safe_float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    selected_user_downline = get_downline_team(search_exec, exec_data_root)
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            base_rate_from_db = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                
                exec_in_db = str(info.get('executive_name', '')).strip().lower()
                sponsor_in_db = str(info.get('sponsor_name', info.get('sponsor', ''))).strip().lower()
                target_exec = str(search_exec).strip().lower()
                
                is_self = (exec_in_db == target_exec)
                is_group = (exec_in_db in selected_user_downline or sponsor_in_db == target_exec)
                
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
                    
                    for pmt in payments:
                        amt = safe_float(pmt['amt'])
                        if amt > 0:
                            gross = (amt * p_pct) / 100
                            disc_amt = (amt / comp_rate) * discount_sqft 
                            net_comm = gross - disc_amt
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            
                            entry_type = "Self" if is_self else "Group"
                            
                            rows.append({
                                "S.No.": count, "Type": entry_type, "Mauja": mauja, "Project": project_name, "Plot": pid, 
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

