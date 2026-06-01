import streamlit as st
import pandas as pd
import datetime

if not st.session_state.get('logged_in'): st.stop()

# सेंट्रल मेमोरी इनिशियलाइज़ेशन
if 'exec_data' not in st.session_state: st.session_state.exec_data = {}
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.markdown("## 👥 Executive & Commission Chain Panel")

# -------------------------------------------------------------
# सेक्शन 1: नया एग्जीक्यूटिव और कमीशन स्ट्रक्चर ऐड करना
# -------------------------------------------------------------
st.subheader("➕ Add Commission Structure", divider="blue")
with st.form("add_exec_form"):
    c1, c2 = st.columns(2)
    proj_list = ["Common / All Projects"] + list(st.session_state.projects.keys())
    layout = c1.selectbox("Select Layout / Project", proj_list)
    exec_name = c2.text_input("Executive Name")

    c3, c4 = st.columns(2)
    senior_name = c3.text_input("Senior Name (Reporting To)")
    comm_type = c4.radio("Commission Type", ["Percentage (%)", "Rupees (₹/Sqft)"], horizontal=True)

    c5, c6 = st.columns(2)
    exec_comm = c5.number_input(f"Executive Commission in {comm_type}", min_value=0.0)
    senior_comm = c6.number_input(f"Senior Commission in {comm_type}", min_value=0.0)

    if st.form_submit_button("✅ Save & Lock Entry", use_container_width=True):
        if exec_name.strip() == "":
            st.error("Please enter Executive Name!")
        else:
            key = f"{exec_name}_{layout}"
            st.session_state.exec_data[key] = {
                "exec_name": exec_name, "layout": layout, "senior": senior_name,
                "comm_type": comm_type, "exec_comm": exec_comm, "senior_comm": senior_comm
            }
            st.success(f"🎉 {exec_name} का डेटा {layout} के लिए सफलतापूर्वक लॉक हो गया!")
            st.rerun()

# -------------------------------------------------------------
# सेक्शन 2: एंट्री एडिट करना (Edit & Save)
# -------------------------------------------------------------
with st.expander("✏️ Edit Existing Entries (Click to Expand)"):
    exec_keys = list(st.session_state.exec_data.keys())
    if exec_keys:
        edit_key = st.selectbox("Select Entry to Edit", ["Select..."] + exec_keys)
        if edit_key != "Select...":
            ed = st.session_state.exec_data[edit_key]
            with st.form("edit_exec_form"):
                st.info(f"**Editing:** {ed['exec_name']} | **Layout:** {ed['layout']}")
                e_sen = st.text_input("Update Senior Name", value=ed['senior'])
                e_type = st.radio("Update Commission Type", ["Percentage (%)", "Rupees (₹/Sqft)"], index=0 if "Percentage" in ed['comm_type'] else 1, horizontal=True)
                
                c7, c8 = st.columns(2)
                e_ec = c7.number_input("Update Executive Comm.", value=float(ed['exec_comm']))
                e_sc = c8.number_input("Update Senior Comm.", value=float(ed['senior_comm']))

                if st.form_submit_button("💾 Save Changes"):
                    st.session_state.exec_data[edit_key].update({
                        "senior": e_sen, "comm_type": e_type,
                        "exec_comm": e_ec, "senior_comm": e_sc
                    })
                    st.success("✅ Changes Updated Successfully!")
                    st.rerun()
    else:
        st.caption("No entries available to edit yet.")

# -------------------------------------------------------------
# सेक्शन 3: Detailed Commission Statement (सटीक कैलकुलेशन लॉजिक)
# -------------------------------------------------------------
st.write("---")
st.subheader("📄 Commission Details Statement", divider="green")

# स्मार्ट सिंक नाम ढूंढना
execs_from_struct = [v["exec_name"] for v in st.session_state.exec_data.values()]
execs_from_bookings = [v.get("exec_name") for v in st.session_state.bookings.values() if v.get("exec_name")]
unique_execs = list(set(execs_from_struct + execs_from_bookings))

