import streamlit as st
import database
import pandas as pd

# Page Configuration
st.set_page_config(layout="wide", page_title="Firstchoice Infra - Final Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# CSS - प्रिंट के लिए सबसे सख्त नियम
st.markdown("""<style>
    /* प्रिंटिंग के दौरान सब कुछ जो .no-print क्लास में है, उसे गायब कर देगा */
    @media print {
        .no-print, [data-testid="stSidebar"], header, footer { display: none !important; }
        body { background: white !important; }
        .a4-container { margin: 0 !important; padding: 0 !important; box-shadow: none !important; }
    }
    .a4-container { background: white; color: black; max-width: 900px; margin: auto; padding: 20px; }
    .header { text-align: center; border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 10px; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 10px; }
    .data-table th, .data-table td { border: 1px solid #000; padding: 4px; text-align: right; }
    .data-table th { background-color: #f0f0f0; text-align: center; }
</style>""", unsafe_allow_html=True)

# इनपुट एरिया को .no-print क्लास में रखा है
st.markdown('<div class="no-print">', unsafe_allow_html=True)
search_exec = st.selectbox("🔎 Select Business Partner", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
col1, col2 = st.columns(2)
start, end = col1.date_input("Start Date"), col2.date_input("End Date")
btn_generate = st.button("🚀 Generate Final Statement")
st.markdown('</div>', unsafe_allow_html=True)

if btn_generate:
    rows = []
    count = 1
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    mapping = {"firstchoice city 2": "Mohadi", "firstchoice city 3": "Pachgaon", "sai samruddhi": "Temsana"}
    
    for project_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            mauja = p_info.get('mauja', mapping.get(project_name.lower(), "Nagpur"))
            comp_rate = float(p_info.get('base_rate', 700))
            for pid, info in (p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots'])):
                info = info if isinstance(info, dict) else {}
                if str(info.get('executive_name', '')).strip().lower() == str(search_exec).strip().lower():
                    payments = [{'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    if 'partial_payments' in info: payments.extend([{'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')} for pmt in info['partial_payments']])
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = (pmt['amt'] * p_pct) / 100
                            discount = (pmt['amt'] * (float(info.get('discount', 0)) / comp_rate)) if comp_rate > 0 else 0
                            net_comm = gross - discount
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            rows.append({"S.No.": count, "Mauja": mauja, "Project": project_name, "Plot": pid, "Customer": info.get('customer_name', 'N/A'), "Received": pmt['amt'], "Date": pmt['date'], "Gross": gross, "Discount": discount, "Net Comm": net_comm, "TDS": tds, "In Hand": in_hand})
                            count += 1
    df = pd.DataFrame(rows)
    totals = {"S.No.": "TOTAL", "Received": df['Received'].sum(), "Gross": df['Gross'].sum(), "Discount": df['Discount'].sum(), "Net Comm": df['Net Comm'].sum(), "TDS": df['TDS'].sum(), "In Hand": df['In Hand'].sum()}
    st.session_state.df_view = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)
    st.session_state.meta = {"exec": search_exec, "start": start, "end": end}

if 'df_view' in st.session_state and st.session_state.df_view is not None:
    df = st.session_state.df_view
    meta = st.session_state.meta
    st.markdown("<div class='a4-container'>", unsafe_allow_html=True)
    st.markdown(f"""<div class='header'>
        <h1 style='margin:0;'>FIRSTCHOICE INFRA</h1>
        <p><i>Symbol Of Trust... | Plot No. 06, Shop No.106, Motilal Nagar, Nagpur-440034</i></p>
    </div>
    <h3 style='text-align:center;'>Executive Commission Statement</h3>
    <div style='margin-bottom:10px;'><b>Partner:</b> {meta['exec']} &nbsp; | &nbsp; <b>Period:</b> {meta['start']} to {meta['end']}</div>""", unsafe_allow_html=True)
    st.markdown(df.to_html(classes='data-table', index=False, float_format="%.2f"), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown('<div class="no-print" style="text-align:center; margin-top:20px;"><button onclick="window.print()">🖨️ Print Final</button></div>', unsafe_allow_html=True)

