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
st.markdown("Dynamic Plot Viewer | Zoom & Pan | Hover for Details")

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
# 🗺️ PLOTLY INTERACTIVE LAYOUT ENGINE
# ==========================================
st.markdown("### 🗺️ Master Layout Plan (Drag to Pan, Scroll to Zoom)")

fig = go.Figure()

# Filter Plots for Search
filtered_plots = {}
for pid, pinfo in plots.items():
    cname = str(pinfo.get('customer_name', '')).lower()
    if search_q and (search_q.lower() not in pid.lower() and search_q.lower() not in cname):
        continue
    filtered_plots[pid] = pinfo

# Drawing the Plots on a 2D Digital Canvas
for i, (pid, pinfo) in enumerate(filtered_plots.items()):
    status = pinfo.get('status', 'Available')
    
    # Colors: Green for Available, Red for Booked
    fill_color = "rgba(16, 185, 129, 0.7)" if status == "Available" else "rgba(239, 68, 68, 0.7)"
    border_color = "#059669" if status == "Available" else "#b91c1c"
    
    # Mathematical Grid Logic (10 Plots per row, with Street Gaps)
    row = i // 10
    col = i % 10
    
    # Coordinates for Rectangle Box
    x0 = col * 20
    x1 = x0 + 16 # Plot Width
    y0 = row * 25
    
    # Adding a "Street / Road" gap after every 2 rows
    if row >= 2: y0 += 20
    if row >= 4: y0 += 20
    if row >= 6: y0 += 20
        
    y1 = y0 + 18 # Plot Length
    
    # 📌 Hover Text Details (CRM Mini-Card)
    hover_text = f"<b>Plot P-{pid}</b><br>Status: {status}<br>Area: {pinfo.get('plot_area', 1116)} Sq.Ft<br>Base Rate: ₹{pinfo.get('company_rate', 700)}"
    if status != "Available":
        hover_text += f"<br><br><b>Client:</b> {pinfo.get('customer_name', 'N/A')}"
        hover_text += f"<br><b>Mobile:</b> {pinfo.get('phone', 'N/A')}"
        hover_text += f"<br><b>Executive:</b> {pinfo.get('executive_name', 'Direct')}"

    # 1. Draw Plot Box (Shape)
    fig.add_shape(
        type="rect", x0=x0, y0=y0, x1=x1, y1=y1,
        fillcolor=fill_color, line=dict(color=border_color, width=2)
    )
    
    # 2. Add Plot Number Text
    fig.add_annotation(
        x=(x0+x1)/2, y=(y0+y1)/2,
        text=f"<b>P-{pid}</b>", showarrow=False,
        font=dict(color="white", size=13)
    )
    
    # 3. Add Invisible Hover Tracker (For CRM Details)
    fig.add_trace(go.Scatter(
        x=[(x0+x1)/2], y=[(y0+y1)/2],
        mode="markers", marker=dict(size=40, color="rgba(0,0,0,0)"),
        hoverinfo="text", hovertext=hover_text, showlegend=False
    ))

# Map UI Styling
fig.update_layout(
    xaxis=dict(visible=False, showgrid=False, zeroline=False),
    yaxis=dict(visible=False, showgrid=False, zeroline=False, autorange="reversed"),
    plot_bgcolor="#e2e8f0", paper_bgcolor="#f8fafc",
    margin=dict(l=10, r=10, t=10, b=10), height=600,
    hovermode="closest", dragmode="pan" # Pan allows moving the map like Google Earth
)

# Render Map
st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

# --- CRM Detailed Section ---
st.write("---")
st.markdown("### 📊 Live Plot Inventory Data")

cols = st.columns(5)
for i, (pid, pinfo) in enumerate(filtered_plots.items()):
    with cols[i % 5]:
        stat = pinfo.get('status', 'Available')
        if stat == 'Available':
            st.markdown(f"<div style='text-align:center; padding:10px; border:2px solid #10b981; border-radius:8px; margin-bottom:10px; background:#d1fae5;'><b>P-{pid}</b><br><span style='font-size:12px; color:#065f46;'>Available</span></div>", unsafe_allow_html=True)
        else:
            c_name = pinfo.get('customer_name', '').split(" ")[0]
            st.markdown(f"<div style='text-align:center; padding:10px; border:2px solid #ef4444; border-radius:8px; margin-bottom:10px; background:#fee2e2;'><b>P-{pid}</b><br><span style='font-size:12px; color:#991b1b;'>{c_name}</span></div>", unsafe_allow_html=True)
