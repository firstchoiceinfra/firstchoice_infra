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
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>📄 Legal Allotment & Agreement Processing Desk</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 14px; color: #475569; margin-bottom: 30px;'>Automated Multi-Language Contract Assembly, Dynamic Placeholders & Live Customization Panel</p>", unsafe_allow_html=True)

# Fetching active layout projects list
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

if not project_names:
    st.warning("⚠️ No active projects found in registry blueprints. Please map infrastructure layouts via Admin Panel first.")
    st.stop()

# --- Dropdown Configuration Matrix ---
col_s1, col_s2 = st.columns(2)
selected_project = col_s1.selectbox("🏢 Select Layout Blueprint Project", project_names)

project_profile = db_data[selected_project]
plot_registry = project_profile.get('plots', {})

if isinstance(plot_registry, list):
    plot_registry = {str(idx): p for idx, p in enumerate(plot_registry) if p is not None}

booked_plots_list = [p_id for p_id, p_info in plot_registry.items() if isinstance(p_info, dict) and p_info.get('status') == 'Booked']

if not booked_plots_list:
    st.info("ℹ️ No active booked plot nodes available in this project profile to compile contracts.")
    st.stop()

selected_plot = col_s2.selectbox("🎯 Select Targeted Booked Plot Unit", sorted(booked_plots_list, key=lambda x: int(x) if x.isdigit() else 9999))

# --- Dynamic Language Selection Interface Feature ---
st.write("")
agreement_lang = st.radio("🌐 Select Document Generation Language / दस्तऐवज भाषा निवडा / दस्तावेज़ भाषा चुनें", ["English", "Hindi (हिंदी)", "Marathi (मराठी)"], horizontal=True)

# --- Extract Customer Structural Node Safely ---
p_data = plot_registry[selected_plot]

c_name = p_data.get('customer_name', 'N/A')
c_phone = p_data.get('phone', 'N/A')
c_dob = p_data.get('dob', 'N/A')
c_address = p_data.get('address', 'N/A')
c_aadhaar = p_data.get('aadhaar', 'N/A')
c_pan = p_data.get('pan', 'N/A')
n_name = p_data.get('nominee_name', 'N/A')
n_age = p_data.get('nominee_age', 'N/A')
p_size = p_data.get('plot_area', 'N/A')

# Calculation metrics for legal variables
rate_selling = float(p_data.get('selling_rate', 0.0))
amt_token = float(p_data.get('token_amount', 0.0))
pmt_mode = p_data.get('payment_mode', 'Cash')
txn_ref = p_data.get('transaction_id', 'N/A')
rcpt_date = p_data.get('receipt_date', p_data.get('booking_date', 'N/A'))

# Extract project layout variables
khasra_no = project_profile.get('khasra', 'N/A')
ph_no = project_profile.get('ph_no', 'N/A')
mauza_loc = project_profile.get('mauza', 'N/A')
tahsil_loc = project_profile.get('tahsil', 'N/A')
dist_loc = project_profile.get('district', 'N/A')

# Calculate Age
try:
    calculated_age = datetime.date.today().year - int(c_dob.split('-')[0]) if '-' in c_dob else 'N/A'
except:
    calculated_age = 'N/A'

partial_payments = p_data.get('partial_payments', [])
total_partial = sum(float(pmt.get('amount', 0.0)) for pmt in partial_payments)
total_accumulated_received = amt_token + total_partial
net_outstanding_balance = max(0.0, rate_selling - total_accumulated_received)

st.write("---")
st.markdown("### 🛠️ Interactive Legal Template Assembler Desk")

# ====================================================================
# 📜 MULTI-LANGUAGE ENGINE TEMPLATES (English, Hindi, Marathi)
# ====================================================================

