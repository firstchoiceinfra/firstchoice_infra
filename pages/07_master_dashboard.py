import streamlit as st
import database
import pandas as pd
import datetime

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Master Dashboard")

# --- 2. SECURITY INTERCEPTOR CHECK (Strict Admin Lock) ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

# Absolute protection layer - Stops non-admin roles instantly
if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 Security Alert: Only authorized Administrators can access the Master Executive Dashboard!")
    st.stop()

# --- 3. Database Initialization ---
database.init_db()
db_data = st.session_state.db_projects

# Global Theme Synchronization Logic
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255, 255, 255, 0.92)"

if '_app_settings' in db_data:
    global_settings = db_data['_app_settings']
    bg_url = global_settings.get('bg_url', bg_url)
    p_color = global_settings.get('primary_color', p_color)
    s_color = global_settings.get('secondary_color', s_color)
    c_bg = global_settings.get('card_bg', c_bg)

st.markdown(f"""
<style>
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stMetric {{ background-color: #ffffff; border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 4px solid {p_color}; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📈 Master Executive Dashboard (Admin Secured)</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 30px;'>Restricted Access Terminal - Live Financial Intelligence & Revenue Stream Metrics</p>", unsafe_allow_html=True)

# --- Core Data Aggregation Engine ---
total_bookings = 0
total_sales_value = 0.0
total_token_collected = 0.0
total_emi_collected = 0.0
project_booking_counts = {}
daily_collection_map = {}

for p_name, p_info in db_data.items():
    if isinstance(p_info, dict) and 'plots' in p_info:
        project_booking_counts[p_name] = 0
        plots = p_info['plots']
        if isinstance(plots, list):
            plots = {str(idx): p for idx, p in enumerate(plots) if p is not None}
        
        for p_id, p_data in plots.items():
            if isinstance(p_data, dict) and p_data.get('status') == 'Booked':
                total_bookings += 1
                project_booking_counts[p_name] += 1
                
                selling_rate = float(p_data.get('selling_rate', 0.0))
                token_amt = float(p_data.get('token_amount', 0.0))
                
                total_sales_value += selling_rate
                total_token_collected += token_amt
                
                t_date = p_data.get('booking_date', str(datetime.date.today()))
                daily_collection_map[t_date] = daily_collection_map.get(t_date, 0.0) + token_amt
                
                partials = p_data.get('partial_payments', [])
                for pmt in partials:
                    pmt_amt = float(pmt.get('amount', 0.0))
                    total_emi_collected += pmt_amt
                    pmt_date = pmt.get('date', str(datetime.date.today()))
                    daily_collection_map[pmt_date] = daily_collection_map.get(pmt_date, 0.0) + pmt_amt

total_overall_collection = total_token_collected + total_emi_collected
total_site_visits = len(db_data.get('site_visits', []))

# --- Top Level Metrics Grid ---
st.markdown("### 📊 Key Performance Indicators (KPIs)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Total Booked Plots", f"{total_bookings} Units")
with c2:
    st.metric("Gross Sales Booked", f"₹ {total_sales_value:,.2f}")
with c3:
    st.metric("Total Cash/Bank Collection", f"₹ {total_overall_collection:,.2f}", delta=f"EMI: ₹{total_emi_collected:,.2f}")
with c4:
    st.metric("Total Site Visits Logged", f"{total_site_visits} Tours")

st.write("---")

# --- Charts & Graphs Visual Layer ---
col_g1, col_g2 = st.columns(2)

with col_g1:
    st.markdown("#### 🏢 Sales Distribution per Project")
    if project_booking_counts and sum(project_booking_counts.values()) > 0:
        df_proj = pd.DataFrame(list(project_booking_counts.items()), columns=["Project", "Bookings"])
        st.bar_chart(df_proj.set_index("Project"))
    else:
        st.info("No active plot bookings recorded yet to map graphical distribution charts.")

with col_g2:
    st.markdown("#### 📅 Timeline Collection Velocity")
    if daily_collection_map:
        sorted_dates = sorted(daily_collection_map.keys())
        df_coll = pd.DataFrame([{ "Date": d, "Amount (₹)": daily_collection_map[d] } for d in sorted_dates])
        st.line_chart(df_coll.set_index("Date"))
    else:
        st.info("No incoming accounting ledger cashflows tracked yet to plot velocity graphs.")

st.write("---")

# --- Detailed Ledger Insights Table ---
st.markdown("### 📋 Executive Project Health Summary Ledger")
project_summary_rows = []
for p_name, p_info in db_data.items():
    if isinstance(p_info, dict) and 'plots' in p_info:
        plots = p_info['plots']
        if isinstance(plots, list):
            plots = {str(idx): p for idx, p in enumerate(plots) if p is not None}
        
        p_booked = 0
        p_sales = 0.0
        p_collected = 0.0
        
        for p_id, p_data in plots.items():
            if isinstance(p_data, dict) and p_data.get('status') == 'Booked':
                p_booked += 1
                p_sales += float(p_data.get('selling_rate', 0.0))
                p_collected += float(p_data.get('token_amount', 0.0))
                for pmt in p_data.get('partial_payments', []):
                    p_collected += float(pmt.get('amount', 0.0))
                    
        project_summary_rows.append({
            "Project Identity": p_name,
            "Total Bookings": p_booked,
            "Gross Value (₹)": p_sales,
            "Total Collected (₹)": p_collected,
            "Outstanding Due (₹)": max(0.0, p_sales - p_collected)
        })

if project_summary_rows:
    df_summary = pd.DataFrame(project_summary_rows)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
else:
    st.caption("No corporate database infrastructure templates located inside memory modules.")
