import streamlit as st
import database
import pandas as pd

# 1. Config & DB
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS - 'Manage App' और बाकी UI हटाने के लिए
st.markdown("""<style>
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton, .stSelectbox, .stDateInput, .stToolbar, .stDecoration { 
            display: none !important; 
        }
        /* 'Manage app' बटन को प्रिंट से जबरदस्ती हटाएं */
        #manage-app, .manage-app, .css-1rs1eb { display: none !important; }
        
        body { background: white !important; }
        .a4-container { display: block !important; width: 100% !important; margin: 0 !important; padding: 10px !important; }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; padding: 20px; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 9px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 4px; }
</style>""", unsafe_allow_html=True)

# 3. Inputs
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Official Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation (सही कैलकुलेशन लॉजिक)
if btn_generate:
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            db_mauja = p_info.get('mauja', '')
            mauja = db_mauja if db_mauja and db_mauja.lower() != project_name.lower() else mapping.get(project_name.lower(), "Nagpur")
            comp_rate = float(p_info.get('base_rate', 700))
            
            # यहाँ एंट्री न छूटे इसके लिए सभी plots को चेक कर रहे हैं
            plots_data = p_info['plots']
            plot_items = plots_data.items() if isinstance(plots_data, dict) else enumerate(plots_data)
            
            for pid, info in plot_items:
                info = info if isinstance(info, dict) else {}
                if str(info.get('executive_name', '')).strip().lower() == str(search_exec).strip().lower():
                    # सभी पेमेंट एंट्रीज निकालें
                    payments = [{'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    if 'partial_payments' in info and isinstance(info['partial_payments'], list):
                        payments.extend([{'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in info['partial_payments']])
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            discount = (pmt['amt'] * (float(info.get('discount', 0)) / comp_rate)) if comp_rate > 0 else 0
                            net_comm = gross - discount # डिस्काउंट के बाद का नेट कमीशन
                            tds = net_comm * 0.02 # 2% TDS
                            in_hand = net_comm - tds # इन हैंड
                            
                            rows.append({
                                "S.No.": count, "Mauja": mauja, "Project": project_name, "Customer": info.get('customer_name', 'N/A'), 
                                "Plot": pid, "Received": pmt['amt'], "Gross": gross, "Discount": discount, 
                                "Net Comm": net_comm, "TDS": tds, "In Hand": in_hand
                            })
                            count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown("<h3>FIRSTCHOICE INFRA | Executive Commission Statement</h3>", unsafe_allow_html=True)
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    
    st.markdown(f"""<div style='margin-top:15px; font-weight:bold;'>
        Total Gross: ₹{df['Gross'].sum():,.2f} | Total In Hand: ₹{df['In Hand'].sum():,.2f}
    </div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="no-print" style="text-align:center;"><button onclick="window.print()">🖨️ Print Final</button></div>', unsafe_allow_html=True)

