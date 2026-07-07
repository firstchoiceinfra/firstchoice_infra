import streamlit as st
import pandas as pd
import database
import datetime
import urllib.parse

st.set_page_config(layout="wide", page_title="FC Infra - Premium Inventory Matrix")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

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
.stApp {{ background-image: url("{bg_url}"); background-attachment: fixed; background-size: cover; }}
.block-container {{ background-color: {c_bg} !important; backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px); padding: 2.5rem 3.5rem !important; border-radius: 24px;
    box-shadow: 0px 20px 40px rgba(0,0,0,0.2); border: 1px solid rgba(255,255,255,0.4);
    margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3, h4 {{ color: {p_color} !important; font-weight: 900; letter-spacing: -0.5px; }}
.plot-card {{ padding: 18px 10px; border-radius: 14px; text-align: center; margin-bottom: 12px;
    box-shadow: 0px 6px 15px rgba(0,0,0,0.08); font-weight: bold; transition: all 0.3s ease; cursor: pointer; }}
.plot-card:hover {{ transform: translateY(-5px); box-shadow: 0px 12px 20px rgba(0,0,0,0.15); }}
.plot-available {{ background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%); color: #155724 !important; border: 1px solid #b1dfbb; }}
.plot-booked {{ background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%); color: #721c24 !important; border: 1px solid #f1b0b7; }}
.plot-hold {{ background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%); color: #856404 !important; border: 1px solid #ffeeba; }}
.plot-locked {{ background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%); color: #475569 !important; border: 1px solid #94a3b8; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important;
    border-radius: 8px; font-weight: 700; border: none; padding: 10px 20px;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4); transition: all 0.3s ease; }}
.stButton>button:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(59, 130, 246, 0.6); }}
.wa-btn {{ display: inline-block; width: 100%; background: linear-gradient(90deg, #25D366 0%, #128C7E 100%);
    color: white; text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; font-size: 14px;
    text-decoration: none; box-shadow: 0 4px 12px rgba(37, 211, 102, 0.4); transition: all 0.3s ease;
    border: none; font-family: inherit; }}
.wa-btn:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(37, 211, 102, 0.6); color: white; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>🏗️ Premium Inventory & Allocation Matrix</h1>", unsafe_allow_html=True)

current_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')
exec_data_root = db_data.get('executives', {})

def get_all_downlines(manager_name):
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data_root.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name))
    return list(set(downlines))

def is_authorized(plot_exec_name):
    if str(user_role).lower() == 'admin': return True
    plot_exec_clean = str(plot_exec_name).strip().lower()
    curr_user_clean = str(current_user).strip().lower()
    if plot_exec_clean == curr_user_clean: return True
    all_downlines_lower = [d.lower() for d in get_all_downlines(curr_user_clean)]
    if plot_exec_clean in all_downlines_lower: return True
    return False

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

