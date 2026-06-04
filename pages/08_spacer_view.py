import streamlit as st
import database
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Spacer View Dashboard")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

# ==========================================
# 🎨 PREMIUM CSS (Spacer Style)
# ==========================================
st.markdown("""
<style>
.block-container { padding: 1.5rem 3rem !important; background-color: #f8fafc; }
.search-box { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #1e3a8a; }
.crm-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 5px solid #3b82f6; }
.stat-box { text-align: center; padding: 15px; background: white; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
.status-avail { color: #10b981; font-weight: bold; background: #d1fae5; padding: 5px 10px; border-radius: 8px; }
.status-booked { color: #ef4444; font-weight: bold; background: #fee2e2; padding: 5px 10px; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Dynamic Layout & CRM (Spacer View)")
st.markdown("Interactive Satellite Map | Global Plot Search | Live CRM")

# --- Fetch Projects ---
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data)]
if not project_names:
    st.warning("No Projects Found.")
    st.stop()

# --- TOP BAR: SEARCH & FILTERS ---
st.markdown('<div class="search-box">', unsafe_allow_html=True)
col_f1, col_f2, col_f3 = st.columns([1, 1, 1.5])
sel_proj = col_f1.selectbox("🏢 Select Project", project_names)
status_filter = col_f2.selectbox("📊 Filter Status", ["All Plots", "Available", "Booked"])
search_q = col_f3.text_input("🔍 Smart Search (Enter Plot No. or Client Name)")
st.markdown('</div>', unsafe_allow_html=True)

project_data = db_data[sel_proj]
plots = project_data.get('plots', {})
if isinstance(plots, list):
    plots = {str(i): p for i, p in enumerate(plots) if p is not None}

# --- MIDDLE SECTION: SATELLITE MAP & CRM ---
col_map, col_crm = st.columns([2, 1.2])

with col_map:
    st.markdown("### 🛰️ Live Satellite Layout View")
    # (नागपुर मोहड़ी/उमरेड रोड का डिफ़ॉल्ट लोकेशन)
    m = folium.Map(location=[20.9320, 79.3140], zoom_start=15, tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}', attr='Google Satellite')
    
    # Adding Dummy Plot Markers on Map for demonstration
    # (भविष्य में हम इसे असली KML या GPS से जोड़ सकते हैं)
    for plot_id, p_info in plots.items():
        status = p_info.get('status', 'Available')
        color = 'green' if status == 'Available' else 'red'
        
        # Adding some random offset just to show pins on map
        import random
        lat_offset = random.uniform(-0.005, 0.005)
        lon_offset = random.uniform(-0.005, 0.005)
        
        folium.Marker(
            [20.9320 + lat_offset, 79.3140 + lon_offset],
            popup=f"Plot: {plot_id} | Status: {status}",
            tooltip=f"P-{plot_id}",
            icon=folium.Icon(color=color, icon='home')
        ).add_to(m)

    st_folium(m, width=700, height=500)

with col_crm:
    st.markdown("### 👤 Dynamic Plot Details (CRM)")
    
    # Filtering logic based on search
    selected_plot_id = None
    for pid, pinfo in plots.items():
        c_name = str(pinfo.get('customer_name', '')).lower()
        if search_q:
            if search_q.lower() in pid.lower() or search_q.lower() in c_name:
                selected_plot_id = pid
                break
    
    if not selected_plot_id and plots:
        selected_plot_id = list(plots.keys())[0] # Default to first plot
        
    if selected_plot_id:
        p_data = plots[selected_plot_id]
        status = p_data.get('status', 'Available')
        
        st.markdown('<div class="crm-card">', unsafe_allow_html=True)
        st.subheader(f"🏠 Plot No: P-{selected_plot_id}")
        
        if status == "Available":
            st.markdown('<span class="status-avail">✅ AVAILABLE INVENTORY</span>', unsafe_allow_html=True)
            st.write("---")
            st.write(f"📐 **Area:** {p_data.get('plot_area', p_data.get('area', '1116'))} Sq.Ft")
            st.write(f"🏢 **Base Rate:** ₹ {p_data.get('company_rate', p_data.get('base_rate', '700'))}/-")
            st.button("📝 Book This Plot Now", type="primary", use_container_width=True)
            
        else:
            st.markdown('<span class="status-booked">🛑 BOOKED / SOLD</span>', unsafe_allow_html=True)
            st.write("---")
            st.write(f"👤 **Client Name:** {p_data.get('customer_name', 'N/A')}")
            st.write(f"📱 **Mobile No:** {p_data.get('phone', 'N/A')}")
            st.write(f"👨‍💼 **Executive:** {p_data.get('executive_name', 'N/A')}")
            
            # Money details
            total_val = float(p_data.get('selling_rate', 0)) * float(p_data.get('plot_area', 1116))
            if total_val == 0: total_val = float(p_data.get('total_value', 191000))
            
            t_paid = float(p_data.get('token_amount', 0)) + sum(float(pmt.get('amount', 0)) for pmt in p_data.get('partial_payments', []))
            
            st.write("---")
            st.write(f"💰 **Total Value:** ₹ {total_val:,.2f}")
            st.write(f"✅ **Total Paid:** ₹ {t_paid:,.2f}")
            st.error(f"⚠️ **Pending Due:** ₹ {max(0, total_val - t_paid):,.2f}")
            
            st.button("💬 Send WhatsApp Reminder", type="primary", use_container_width=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

# --- BOTTOM SECTION: PLOT GALLERY ---
st.write("---")
st.markdown("### 🖼️ Project Plot Gallery")

# Filter plots
filtered_plots = {}
for pid, pinfo in plots.items():
    stat = pinfo.get('status', 'Available')
    cname = str(pinfo.get('customer_name', '')).lower()
    
    if status_filter != "All Plots" and stat != status_filter: continue
    if search_q and (search_q.lower() not in pid.lower() and search_q.lower() not in cname): continue
    filtered_plots[pid] = pinfo

cols = st.columns(6)
for i, (pid, pinfo) in enumerate(filtered_plots.items()):
    with cols[i % 6]:
        stat = pinfo.get('status', 'Available')
        if stat == 'Available':
            st.markdown(f"<div class='stat-box' style='border-bottom: 4px solid #10b981;'><b>P-{pid}</b><br><span style='font-size:12px; color:#10b981;'>Available</span></div><br>", unsafe_allow_html=True)
        else:
            c_name = pinfo.get('customer_name', '').split(" ")[0]
            st.markdown(f"<div class='stat-box' style='border-bottom: 4px solid #ef4444;'><b>P-{pid}</b><br><span style='font-size:12px; color:#ef4444;'>{c_name}</span></div><br>", unsafe_allow_html=True)