# 1. ENGLISH TEMPLATE STRUCT
template_en = f"""AGREEMENT TO SALE / ALLOTMENT CUM CONTRACT LETTERS
================================================================================

This Agreement to Sale is executed on this date {datetime.date.today().strftime('%B %d, %Y')} at Nagpur, Maharashtra.

BY AND BETWEEN:
M/s. FIRSTCHOICE INFRA, having its operational business desk at Nagpur, Maharashtra, represented through its Managing Director/Authorized Signatory (hereinafter referred to as the "DEVELOPER") of the FIRST PART.

AND:
Mr./Ms. {c_name.upper()}, Aged about {calculated_age} years, residing at permanent address: {c_address}, holding Contact No: {c_phone}, Aadhaar Card No: {c_aadhaar}, and PAN Registry ID: {c_pan} (hereinafter referred to as the "ALLOTTEE") of the SECOND PART.

WHEREAS, the Developer is developing a residential layout plotting infrastructure project named "{selected_project.upper()}" situated at Khasra No: {khasra_no}, PH No: {ph_no}, Mauza: {mauza_loc}, Tahsil: {tahsil_loc}, District: {dist_loc}, Maharashtra.

AND WHEREAS, the Allottee has inspected the layout blueprint and has requested to purchase and secure one specific plot designated as Plot No: P-{selected_plot}, measuring an approximate dimension area size of {p_size} Sq.Ft.

NOW THIS AGREEMENT WITNESSETH AND IT IS MUTUALLY AGREED AS FOLLOWS:

1. CONSIDERATION & PAYOUT STRUCTURE:
   The total mutually agreed commercial value for the scheduling of the said plot unit is finalized at Gross Value: ₹{rate_selling:,.2f} (Rupees Only).

2. ADVANCE BOOKING TOKEN RECEIPT LOG:
   The Allottee has secured the allocation booking parameters by paying an initial Token/Advance amount of ₹{amt_token:,.2f} via Payment Channel: {pmt_mode} (Ref Transaction ID: {txn_ref}) cleared on date: {rcpt_date}.
   Subsequent partial installment credits tracked on financial ledgers amount to: ₹{total_partial:,.2f}.
   Total Accumulated Credits Received till date: ₹{total_accumulated_received:,.2f}.

3. BALANCE REMAINING OUTSTANDING:
   The remaining outstanding balance value of ₹{net_outstanding_balance:,.2f} shall be paid by the Allottee in progressive structural installment timelines as mutually configured with the Accounts Desk of Firstchoice Infra.

4. NOMINEE ATTRIBUTION DECLARATION:
   In the event of unforeseen causalities, the rights, titles, and legal attributes of this plot allocation contract shall transfer completely to the designated nominee: {n_name} (Stated Age Reference: {n_age} years).

5. TERMS OF SPECIFICATION AND DEVELOPMENT:
   The Developer covenants to deliver pristine plotting standards including foundational infrastructure layouts, layout markings, and demarcated boundary pathways according to layout specification blueprints.

IN WITNESS WHEREOF, both contracting parties have affixed their signatures and authorization seals under free will and consent on the day and year first above written.


----------------------------------------- -----------------------------------------
FIRSTCHOICE INFRA (DEVELOPER) ALLOTTEE / CLIENT SIGNATURE


Witness 1: ______________________________ Witness 2: ______________________________
"""

