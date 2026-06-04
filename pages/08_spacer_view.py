import streamlit as st
import database
import pandas as pd
import plotly.graph_objects as go

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Spacer View Dashboard")

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
.crm-card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); border-top: 5px solid #3b82f6; }
</style>
""", unsafe_allow_html=True)

st.title("🌍 Interactive Layout & CRM (Spacer View)")
st.markdown("Firstchoice City 2 Real Layout Matrix | Zoom & Pan | Hover for Details")

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
# 🗺️ REAL MAP DATA INJECTION (FIRSTCHOICE CITY 2)
# ==========================================
# आपके नक्शे के हिसाब से हर प्लॉट का असली Sq.Ft एरिया:
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

st.markdown("### 🗺️ Master Layout Plan (Drag to Pan, Scroll to Zoom)")

fig = go.Figure()

# Filter Plots for Search
filtered_plots = {}
# Forcing 42 plots structure for display
for pid in range(1, 43):
    str_pid = str(pid)
    pinfo = plots.get(str_pid, {"status": "Available"})
    cname = str(pinfo.get('customer_name', '')).lower()
    
    if search_q and (search_q.lower() not in str_pid and search_q.lower() not in cname):
        continue
    filtered_plots[str_pid] = pinfo

# Drawing the Plots resembling physical blocks
for str_pid, pinfo in filtered_plots.items():
    pid = int(str_pid)
    status = pinfo.get('status', 'Available')
    
    # Colors: Spacer style (Green = Available, Red = Booked)
    fill_color = "rgba(16, 185, 129, 0.75)" if status == "Available" else "rgba(239, 68, 68, 0.75)"
    border_color = "#059669" if status == "Available" else "#b91c1c"
    
    # 📐 Custom Grid Placement (Mimicking your layout structure)
    x0, y0 = 0, 0
    w, h = 18, 25 # Default width and height
    
    # Block A (Bottom Row: 31 to 41)
    if 31 <= pid <= 41:
        x0 = (pid - 31) * 20
        y0 = 0
    # Block B (Middle Bottom: 26 to 30)
    elif 26 <= pid <= 30:
        x0 = (pid - 26) * 20
        y0 = 40 # Road Gap
    # Block C (Middle Bottom Right: 15 to 19)
    elif 15 <= pid <= 19:
        x0 = 110 + (pid - 15) * 20
        y0 = 40
    # Block D (Middle Top: 20 to 25)
    elif 20 <= pid <= 25:
        x0 = (pid - 20) * 20
        y0 = 70
    # Block E (Middle Top Right: 10 to 14)
    elif 10 <= pid <= 14:
        x0 = 130 + (pid - 10) * 20
        y0 = 70
    # Block F (Top Right: 5 to 9)
    elif 5 <= pid <= 9:
        x0 = 130 + (pid - 5) * 20
        y0 = 100
    # Block G (Far Right Irregular: 1 to 4, 42)
    elif pid in [1, 2, 3, 4, 42]:
        x0 = 240
        y0 = (pid - 1) * 30
        w, h = 25, 28
        if pid == 42: y0 = 120
    
    x1 = x0 + w
    y1 = y0 + h
    
    # Fetch real area from dictionary
    actual_area = real_plot_areas.get(pid, 1116)
    
    # 📌 Hover Text Details (CRM Mini-Card)
    hover_text = f"<b>Plot P-{pid}</b><br>Status: {status}<br>Actual Area: {actual_area} Sq.Ft"
    if status != "Available":
        hover_text += f"<br><br><b>Client:</b> {pinfo.get('customer_name', 'N/A')}"
        hover_text += f"<br><b>Mobile:</b> {pinfo.get('phone', 'N/A')}"
        hover_text += f"<br><b>Executive:</b> {pinfo.get('executive_name', 'Direct')}"

    # Draw Plot Box
    fig.add_shape(
        type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
        fillcolor=fill_color, line=dict(color=border_color, width=2)
    )
    
    # Add Plot Number
    fig.add_annotation(
        x=(x0+x1)/2, y=(y0+y1)/2,
        text=f"<b>P-{pid}</b>", showarrow=False,
        font=dict(color="white", size=14)
    )
    
    # Add Invisible Hover Tracker
    fig.add_trace(go.Scatter(
        x=[(x0+x1)/2], y=[(y0+y1)/2],
        mode="markers", marker=dict(size=40, color="rgba(0,0,0,0)"),
        hoverinfo="text", hovertext=hover_text, showlegend=False
    ))

# Render Map Background (Light Grey for layout feel)
fig.update_layout(
    xaxis=dict(visible=False, showgrid=False, zeroline=False),
    yaxis=dict(visible=False, showgrid=False, zeroline=False),
    plot_bgcolor="#e2e8f0", paper_bgcolor="#f8fafc",
    margin=dict(l=10, r=10, t=10, b=10), height=650,
    hovermode="closest", dragmode="pan"
)

st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

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
