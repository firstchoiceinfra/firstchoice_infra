import streamlit as st
import pandas as pd
import database
import datetime
import urllib.parse

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Premium Inventory Matrix")

# --- 2. Security Interceptor Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

# --- 3. Database Sync ---
database.init_db()
db_data = st.session_state.db_projects

# Initialize Team Hierarchy Dictionary if not present
if 'team_hierarchy' not in db_data:
    db_data['team_hierarchy'] = {}

# ====================================================================
# 🎨 Premium UI & Glassmorphism Theme Sync
# ====================================================================
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255, 255, 255, 0.85)" 

if '_app_settings' in db_data:
    global_settings = db_data['_app_settings']
    bg_url = global_settings.get('bg_url', bg_url)
    p_color = global_settings.get('primary_color', p_color)
    s_color = global_settings.get('secondary_color', s_color)

st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_url}");
    background-attachment: fixed;
    background-size: cover;
}}
.block-container {{
    background-color: {c_bg} !important;
    backdrop-filter: blur(12px); 
    -webkit-backdrop-filter: blur(12px);
    padding: 2.5rem 3.5rem !important;
    border-radius: 24px;
    box-shadow: 0px 20px 40px rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.4);
    margin-top: 2rem;
    margin-bottom: 2rem;
}}
h1, h2, h3, h4 {{
    color: {p_color} !important;
    font-weight: 900;
    letter-spacing: -0.5px;
}}
/* Premium Plot Cards */
.plot-card {{
    padding: 18px 10px;
    border-radius: 14px;
    text-align: center;
    margin-bottom: 12px;
    box-shadow: 0px 6px 15px rgba(0,0,0,0.08);
    font-weight: bold;
    transition: all 0.3s ease;
    cursor: pointer;
}}
.plot-card:hover {{
    transform: translateY(-5px);
    box-shadow: 0px 12px 20px rgba(0,0,0,0.15);
}}
.plot-available {{
    background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
    color: #155724 !important;
    border: 1px solid #b1dfbb;
}}
.plot-booked {{
    background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
    color: #721c24 !important;
    border: 1px solid #f1b0b7;
}}
/* Locked Privacy Status CSS */
.plot-locked {{
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
    color: #475569 !important;
    border: 1px solid #94a3b8;
}}
.plot-hold {{
    background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
    color: #856404 !important;
    border: 1px solid #ffeeba;
}}
/* Premium Buttons */
.stButton>button {{
    background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%);
    color: white !important;
    border-radius: 8px;
    font-weight: 700;
    border: none;
    padding: 10px 20px;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    transition: all 0.3s ease;
}}
.stButton>button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(59, 130, 246, 0.6);
}}
.wa-btn {{
    display: inline-block;
    width: 100%;
    background: linear-gradient(90deg, #25D366 0%, #128C7E 100%);
    color: white;
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 14px;
    text-decoration: none;
    box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4);
    transition: all 0.3s ease;
    border: none;
    font-family: inherit;
}}
.wa-btn:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(37, 211, 102, 0.6);
    color: white;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>🏗️ Premium Inventory & Allocation Matrix</h1>", unsafe_allow_html=True)

# --- Fetch Current User Details ---
current_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# --- Helper: Check Downline Authorization ---
def get_all_downlines(manager_name):
    downlines = db_data.get('team_hierarchy', {}).get(manager_name, [])
    all_d = list(downlines)
    for d in downlines:
        all_d.extend(get_all_downlines(d))
    return all_d

def is_authorized(plot_exec_name):
    if user_role == 'admin': return True
    if plot_exec_name == current_user: return True
    if plot_exec_name in get_all_downlines(current_user): return True
    return False

# =========================================================
# 🌟 Smart Associate Auto-Complete Registry
# =========================================================
project_names = []
exec_list_temp = []

for key, val in db_data.items():
    if isinstance(val, dict) and ('plots' in val or 'total_plots' in val or 'khasra' in val):
        project_names.append(key)
    else:
        if isinstance(val, dict):
            for k, v in val.items():
                exec_list_temp.append(str(k))
                if isinstance(v, dict):
                    if 'name' in v: exec_list_temp.append(str(v['name']))
                    if 'Name' in v: exec_list_temp.append(str(v['Name']))
                    if 'exec_name' in v: exec_list_temp.append(str(v['exec_name']))
        elif isinstance(val, list):
            exec_list_temp.extend([str(e) for e in val if isinstance(e, str)])