# 2. HINDI TEMPLATE STRUCT
template_hi = f"""विक्रय अनुबंध / आवंटन सह अनुबंध पत्र
================================================================================

यह विक्रय अनुबंध आज दिनांक {datetime.date.today().strftime('%d-%m-%Y')} को नागपुर, महाराष्ट्र में निष्पादित किया गया है।

प्रथम पक्ष (विकासकर्ता):
मेसर्स फर्स्टचॉइस इन्फ्रा (M/s. FIRSTCHOICE INFRA), मुख्य कार्यालय नागपुर, महाराष्ट्र, द्वारा अधिकृत हस्ताक्षरकर्ता/प्रबंध निदेशक (जिन्हें आगे "विकासकर्ता/डेवलपर" कहा जाएगा)।

द्वितीय पक्ष (आवंटिती/क्रेता):
श्री/श्रीमती/सुश्री {c_name.upper()}, आयु लगभग {calculated_age} वर्ष, निवासी स्थाई पता: {c_address}, मोबाइल नंबर: {c_phone}, आधार कार्ड नंबर: {c_aadhaar}, एवं पैन कार्ड नंबर: {c_pan} (जिन्हें आगे "आवंटिती/क्रेता" कहा जाएगा)।

चूंकि, विकासकर्ता नागपुर, महाराष्ट्र में एक आवासीय प्लॉटिंग प्रोजेक्ट का विकास कर रहा है, जिसका नाम "{selected_project.upper()}" है, जो कि खसरा नंबर: {khasra_no}, पटवारी हल्का नंबर (PH No): {ph_no}, मौजा: {mauza_loc}, तहसील: {tahsil_loc}, जिला: {dist_loc}, महाराष्ट्र पर स्थित है।

और चूंकि, आवंटिती ने उक्त लेआउट का निरीक्षण किया है और प्लॉट नंबर: P-{selected_plot} को खरीदने का अनुरोध किया है, जिसका कुल क्षेत्रफल लगभग {p_size} वर्ग फीट है।

अतः अब यह अनुबंध निम्नलिखित शर्तों के अधीन दोनों पक्षों के बीच सहमति से निष्पादित किया जाता है:

1. कुल प्रतिफल राशि (सौदे का मूल्य):
   उक्त प्लॉट का कुल परस्पर तयशुदा व्यावसायिक मूल्य ₹{rate_selling:,.2f} (अक्षरी केवल रुपये) निश्चित किया गया है।

2. अग्रिम बुकिंग टोकन राशि का विवरण:
   आवंटिती ने प्लॉट सुरक्षित करने हेतु अग्रिम टोकन राशि ₹{amt_token:,.2f}, भुगतान माध्यम: {pmt_mode} (ट्रांजैक्शन आईडी/संदर्भ संख्या: {txn_ref}) के द्वारा दिनांक: {rcpt_date} को भुगतान कर दिया है।
   इसके पश्चात खातों में जमा की गई आंशिक किश्त राशि: ₹{total_partial:,.2f} है।
   आज दिनांक तक प्राप्त कुल संचित जमा राशि (Total Paid): ₹{total_accumulated_received:,.2f} है।

3. शेष बकाया राशि (Outstanding Due):
   सौदे की बची हुई शेष राशि ₹{net_outstanding_balance:,.2f} आवंटिती द्वारा फर्स्टचॉइस इन्फ्रा के लेखा विभाग के साथ तय समयावधि के भीतर किश्तों के रूप में देय होगी।

4. नामांकित व्यक्ति (Nominee) की घोषणा:
   किसी भी अप्रत्याशित परिस्थिति या आकस्मिक घटना की स्थिति में, इस आवंटन अनुबंध के सभी कानूनी अधिकार और स्वत्व आवंटिती द्वारा घोषित नामांकित व्यक्ति: {n_name} (आयु लगभग: {n_age} वर्ष) को हस्तांतरित कर दिए जाएंगे।

5. विकास एवं बुनियादी ढांचा शर्तें:
   विकासकर्ता लेआउट ब्ल्यूप्रिंट के अनुसार सीमेंट रोड (Cement Road), लेआउट सीमांकन, और मूलभूत बुनियादी ढांचा मानकों को समय पर पूरा करने के लिए प्रतिबद्ध है।

जिसके साक्ष्य के रूप में, दोनों पक्षों ने बिना किसी दबाव के अपनी स्वेच्छा और सहमति से इस दस्तावेज़ पर अपने हस्ताक्षर और मुहर अंकित कर दिए हैं।


----------------------------------------- -----------------------------------------
फर्स्टचॉइस इन्फ्रा (विकासकर्ता) आवंटिती / क्रेता के हस्ताक्षर


गवाह १: ______________________________ गवाह २: ______________________________
"""

