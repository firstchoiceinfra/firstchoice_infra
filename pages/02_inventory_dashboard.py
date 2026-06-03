import streamlit as st
import pandas as pd
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

# ====================================================================
# 🎨 Universal Theme Sync + Premium CSS Layout
# ====================================================================
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
.stApp {{
    background-image: url("{bg_url}");
    background-attachment: fixed;
    background-size: cover;
}}
.block-container {{
    background-color: {c_bg} !important;
    padding: 2rem 3rem !important;
    border-radius: 20px;
    box-shadow: 0px 10px 30px rgba(0,0,0,0.3);
    margin-top: 2rem;
    margin-bottom: 2rem;
}}
h1, h2, h3, h4, h5, h6, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{
    color: {p_color} !important;
    font-weight: 800;
}}
.plot-card {{
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin-bottom: 10px;
    box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    font-weight: bold;
}}
.plot-available {{
    background-color: #d4edda !important;
    color: #155724 !important;
    border: 2px solid #c3e6cb;
}}
.plot-booked {{
    background-color: #f8d7da !important;
    color: #721c24 !important;
    border: 2px solid #f5c6cb;
}}
.stButton>button {{
    background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%);
    color: white !important;
    border-radius: 6px;
    font-weight: bold;
}}
div[data-testid="stForm"] {{
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 25px;
}}
</style>
""", unsafe_allow_html=True)
# ====================================================================

st.markdown("<h1 style='text-align: center;'>🏗️ FirstChoice Infra - Inventory Dashboard</h1>", unsafe_allow_html=True)

# =========================================================
# 🌟 Smart Associate Auto-Complete Registry Scanner
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
# =========================================================

# --- Sidebar Controls ---
if st.sidebar.button("🔄 Sync Cloud Storage (Refresh)"):
    with st.spinner("Synchronizing database..."):
        database.load_db_data()
        st.success("Cloud Synchronized!")
        st.rerun()

st.sidebar.divider()
st.sidebar.header("Select Project Blueprint")

if not project_names:
    st.warning("No initialized layout found. Please construct projects via Admin Desk.")
    st.stop()

selected_project_name = st.sidebar.selectbox("Active Blueprints Registry", project_names)

# Array Node Structure Safety Fix
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
   
    # --- A. Full Booking Form (Restored with ALL Missing Columns) ---
    if curr_stat == "Available":
        st.info(f"📍 **Land Location Specifications:** Khasra No: {p_khasra} | PH No: {p_ph} | Mauza: {p_mauza} | Tahsil: {p_tahsil} | District: {p_dist}")
       
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
        col8, col9, col10 = st.columns(3)
        plot_area = col8.text_input("Plot Dimensions / Area (Sq.Ft / Sq.M)")
        company_rate = col9.number_input("Standard Company Base Rate (₹)", min_value=0.0, step=50.0)
        selling_rate = col10.number_input("Final Negotiated Selling Rate (₹) *", min_value=0.0, step=50.0)
       
        # Automatic pricing adjustments string output
        discount = company_rate - selling_rate
        if discount > 0:
            st.success(f"🎉 **Authorized Instant Discount: ₹ {discount}**")
        elif discount < 0:
            st.warning(f"⚠️ Premium Surcharge Value Applied: ₹ {abs(discount)}")
           
        st.subheader("💳 Secured Advance & Token Collection Details", divider="blue")
        col11, col12, col13 = st.columns(3)
        token_amt = col11.number_input("Deposited Token Amount (₹) *", min_value=0.0, step=1000.0)
        pay_mode = col12.selectbox("Payment Channel Mode", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
        trans_id = col13.text_input("Transaction ID / Instrument Reference Number")
       
        receive_date = st.date_input("Date of Advance Receipt Collection")
       
        st.subheader("👨‍💼 Associated Partner Credit Allocation", divider="blue")
        st.caption("💡 *Type the initial characters in the input dropdown box to trigger the auto-search indexing filters instantly.*")
       
        # Role Protection Guard Engine
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
                booking_data = {
                    "status": "Booked",
                    "customer_name": c_name.strip(),
                    "dob": str(c_dob),
                    "phone": c_phone.strip(),
                    "address": c_address.strip(),
                    "aadhaar": c_aadhaar.strip(),
                    "pan": c_pan.strip(),
                    "nominee_name": n_name.strip(),
                    "nominee_age": n_age.strip(),
                    "plot_area": plot_area.strip(),
                    "company_rate": company_rate,
                    "selling_rate": selling_rate,
                    "discount": discount,
                    "token_amount": token_amt,
                    "payment_mode": pay_mode,
                    "transaction_id": trans_id.strip(),
                    "receipt_date": str(receive_date),
                    "executive_name": final_exec_name,
                    "booking_date": str(datetime.date.today())
                }
               
                st.session_state.db_projects[proj]['plots'][plt].update(booking_data)
               
                with st.spinner("Locking transaction matrix onto cloud cloud security..."):
                    if database.save_db_data():
                        st.success(f"🎉 Congratulations! Plot Unit P-{plt} successfully secured under client reference '{c_name.strip()}'!")
                        del st.session_state['booking_popup']
                        st.rerun()

    # --- B. Comprehensive Statement Dashboard (If Unit is Already Booked) ---
    else:
        p_data = st.session_state.db_projects[proj]['plots'][plt]
        st.error(f"⚠️ Allocation Alert: This plot is locked out. Comprehensive allotment statement details below:")
       
        c1, c2, c3 = st.columns(3)
        c1.metric("Customer Identity Holder", p_data.get('customer_name', 'N/A'))
        c1.write(f"**DOB:** {p_data.get('dob', 'N/A')} | **Address:** {p_data.get('address', 'N/A')}")
       
        c2.metric("Contact Profile String", p_data.get('phone', 'N/A'))
        c2.write(f"**Aadhaar ID:** {p_data.get('aadhaar', 'N/A')} | **PAN Card ID:** {p_data.get('pan', 'N/A')}")
       
        c3.metric("Credential Credit Owner", p_data.get('executive_name', 'N/A'))
        c3.write(f"**Nominee:** {p_data.get('nominee_name', 'N/A')} (Age Ref: {p_data.get('nominee_age', 'N/A')})")
       
        with st.expander("📄 Financial Commercial Statement & Payout Ledger", expanded=True):
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.write(f"📐 **Mapped Plot Size:** {p_data.get('plot_area', 'N/A')}")
            col_s1.write(f"📆 **Allotment Settlement Date:** {p_data.get('booking_date', 'N/A')}")
           
            col_s2.write(f"🏢 **Base Book Value:** ₹{p_data.get('company_rate', 0)}")
            col_s2.write(f"💰 **Gross Selling Rate:** ₹{p_data.get('selling_rate', 0)}")
            col_s2.success(f"💸 **Adjusted Discount Cut:** ₹{p_data.get('discount', 0)}")
           
            col_s3.warning(f"💳 **Deposited Advance Token:** ₹{p_data.get('token_amount', 0)}")
            col_s3.write(f"🏪 **Payment Channel Mode:** {p_data.get('payment_mode', 'N/A')}")
            col_s3.write(f"🔑 **Instrument/Ref ID:** {p_data.get('transaction_id', 'N/A')}")
            col_s3.write(f"📅 **Advance Receipt Date:** {p_data.get('receipt_date', 'N/A')}")
            
            # =======================================================
            # 🚀 NEW: LIVE EMI & PAYMENT SYNC ENGINE
            # =======================================================
            st.markdown("#### 🔄 Live Payment & EMI Sync (Auto-Fetched from EMI Tracker)")
            
            # Safe float calculator to prevent app crash on empty inputs
            def sf(val, default=0.0):
                try:
                    if val is None or str(val).strip() == "": return float(default)
                    return float(val)
                except: return float(default)
                
            token_amt_val = sf(p_data.get('token_amount', 0.0))
            plot_area_val = sf(p_data.get('plot_area', p_data.get('area', 1116.23)))
            s_rate_val = sf(p_data.get('selling_rate', 0.0))
            
            # Calculating precise gross value (Rate x Area)
            if 0 < s_rate_val < 10000:
                total_cost_val = s_rate_val * plot_area_val
            else:
                total_cost_val = s_rate_val if s_rate_val > 0 else sf(p_data.get('total_value', 191000.0))
                
            partial_payments = p_data.get('partial_payments', [])
            total_emi_paid = sum(sf(pmt.get('amount', 0.0)) for pmt in partial_payments)
            
            # Adding Token + All EMIs
            total_overall_paid = token_amt_val + total_emi_paid
            net_outstanding = max(0.0, total_cost_val - total_overall_paid)
            
            c_emi1, c_emi2, c_emi3 = st.columns(3)
            c_emi1.metric("Gross Plot Value", f"₹ {total_cost_val:,.2f}")
            c_emi2.metric("Total Collection (Token + EMI)", f"₹ {total_overall_paid:,.2f}")
            c_emi3.metric("Net Outstanding Balance", f"₹ {net_outstanding:,.2f}")
            
            # Expandable detailed payment history table
            with st.expander("📜 View Complete Payment History Ledger (Token + All EMIs)", expanded=False):
                history_rows = []
                history_rows.append({
                    "Date": p_data.get('receipt_date', p_data.get('booking_date', 'N/A')),
                    "Type": "Booking Advance (Token)",
                    "Mode": p_data.get('payment_mode', 'N/A'),
                    "Amount (₹)": f"{token_amt_val:,.2f}"
                })
                for pmt in partial_payments:
                    history_rows.append({
                        "Date": pmt.get('date', 'N/A'),
                        "Type": pmt.get('remarks', 'Installment Payment'),
                        "Mode": pmt.get('mode', 'N/A'),
                        "Amount (₹)": f"{sf(pmt.get('amount', 0.0)):,.2f}"
                    })
                st.dataframe(pd.DataFrame(history_rows), use_container_width=True, hide_index=True)
            # =======================================================
           
        # Admin Override Privilege Check for Termination
        if st.session_state.get('user_role', 'admin') == 'admin':
            st.write("")
            st.warning("Strategic Action: Proceed with structural contract termination to restore unit to Vacant Inventory?")
            if st.button("✅ Force Cancel Allotment & Revoke Allocation", use_container_width=True):
                st.session_state.db_projects[proj]['plots'][plt] = {"status": "Available"}
                with st.spinner("Revoking ledger data strings..."):
                    if database.save_db_data():
                        st.success(f"Plot P-{plt} successfully restored to active open inventory!")
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
           
            if status == "Available":
                st.markdown(f'<div class="plot-card plot-available">🏠 Plot {plot_id}<br>✅ Available</div>', unsafe_allow_html=True)
                btn_txt = "📝 Book Unit"
            else:
                cust = plot_info.get('customer_name', 'N/A')
                st.markdown(f'<div class="plot-card plot-booked">🛑 Plot {plot_id}<br>❌ Booked ({cust})</div>', unsafe_allow_html=True)
                btn_txt = "📄 Statement"
           
            if st.button(btn_txt, key=f"btn_{selected_project_name}_{plot_id}", use_container_width=True):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id,
                    'current_status': status
                }
                st.rerun()
