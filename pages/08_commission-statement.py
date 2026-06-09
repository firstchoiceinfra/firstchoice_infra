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

exec_list = [k for k, v in exec_data_root.items() if isinstance(v, dict)]
search_exec = st.selectbox("🔎 Select Executive", exec_list)
col1, col2 = st.columns(2)
start = col1.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end = col2.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger", use_container_width=True):
    rows = []
    s_no = 1
    
    # पार्टनर स्लैब
    p_profile = exec_data_root.get(search_exec, {})
    p_pct = float(p_profile.get('percentage_exec', 0))
    
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    
                    # प्लॉट की डिटेल्स
                    comp_rate = float(info.get('company_rate', p_info.get('base_rate', 700)))
                    discount = float(info.get('discount', 0)) # प्रति sqft डिस्काउंट
                    
                    # डिस्काउंट का % प्रभाव
                    disc_impact = (discount / comp_rate) * 100 if comp_rate > 0 else 0
                    net_slab = max(0, p_pct - disc_impact)
                    
                    # भुगतान
                    payments = [{'type': 'Booking Token', 'amt': float(info.get('token_amount', 0)), 'date': info.get('booking_date', '')}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0)), 'date': pmt.get('date', '')})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            # कैलकुलेशन
                            gross = (pmt['amt'] * net_slab) / 100
                            tds = gross * 0.02
                            in_hand = gross - tds
                            
                            rows.append({
                                "S.No.": s_no, "Customer": info.get('customer_name'), "Plot": pid, 
                                "Mauza": p_info.get('mauza', 'N/A'), "Received Amt": pmt['amt'], 
                                "Date": pmt['date'], "Gross": round(gross, 2), 
                                "Discount Impact": f"{disc_impact:.2f}%", 
                                "TDS (2%)": round(tds, 2), "Net In Hand": round(in_hand, 2)
                            })
                            s_no += 1
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        
        # टोटल कैलकुलेशन
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Gross", f"₹ {df['Gross'].sum():,.2f}")
        c2.metric("Total Discount Impact", f"{df['Discount Impact'].str.rstrip('%').astype(float).sum():.2f}%")
        c3.metric("Total TDS", f"₹ {df['TDS (2%)'].sum():,.2f}")
        c4.metric("🏆 Net In Hand", f"₹ {df['Net In Hand'].sum():,.2f}")
        
        # एक्सपोर्ट और WhatsApp
        cb1, cb2 = st.columns(2)
        if cb1.button("🖨️ Print Statement"): st.write("Print mode enabled...")
        if cb2.button("💬 Send to WhatsApp"): st.write("WhatsApp share link ready...")
    else:
        st.info("इस एग्जीक्यूटिव के नाम पर कोई बुकिंग रिकॉर्ड नहीं मिला।")

