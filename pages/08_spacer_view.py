import streamlit as st
import database
import pandas as pd
import plotly.graph_objects as go

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Satellite Spacer View")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page first.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

# ==========================================
# 🎨 PREMIUM CSS
# ==========================================
st.markdown("""
<style>
.block-container { padding: 1.5rem 3rem !important; background-color: #f8fafc; }
.search-box { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 20px; border-left: 5px solid #1e3a8a; }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Live Satellite Layout & CRM (Spacer View)")
st.markdown("Firstchoice City 2 | Google Satellite Engine | Interactive GPS Overlay")

# --- Fetch Projects ---
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and ('plots' in data)]
if not project_names:
    st.warning("No Projects Found.")
    st.stop()

# --- TOP BAR: SEARCH & FILTERS ---
st.markdown('<div class="search-box">', unsafe_allow_html=True)
col_f1, col_f2 = st.columns([1, 2])
sel_proj = col_f1.selectbox("🏢 Select Project Blueprint", project_names)
search_q = col_f2.text_input("🔍 Smart Search (Find Plot No. or Client Name)")
st.markdown('</div>', unsafe_allow_html=True)

project_data = db_data[sel_proj]
plots = project_data.get('plots', {})
if isinstance(plots, list):
    plots = {str(i): p for i, p in enumerate(plots) if p is not None}

# ==========================================
# 🛰️ REAL SATELLITE MAP DATA INJECTION
# ==========================================
real_plot_areas = {
    1: 2254.63, 2: 2245.16, 3: 2382.61, 4: 2514.47, 5: 1086.63,
    6: 1116.23, 7: 1116.23, 8: 1116.23, 9: 1210.20, 10: 1162.83,
    11: 1181.89, 12: 1181.89, 13: 1181.89, 14: 1019.03, 15: 1055.73,
    16: 1181.89, 17: 1181.89, 18: 1181.89, 19: 1162.83, 20: 1013.22,
    21: 1000.00, 22: 1000.00, 23: 1000.00, 24: 1000.00, 25: 854.88,
    26: 962.52, 27: 1000.00, 28: 1000.00, 29: 1000.00, 30: 1000.00,
    31: 1013.22, 32: 1124.08, 33: 1200.00, 34: 1200.00, 35: 1200.00,
    36: 1200.00, 37: 1200.00, 38: 1200.00, 39: 1200.00, 40: 1200.00,
    41: 1200.00, 42: 2755.15
}

# 🚀 YOUR EXACT SITE GPS COORDINATES
lat_base = 21.056517
lon_base = 79.217038
scale = 0.000015 # GPS Scale multiplier 

fig = go.Figure()

filtered_plots = {}
for pid in range(1, 43):
    str_pid = str(pid)
    pinfo = plots.get(str_pid, {"status": "Available"})
    cname = str(pinfo.get('customer_name', '')).lower()
    if search_q and (search_q.lower() not in str_pid and search_q.lower() not in cname):
        continue
    filtered_plots[str_pid] = pinfo

# Drawing GPS Polygons on Satellite Map
for str_pid, pinfo in filtered_plots.items():
    pid = int(str_pid)
    status = pinfo.get('status', 'Available')
    
    fill_color = "rgba(16, 185, 129, 0.6)" if status == "Available" else "rgba(239, 68, 68, 0.6)"
    border_color = "#059669" if status == "Available" else "#b91c1c"
    
    x0, y0 = 0, 0
    w, h = 18, 25 
    
    if 31 <= pid <= 41: x0, y0 = (pid - 31) * 20, 0
    elif 26 <= pid <= 30: x0, y0 = (pid - 26) * 20, 40
    elif 15 <= pid <= 19: x0, y0 = 110 + (pid - 15) * 20, 40
    elif 20 <= pid <= 25: x0, y0 = (pid - 20) * 20, 70
    elif 10 <= pid <= 14: x0, y0 = 130 + (pid - 10) * 20, 70
    elif 5 <= pid <= 9: x0, y0 = 130 + (pid - 5) * 20, 100
    elif pid in [1, 2, 3, 4, 42]:
        x0, y0 = 240, (pid - 1) * 30
        w, h = 25, 28
        if pid == 42: y0 = 120
    
    x1, y1 = x0 + w, y0 + h
    
    # Mapping to Real Earth Coordinates
    lons = [lon_base + x0*scale, lon_base + x1*scale, lon_base + x1*scale, lon_base + x0*scale, lon_base + x0*scale]
    lats = [lat_base + y0*scale, lat_base + y0*scale, lat_base + y1*scale, lat_base + y1*scale, lat_base + y0*scale]
    
    hover_text = f"<b>Plot P-{pid}</b><br>Status: {status}<br>Area: {real_plot_areas.get(pid, 1116)} Sq.Ft"
    if status != "Available":
        hover_text += f"<br>Client: {pinfo.get('customer_name', 'N/A')}<br>Mob: {pinfo.get('phone', 'N/A')}"

    # Draw Transparent Colored Boxes
    fig.add_trace(go.Scattermapbox(
        lon=lons, lat=lats, mode='lines', fill='toself',
        fillcolor=fill_color, line=dict(color=border_color, width=2),
        hoverinfo='text', hovertext=hover_text, name=f"P-{pid}", showlegend=False
    ))
    
    # Add Plot Numbers
    fig.add_trace(go.Scattermapbox(
        lon=[lon_base + (x0+x1)/2 * scale],
        lat=[lat_base + (y0+y1)/2 * scale],
        mode='text', text=[f"P-{pid}"],
        textfont=dict(color="white", size=12, family="Arial Black"),
        hoverinfo='none', showlegend=False
    ))

# 🚀 INJECTING GOOGLE SATELLITE ENGINE
fig.update_layout(
    mapbox=dict(
        style="white-bg",
        layers=[
            dict(
                sourcetype="raster",
                source=["https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"],
                below="traces"
            )
        ],
        # Centering map EXACTLY on your site
        center=dict(lat=lat_base + 0.001, lon=lon_base + 0.002), 
        zoom=17, # Zooming in perfectly on the site
        pitch=0 
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
    height=700
)

st.plotly_chart(fig, use_container_width=True)

# --- CRM Detailed Section ---
st.write("---")
st.markdown("### 📊 Interactive Mini-CRM Inventory")

cols = st.columns(6)
count = 0
for str_pid, pinfo in filtered_plots.items():
    with cols[count % 6]:
        stat = pinfo.get('status', 'Available')
        if stat == 'Available':
            st.markdown(f"<div style='text-align:center; padding:10px; border:2px solid #10b981; border-radius:8px; margin-bottom:10px; background:#d1fae5;'><b>P-{str_pid}</b><br><span style='font-size:12px; color:#065f46;'>Available</span></div>", unsafe_allow_html=True)
        else:
            c_name = pinfo.get('customer_name', '').split(" ")[0]
            st.markdown(f"<div style='text-align:center; padding:10px; border:2px solid #ef4444; border-radius:8px; margin-bottom:10px; background:#fee2e2;'><b>P-{str_pid}</b><br><span style='font-size:12px; color:#991b1b;'>{c_name}</span></div>", unsafe_allow_html=True)
    count += 1
