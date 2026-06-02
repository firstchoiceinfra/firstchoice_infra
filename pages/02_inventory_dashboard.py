import streamlit as st
import database
import datetime

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Inventory Matrix")

# --- 2. Security Interceptor Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

# --- 3. Database Sync ---
database.init_db()
db_data = st.session_state.db_projects

# Global Theme Sync Setup
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
.block-container {{ background-color: {c_bg} !important; padding: 1.5rem 2.5rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 1.5rem; margin-bottom: 1.5rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; }}
.plot-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(70px, 1fr)); gap: 8px; margin-top: 15px; margin-bottom: 25px; }}
.plot-box {{ padding: 12px 5px; text-align: center; border-radius: 6px; font-weight: 700; color: white; font-size: 13px; box-shadow: inset 0px -3px 0px rgba(0,0,0,0.2); }}
.plot-available {{ background-color: #22c55e; border: 1px solid #16a34a; }}
.plot-booked {{ background-color: #ef4444; border: 1px solid #dc2626; }}
div[data-testid="stForm"] {{ background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📊 Inventory Mapping & Allocation Matrix</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 30px;'>Real-time Interactive Plot Grid and Processing Desk</p>", unsafe_allow_html=True)

# Fetching list of available layout profiles
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)]

if not project_names:
    st.warning("⚠️ No active projects configured in Cloud Dashboard. Please initialize projects via Admin Desk first.")
    st.stop()

# Selector Controls
selected_proj = st.selectbox("🏢 Select Layout Project Blueprint", project_names)
proj_profile = db_data[selected_proj]
plot_registry = proj_profile.get('plots', {})

# Data Safety check mapping structures
if isinstance(plot_registry, list):
    plot_registry = {str(idx): p for idx, p in enumerate(plot_registry) if p is not None}

# Count allocation variables
total_units = len(plot_registry)
booked_units = sum(1 for p in plot_registry.values() if isinstance(p, dict) and p.get('status') == 'Booked')
available_units = total_units - booked_units

# Metrics summary bar
c_m1, c_m2, c_m3 = st.columns(3)
c_m1.metric("Total Plots Registered", total_units)
c_m2.metric("Available Inventory Plots", available_units, delta="Ready to Book")
c_m3.metric("Booked Allocation Units", booked_units, delta="- Closed Deals", delta_color="inverse")

# --- Interactive Layout Map Matrix ---
st.markdown("### 🗺️ Live Graphical Layout Chart Map")
st.markdown("""<div style='display: flex; gap: 15px; font-size:12px; font-weight:600; margin-bottom:10px;'>
    <div style='display:flex; align-items:center; gap:5px;'><div style='width:15px; height:15px; background:#22c55e; border-radius:3px;'></div>Available Plot</div>
    <div style='display:flex; align-items:center; gap:5px;'><div style='width:15px; height:15px; background:#ef4444; border-radius:3px;'></div>Booked Out Unit</div>
</div>""", unsafe_allow_html=True)

grid_html = '<div class="plot-grid">'
sorted_keys = sorted(plot_registry.keys(), key=lambda x: int(x) if x.isdigit() else 9999)

for p_num in sorted_keys:
    p_details = plot_registry[p_num]
    status_style = "plot-booked" if p_details.get('status') == 'Booked' else "plot-available"
    grid_html += f'<div class="plot-box {status_style}">P-{p_num}</div>'
grid_html += '</div>'
st.markdown(grid_html, unsafe_allow_html=True)

# Filter open plots dropdown matrix
vacant_plots_list = [p for p in sorted_keys if plot_registry[p].get('status', 'Available') == 'Available']

# --- Real-time Booking Panel Desk ---
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown("### ✍️ Processing Ledger Form Assignment")

if not vacant_plots_list:
    st.info("🎉 Outstanding! This project's registered inventory has completely sold out!")
else:
    with st.form("plot_booking_form"):
        col_f1, col_f2 = st.columns(2)
        target_plot = col_f1.selectbox("🎯 Choose Target Plot for Reservation", vacant_plots_list)
        client_name = col_f2.text_input("👤 Client Full Name *")
        
        st.markdown("#### 💵 Commercial Payout Audit Specifications")
        col_c1, col_c2, col_c3 = st.columns(3)
        selling_rate = col_c1.number_input("Selling Gross Value (Total Base Rate ₹) *", min_value=0.0, step=10000.0)
        token_amt = col_c2.number_input("Token / Advance Value Collected (₹)", min_value=0.0, step=5000.0)
        discount_val = col_c3.number_input("Authorized Special Adjustments / Discount Given (₹)", min_value=0.0, step=1000.0)
        
        # Smart Role Management Selection Check
        executives_root = db_data.get('executives', {})
        active_exec_list = [k for k, v in executives_root.items() if isinstance(v, dict)]
        
        st.markdown("#### 🔐 Associated Network Attributions")
        # Rule Check: If user is simple executive profile, block cross-profile assignment tampering
        if st.session_state.get('user_role', 'executive') == 'executive':
            logged_name = st.session_state.get('current_user_name', 'Direct')
            st.text_input("Associate Credit Assignment Account", value=logged_name, disabled=True)
            chosen_exec = logged_name
        else:
            # Administrators retain the privilege to freely select or override staff allocations
            chosen_exec = st.selectbox("Associate Account Holder Credit Allocation", ["Direct"] + active_exec_list)

        st.write("")
        process_booking = st.form_submit_button("🔒 Lock Plot Reservation & Log Commercial Ledger", use_container_width=True)

        if process_booking:
            if client_name.strip() == "" or selling_rate <= 0:
                st.error("🚨 Client Name and Selling Gross Value are mandatory to secure inventory!")
            else:
                # Update targeted plot index node directly on database
                st.session_state.db_projects[selected_proj]['plots'][target_plot] = {
                    "status": "Booked",
                    "customer_name": client_name.strip(),
                    "selling_rate": selling_rate,
                    "token_amount": token_amt,
                    "discount": discount_val,
                    "executive_name": chosen_exec,
                    "booking_date": str(datetime.date.today())
                }
                
                with st.spinner("Logging allocation data onto secure ledger..."):
                    if database.save_db_data():
                        st.success(f"🚀 Success! Plot P-{target_plot} successfully locked under client '{client_name.strip()}'!")
                        st.rerun()