if 'booking_popup' in st.session_state:
    p_info = st.session_state.booking_popup
    proj = p_info['project']
    plt = p_info['plot']
    curr_stat = p_info['current_status']

    p_khasra = project_data.get('khasra', 'N/A')
    p_ph = project_data.get('ph_no', 'N/A')
    p_mauza = project_data.get('mauza', 'N/A')
    p_tahsil = project_data.get('tahsil', 'N/A')

    st.markdown(f"### 📝 Project Matrix: {proj} | Plot: P-{plt}")

    if curr_stat == "Hold":
        st.warning(f"🚧 Plot P-{plt} is on HOLD.")
        if st.session_state.get('user_role') == 'admin':
            if st.button("✅ Unblock & Make Available", use_container_width=True, type="primary"):
                st.session_state.db_projects[proj]['plots'][plt] = {"status": "Available"}
                if database.save_db_data():
                    st.success("Plot is now available!")
                    del st.session_state['booking_popup']
                    st.rerun()
        else:
            st.error("🔒 Only Admins can unblock.")

    elif curr_stat == "Available":
        if st.session_state.get('user_role') == 'admin':
            if st.button("⏸️ Block Unit / Put on Hold", use_container_width=True):
                st.session_state.db_projects[proj]['plots'][plt] = {"status": "Hold"}
                if database.save_db_data():
                    st.success("Plot placed on Hold!")
                    del st.session_state['booking_popup']
                    st.rerun()
            st.write("---")

        st.info(f"📍 Khasra: {p_khasra} | PH: {p_ph} | Mauza: {p_mauza} | Tahsil: {p_tahsil}")

        st.subheader("🔗 Joint / Combo Booking (Optional)", divider="blue")
        available_others = [p for p, d in st.session_state.db_projects[proj]['plots'].items()
                            if d.get('status', 'Available') == 'Available' and p != plt]
        combo_selections = st.multiselect(f"Additional plots with P-{plt}:", available_others)
        all_booking_plots = [plt] + combo_selections
        joined_plots_str = ", ".join(all_booking_plots)
        if combo_selections:
            st.success(f"🤝 Joint Booking: P-{joined_plots_str}")

        st.subheader("👤 Client KYC", divider="blue")
        col1, col2, col3 = st.columns(3)
        c_name  = col1.text_input("Client Full Name *")
        c_dob   = col2.date_input("Date of Birth", min_value=datetime.date(1950, 1, 1))
        c_phone = col3.text_input("Contact Mobile *")
        c_address = st.text_area("Permanent Address")
        col4, col5 = st.columns(2)
        c_aadhaar = col4.text_input("Aadhaar Number")
        c_pan     = col5.text_input("PAN Card")
        col6, col7 = st.columns(2)
        n_name = col6.text_input("Nominee Name")
        n_age  = col7.text_input("Nominee Age")

        st.subheader("📐 Commercial Valuation", divider="blue")
        st.caption("Company Rate = original rate | Selling Rate = actual deal rate | Difference = discount")

        col8, col9, col10 = st.columns(3)
        plot_area_input = col8.text_input("Total Plot Area (Sq.Ft) *", value="0")
        try: area_val = float(plot_area_input.strip())
        except: area_val = 0.0

        company_rate      = col9.number_input("🏢 Company Rate (per Sq.Ft) *", min_value=0.0, step=1.0)
        selling_rate_sqft = col10.number_input("💸 Selling Rate (per Sq.Ft) *", min_value=0.0, step=1.0)

        if company_rate > 0 and selling_rate_sqft > 0:
            if selling_rate_sqft < company_rate:
                disc_rs  = company_rate - selling_rate_sqft
                disc_pct = (disc_rs / company_rate) * 100
                st.warning(f"⚠️ Discount: ₹{disc_rs:.0f}/Sq.Ft ({disc_pct:.2f}%)")
            elif selling_rate_sqft == company_rate:
                st.success("✅ No discount.")
            else:
                st.info("ℹ️ Selling above company rate.")

        auto_calc_total = area_val * selling_rate_sqft
        if auto_calc_total > 0:
            st.success(f"💡 {area_val} Sq.Ft × ₹{selling_rate_sqft} = **₹ {auto_calc_total:,.2f}**")

        selling_rate_total = st.number_input("💰 Final Total Deal Value (₹) *", min_value=0.0,
                                              value=float(auto_calc_total) if auto_calc_total > 0 else 0.0,
                                              step=1000.0)

        st.subheader("💳 Token Collection", divider="blue")
        col11, col12, col13 = st.columns(3)
        token_amt    = col11.number_input("Token Amount (₹) *", min_value=0.0, step=1000.0)
        pay_mode     = col12.selectbox("Payment Mode", ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"])
        trans_id     = col13.text_input("Transaction ID / Ref")
        receive_date = st.date_input("Date of Receipt")

        st.subheader("👨‍💼 Partner Credit", divider="blue")
        if st.session_state.get('user_role') == 'executive':
            logged_name = st.session_state.get('current_user_name', 'Direct Sale')
            st.text_input("Partner", value=logged_name, disabled=True)
            final_exec_name = logged_name
        else:
            final_exec_name = st.selectbox("Partner", exec_list, index=0)

        st.write("")
        if st.button("🔒 Execute Booking", use_container_width=True, type="primary"):
            if c_name.strip() == "" or c_phone.strip() == "":
                st.error("🚨 Client Name and Mobile are mandatory!")
            elif token_amt <= 0:
                st.error("🚨 Token amount must be > 0!")
            elif selling_rate_total <= 0:
                st.error("🚨 Total Deal Value cannot be zero!")
            elif company_rate <= 0:
                st.error("🚨 Company Rate is mandatory!")
            else:
                primary_booking_data = {
                    "status": "Booked", "customer_name": c_name.strip(), "dob": str(c_dob),
                    "phone": c_phone.strip(), "address": c_address.strip(),
                    "aadhaar": c_aadhaar.strip(), "pan": c_pan.strip(),
                    "nominee_name": n_name.strip(), "nominee_age": n_age.strip(),
                    "plot_area": plot_area_input.strip(),
                    "company_rate": company_rate,
                    "selling_rate": selling_rate_total,
                    "rate_per_sqft": selling_rate_sqft,
                    "token_amount": token_amt, "payment_mode": pay_mode,
                    "transaction_id": trans_id.strip(), "receipt_date": str(receive_date),
                    "executive_name": final_exec_name, "booking_date": str(datetime.date.today()),
                    "booked_plots_str": joined_plots_str, "is_primary": True, "primary_plot_id": plt
                }
                st.session_state.db_projects[proj]['plots'][plt].update(primary_booking_data)
                for child_plt in combo_selections:
                    st.session_state.db_projects[proj]['plots'][child_plt].update({
                        "status": "Booked", "customer_name": c_name.strip(), "phone": c_phone.strip(),
                        "executive_name": final_exec_name, "booked_plots_str": joined_plots_str,
                        "is_primary": False, "primary_plot_id": plt,
                        "selling_rate": 0, "token_amount": 0, "plot_area": 0
                    })
                with st.spinner("Saving..."):
                    if database.save_db_data():
                        st.success(f"🎉 Plot(s) P-{joined_plots_str} booked!")
                        del st.session_state['booking_popup']
                        st.rerun()

    else:
        p_data = st.session_state.db_projects[proj]['plots'][plt]

        if not is_authorized(p_data.get('executive_name', '')):
            st.error("🔒 Access Denied.")
            if st.button("❌ Back", use_container_width=True):
                del st.session_state['booking_popup']
                st.rerun()
            st.stop()

        if not p_data.get('is_primary', True):
            prim_id = p_data.get('primary_plot_id')
            if prim_id and prim_id in st.session_state.db_projects[proj]['plots']:
                p_data = st.session_state.db_projects[proj]['plots'][prim_id]
                st.info(f"🔗 Joint Booking — Master Ledger: P-{p_data.get('booked_plots_str')}")

        joined_view_str = p_data.get('booked_plots_str', str(plt))
        st.error(f"⚠️ Plot(s) P-{joined_view_str} locked.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Customer", p_data.get('customer_name', 'N/A'))
        c1.write(f"**DOB:** {p_data.get('dob','N/A')} | **Address:** {p_data.get('address','N/A')}")
        c2.metric("Contact", p_data.get('phone', 'N/A'))
        c2.write(f"**Aadhaar:** {p_data.get('aadhaar','N/A')} | **PAN:** {p_data.get('pan','N/A')}")
        c3.metric("Executive", p_data.get('executive_name', 'N/A'))
        c3.write(f"**Nominee:** {p_data.get('nominee_name','N/A')} (Age: {p_data.get('nominee_age','N/A')})")

        with st.expander("📄 Financial Statement & Payout Ledger", expanded=True):
            def sf(val, default=0.0):
                try:
                    if val is None or str(val).strip() == "": return float(default)
                    return float(val)
                except: return float(default)

            plot_area_val      = sf(p_data.get('plot_area', 0.0))
            saved_selling_rate = sf(p_data.get('selling_rate', 0.0))
            comp_rate_saved    = sf(p_data.get('company_rate', 0.0))
            rate_sqft_saved    = sf(p_data.get('rate_per_sqft', 0.0))

            if saved_selling_rate > 0 and saved_selling_rate <= 100000 and plot_area_val > 0:
                total_cost_val = plot_area_val * saved_selling_rate
                rate_applied   = saved_selling_rate
            else:
                total_cost_val = saved_selling_rate
                rate_applied   = rate_sqft_saved

            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.write(f"📐 **Plot Size:** {p_data.get('plot_area','N/A')} Sq.Ft")
            col_s1.write(f"📆 **Booking Date:** {p_data.get('booking_date','N/A')}")
            col_s1.write(f"🏢 **Company Rate:** ₹ {comp_rate_saved:,.0f}/Sq.Ft")
            col_s2.write(f"💰 **Total Deal Value:** ₹ {total_cost_val:,.2f}")
            col_s2.write(f"📊 **Selling Rate:** ₹ {rate_applied}/Sq.Ft")
            if comp_rate_saved > 0 and rate_applied > 0 and rate_applied < comp_rate_saved:
                disc = comp_rate_saved - rate_applied
                disc_pct = (disc / comp_rate_saved) * 100
                col_s2.warning(f"⚠️ Discount: ₹{disc:.0f}/Sq.Ft ({disc_pct:.2f}%)")
            col_s3.warning(f"💳 **Token:** ₹ {p_data.get('token_amount', 0)}")
            col_s3.write(f"🏪 **Mode:** {p_data.get('payment_mode','N/A')}")
            col_s3.write(f"🔑 **Ref ID:** {p_data.get('transaction_id','N/A')}")

            st.markdown("#### 🔄 Live Payment & EMI Sync")
            token_amt_val    = sf(p_data.get('token_amount', 0.0))
            partial_payments = p_data.get('partial_payments', [])
            total_emi_paid   = sum(sf(pmt.get('amount', 0.0)) for pmt in partial_payments)
            total_overall_paid = token_amt_val + total_emi_paid
            net_outstanding  = max(0.0, total_cost_val - total_overall_paid)

            c_emi1, c_emi2, c_emi3 = st.columns(3)
            c_emi1.metric("Gross Deal Value", f"₹ {total_cost_val:,.2f}")
            c_emi2.metric("Total Paid", f"₹ {total_overall_paid:,.2f}")
            c_emi3.metric("Net Outstanding", f"₹ {net_outstanding:,.2f}")

            history_rows = []
            history_rows.append({
                "Date": p_data.get('receipt_date', p_data.get('booking_date', 'N/A')),
                "Type": "Booking Advance (Token)",
                "Mode": p_data.get('payment_mode', 'N/A'),
                "Slip No": p_data.get('token_slip_no', 'N/A'),
                "Amount (₹)": token_amt_val
            })
            for pmt in partial_payments:
                history_rows.append({
                    "Date": pmt.get('date', 'N/A'),
                    "Type": pmt.get('remarks', 'Installment Payment'),
                    "Mode": pmt.get('mode', 'N/A'),
                    "Slip No": pmt.get('slip_no', 'N/A'),
                    "Amount (₹)": sf(pmt.get('amount', 0.0))
                })

            df_display = pd.DataFrame(history_rows)
            df_display['Amount (₹)'] = df_display['Amount (₹)'].apply(lambda x: f"₹ {x:,.2f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # ── ADMIN EDIT SECTION ────────────────────────────
            if st.session_state.get('user_role') == 'admin':
                st.write("")

                # ✅ Update Company Rate
                with st.expander("🏢 Update Company Rate (For Commission Calculation)", expanded=False):
                    st.caption("⚠️ Purani bookings mein Company Rate nahi tha — yahan add/update karo.")
                    with st.form(f"update_company_rate_{plt}"):
                        current_cr = sf(p_data.get('company_rate', 0.0))
                        new_cr = st.number_input("Company Rate per Sq.Ft (₹)",
                                                  min_value=0.0, step=1.0, value=current_cr)
                        curr_sr = sf(p_data.get('rate_per_sqft',
                                    sf(p_data.get('selling_rate', 0.0))))
                        if new_cr > 0 and curr_sr > 0 and curr_sr < new_cr:
                            d = new_cr - curr_sr
                            dp = (d / new_cr) * 100
                            st.warning(f"Discount: ₹{d:.0f}/Sq.Ft = {dp:.2f}%")
                        if st.form_submit_button("💾 Save Company Rate", use_container_width=True):
                            actual_plt = st.session_state.booking_popup['plot']
                            real_plt   = st.session_state.db_projects[proj]['plots'].get(
                                actual_plt, {}).get('primary_plot_id', actual_plt)
                            st.session_state.db_projects[proj]['plots'][real_plt]['company_rate'] = new_cr
                            if database.save_db_data():
                                st.success(f"✅ Company Rate updated to ₹{new_cr}/Sq.Ft!")
                                st.rerun()

                # ✅ FULL EDIT — Token + All EMI payments
                with st.expander("✏️ Edit / Correct Payment Entries (Admin Only)", expanded=False):
                    st.caption("💡 Yahan token aur kisi bhi EMI ka amount, date, mode, slip number sab edit kar sakte ho.")

                    with st.form(f"full_edit_form_{plt}"):
                        st.markdown("**📌 Token / Booking Advance**")
                        col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                        new_tok_amt  = col_t1.number_input("Token Amount (₹)",
                                                            min_value=0.0, step=100.0,
                                                            value=float(token_amt_val))
                        new_tok_date = col_t2.text_input("Token Date (YYYY-MM-DD)",
                                                          value=str(p_data.get('receipt_date',
                                                          p_data.get('booking_date', ''))))
                        new_tok_mode = col_t3.selectbox("Token Mode",
                                                         ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"],
                                                         index=["Cash","Online/UPI","Cheque","RTGS/NEFT"].index(
                                                             p_data.get('payment_mode','Cash'))
                                                         if p_data.get('payment_mode','Cash') in
                                                         ["Cash","Online/UPI","Cheque","RTGS/NEFT"] else 0)
                        new_tok_slip = col_t4.text_input("Token Slip No",
                                                          value=p_data.get('token_slip_no', ''))

                        st.markdown("---")
                        st.markdown("**📋 EMI / Installment Payments**")

                        new_emi_data = []
                        for i, pmt in enumerate(partial_payments):
                            st.markdown(f"**EMI #{i+1}**")
                            ec1, ec2, ec3, ec4 = st.columns(4)
                            e_amt  = ec1.number_input(f"Amount (₹) #{i+1}",
                                                       min_value=0.0, step=100.0,
                                                       value=float(sf(pmt.get('amount', 0.0))),
                                                       key=f"emi_amt_{i}")
                            e_date = ec2.text_input(f"Date #{i+1}",
                                                     value=str(pmt.get('date', '')),
                                                     key=f"emi_date_{i}")
                            e_mode = ec3.selectbox(f"Mode #{i+1}",
                                                    ["Cash", "Online/UPI", "Cheque", "RTGS/NEFT"],
                                                    index=["Cash","Online/UPI","Cheque","RTGS/NEFT"].index(
                                                        pmt.get('mode','Cash'))
                                                    if pmt.get('mode','Cash') in
                                                    ["Cash","Online/UPI","Cheque","RTGS/NEFT"] else 0,
                                                    key=f"emi_mode_{i}")
                            e_slip = ec4.text_input(f"Slip No #{i+1}",
                                                     value=str(pmt.get('slip_no', '')),
                                                     key=f"emi_slip_{i}")
                            e_rmk  = st.text_input(f"Remarks #{i+1}",
                                                    value=str(pmt.get('remarks', 'Installment Payment')),
                                                    key=f"emi_rmk_{i}")
                            new_emi_data.append({
                                'amount' : e_amt,
                                'date'   : e_date,
                                'mode'   : e_mode,
                                'slip_no': e_slip,
                                'remarks': e_rmk,
                            })

                        if st.form_submit_button("💾 Save All Changes", use_container_width=True, type="primary"):
                            actual_plt = st.session_state.booking_popup['plot']
                            real_plt   = st.session_state.db_projects[proj]['plots'].get(
                                actual_plt, {}).get('primary_plot_id', actual_plt)

                            # Save token updates
                            st.session_state.db_projects[proj]['plots'][real_plt]['token_amount']  = new_tok_amt
                            st.session_state.db_projects[proj]['plots'][real_plt]['receipt_date']  = new_tok_date
                            st.session_state.db_projects[proj]['plots'][real_plt]['payment_mode']  = new_tok_mode
                            st.session_state.db_projects[proj]['plots'][real_plt]['token_slip_no'] = new_tok_slip

                            # Save EMI updates
                            for i, emi in enumerate(new_emi_data):
                                st.session_state.db_projects[proj]['plots'][real_plt]['partial_payments'][i].update(emi)

                            if database.save_db_data():
                                st.success("✅ Sab changes save ho gaye!")
                                st.rerun()

            st.write("---")
            c_btn1, c_btn2 = st.columns(2)

            csv_statement = pd.DataFrame(history_rows).to_csv(index=False).encode('utf-8-sig')
            with c_btn1:
                st.download_button(
                    label="🖨️ Download Statement",
                    data=csv_statement,
                    file_name=f"Plot_{joined_view_str}_{p_data.get('customer_name','Client').replace(' ','_')}.csv",
                    mime="text/csv", use_container_width=True)

            cust_phone = str(p_data.get('phone', '')).replace(' ','').replace('+','').strip()
            if len(cust_phone) == 10: cust_phone = "91" + cust_phone

            wa_msg = (f"🌟 *FirstChoice Infra - Payment Update* 🌟\n\n"
                      f"Dear *{str(p_data.get('customer_name','Sir/Madam')).title()}*,\n"
                      f"Plot(s) *P-{joined_view_str}* in *{proj}*:\n\n"
                      f"🔹 *Total Value:* ₹ {total_cost_val:,.2f}\n"
                      f"✅ *Total Paid:* ₹ {total_overall_paid:,.2f}\n"
                      f"⚠️ *Outstanding:* ₹ {net_outstanding:,.2f}\n\n"
                      f"Thank you!\n*FC Infra Team*")
            wa_url = f"https://wa.me/{cust_phone}?text={urllib.parse.quote(wa_msg)}"
            with c_btn2:
                st.markdown(f'<a href="{wa_url}" target="_blank" class="wa-btn">💬 WhatsApp Update</a>',
                            unsafe_allow_html=True)

        if st.session_state.get('user_role') == 'admin':
            st.write("")
            st.warning("Force Cancel will revoke all plots in this booking.")
            if st.button("✅ Force Cancel & Revoke", use_container_width=True):
                plots_to_free = [p.strip() for p in p_data.get('booked_plots_str', str(plt)).split(",")]
                for f_plt in plots_to_free:
                    if f_plt in st.session_state.db_projects[proj]['plots']:
                        st.session_state.db_projects[proj]['plots'][f_plt] = {"status": "Available"}
                with st.spinner("Revoking..."):
                    if database.save_db_data():
                        st.success(f"Plots P-{joined_view_str} restored!")
                        del st.session_state['booking_popup']
                        st.rerun()

    st.write("---")
    if st.button("❌ Back to Grid", use_container_width=True):
        del st.session_state['booking_popup']
        st.rerun()
    st.stop()

st.markdown(f"### 📋 Project Inventory: {selected_project_name}")
st.write(f"📍 Khasra: {project_data.get('khasra','N/A')} | Mauza: {project_data.get('mauza','N/A')} | Total: {project_data.get('total_plots', 0)}")

cols_per_row = 5
plot_items   = list(plots.items())
rows         = [plot_items[i:i+cols_per_row] for i in range(0, len(plot_items), cols_per_row)]

for row in rows:
    cols = st.columns(cols_per_row)
    for i, (plot_id, plot_info) in enumerate(row):
        with cols[i]:
            status         = plot_info.get('status', 'Available')
            plot_exec_name = plot_info.get('executive_name', '')

            if status == "Available":
                st.markdown(f'<div class="plot-card plot-available">🏠 Plot {plot_id}<br>✅ Available</div>', unsafe_allow_html=True)
                btn_txt = "📝 Book Unit"; btn_disabled = False
            elif status == "Hold":
                st.markdown(f'<div class="plot-card plot-hold">🚧 Plot {plot_id}<br>🔒 On Hold</div>', unsafe_allow_html=True)
                btn_txt = "🔓 View Hold"; btn_disabled = False
            else:
                if is_authorized(plot_exec_name):
                    cust = plot_info.get('customer_name', 'N/A')
                    st.markdown(f'<div class="plot-card plot-booked">🛑 Plot {plot_id}<br>❌ Booked ({cust.split(" ")[0]})</div>', unsafe_allow_html=True)
                    btn_txt = "📄 Statement"; btn_disabled = False
                else:
                    st.markdown(f'<div class="plot-card plot-locked">🛑 Plot {plot_id}<br>🔒 Booked</div>', unsafe_allow_html=True)
                    btn_txt = "🔒 Access Denied"; btn_disabled = True

            if st.button(btn_txt, key=f"btn_{selected_project_name}_{plot_id}",
                         use_container_width=True, disabled=btn_disabled):
                st.session_state['booking_popup'] = {
                    'project': selected_project_name,
                    'plot': plot_id, 'current_status': status}
                st.rerun()