exec_list = ["Direct Sale"]
for e in exec_list_temp:
    e_clean = e.strip()
    if e_clean and e_clean not in exec_list and e_clean.lower() not in ['true', 'false', 'none', 'select']:
        exec_list.append(e_clean)
exec_list.sort()

# --- Sidebar Controls ---
if st.sidebar.button("🔄 Sync Cloud Storage (Refresh)"):
    with st.spinner("Synchronizing database..."):
        database.load_db_data()
        st.success("Cloud Synchronized!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("🏢 Select Project Blueprint")

if not project_names:
    st.warning("No initialized layout found. Please construct projects via Admin Desk.")
    st.stop()

selected_project_name = st.sidebar.selectbox("Active Blueprints Registry", project_names)

if isinstance(st.session_state.db_projects[selected_project_name].get('plots'), list):
    fixed_plots = {str(i): plot for i, plot in enumerate(st.session_state.db_projects[selected_project_name]['plots']) if plot is not None}
    st.session_state.db_projects[selected_project_name]['plots'] = fixed_plots

project_data = st.session_state.db_projects[selected_project_name]
plots = project_data.get('plots', {})

if not plots:
    st.info("No plot matrix mapped inside this project profile.")
    st.stop()


# =========================================================
# 📝 Interactive Booking Assignment Form Desk
# =========================================================
if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']
   
    p_khasra = project_data.get('khasra', 'N/A')
    p_ph = project_data.get('ph_no', 'N/A')
    p_mauza = project_data.get('mauza', 'N/A')
    p_tahsil = project_data.get('tahsil', 'N/A')
    p_dist = project_data.get('district', 'N/A')

    st.markdown(f"### 📝 Project Matrix: {proj} | Secure Plot Node Assignment: P-{plt}")
   
    # --- A. HOLD STATUS VIEW ---
    if curr_stat == "Hold":
        st.warning(f"🚧 **Plot P-{plt} is currently on HOLD (Blocked from Sale / Not for Sale).**")
        st.info("This plot cannot be booked by executives.")
        
        if st.session_state.get('user_role', 'executive') == 'admin':
            if st.button("✅ Unblock & Make Available (Admin)", use_container_width=True, type="primary"):
                st.session_state.db_projects[proj]['plots'][plt] = {"status": "Available"}
                if database.save_db_data():
                    st.success(f"Plot P-{plt} is now available for booking!")
                    del st.session_state['booking_popup']
                    st.rerun()
        else:
            st.error("🔒 Only Admins have the authority to unblock this plot.")
            
    # --- B. AVAILABLE BOOKING FORM ---
    elif curr_stat == "Available":
        
        # 🟡 ADMIN HOLD BUTTON
        if st.session_state.get('user_role', 'executive') == 'admin':
            if st.button("⏸️ Block Unit / Put on Hold (Admin Action)", use_container_width=True):
                st.session_state.db_projects[proj]['plots'][plt] = {"status": "Hold"}
                if database.save_db_data():
                    st.success("Plot placed on Hold!")
                    del st.session_state['booking_popup']
                    st.rerun()
            st.write("---")

        st.info(f"📍 **Land Location Specifications:** Khasra No: {p_khasra} | PH No: {p_ph} | Mauza: {p_mauza} | Tahsil: {p_tahsil}")
       
        # 🔗 COMBO BOOKING ENGINE
        st.subheader("🔗 Joint / Combo Booking (Optional)", divider="blue")
        st.caption("💡 Select additional plots below if the client is buying multiple units. They will be merged into a single Master Ledger.")
        
        available_others = [p for p, d in st.session_state.db_projects[proj]['plots'].items() if d.get('status', 'Available') == 'Available' and p != plt]
        combo_selections = st.multiselect(f"Select additional plots to combine with P-{plt}:", available_others)
        
        all_booking_plots = [plt] + combo_selections
        joined_plots_str = ", ".join(all_booking_plots)
        
        if combo_selections:
            st.success(f"🤝 **Joint Booking Active!** Master Ledger will be created for Plots: **P-{joined_plots_str}**")

        st.subheader("👤 Client KYC & Personal Information", divider="blue")
        col1, col2, col3 = st.columns(3)
        c_name = col1.text_input("Client Full Name *")
        c_dob = col2.date_input("Date of Birth (DOB)", min_value=datetime.date(1950, 1, 1))
        c_phone = col3.text_input("Contact Mobile Number *")
       
        c_address = st.text_area("Permanent Residential Address")
       
        col4, col5 = st.columns(2)
        c_aadhaar = col4.text_input("Aadhaar National ID Number")
        c_pan = col5.text_input("PAN Card Alpha-Numeric ID")
       
        col6, col7 = st.columns(2)
        n_name = col6.text_input("Nominee Attributed Full Name")
        n_age = col7.text_input("Nominee Declared Age")
       
        st.subheader("📐 Layout Specifications & Commercial Valuation", divider="blue")
        st.caption("*(Note: For Combo Booking, enter the TOTAL Combined Area, Company Rate, and Selling Rate for all plots)*")
        
        col8, col9, col10 = st.columns(3)
        plot_area = col8.text_input("Total Combined Dimensions / Area (Sq.Ft / Sq.M)")
        company_rate = col9.number_input("Total Standard Company Base Rate (₹)", min_value=0.0, step=50.0)
        selling_rate = col10.number_input("Total Final Negotiated Selling Rate (₹) *", min_value=0.0, step=50.0)
       
        discount = company_rate - selling_rate
        if discount > 0: st.success(f"🎉 **Authorized Instant Discount: ₹ {discount}**")
        elif discount < 0: st.warning(f"⚠️ Premium Surcharge Value Applied: ₹ {abs(discount)}")
           
        st.subheader("💳 Secured Advance & Token Collection Details", divider="blue")
        col11, col12, col13 = st.columns(3)
        token_amt = col11.number_input("Total Deposited Token Amount (₹) *", min_value=0.0, step=1000.0)
        pay_mode = col12.selectbox("Payment Channel Mode", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
        trans_id = col13.text_input("Transaction ID / Instrument Reference Number")
       
        receive_date = st.date_input("Date of Advance Receipt Collection")
       
        st.subheader("👨‍💼 Associated Partner Credit Allocation", divider="blue")
       
        if st.session_state.get('user_role', 'executive') == 'executive':
            logged_name = st.session_state.get('current_user_name', 'Direct Sale')
            st.text_input("Attributed Partner Profile", value=logged_name, disabled=True)
            final_exec_name = logged_name
        else:
            final_exec_name = st.selectbox("Attributed Partner Profile", exec_list, index=0)
       
        st.write("")
        if st.button("🔒 Execute Permanent Inventory Lock & Allocation", use_container_width=True, type="primary"):
            if c_name.strip() == "" or c_phone.strip() == "":
                st.error("🚨 Validation Failure: Client Name and Mobile Contact Number are mandatory fields!")
            elif token_amt <= 0:
                st.error("🚨 Accounting Failure: Token Deposit Value must be greater than zero!")
            else:
                # 1. Save Primary Plot
                primary_booking_data = {
                    "status": "Booked", "customer_name": c_name.strip(), "dob": str(c_dob),
                    "phone": c_phone.strip(), "address": c_address.strip(), "aadhaar": c_aadhaar.strip(),
                    "pan": c_pan.strip(), "nominee_name": n_name.strip(), "nominee_age": n_age.strip(),
                    "plot_area": plot_area.strip(), "company_rate": company_rate, "selling_rate": selling_rate,
                    "discount": discount, "token_amount": token_amt, "payment_mode": pay_mode,
                    "transaction_id": trans_id.strip(), "receipt_date": str(receive_date),
                    "executive_name": final_exec_name, "booking_date": str(datetime.date.today()),
                    "booked_plots_str": joined_plots_str, "is_primary": True, "primary_plot_id": plt
                }
                st.session_state.db_projects[proj]['plots'][plt].update(primary_booking_data)
                
                # 2. Save Combo Child Plots 
                for child_plt in combo_selections:
                    child_data = {
                        "status": "Booked", "customer_name": c_name.strip(), "phone": c_phone.strip(),
                        "executive_name": final_exec_name, "booked_plots_str": joined_plots_str,
                        "is_primary": False, "primary_plot_id": plt,
                        "selling_rate": 0, "token_amount": 0, "company_rate": 0, "plot_area": 0
                    }
                    st.session_state.db_projects[proj]['plots'][child_plt].update(child_data)
               
                with st.spinner("Locking transaction matrix onto cloud security..."):
                    if database.save_db_data():
                        st.success(f"🎉 Congratulations! Plot(s) P-{joined_plots_str} successfully secured!")
                        del st.session_state['booking_popup']
                        st.rerun()

    # --- C. Comprehensive Statement Dashboard (BOOKED) ---
    else:
        p_data = st.session_state.db_projects[proj]['plots'][plt]
        
        # 🔒 FINAL PRIVACY CHECK BEFORE SHOWING STATEMENT
        if not is_authorized(p_data.get('executive_name', '')):
            st.error("🔒 **ACCESS DENIED:** You are not authorized to view the commercial statement of this plot because it belongs to another executive's portfolio.")
            if st.button("❌ Back to Grid Matrix Map View", use_container_width=True):
                del st.session_state['booking_popup']
                st.rerun()
            st.stop()

        # 🔗 COMBO RESOLVER
        if not p_data.get('is_primary', True):
            prim_id = p_data.get('primary_plot_id')
            if prim_id and prim_id in st.session_state.db_projects[proj]['plots']:
                p_data = st.session_state.db_projects[proj]['plots'][prim_id]
                st.info(f"🔗 **Joint Booking Detected!** You are viewing the unified Master Ledger for Plots: **P-{p_data.get('booked_plots_str')}**")
        
        joined_view_str = p_data.get('booked_plots_str', str(plt))
        st.error(f"⚠️ Allocation Alert: Plot(s) **P-{joined_view_str}** are locked. Comprehensive allotment details below:")
       
        c1, c2, c3 = st.columns(3)
        c1.metric("Customer Identity Holder", p_data.get('customer_name', 'N/A'))
        c1.write(f"**DOB:** {p_data.get('dob', 'N/A')} | **Address:** {p_data.get('address', 'N/A')}")
       
        c2.metric("Contact Profile String", p_data.get('phone', 'N/A'))
        c2.write(f"**Aadhaar ID:** {p_data.get('aadhaar', 'N/A')} | **PAN Card ID:** {p_data.get('pan', 'N/A')}")
       
        c3.metric("Credential Credit Owner", p_data.get('executive_name', 'N/A'))
        c3.write(f"**Nominee:** {p_data.get('nominee_name', 'N/A')} (Age: {p_data.get('nominee_age', 'N/A')})")
       
        with st.expander("📄 Financial Commercial Statement & Payout Ledger", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.write(f"📐 **Total Plot Size:** {p_data.get('plot_area', 'N/A')}")
            col_s1.write(f"📆 **Allotment Date:** {p_data.get('booking_date', 'N/A')}")
           
            col_s2.write(f"🏢 **Total Base Value:** ₹{p_data.get('company_rate', 0)}")
            col_s2.write(f"💰 **Gross Selling Rate:** ₹{p_data.get('selling_rate', 0)}")
            col_s2.success(f"💸 **Adjusted Discount Cut:** ₹{p_data.get('discount', 0)}")
           
            col_s3.warning(f"💳 **Deposited Advance Token:** ₹{p_data.get('token_amount', 0)}")
            col_s3.write(f"🏪 **Payment Mode:** {p_data.get('payment_mode', 'N/A')}")
            col_s3.write(f"🔑 **Ref ID:** {p_data.get('transaction_id', 'N/A')}")
           
            st.markdown("#### 🔄 Live Payment & EMI Sync")
           
            def sf(val, default=0.0):
                try:
                    if val is None or str(val).strip() == "": return float(default)
                    return float(val)
                except: return float(default)
               
            token_amt_val = sf(p_data.get('token_amount', 0.0))
            s_rate_val = sf(p_data.get('selling_rate', 0.0))
            total_cost_val = s_rate_val 
               
            partial_payments = p_data.get('partial_payments', [])
            total_emi_paid = sum(sf(pmt.get('amount', 0.0)) for pmt in partial_payments)
           
            total_overall_paid = token_amt_val + total_emi_paid
            net_outstanding = max(0.0, total_cost_val - total_overall_paid)
           
            c_emi1, c_emi2, c_emi3 = st.columns(3)
            c_emi1.metric("Gross Plot Value", f"₹ {total_cost_val:,.2f}")
            c_emi2.metric("Total Collection (Paid)", f"₹ {total_overall_paid:,.2f}")
            c_emi3.metric("Net Outstanding Due", f"₹ {net_outstanding:,.2f}")
           
            history_rows = []
            history_rows.append({"Date": p_data.get('receipt_date', p_data.get('booking_date', 'N/A')), "Type": "Booking Advance (Token)", "Mode": p_data.get('payment_mode', 'N/A'), "Amount (₹)": token_amt_val})
            for pmt in partial_payments:
                history_rows.append({"Date": pmt.get('date', 'N/A'), "Type": pmt.get('remarks', 'Installment Payment'), "Mode": pmt.get('mode', 'N/A'), "Amount (₹)": sf(pmt.get('amount', 0.0))})
           
            df_display = pd.DataFrame(history_rows)
            df_display['Amount (₹)'] = df_display['Amount (₹)'].apply(lambda x: f"₹ {x:,.2f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)
           
            st.write("---")
            c_btn1, c_btn2 = st.columns(2)
           
            csv_statement = pd.DataFrame(history_rows).to_csv(index=False).encode('utf-8-sig')
            with c_btn1:
                st.download_button(
                    label="🖨️ Download Statement (Print/Save)",
                    data=csv_statement,
                    file_name=f"Plot_{joined_view_str}_Statement_{p_data.get('customer_name', 'Client').replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
           
            cust_phone = str(p_data.get('phone', '')).replace(' ', '').replace('+', '').strip()
            if len(cust_phone) == 10:
                cust_phone = "91" + cust_phone
               
            wa_msg = f"🌟 *FirstChoice Infra - Payment Update* 🌟\n\nDear *{str(p_data.get('customer_name', 'Sir/Madam')).title()}*,\nHere is the live payment status for your Plot(s) *P-{joined_view_str}* in *{proj}*:\n\n🔹 *Total Value:* ₹ {total_cost_val:,.2f}\n✅ *Total Amount Paid:* ₹ {total_overall_paid:,.2f}\n⚠️ *Net Outstanding Balance:* ₹ {net_outstanding:,.2f}\n\nThank you for your trust and association with us!\n\nRegards,\n*FC Infra Team*"
            wa_url = f"https://wa.me/{cust_phone}?text={urllib.parse.quote(wa_msg)}"
           
            with c_btn2:
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">💬 Send Live Update on WhatsApp</a>', unsafe_allow_html=True)
           
        if st.session_state.get('user_role', 'admin') == 'admin':
            st.write("")
            st.warning("Strategic Action: Force Cancel will revoke all plots attached to this Joint Booking.")
            if st.button("✅ Force Cancel Allotment & Revoke Allocation", use_container_width=True):
                plots_to_free = [p.strip() for p in p_data.get('booked_plots_str', str(plt)).split(",")]
                for f_plt in plots_to_free:
                    if f_plt in st.session_state.db_projects[proj]['plots']:
                        st.session_state.db_projects[proj]['plots'][f_plt] = {"status": "Available"}
                        
                with st.spinner("Revoking ledger data strings..."):
                    if database.save_db_data():
                        st.success(f"Plots P-{joined_view_str} successfully restored to active open inventory!")
                        del st.session_state['booking_popup']
                        st.rerun()

    st.write("---")
    if st.button("❌ Back to Grid Matrix Map View", use_container_width=True):
        del st.session_state['booking_popup']
        st.rerun()

    st.stop()

# =========================================================
# 📊 Interactive Plot Grid Matrix Render Layout
# =========================================================
st.markdown(f"### 📋 Project Inventory Gallery: {selected_project_name}")
st.write(f"📍 Location Profile Matrix: Khasra No: {project_data.get('khasra','N/A')} | Mauza: {project_data.get('mauza','N/A')} | Registered Unit Base Count: {project_data.get('total_plots', 0)}")

cols_per_row = 5
plot_items = list(plots.items())
rows = [plot_items[i:i + cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status = plot_info.get('status', 'Available')
            plot_exec_name = plot_info.get('executive_name', '')
           
            if status == "Available":
                st.markdown(f'<div class="plot-card plot-available">🏠 Plot {plot_id}<br>✅ Available</div>', unsafe_allow_html=True)
                btn_txt = "📝 Book Unit"
                btn_disabled = False
            elif status == "Hold":
                st.markdown(f'<div class="plot-card plot-hold">🚧 Plot {plot_id}<br>🔒 On Hold</div>', unsafe_allow_html=True)
                btn_txt = "🔓 View Hold"
                btn_disabled = False
            else:
                # 🔒 PRIVACY LOGIC: Check if this user is allowed to see the details
                if is_authorized(plot_exec_name):
                    cust = plot_info.get('customer_name', 'N/A')
                    st.markdown(f'<div class="plot-card plot-booked">🛑 Plot {plot_id}<br>❌ Booked ({cust.split(" ")[0]})</div>', unsafe_allow_html=True)
                    btn_txt = "📄 Statement"
                    btn_disabled = False
                else:
                    # 🔒 LOCKED VIEW FOR UNAUTHORIZED EXECUTIVES
                    st.markdown(f'<div class="plot-card plot-locked">🛑 Plot {plot_id}<br>🔒 Booked</div>', unsafe_allow_html=True)
                    btn_txt = "🔒 Access Denied"
                    btn_disabled = True
           
            if st.button(btn_txt, key=f"btn_{selected_project_name}_{plot_id}", use_container_width=True, disabled=btn_disabled):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }
                st.rerun()
