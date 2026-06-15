import streamlit as st
import streamlit.components.v1 as components
import database
import pandas as pd

# 1. Page Config (Locked)
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS - 100% Strict Print Mode & UI Cleanup
st.markdown("""<style>
    @media print {
        [data-testid="stHeader"], [data-testid="stDecoration"], header, .stAppHeader, 
        [data-testid="stSidebar"], [data-testid="stToolbar"], #Manage-app, .viewerBadge_container__1QSob { 
            display: none !important; 
        }
        [data-testid="stSelectbox"], [data-testid="stHorizontalBlock"], div.stButton, .no-print {
            display: none !important;
        }
        body, html, .stApp, main { background: white !important; }
        .a4-container { 
            display: block !important; 
            width: 100% !important; 
            position: absolute !important; 
            top: 0 !important; 
            left: 0 !important; 
            margin: 0 !important; 
            padding: 0 !important; 
            border: none !important; 
        }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 20px; }
    .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px; }
    .title { font-size: 30px; font-weight: bold; margin: 0; color: #000; text-transform: uppercase; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 11px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 6px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# 3. Inputs
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")

# Safe Float Function
def safe_float(val):
    try:
        return float(str(val).strip() or 0)
    except:
        return 0.0

# 4. Calculation Logic (Locked & Accurate)
if btn_generate:
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = safe_float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            base_rate_from_db = safe_float(p_info.get('base_rate', 650))
            
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                if str(info.get('executive_name', '')).strip().lower() == str(search_exec).strip().lower():
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
                            rows.append({
                                "S.No.": count, "Mauja": mauja, "Project": project_name, "Plot": pid, 
                                "Customer": info.get('customer_name', 'N/A'), "Received": amt, 
                                "Date": pmt['date'], "Gross": gross, "Discount": disc_amt, 
                                "Net Comm": net_comm, "TDS": tds, "In Hand": in_hand
                            })
                            count += 1
    
    df = pd.DataFrame(rows)
    totals = {
        "S.No.": "TOTAL", "Mauja": "", "Project": "", "Plot": "", "Customer": "", "Date": "",
        "Received": df['Received'].sum() if not df.empty else 0, 
        "Gross": df['Gross'].sum() if not df.empty else 0, 
        "Discount": df['Discount'].sum() if not df.empty else 0, 
        "Net Comm": df['Net Comm'].sum() if not df.empty else 0, 
        "TDS": df['TDS'].sum() if not df.empty else 0, 
        "In Hand": df['In Hand'].sum() if not df.empty else 0
    }
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    st.session_state.df_view = df
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display Render
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        <h1 class='title'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust...</i></p>
        <p style='font-size:12px;'>Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
    </div>
    <h3 style='text-align:center; margin-top:0;'>Executive Commission Statement</h3>
    <div style='margin-bottom:10px; font-size:13px;'>
        <b>Partner:</b> {meta['exec']} <span style="float:right;"><b>Period:</b> {meta['start']} to {meta['end']}</span>
    </div>""", unsafe_allow_html=True)
    
    html_table = df.to_html(classes='data-table', index=False, float_format="%.2f")
    st.markdown(html_table, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 6. Active Print Button (100% Working)
    components.html(
        """
        <style>
            /* प्रिंटिंग के समय यह बटन गायब हो जाएगा ताकि कागज पर न छपे */
            @media print { body { display: none !important; } }
        </style>
        <div style="text-align:center; margin-top:20px;">
            <button onclick="window.parent.print()" style="padding:12px 30px; background-color:#1e3a8a; color:white; border:none; border-radius:5px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif;">
                🖨️ Print Final Document
            </button>
        </div>
        """,
        height=80
    )

