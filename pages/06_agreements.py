import streamlit as st
import database
import datetime

# --- 1. Page Configuration ---
st.set_page_config(layout="wide", page_title="FC Infra - Legal Desk")

# --- 2. Security Interceptor Check ---
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

if st.session_state.get('user_role', 'admin') != 'admin':
    st.error("🚨 Security Alert: Only authorized Administrators can access the Legal Documentation Desk!")
    st.stop()

# --- 3. Database Initialization ---
database.init_db()
db_data = st.session_state.db_projects

# Global Theme Synchronization Logic
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
.block-container {{ background-color: {c_bg} !important; padding: 2rem 3rem !important; border-radius: 20px; box-shadow: 0px 10px 30px rgba(0,0,0,0.3); margin-top: 2rem; margin-bottom: 2rem; }}
h1, h2, h3 {{ color: {p_color} !important; font-weight: 800; }}
.stButton>button {{ background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%); color: white !important; border-radius: 6px; font-weight: bold; }}
textarea {{ font-family: 'Courier New', Courier, monospace !important; font-size: 14px !important; line-height: 1.6 !important; background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important; border-radius: 8px !important; padding: 15px !important; }}
.tag-help {{ background-color: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 15px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📄 Legal Allotment & Custom Agreement Desk</h1>", unsafe_allow_html=True)

# Initialize Agreement Template Storage Node in Database if completely missing
if '_agreement_templates' not in st.session_state.db_projects:
    st.session_state.db_projects['_agreement_templates'] = {
        "en": "AGREEMENT TO SALE\n=================\n\nThis agreement is made between M/s FIRSTCHOICE INFRA and Client {CLIENT_NAME}.\nPlot Details: Plot No {PLOT_NO} in project {PROJECT_NAME}.\nTotal Value: INR {SELLING_RATE}.\nAdvance Token Paid: INR {TOKEN_AMOUNT}.\nRemaining Outstanding: INR {OUTSTANDING_BALANCE}.",
        "hi": "विक्रय अनुबंध पत्र\n===============\n\nयह अनुबंध मेसर्स फर्स्टचॉइस इन्फ्रा एवं ग्राहक {CLIENT_NAME} के मध्य निष्पादित किया गया है।\nप्लॉट विवरण: प्रोजेक्ट {PROJECT_NAME} के अंतर्गत प्लॉट नंबर {PLOT_NO}।\nकुल सौदा मूल्य: ₹{SELLING_RATE}.\nजमा टोकन राशि: ₹{TOKEN_AMOUNT}.\nशेष बकाया राशि: ₹{OUTSTANDING_BALANCE}।",
        "mr": "विक्री करारनामा\n==============\n\nहा करारनामा मेसर्स फर्स्टचॉईस इन्फ्रा आणि ग्राहक {CLIENT_NAME} यांच्यात करण्यात आला आहे.\nप्लॉट तपशील: प्रोजेक्ट {PROJECT_NAME} मधील प्लॉट क्रमांक {PLOT_NO}.\nएकूण किंमत: ₹{SELLING_RATE}.\nजमा टोकन रक्कम: ₹{TOKEN_AMOUNT}.\nउर्वरित थकबाकी: ₹{OUTSTANDING_BALANCE}."
    }

# ====================================================================
# ⚙️ ADMIN ONLY: Custom Master Template Upload Panel
# ====================================================================
with st.expander("🛠️ Admin Master Template Configuration Desk (Upload Your Formats Here)"):
    st.markdown("#### Paste your professional lawyer-approved formats below. Use the exact tags to auto-fill customer metrics:")
    st.markdown("""
    <div class="tag-help">
        <b>Smart Alignment Tags:</b><br>
        <code>{CLIENT_NAME}</code> - Customer Name | <code>{CLIENT_PHONE}</code> - Contact Number | <code>{CLIENT_ADDRESS}</code> - Address<br>
        <code>{CLIENT_AADHAAR}</code> - Aadhaar Card | <code>{CLIENT_PAN}</code> - PAN Card | <code>{NOMINEE_NAME}</code> - Nominee Name<br>
        <code>{PROJECT_NAME}</code> - Project Name | <code>{PLOT_NO}</code> - Plot Number | <code>{PLOT_SIZE}</code> - Area Sq.Ft<br>
        <code>{KHASRA_NO}</code> - Khasra No | <code>{MAUZA}</code> - Mauza Location | <code>{TAHSIL}</code> - Tahsil Location<br>
        <code>{SELLING_RATE}</code> - Deal Price | <code>{TOKEN_AMOUNT}</code> - Token Advance | <code>{OUTSTANDING_BALANCE}</code> - Remaining Outstanding Due
    </div>
    """, unsafe_allow_html=True)
    
    tab_en, tab_hi, tab_mr = st.tabs(["English Format", "Hindi Format (हिंदी)", "Marathi Format (मराठी)"])
    
    with tab_en:
        custom_en = st.text_area("Master English Template Structure", value=st.session_state.db_projects['_agreement_templates']['en'], height=250, key="cfg_en")
    with tab_hi:
        custom_hi = st.text_area("Master Hindi Template Structure", value=st.session_state.db_projects['_agreement_templates']['hi'], height=250, key="cfg_hi")
    with tab_mr:
        custom_mr = st.text_area("Master Marathi Template Structure", value=st.session_state.db_projects['_agreement_templates']['mr'], height=250, key="cfg_mr")
        
    if st.button("💾 Save Custom Templates Permanently to Cloud Database", use_container_width=True):
        st.session_state.db_projects['_agreement_templates']['en'] = custom_en
        st.session_state.db_projects['_agreement_templates']['hi'] = custom_hi
        st.session_state.db_projects['_agreement_templates']['mr'] = custom_mr
        if database.save_db_data():
            st.success("🎉 Your custom legal formats have been successfully uploaded and securely saved!")
            st.rerun()

# --- Dropdown Configuration Matrix ---
st.markdown("### 🏢 Select Customer Node to Compile Contract")
col_s1, col_s2 = st.columns(2)
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

if not project_names:
    st.warning("⚠️ No active projects found in blueprints registry. Please map layouts via Admin Panel first.")
    st.stop()

selected_project = col_s1.selectbox("🏢 Select Active Layout Project", project_names)

project_profile = db_data[selected_project]
plot_registry = project_profile.get('plots', {})
if isinstance(plot_registry, list):
    plot_registry = {str(idx): p for idx, p in enumerate(plot_registry) if p is not None}

booked_plots_list = [p_id for p_id, p_info in plot_registry.items() if isinstance(p_info, dict) and p_info.get('status') == 'Booked']

if not booked_plots_list:
    st.info("ℹ️ No active booked plot nodes available in this project profile to compile contracts.")
    st.stop()

selected_plot = col_s2.selectbox("🎯 Select Targeted Booked Plot Unit", sorted(booked_plots_list, key=lambda x: int(x) if x.isdigit() else 9999))

# --- Language Selection Interface Feature ---
agreement_lang = st.radio("🌐 Choose Output Language for Printing / दस्तऐवज भाषा निवडा / दस्तावेज़ भाषा चुनें", ["English", "Hindi (हिंदी)", "Marathi (मराठी)"], horizontal=True)

# --- Extract Customer Structural Node Safely ---
p_data = plot_registry[selected_plot]

c_name = p_data.get('customer_name', 'N/A')
c_phone = p_data.get('phone', 'N/A')
c_address = p_data.get('address', 'N/A')
c_aadhaar = p_data.get('aadhaar', 'N/A')
c_pan = p_data.get('pan', 'N/A')
n_name = p_data.get('nominee_name', 'N/A')
p_size = p_data.get('plot_area', 'N/A')

# Calculation metrics for legal variables
rate_selling = float(p_data.get('selling_rate', 0.0))
amt_token = float(p_data.get('token_amount', 0.0))

# Extract project layout variables
khasra_no = project_profile.get('khasra', 'N/A')
mauza_loc = project_profile.get('mauza', 'N/A')
tahsil_loc = project_profile.get('tahsil', 'N/A')

# Calculate EMI remaining outstanding components
partial_payments = p_data.get('partial_payments', [])
total_partial = sum(float(pmt.get('amount', 0.0)) for pmt in partial_payments)
total_accumulated_received = amt_token + total_partial
net_outstanding_balance = max(0.0, rate_selling - total_accumulated_received)

# --- Fetch the Custom Uploaded Template based on selected language ---
if agreement_lang == "Hindi (हिंदी)":
    base_template = st.session_state.db_projects['_agreement_templates']['hi']
elif agreement_lang == "Marathi (मराठी)":
    base_template = st.session_state.db_projects['_agreement_templates']['mr']
else:
    base_template = st.session_state.db_projects['_agreement_templates']['en']

# --- Dynamic Replacement Engine ---
compiled_contract = base_template\
    .replace("{CLIENT_NAME}", str(c_name).upper())\
    .replace("{CLIENT_PHONE}", str(c_phone))\
    .replace("{CLIENT_ADDRESS}", str(c_address))\
    .replace("{CLIENT_AADHAAR}", str(c_aadhaar))\
    .replace("{CLIENT_PAN}", str(c_pan).upper())\
    .replace("{NOMINEE_NAME}", str(n_name).upper())\
    .replace("{PROJECT_NAME}", str(selected_project).upper())\
    .replace("{PLOT_NO}", str(selected_plot))\
    .replace("{PLOT_SIZE}", str(p_size))\
    .replace("{KHASRA_NO}", str(khasra_no))\
    .replace("{MAUZA}", str(mauza_loc))\
    .replace("{TAHSIL}", str(tahsil_loc))\
    .replace("{SELLING_RATE}", f"{rate_selling:,.2f}")\
    .replace("{TOKEN_AMOUNT}", f"{amt_token:,.2f}")\
    .replace("{OUTSTANDING_BALANCE}", f"{net_outstanding_balance:,.2f}")

st.write("---")
st.markdown("### 📝 Live Assembled Contract Preview (Editable Window)")
st.caption("Review the auto-populated contract data. You can modify any terms or clauses manually in this text area below before hitting print.")

# Interactive text box containing fully rendered contract ready to be edited or printed
final_printable_text = st.text_area("Live Contract Workspace Editor Pane", value=compiled_contract, height=500)

# --- Print / Download Export Desk Controls ---
st.write("")
col_b1, col_b2 = st.columns(2)
agreement_bytes = final_printable_text.encode('utf-8')

col_b1.download_button(
    label="📥 Download Agreement File (.txt format)",
    data=agreement_bytes,
    file_name=f"Agreement_Project_{selected_project}_Plot_{selected_plot}.txt",
    mime="text/plain",
    use_container_width=True
)

with col_b2:
    if st.button("🖨️ Open Browser Print Window (Ctrl+P)", use_container_width=True):
        st.info("💡 To print flawlessly: Simply click inside the text window, press Ctrl+A to select all, copy it, and paste it into Microsoft Word / Notepad for your exact letterhead margin alignments.")
