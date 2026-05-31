import streamlit as st
import pandas as pd
import datetime

if not st.session_state.get('logged_in'): st.stop()

# -------------------------------------------------------------
# सेंट्रल मेमोरी (Central Database) इनिशियलाइज़ेशन 
# (यही वो जादू है जिससे हर पेज का डेटा आपस में जुड़ता है)
# -------------------------------------------------------------
if 'exec_data' not in st.session_state: st.session_state.exec_data = {}
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'bookings' not in st.session_state: st.session_state.bookings = {}

st.markdown("## 👥 Executive & Commission Panel")

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
    comm_type = c4.radio("Commission Type", ["Percentage (%)", "Rupees (₹)"], horizontal=True)

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
                e_type = st.radio("Update Commission Type", ["Percentage (%)", "Rupees (₹)"], index=0 if "Percentage" in ed['comm_type'] else 1, horizontal=True)
                
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
# सेक्शन 3: Detailed Commission Statement (Connected with Inventory)
# -------------------------------------------------------------
st.write("---")
st.subheader("📄 Commission Details Statement", divider="green")

# स्मार्ट सिंक: उन सभी एग्जीक्यूटिव्स का नाम ढूंढना जो या तो यहाँ ऐड हुए हैं, या इन्वेंट्री बुकिंग में हैं!
execs_from_struct = [v["exec_name"] for v in st.session_state.exec_data.values()]
execs_from_bookings = [v.get("exec_name") for v in st.session_state.bookings.values() if v.get("exec_name")]
unique_execs = list(set(execs_from_struct + execs_from_bookings))

if unique_execs:
    sc1, sc2, sc3 = st.columns([2, 1, 1])
    search_exec = sc1.selectbox("🔍 Select Executive", ["Select..."] + unique_execs)
    
    start_date = sc2.date_input("📅 Start Date", value=datetime.date.today().replace(day=1))
    end_date = sc3.date_input("📅 End Date", value=datetime.date.today())

    if search_exec != "Select...":
        st.markdown(f"#### 👤 Statement for: **{search_exec}** ({start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')})")
        
        exec_bookings = []
        sr_no = 1
        total_net_payable = 0

        # सीधा इन्वेंट्री के डेटाबेस (st.session_state.bookings) से डाटा खींचना
        for b_key, b_val in st.session_state.bookings.items():
            if b_val.get("exec_name") == search_exec:
                b_date = b_val.get("recv_date", datetime.date.today())
                
                if isinstance(b_date, datetime.date) and (start_date <= b_date <= end_date):
                    proj_name, plot_no = b_key.rsplit("_", 1)
                    mauza = st.session_state.projects.get(proj_name, {}).get("mauza", "N/A")
                    
                    # कमीशन कैलकुलेशन
                    struct_key = f"{search_exec}_{proj_name}"
                    gross_comm = 0
                    rate_text = "Rule Not Set"
                    
                    if struct_key in st.session_state.exec_data:
                        struct = st.session_state.exec_data[struct_key]
                        rate = struct['exec_comm']
                        if "Percentage" in struct['comm_type']:
                            gross_comm = (b_val.get("received_amt", 0) * rate) / 100
                            rate_text = f"{rate}%"
                        else:
                            gross_comm = rate
                            rate_text = f"₹{rate}"

                    discount_deducted = b_val.get("exec_discount_penalty", 0) 
                    comm_after_disc = gross_comm - discount_deducted
                    tds_amount = comm_after_disc * 0.02
                    net_comm = comm_after_disc - tds_amount
                    
                    total_net_payable += net_comm

                    # टेबल के लिए डेटा
                    exec_bookings.append({
                        "Sr.": sr_no,
                        "Plot": f"{proj_name} - #{plot_no}",
                        "Client Name": b_val.get("c_name", "N/A"),
                        "Mauza": mauza,
                        "Amount & Date": f"₹{b_val.get('received_amt', 0)} on {b_date.strftime('%d-%m-%Y')}",
                        "Comm. Rate": rate_text,
                        "Calc. Comm.": f"₹{round(gross_comm, 2)}",
                        "Discount (-)": f"₹{round(discount_deducted, 2)}",
                        "TDS 2% (-)": f"₹{round(tds_amount, 2)}",
                        "Net Payable": f"₹{round(net_comm, 2)}"
                    })
                    sr_no += 1

        if exec_bookings:
            st.dataframe(pd.DataFrame(exec_bookings), use_container_width=True, hide_index=True)
            st.success(f"### 💰 Total Net Payable Commission: ₹{round(total_net_payable, 2)}")
            
            st.write("---")
            c4, c5, c6 = st.columns([1, 1, 2])
            if c4.button("🖨️ Print Statement", use_container_width=True):
                st.info("प्रिंटिंग प्रोसेस शुरू हो रहा है...")
            if c5.button("💬 WhatsApp Statement", use_container_width=True):
                st.success("WhatsApp लिंक जनरेट हो गया है!")
        else:
            st.warning("🚨 इस एग्जीक्यूटिव की दी गई तारीखों के बीच कोई बुकिंग दर्ज नहीं है।")