if unique_execs:
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    search_exec = sc1.selectbox("🔍 Select Executive to View Statement", ["Select..."] + unique_execs)
    
    # तारीख फ़िल्टर
    start_date = sc2.date_input("📅 Start Date", value=datetime.date.today().replace(day=1))
    end_date = sc3.date_input("📅 End Date", value=datetime.date.today())

    if search_exec != "Select...":
        st.markdown(f"#### 👤 Detailed Statement for: **{search_exec}**")
        st.caption(f"Period: {start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')}")
        
        exec_bookings = []
        sr_no = 1
        total_gross_comm = 0
        total_tds = 0
        total_net_payable = 0

        # सभी बुकिंग्स और उनकी EMI पेमेंट हिस्ट्री को स्कैन करना
        for b_key, b_val in st.session_state.bookings.items():
            if b_val.get("exec_name") == search_exec:
                proj_name, plot_no = b_key.rsplit("_", 1)
                mauza = st.session_state.projects.get(proj_name, {}).get("mauza", "N/A")
                
                comp_rate = float(b_val.get("comp_rate", 0))
                sell_rate = float(b_val.get("sell_rate", 0))
                client_name = b_val.get("c_name", "N/A")
                
                # कमीशन रूल चेक करना
                struct_key = f"{search_exec}_{proj_name}"
                base_rate = 0
                comm_type_text = "N/A"
                
                if struct_key in st.session_state.exec_data:
                    struct = st.session_state.exec_data[struct_key]
                    base_rate = struct['exec_comm']
                    comm_type_text = struct['comm_type']
                else:
                    proj_data = st.session_state.projects.get(proj_name, {})
                    base_rate = proj_data.get("max_commission", 0)
                    comm_type_text = proj_data.get("comm_type", "N/A")

                # हर एक पेमेंट (टोकन या EMI) को अलग-अलग तारीख के हिसाब से कैलकुलेट करना
                for payment in b_val.get("payment_history", []):
                    p_date = payment.get("date")
                    
                    # सिर्फ़ चुनी हुई तारीखों के बीच का पेमेंट प्रोसेस करना
                    if isinstance(p_date, datetime.date) and (start_date <= p_date <= end_date):
                        p_amt = float(payment.get("amount", 0))
                        
                        # 1. रिसीव्ड अमाउंट के आधार पर चुकाया गया स्क्वायर फीट एरिया निकालना
                        paid_area = p_amt / comp_rate if comp_rate > 0 else 0
                        
                        # 2. प्रति स्क्वायर फीट डिस्काउंट निकालना
                        discount_per_sqft = max(0.0, comp_rate - sell_rate)
                        total_discount_deducted = paid_area * discount_per_sqft
                        
                        # 3. कमीशन टाइप के हिसाब से बेस कैलकुलेशन
                        if "Percentage" in comm_type_text:
                            base_comm = p_amt * (base_rate / 100)
                            gross_comm = base_comm - total_discount_deducted
                        else:
                            # यदि रुपयों में है (उदा. ₹250/sqft - ₹75/sqft = ₹175/sqft)
                            base_comm = paid_area * base_rate
                            gross_comm = paid_area * (base_rate - discount_per_sqft)
                        
                        gross_comm = max(0.0, gross_comm)
                        tds_amount = gross_comm * 0.02
                        net_payable = gross_comm - tds_amount
                        
                        # ग्रैंड टोटल्स जोड़ना
                        total_gross_comm += gross_comm
                        total_tds += tds_amount
                        total_net_payable += net_payable

                        # एकदम सटीक कॉलम स्ट्रक्चर तैयार करना
                        exec_bookings.append({
                            "Sr.": sr_no,
                            "Plot & Mauza": f"{proj_name} #{plot_no} ({mauza})",
                            "Client Name": client_name,
                            "Amount & Date Received": f"₹{p_amt} on {p_date.strftime('%d-%m-%Y')}",
                            "Paid Area (Sqft)": round(paid_area, 2),
                            "Comm Rule": f"{base_rate} ({'%' if 'Percentage' in comm_type_text else '₹/Sqft'})",
                            "Base Comm": f"₹{round(base_comm, 2)}",
                            "Discount (-)": f"₹{round(total_discount_deducted, 2)}",
                            "Gross Comm": f"₹{round(gross_comm, 2)}",
                            "TDS 2% (-)": f"₹{round(tds_amount, 2)}",
                            "Net Payable": f"₹{round(net_payable, 2)}"
                        })
                        sr_no += 1

        # रिजल्ट ग्रिड रेंडर करना
        if exec_bookings:
            df_statement = pd.DataFrame(exec_bookings)
            st.dataframe(df_statement, use_container_width=True, hide_index=True)
            
            # आकर्षक समरी बॉक्स
            st.write("")
            c_sm1, c_sm2, c_sm3 = st.columns(3)
            c_sm1.metric("📊 Total Gross Commission", f"₹{round(total_gross_comm, 2)}")
            c_sm2.metric("🛡️ Total TDS Deducted (2%)", f"₹{round(total_tds, 2)}")
            c_sm3.metric("💰 Total Net Payable (Hand Cash)", f"₹{round(total_net_payable, 2)}")
            
            st.write("---")
            # एक्शन बटन्स
            c4, c5 = st.columns(2)
            if c4.button("🖨️ Print Statement", use_container_width=True):
                st.success("📄 प्रिंट रेडी प्रारूप जनरेट हो रहा है...")
                
            if c5.button("💬 Send Statement via WhatsApp", use_container_width=True):
                st.success(f"📲 {search_exec} के व्हाट्सएप पर स्टेटमेंट समरी भेजने का लिंक तैयार है!")
        else:
            st.warning("🚨 इस समयावधि (Date Range) के बीच इस एग्जीक्यूटिव की कोई पेमेंट एंट्री नहीं मिली।")
else:
    st.caption("No executives logged in the database yet.")
