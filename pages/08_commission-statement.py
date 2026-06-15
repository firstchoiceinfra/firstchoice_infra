import streamlit as st
import database
import pandas as pd

# 1. Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. CSS (प्रिंट के लिए फाइनल क्लीनअप)
st.markdown("""<style>
    /* ये प्रिंटिंग के समय बाकी सब कुछ गायब कर देगा */
    @media print {
        [data-testid="stSidebar"], .no-print, header, footer, .stButton, .stSelectbox, .stDateInput { 
            display: none !important; 
        }
        body, html { background: white !important; }
        
        /* पूरा डेटा पेज पर सही से आए इसके लिए */
        .a4-container { 
            display: block !important; 
            width: 100% !important; 
            margin: 0 !important; 
            padding: 20px !important;
            position: absolute !important;
            top: 0 !important;
            left: 0 !important;
        }
    }
    .a4-container { background: white; color: black; max-width: 1000px; margin: auto; }
    .data-table { width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 10px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 5px; text-align: left; }
    .data-table th { background-color: #f0f0f0; }
</style>""", unsafe_allow_html=True)

# 3. Inputs (प्रिंट में नहीं दिखेंगे)
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Statement")
st.markdown('</div>', unsafe_allow_html=True)

# 4. Calculation
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
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if info.get('executive_name', '').lower() == search_exec.lower() and info.get('status', '').lower() == 'booked':
                    amt = float(info.get('token_amount', 0))
                    if amt > 0:
                        gross = (amt * p_pct) / 100
                        rows.append({"S.No.": count, "Mauja": mauja, "Project": project_name, "Customer": info.get('customer_name', 'N/A'), "Plot": pid, "Received": amt, "Date": info.get('booking_date', ''), "Gross": gross, "Net In Hand": gross * 0.98})
                        count += 1
    st.session_state.df_view = pd.DataFrame(rows) if rows else None
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

# 5. Display (A4 Container)
if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"<h2>FIRSTCHOICE INFRA</h2><p>Partner: {meta['exec']} | Period: {meta['start']} to {meta['end']}</p>", unsafe_allow_html=True)
    st.markdown(df.to_html(classes='data-table', index=False), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # प्रिंट बटन
    st.markdown('<div class="no-print" style="text-align:center;"><button onclick="window.print()" style="padding:10px 20px;">🖨️ Print Statement</button></div>', unsafe_allow_html=True)

