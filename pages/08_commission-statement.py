import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(layout="wide")

# ==========================================
# 🔒 1. ADMIN SECURITY LOCK
# ==========================================
if st.session_state.get('user_role') != 'admin':
    st.error("🚨 Access Denied! This page is strictly restricted to Administrators only.")
    st.stop()

# ==========================================
# 2. DATABASE INITIALIZATION
# ==========================================
if 'db_projects' not in st.session_state:
    try:
        database.init_db()
    except Exception as e:
        st.error("डेटाबेस लोड करने में समस्या: " + str(e))

db_projects = st.session_state.get('db_projects', {})
executives = db_projects.get('executives', {})

# ==========================================
# 🔄 3. SMART SYNC & AGGRESSIVE DATA TRACKER
# ==========================================
def parse_percentage(val):
    try:
        if isinstance(val, str):
            val = val.replace('%', '').strip()
        val = float(val)
        return val / 100 if val > 1 else val
    except:
        return 0.23 # डिफ़ॉल्ट 23%

def get_exec_details(target_name, exec_dict):
    """पार्टनर का Upline और Commission Percentage निकालता है (Case-Insensitive)"""
    upline = ""
    perc = 0.23 
    target_clean = str(target_name).strip().lower()
    
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            current_name = str(v.get('name', k)).strip().lower()
            if current_name == target_clean:
                # upline/sponsor ढूँढने के लिए सारे संभावित नाम
                upline_raw = v.get('sponsor', v.get('upline', v.get('referred_by', v.get('partner_name', ''))))
                upline = str(upline_raw).strip().lower()
                
                saved_perc = v.get('commission_percentage', v.get('percentage', v.get('comm_perc', 23)))
                perc = parse_percentage(saved_perc)
                break
    return upline, perc

def get_all_downlines(target_name, exec_dict):
    """पार्टनर के नीचे जुडी पूरी चेन ढूँढता है (Aggressive Match)"""
    downlines = []
    target_clean = str(target_name).strip().lower()
    
    for k, v in exec_dict.items():
        if isinstance(v, dict):
            exec_name_raw = str(v.get('name', k)).strip()
            exec_name_clean = exec_name_raw.lower()
            
            upline_raw = v.get('sponsor', v.get('upline', v.get('referred_by', v.get('partner_name', ''))))
            upline_clean = str(upline_raw).strip().lower()
            
            if upline_clean == target_clean and exec_name_clean != target_clean:
                downlines.append(exec_name_raw) # असली नाम सेव करें
                downlines.extend(get_all_downlines(exec_name_raw, exec_dict))
                
    return list(set(downlines))

def get_total_received_in_range(plot_info, start_d, end_d):
    """EMI + Token Tracker: प्लॉट के अंदर हर जगह पेमेंट ढूँढता है"""
    total = 0.0
    
    # 1. पहले बुकिंग/टोकन अमाउंट चेक करें
    b_date_str = str(plot_info.get('booking_date', '')).strip()
    if b_date_str:
        try:
            b_date = datetime.datetime.strptime(b_date_str[:10], "%Y-%m-%d").date()
            if start_d <= b_date <= end_d:
                total += float(plot_info.get('token_amount', plot_info.get('booking_amount', 0)))
        except:
            pass

    # 2. अब प्लॉट के अंदर मौजूद सभी लिस्ट/डिक्शनरी में EMI ढूँढें
    for key, val in plot_info.items():
        if isinstance(val, (dict, list)) and key.lower() not in ['customer_details']:
            items = val.values() if isinstance(val, dict) else val
            for item in items:
                if isinstance(item, dict):
                    # पेमेंट की डेट और अमाउंट ढूँढने की कोशिश
                    p_date_str = str(item.get('date', item.get('payment_date', item.get('receipt_date', '')))).strip()
                    p_amt_raw = item.get('amount', item.get('paid_amount', item.get('emi_amount', 0)))
                    
                    try:
                        p_amt = float(p_amt_raw)
                        if p_date_str and p_amt > 0:
                            p_date = datetime.datetime.strptime(p_date_str[:10], "%Y-%m-%d").date()
                            if start_d <= p_date <= end_d:
                                total += p_amt
                    except:
                        pass # अगर डेट गलत है या अमाउंट नंबर नहीं है तो छोड़ दें
                        
    return total

# ---------------------------------------------------------

partner_list = []
if isinstance(executives, dict) and executives:
    # लिस्ट में असली नाम (Original Case) दिखाएं
    partner_list = sorted(list(set([str(v.get('name', k)).strip() for k, v in executives.items() if isinstance(v, dict)])))

