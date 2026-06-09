import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(layout="wide", page_title="Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# Global Theme Sync Function
def apply_theme():
    settings = db_data.get('_app_settings', {})
    bg_url = settings.get('bg_url', "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop")
    p_color = settings.get('primary_color', "#1e3a8a")
    st.markdown(f"""<style>.stApp {{background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover;}} .block-container {{background: rgba(255, 255, 255, 0.95) !important; padding: 2rem; border-radius: 20px;}} h1, h2 {{color: {p_color} !important;}}</style>""", unsafe_allow_html=True)

apply_theme()

st.title("📊 Advanced Statement & Payout Ledger")
search_exec = st.selectbox("🔎 Select Executive", [k for k, v in exec_data_root.items() if isinstance(v, dict)])
start, end = st.columns(2)
start_date = start.date_input("Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = end.date_input("End Date", datetime.date.today())

if st.button("🔍 Generate Ledger", use_container_width=True):
    rows = []
    for p_name, p_info in db_data.items():
        if isinstance(p_info, dict) and 'plots' in p_info:
            for pid, info in p_info['plots'].items() if isinstance(p_info['plots'], dict) else enumerate(p_info['plots']):
                info = info if isinstance(info, dict) else {}
                if str(info.get('status', '')).lower() == 'booked' and info.get('executive_name', '').lower() == search_exec.lower():
                    # टोकन और इंस्टॉलमेंट्स को इकट्ठा करें
                    payments = [{'type': 'Booking Token', 'amt': float(info.get('token_amount', 0))}]
                    for pmt in info.get('partial_payments', []):
                        payments.append({'type': pmt.get('remarks', 'Installment'), 'amt': float(pmt.get('amount', 0))})
                    
                    for pmt in payments:
                        if pmt['amt'] > 0:
                            gross = pmt['amt'] * 0.05 # अपना स्लैब लॉजिक यहाँ रखें
                            rows.append({"Client": info.get('customer_name'), "Type": pmt['type'], "Paid Amt (₹)": pmt['amt'], "Gross (₹)": gross, "Net Payout (₹)": gross * 0.98})
    
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True)
        st.metric("🏆 Grand Net Payable", f"₹ {df['Net Payout (₹)'].sum():,.2f}")
    else:
        st.info("कोई बुकिंग नहीं मिली।")

