import streamlit as st
import database
import pandas as pd
import datetime

st.set_page_config(layout="wide", page_title="Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# प्रीमियम थीम
def apply_premium_theme():
    p_color = db_data.get('_app_settings', {}).get('primary_color', "#1e3a8a")
    st.markdown(f"""<style>.block-container {{ background: rgba(255, 255, 255, 0.7) !important; backdrop-filter: blur(15px); padding: 2rem !important; border-radius: 30px; }} h1 {{ color: {p_color} !important; }}</style>""", unsafe_allow_html=True)

apply_premium_theme()

st.title("📊 Advanced Statement & Payout Ledger")

# सही सेलेक्टबॉक्स
exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger", use_container_width=True):
    rows = []
    s_no = 1
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    
                    payments = [{'type': 'Booking Token', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            # कैलकुलेशन
                            gross = pmt['amt'] * 0.05 # यहाँ अपना स्लैब % लगाएं
                            disc = float(info.get('discount', 0))
                            net_comm = max(0, gross - disc)
                            tds = net_comm * 0.02
                            in_hand = net_comm - tds
                            
                            rows.append({
                                "S.No.": s_no, "Customer": info.get('customer_name'), "Plot": pid, 
                                "Mauza": p_info.get('mauza', 'N/A'), "Received Amt": pmt['amt'], 
                                "Date": pmt['date'], "Gross": gross, "Discount": disc, 
                                "Net Comm": net_comm, "TDS (2%)": tds, "Net In Hand": in_hand
                            })
                            s_no += 1
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # नीचे टोटल दिखाना
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Gross", f"₹ {df['Gross'].sum():,.2f}")
        c2.metric("Total Discount", f"₹ {df['Discount'].sum():,.2f}")
        c3.metric("Total TDS", f"₹ {df['TDS (2%)'].sum():,.2f}")
        c4.metric("🏆 Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
        
        # WhatsApp और Print बटन्स
        cb1, cb2 = st.columns(2)
        if cb1.button("🖨️ Print Statement"): st.write("Print command initiated...")
        if cb2.button("💬 Send to WhatsApp"): st.write("WhatsApp redirecting...")
    else:
        st.info("कोई बुकिंग नहीं मिली।")

