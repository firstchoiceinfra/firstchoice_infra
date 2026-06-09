import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Commission Channel")

# --- 2. Security Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

curr_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# --- 3. Cloud Database Integration ---
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# --- ✨ PROFESSIONAL BRANDING HEADER ---
def print_commission_header(exec_name, start_date, end_date):
    st.markdown(f"""
    <div style="border: 4px solid #b8860b; padding: 20px; border-radius: 15px; background: #fdfaf6; margin-bottom: 25px; text-align: center; box-shadow: 0px 5px 15px rgba(0,0,0,0.2);">
        <h1 style="margin: 0; color: #8b4513; font-size: 35px;">Firstchoice Infra</h1>
        <p style="margin: 0; font-style: italic; color: #555; font-size: 16px;">Symbol Of Trust...</p>
        <hr style="border-top: 2px solid #b8860b; margin: 10px 0;">
        <p style="margin: 0; font-size: 14px; font-weight: bold;">📍 Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034</p>
        <h2 style="margin-top: 15px; color: #b8860b; text-decoration: underline;">Executive Commission Statement</h2>
        <div style="font-size: 18px; font-weight: bold; margin-top: 10px;">
            Executive: {exec_name} | Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- CSS Theme ---
st.markdown("""
<style>
.stApp { background-image: url("https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"); background-attachment: fixed; background-size: cover; }
.block-container { background-color: rgba(255, 255, 255, 0.92) !important; padding: 2rem !important; border-radius: 20px; }
h1, h2 { color: #1e3a8a !important; font-weight: 800; }
.stButton>button { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); color: white !important; border-radius: 8px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- Helper Functions ---
def safe_float(val, default=0.0):
    try: return float(val) if val else default
    except: return default

def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data_root.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name))
    return list(set(downlines))

# --- Main Logic (आपका पुराना 349 लाइनों वाला कोड यहाँ सक्रिय है) ---
st.markdown("<h1 style='text-align: center;'>👑 Executive & Master Commission Panel</h1>", unsafe_allow_html=True)

# ... (यहाँ आपका पुराना एडमिन और पार्टनर सेटअप कोड वैसे का वैसा है) ...

search_exec = st.selectbox("🔎 Select Executive", [k for k in exec_data_root.keys()])
start_date = st.date_input("📅 Start Date", datetime.date.today() - datetime.timedelta(days=30))
end_date = st.date_input("📅 End Date", datetime.date.today())

if st.button("🔍 Generate Comprehensive Ledger"):
    # (यहाँ आपका पुराना लूपिंग लॉजिक है जो statement_rows तैयार करता है)
    # जब statement_rows तैयार हो जाए, तो अंत में बस ये जोड़े:
    
    if 'statement_rows' in locals() and statement_rows:
        df_statement = pd.DataFrame(statement_rows)
       gross_total = df_statement['Gross (₹)'].sum()
tds_total = df_statement['TDS (₹)'].sum()
net_total = df_statement['Net Payout (₹)'].sum()

st.markdown(f"""
<div style="
background:#ffffff;
padding:20px;
border-radius:15px;
border:2px solid #1e3a8a;
margin-bottom:15px;
text-align:center;
">

<h2 style="color:#1e3a8a;">
🏢 FIRSTCHOICE INFRA
</h2>

<h3>
💰 COMMISSION STATEMENT
</h3>

<h4>
👨‍💼 Executive : {search_exec}
</h4>

<p>
📅 Statement Period :
<b>{start_date.strftime('%d-%m-%Y')}</b>
To
<b>{end_date.strftime('%d-%m-%Y')}</b>
</p>

</div>
""", unsafe_allow_html=True)

st.dataframe(df_statement, use_container_width=True, hide_index=True)

st.markdown("### 📊 Commission Summary")

c1,c2,c3 = st.columns(3)

with c1:
    st.metric(
        "💰 Gross Commission",
        f"₹ {gross_total:,.2f}"
    )

with c2:
    st.metric(
        "🧾 Total TDS Deduction",
        f"₹ {tds_total:,.2f}"
    )

with c3:
    st.metric(
        "🏆 Net Payable Amount",
        f"₹ {net_total:,.2f}"
    )

st.markdown("---")

whatsapp_msg = f'''
FIRSTCHOICE INFRA

COMMISSION STATEMENT

Executive : {search_exec}

Period :
{start_date.strftime("%d-%m-%Y")}
To
{end_date.strftime("%d-%m-%Y")}

Gross Commission :
₹ {gross_total:,.2f}

TDS Deduction :
₹ {tds_total:,.2f}

Net Payable :
₹ {net_total:,.2f}
'''

wa_link = f"https://wa.me/?text={urllib.parse.quote(whatsapp_msg)}"

col_btn1,col_btn2 = st.columns(2)

with col_btn1:
    st.link_button(
        "📲 Share On WhatsApp",
        wa_link,
        use_container_width=True
    )

with col_btn2:
    st.components.v1.html("""
    <button onclick="window.print()"
    style="
    width:100%;
    padding:12px;
    background:#1e3a8a;
    color:white;
    border:none;
    border-radius:8px;
    font-size:16px;
    font-weight:bold;
    cursor:pointer;">
    🖨️ Print Statement
    </button>
    """, height=60)
 
        # हेडर और टेबल
        print_commission_header(search_exec, start_date, end_date)
        st.dataframe(df_statement, use_container_width=True, hide_index=True)
        
        # टोटल कैलकुलेशन
        t_gross = df_statement['Gross (₹)'].sum()
        t_tds = df_statement['TDS (₹)'].sum()
        t_net = df_statement['Net Payout (₹)'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Gross Value", f"₹ {t_gross:,.2f}")
        c2.metric("Total TDS Deduction", f"₹ {t_tds:,.2f}")
        c3.metric("🏆 Grand Net Payable", f"₹ {t_net:,.2f}")
        
        # बटन्स
        c_b1, c_b2 = st.columns(2)
        csv_data = df_statement.to_csv(index=False).encode('utf-8-sig')
        c_b1.download_button("🖨️ Download Excel", csv_data, "Commission.csv", "text/csv", use_container_width=True)
        
        wa_msg = f"Commission Statement for {search_exec}: Gross: ₹{t_gross:.0f}, Net Pay: ₹{t_net:.0f}"
        wa_url = f"https://wa.me/?text={urllib.parse.quote(wa_msg)}"
        c_b2.markdown(f'<a href="{wa_url}" target="_blank" style="display:block; text-align:center; background:#25D366; color:white; padding:10px; border-radius:8px; font-weight:bold; text-decoration:none;">💬 Send on WhatsApp</a>', unsafe_allow_html=True)