if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# ==========================================
# 🌟 DASHBOARD PAGE (Admin View)
# ==========================================
if st.session_state.page == 'dashboard':
    st.title("📊 Executive Commission Dashboard (Admin)")

    if not partner_list:
        st.warning("⚠️ No partners found in database.")
    else:
        search_exec = st.selectbox("👤 Select Main Partner", options=partner_list)
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        scope = st.radio("📑 Commission Scope", ["Self", "Group", "All"], horizontal=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        start_d = col1.date_input("📅 Start Date", datetime.date(2024, 6, 6))
        end_d = col2.date_input("📅 End Date", datetime.date(2026, 6, 24))

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🚀 Generate Systematic Statement", use_container_width=True):
            rows = []
            
            # 1. डाउनलाइन सेट करें (Case-Insensitive Match के लिए)
            search_exec_clean = search_exec.lower()
            if scope == "Self":
                valid_execs_clean = [search_exec_clean]
            else:
                downlines_list = get_all_downlines(search_exec, executives)
                valid_execs_clean = [search_exec_clean] + [d.lower() for d in downlines_list]
            
            # 2. मेन पार्टनर का अपना कमीशन %
            _, my_perc = get_exec_details(search_exec, executives)
            
            for p_name, p_info in db_projects.items() if isinstance(db_projects, dict) else {}:
                if isinstance(p_info, dict) and p_name not in ['executives', '_app_settings']:
                    mauja = next((str(v) for k, v in p_info.items() if str(k).lower() in ['mauza', 'mauja']), "N/A")
                    plots = p_info.get('plots', {})
                    
                    plot_items = plots.items() if isinstance(plots, dict) else enumerate(plots)
                    
                    for pid, info in plot_items:
                        if isinstance(info, dict):
                            exec_name = str(info.get('executive_name', '')).strip()
                            exec_name_clean = exec_name.lower()
                            
                            if exec_name_clean in valid_execs_clean:
                                # 3. Token + EMI Tracker से टोटल अमाउंट निकालें
                                amt = get_total_received_in_range(info, start_d, end_d)
                                
                                # अगर इस डेट रेंज में कोई पेमेंट नहीं आई, तो स्किप करें
                                if amt <= 0:
                                    continue
                                    
                                # 4. Difference Amount Calculator
                                if exec_name_clean == search_exec_clean:
                                    diff_perc = my_perc
                                    is_downline = False
                                else:
                                    _, downline_perc = get_exec_details(exec_name, executives)
                                    diff_perc = my_perc - downline_perc
                                    is_downline = True
                                    
                                # अगर डिफरेंस 0 या नेगेटिव है, तो कमीशन नहीं जुड़ेगा
                                if diff_perc <= 0:
                                    continue
                                
                                # 5. फाइनल कैलकुलेशन
                                gross = amt * diff_perc        
                                discount = (amt * 0.037) * (diff_perc / 0.23) if my_perc > 0 else 0 
                                net_comm = gross - discount
                                tds = net_comm * 0.02
                                in_hand = net_comm - tds
                                
                                cust_name = str(info.get('customer_name', 'N/A')).title()
                                if is_downline:
                                    cust_name += f" <br><span style='font-size:10px; color:#555;'><i>(via {exec_name.title()})</i></span>"
                                
                                # डेट दिखाने के लिए बुकिंग डेट का इस्तेमाल करें
                                b_date_str = info.get('booking_date', 'N/A')
                                
                                rows.append({
                                    "S.No.": len(rows) + 1, 
                                    "Mauja": str(mauja).capitalize(), 
                                    "Project": str(p_name), 
                                    "Plot": str(pid), 
                                    "Customer": cust_name,
                                    "Received": amt, 
                                    "Date": b_date_str,
                                    "Gross": gross, 
                                    "Discount": discount, 
                                    "Net Comm": net_comm, 
                                    "TDS": tds, 
                                    "In Hand": in_hand
                                })
            
            if rows:
                df = pd.DataFrame(rows)
                
                total_row = {
                    "S.No.": "TOTAL", 
                    "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
                    "Received": df["Received"].sum(),
                    "Gross": df["Gross"].sum(),
                    "Discount": df["Discount"].sum(),
                    "Net Comm": df["Net Comm"].sum(),
                    "TDS": df["TDS"].sum(),
                    "In Hand": df["In Hand"].sum()
                }
                
                for col in ["Received", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]:
                    df[col] = df[col].apply(lambda x: f"{float(x):.2f}")
                    total_row[col] = f"{float(total_row[col]):.2f}"
                
                df.loc[len(df)] = total_row
                
                st.session_state.final_df = df
                st.session_state.meta_data = {
                    "partner": search_exec, 
                    "scope": scope, 
                    "start": start_d, 
                    "end": end_d
                }
                st.session_state.page = 'report' 
                st.rerun()
            else:
                st.error("❌ इस डेट रेंज और स्कोप में कोई ट्रांजैक्शन या डिफरेंस अमाउंट नहीं मिला!")

# ==========================================
# 📄 REPORT PAGE (PDF Format Style)
# ==========================================
elif st.session_state.page == 'report':
    
    st.title("📄 Executive Commission Statement")
    
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if 'final_df' in st.session_state:
        meta = st.session_state.meta_data
        df = st.session_state.final_df
        
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🖨️ Print Statement (PDF Format)", type="primary"):
            html = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; color: #000; padding: 15px; font-size: 13px; }}
                    .header-section {{ text-align: center; margin-bottom: 25px; }}
                    .header-section h1 {{ margin: 0; font-size: 28px; font-weight: bold; letter-spacing: 1px; color: #000; }}
                    .header-section p {{ margin: 4px 0; font-size: 14px; }}
                    .tagline {{ font-style: italic; font-weight: bold; }}
                    .title-box {{ font-weight: bold; font-size: 18px; text-decoration: underline; text-align: center; margin: 20px 0; }}
                    .info-section {{ margin-bottom: 15px; font-size: 14px; line-height: 1.6; }}
                    .table-container {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }}
                    .table-container th, .table-container td {{ border: 1px solid #000; padding: 5px; text-align: center; }}
                    .table-container th {{ font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header-section">
                    <h1>FIRSTCHOICE INFRA</h1>
                    <p class="tagline">Symbol Of Trust...</p>
                    <p>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi (Sim) Bahadura, Nagpur-440034</p>
                </div>
                
                <div class="title-box">Executive Commission Statement</div>
                
                <div class="info-section">
                    <b>Partner:</b> {meta['partner']} <br>
                    <b>Scope:</b> {meta['scope']} <br>
                    <b>Period:</b> {meta['start']} to {meta['end']}
                </div>
                
                {df.to_html(classes='table-container', index=False, escape=False)}
                
            </body>
            </html>
            <script>window.print();</script>
            """
            st.components.v1.html(html, height=800)
    else:
        st.error("No data found!")
        st.session_state.page = 'dashboard'