# 3. MARATHI TEMPLATE STRUCT
template_mr = f"""विक्री करारनामा / वाटप पत्र व करारनामा
================================================================================

हा विक्री करारनामा आज दिनांक {datetime.date.today().strftime('%d-%m-%Y')} रोजी नागपूर, महाराष्ट्र येथे निष्पादित करण्यात आला आहे।

प्रथम पक्ष (डेव्हलपर):
मेसर्स फर्स्टचॉइस इन्फ्रा (M/s. FIRSTCHOICE INFRA), मुख्य कार्यालय नागपूर, महाराष्ट्र, तर्फे व्यवस्थापकीय संचालक/अधिकृत स्वाक्षरीकर्ता (ज्यांचा उल्लेख पुढे "डेव्हलपर" असा केला जाईल)।

द्वितीय पक्ष (वाटपधारक/खरेदीदार):
श्री/श्रीमती/कु. {c_name.upper()}, वय अंदाजे {calculated_age} वर्षे, राहणार कायमचा पत्ता: {c_address}, मोबाईल क्रमांक: {c_phone}, आधार कार्ड क्रमांक: {c_aadhaar}, आणि पॅन कार्ड क्रमांक: {c_pan} (ज्यांचा उल्लेख पुढे "वाटपधारक/खरेदीदार" असा केला जाईल)।

ज्याअर्थी, डेव्हलपर नागपूर, महाराष्ट्र येथे एक निवासी प्लॉटिंग प्रोजेक्ट विकसित करीत आहे, ज्याचे नाव "{selected_project.upper()}" असे असून ते खसरा क्रमांक: {khasra_no}, पटवारी हल्का क्रमांक (PH No): {ph_no}, मौजा: {mauza_loc}, तालुका: {tahsil_loc}, जिल्हा: {dist_loc}, महाराष्ट्र येथे स्थित आहे।

आणि ज्याअर्थी, वाटपधारकाने सदर लेआउटची पाहणी केली आहे आणि प्लॉट क्रमांक: P-{selected_plot} खरेदी करण्याची विनंती केली आहे, ज्याचे एकूण क्षेत्रफळ अंदाजे {p_size} स्क्वेअर फीट आहे।

म्हणून आता हा करारनामा खालील अटी व शर्तींनुसार दोन्ही पक्षांच्या संमतीने निश्चित करण्यात येत आहे:

1. एकूण खरेदी किंमत (व्यवहार मूल्य):
   सदर प्लॉटची एकूण परस्पर संमत झालेली किंमत ₹{rate_selling:,.2f} (अक्षरी फक्त रुपये) निश्चित करण्यात आली आहे।

2. अनामत बुकिंग टोकन रकमेचा तपशील:
   वाटपधारकाने प्लॉट आरक्षित करण्यासाठी सुरुवातीची टोकन रक्कम ₹{amt_token:,.2f}, पेमेंट मोड: {pmt_mode} (ट्रान्झॅक्शन आयडी/संदर्भ क्रमांक: {txn_ref}) द्वारे दिनांक: {rcpt_date} रोजी अदा केली आहे।
   त्यानंतर खात्यात जमा झालेली अंशतः हप्त्याची रक्कम: ₹{total_partial:,.2f} आहे।
   आजच्या तारखेपर्यंत प्राप्त झालेली एकूण जमा रक्कम (Total Paid): ₹{total_accumulated_received:,.2f} आहे।

3. उर्वरित थकीत रक्कम (Outstanding Due):
   व्यवहाराची उर्वरित थकीत रक्कम ₹{net_outstanding_balance:,.2f} वाटपधारकाने फर्स्टचॉईस इन्फ्राच्या अकाऊंट्स विभागासोबत ठरवलेल्या मुदतीत हप्त्यांद्वारे भरणे बंधनकारक राहील।

4. वारसदार (Nominee) घोषणा:
   कोणत्याही अनपेक्षित परिस्थिती उद्भवल्यास, या वाटप कराराचे सर्व कायदेशीर हक्क आणि मालकी वाटपधारकाने घोषित केलेले वारसदार: {n_name} (वय अंदाजे: {n_age} वर्षे) यांच्याकडे पूर्णपणे हस्तांतरित केले जातील।

5. लेआउट विकास व पायाभूत सुविधा अटी:
   डेव्हलपर लेआउट ब्ल्यूप्रिंटनुसार सिमेंट रोड (Cement Road), लेआउट सीमांकन आणि मूलभूत पायाभूत सुविधांचे काम विहित वेळेत पूर्ण करण्यास वचनबद्ध आहे।

ज्याचा पुरावा म्हणून, दोन्ही पक्षांनी कोणत्याही दबावाशिवाय आपल्या स्वेच्छेने या दस्तऐवजावर स्वाक्षऱ्या आणि अधिकृत शिक्के लावले आहेत।


----------------------------------------- -----------------------------------------
फर्स्टचॉईस इन्फ्रा (डेव्हलपर) वाटपधारक / खरेदीदाराची स्वाक्षरी


साक्षीदार १: ______________________________ साक्षीदार २: ______________________________
"""

# Select the appropriate template string based on user radio selection
if agreement_lang == "Hindi (हिंदी)":
    selected_template = template_hi
elif agreement_lang == "Marathi (मराठी)":
    selected_template = template_mr
else:
    selected_template = template_en

# Render the assembled legal draft inside an interactive text area element block
customized_agreement_text = st.text_area(
    label="Assembled Dynamic Multi-Language Contract Text Frame Editor Pane",
    value=selected_template,
    height=550
)

# --- Print / Download Export Desk Controls ---
st.write("")
col_b1, col_b2 = st.columns([1, 1])

agreement_bytes = customized_agreement_text.encode('utf-8')

col_b1.download_button(
    label="💾 Download Finished Legal Contract (Clean Text Format)",
    data=agreement_bytes,
    file_name=f"Agreement_Plot_{selected_plot}_{c_name.replace(' ', '_')}.txt",
    mime="text/plain",
    use_container_width=True
)

with col_b2:
    if st.button("🖨️ Direct Print Document (Send to Laser Printer)", use_container_width=True):
        st.info("💡 To print directly: Simply press Ctrl+P on your keyboard to trigger browser layout printing templates, or copy the edited text box into Microsoft Word / Notepad for custom page alignments.")

