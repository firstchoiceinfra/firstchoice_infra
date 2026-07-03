import streamlit as st
import pandas as pd
import database
import datetime
import io
import base64

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import streamlit.components.v1 as components

# ---------------------------------------------------------------
# 1. PAGE CONFIG
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

# ---------------------------------------------------------------
# 2. SECURITY — SIRF ADMIN KO ACCESS
# ---------------------------------------------------------------
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

if st.session_state.get('user_role', 'executive') != 'admin':
    st.error("🚨 Access Denied! Yeh page sirf Admin ke liye hai.")
    st.info("💡 Commission Statement dekhne ke liye Admin se contact karo.")
    st.stop()

# ---------------------------------------------------------------
# 3. DATABASE
# ---------------------------------------------------------------
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# ---------------------------------------------------------------
# 4. THEME
# ---------------------------------------------------------------
bg_url = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg = "rgba(255,255,255,0.92)"

if '_app_settings' in db_data:
    gs = db_data['_app_settings']
    bg_url = gs.get('bg_url', bg_url)
    p_color = gs.get('primary_color', p_color)
    s_color = gs.get('secondary_color', s_color)
    c_bg = gs.get('card_bg', c_bg)

st.markdown(f"""
<style>
.stApp {{
    background-image: url("{bg_url}");
    background-attachment: fixed;
    background-size: cover;
}}
.block-container {{
    background-color: {c_bg} !important;
    padding: 2.5rem 3.5rem !important;
    border-radius: 24px;
    box-shadow: 0px 20px 40px rgba(0,0,0,0.2);
    margin-top: 2rem;
    margin-bottom: 2rem;
}}
h1, h2, h3, h4 {{ color: {p_color} !important; font-weight: 900; }}
.stButton>button {{
    background: linear-gradient(90deg, {p_color} 0%, {s_color} 100%);
    color: white !important;
    border-radius: 8px;
    font-weight: 700;
    border: none;
    padding: 10px 20px;
    box-shadow: 0 4px 12px rgba(59,130,246,0.4);
    transition: all 0.3s ease;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# 5. HEADING
# ---------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>💼 FC Infra — Commission Statement</h1>",
            unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:15px;'>"
    "🔐 Admin Only Panel — Partner commission generate karo</p>",
    unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------------
# 6. HELPER FUNCTIONS
# ---------------------------------------------------------------
def sf(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return float(default)
        return float(val)
    except: return float(default)


def get_exec_info(name):
    for k, v in exec_data_root.items():
        if str(k).strip().lower() == str(name).strip().lower():
            return v
    return {}


def get_exec_slab(name):
    info = get_exec_info(name)
    return sf(info.get('percentage_exec', 0.0)), sf(info.get('rupees_exec', 0.0))


def get_exec_senior(name):
    info = get_exec_info(name)
    s = str(info.get('senior_name', '')).strip()
    if s.lower() in ['', 'company', 'direct', 'none', '-']:
        return None
    return s


def is_top_level(senior_val):
    return str(senior_val).strip().lower() in ['', 'company', 'direct', 'none', '-']


def get_direct_downlines(manager_name):
    mgr = str(manager_name).strip().lower()
    result = []
    for ex, det in exec_data_root.items():
        if not isinstance(det, dict): continue
        senior = str(det.get('senior_name', '')).strip().lower()
        if senior == mgr and not is_top_level(senior):
            result.append(ex)
    return result


def get_all_downlines(manager_name):
    result = []
    for dl in get_direct_downlines(manager_name):
        result.append(dl)
        result.extend(get_all_downlines(dl))
    return list(set(result))


def get_project_comm_type(project_name):
    p = db_data.get(project_name, {})
    return p.get('comm_type', 'Percentage (%)')


def get_project_mauza(project_name):
    p = db_data.get(project_name, {})
    return p.get('mauza', '')


def get_company_rate(plot_info):
    return sf(plot_info.get('rate_per_sqft', 0.0))


def get_actual_rate(plot_info):
    plot_area = sf(plot_info.get('plot_area', 0.0))
    sell_rate = sf(plot_info.get('selling_rate', 0.0))
    rate_sqft = sf(plot_info.get('rate_per_sqft', 0.0))
    if sell_rate > 100000:
        return (sell_rate / plot_area) if plot_area > 0 else rate_sqft
    else:
        return sell_rate


def compute_discount_pct(company_rate, actual_rate):
    if company_rate <= 0 or actual_rate >= company_rate:
        return 0.0
    return ((company_rate - actual_rate) / company_rate) * 100.0


def compute_row(received, exec_pct, rs_fixed, comm_type, discount_pct):
    if received <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0
    is_pct = '%' in str(comm_type) or 'percentage' in str(comm_type).lower()
    if is_pct:
        gross = received * exec_pct / 100.0
        discount_amt = gross * discount_pct / 100.0
        net_comm = max(0.0, gross - discount_amt)
    else:
        gross = rs_fixed
        discount_amt = 0.0
        net_comm = gross
    tds = net_comm * 0.02
    in_hand = net_comm - tds
    return gross, discount_amt, net_comm, tds, in_hand


def get_payments(plot_info, date_from, date_to):
    payments = []
    tok = sf(plot_info.get('token_amount', 0.0))
    tok_date = plot_info.get('receipt_date', plot_info.get('booking_date', str(datetime.date.today())))
    if tok > 0:
        try: d = datetime.date.fromisoformat(str(tok_date)[:10])
        except: d = datetime.date.today()
        if date_from <= d <= date_to:
            payments.append({'date': str(d), 'amount': tok})
    for p in plot_info.get('partial_payments', []):
        amt = sf(p.get('amount', 0.0))
        if amt <= 0: continue
        try: d = datetime.date.fromisoformat(str(p.get('date', ''))[:10])
        except: d = datetime.date.today()
        if date_from <= d <= date_to:
            payments.append({'date': str(d), 'amount': amt})
    return payments


def fetch_exec_records(exec_name, date_from, date_to, override_pct=None):
    """Fetch payment records for exec_name. override_pct for difference commission."""
    exec_pct, rs_fixed = get_exec_slab(exec_name)
    use_pct = override_pct if override_pct is not None else exec_pct

    records = []
    project_names = [n for n, d in db_data.items()
                     if isinstance(d, dict) and ('plots' in d or 'total_plots' in d)]

    for p_name in project_names:
        p_info = db_data[p_name]
        p_plots = p_info.get('plots', {})
        if isinstance(p_plots, list):
            p_plots = {str(i): p for i, p in enumerate(p_plots) if p is not None}

        comm_type = get_project_comm_type(p_name)
        mauza = get_project_mauza(p_name)

        for plot_id, plot_info in p_plots.items():
            if not isinstance(plot_info, dict): continue
            if str(plot_info.get('status', '')).lower() != 'booked': continue
            if plot_info.get('is_primary', True) is False: continue
            if str(plot_info.get('executive_name', '')).strip().lower() != str(exec_name).strip().lower():
                continue

            customer = str(plot_info.get('customer_name', 'N/A')).title()
            booked_str = plot_info.get('booked_plots_str', plot_id)
            comp_rate = get_company_rate(plot_info)
            actual_rate = get_actual_rate(plot_info)
            disc_pct = compute_discount_pct(comp_rate, actual_rate)

            for pmt in get_payments(plot_info, date_from, date_to):
                gross, disc_amt, net_comm, tds, in_hand = compute_row(
                    pmt['amount'], use_pct, rs_fixed, comm_type, disc_pct)
                if gross <= 0: continue
                records.append({
                    'project' : p_name,
                    'plot' : booked_str,
                    'mauza' : mauza,
                    'customer' : customer,
                    'received' : pmt['amount'],
                    'date' : pmt['date'],
                    'gross' : gross,
                    'disc_pct' : disc_pct,
                    'disc_amt' : disc_amt,
                    'net_comm' : net_comm,
                    'tds' : tds,
                    'in_hand' : in_hand,
                    'comm_pct' : use_pct,
                    'via' : '',
                })
    return records


# ---------------------------------------------------------------
# 7. BUILD STATEMENT LOGIC
# ---------------------------------------------------------------
def build_self(exec_name, date_from, date_to):
    """Sirf apni khud ki bookings — full slab."""
    return fetch_exec_records(exec_name, date_from, date_to)


def build_group(exec_name, date_from, date_to):
    """
    Difference commission from downlines chain.

    Chain: A(23%) > B(18%) > C(15%) > D(8%)

    A ka GROUP:
      B ki bookings → A gets (23-18)=5%
      C ki bookings → A gets (23-18)=5% [same diff, not 23-15]
      D ki bookings → A gets (23-18)=5% [same diff, not 23-8]

    B ka GROUP:
      C ki bookings → B gets (18-15)=3%
      D ki bookings → B gets (18-15)=3%

    Rule: Senior gets (his_pct - direct_downline_pct) on ALL bookings
          under that downline's ENTIRE chain.
    """
    records = []
    exec_pct, _ = get_exec_slab(exec_name)

    def collect_chain(senior_name, senior_pct):
        for dl in get_direct_downlines(senior_name):
            dl_pct, _ = get_exec_slab(dl)
            diff_pct = senior_pct - dl_pct
            if diff_pct > 0:
                # dl ki apni bookings pe diff
                for r in fetch_exec_records(dl, date_from, date_to, override_pct=diff_pct):
                    r['customer'] = f"{r['customer']} [{dl}]"
                    records.append(r)
                # dl ke saare sub-downlines pe bhi same diff_pct
                def get_sub_all(node):
                    for sub in get_direct_downlines(node):
                        for r in fetch_exec_records(sub, date_from, date_to, override_pct=diff_pct):
                            r['customer'] = f"{r['customer']} [{sub}]"
                            records.append(r)
                        get_sub_all(sub)
                get_sub_all(dl)

    collect_chain(exec_name, exec_pct)
    return records


def build_all(exec_name, date_from, date_to):
    """Self + Group dono."""
    self_recs = build_self(exec_name, date_from, date_to)
    group_recs = build_group(exec_name, date_from, date_to)
    return self_recs + group_recs


# ---------------------------------------------------------------
# 8. PDF GENERATOR (A4 Portrait)
# ---------------------------------------------------------------
def generate_pdf(exec_name, records, date_from, date_to, mode_label):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
               rightMargin=12*mm, leftMargin=12*mm,
               topMargin=10*mm, bottomMargin=10*mm)

    NAVY = colors.HexColor("#1e3a8a")
    LTBLUE = colors.HexColor("#e0f2fe")
    GREY = colors.HexColor("#f8fafc")
    GREEN = colors.HexColor("#d1fae5")
    DKGREEN = colors.HexColor("#065f46")
    BLACK = colors.black
    story = []

    # Company Header
    story.append(Paragraph("<b>FIRSTCHOICE INFRA</b>",
        ParagraphStyle('TT', fontSize=20, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=3)))
    story.append(Paragraph("<i>Symbol Of Trust...</i>",
        ParagraphStyle('ST', fontSize=9, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph(
        "Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034",
        ParagraphStyle('AD', fontSize=8, alignment=TA_CENTER, spaceAfter=5)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4))
    story.append(Paragraph(f"<b>Executive Commission Statement — {mode_label}</b>",
        ParagraphStyle('ES', fontSize=12, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY, spaceAfter=6))

    # Partner (left) + Period (right)
    exec_info = get_exec_info(exec_name)
    senior_nm = exec_info.get('senior_name', 'Direct')
    pct, rs_d = get_exec_slab(exec_name)
    slab_str = (f"{pct}% (Disc: Rs {rs_d:,.0f})" if pct > 0 and rs_d > 0
                 else f"{pct}%" if pct > 0 else f"Rs {rs_d:,.0f} Fixed")

    hdr_tbl = Table([[
        Paragraph(f"<b>Partner:</b> {exec_name} &nbsp;&nbsp; <b>Senior:</b> {senior_nm} &nbsp;&nbsp; <b>Slab:</b> {slab_str}",
                  ParagraphStyle('PL', fontSize=9)),
        Paragraph(f"<b>Period:</b> {date_from} to {date_to}<br/><b>Generated:</b> {datetime.date.today()}",
                  ParagraphStyle('PR', fontSize=9, alignment=TA_RIGHT)),
    ]], colWidths=[105*mm, 65*mm])
    hdr_tbl.setStyle(TableStyle([('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 6))

    # Main Table
    headers = ["Sr\nNo", "Project", "Plot\nNo", "Mauza", "Client Name",
               "Received\nAmt (Rs)", "Received\nDate",
               "Gross\nComm", "Discount\nAmt", "Net\nComm", "TDS\n2%", "In\nHand"]
    cw = [8*mm, 28*mm, 10*mm, 16*mm, 30*mm,
          18*mm, 17*mm, 16*mm, 16*mm, 15*mm, 11*mm, 15*mm]

    tdata = [headers]
    tot = {k: 0.0 for k in ['received','gross','disc_amt','net_comm','tds','in_hand']}

    for idx, r in enumerate(records, 1):
        tdata.append([
            str(idx),
            r['project'], str(r['plot']), r['mauza'], r['customer'],
            f"{r['received']:,.2f}", r['date'],
            f"{r['gross']:,.2f}", f"{r['disc_amt']:,.2f}",
            f"{r['net_comm']:,.2f}", f"{r['tds']:,.2f}", f"{r['in_hand']:,.2f}",
        ])
        for k in tot: tot[k] += r[k]

    tdata.append(["TOTAL","","","","",
        f"{tot['received']:,.2f}","",
        f"{tot['gross']:,.2f}", f"{tot['disc_amt']:,.2f}",
        f"{tot['net_comm']:,.2f}", f"{tot['tds']:,.2f}", f"{tot['in_hand']:,.2f}",
    ])

    tbl = Table(tdata, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), NAVY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,0), 7),
        ('ALIGN', (0,0),(-1,0), 'CENTER'),
        ('FONTNAME', (0,1),(-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1),(-1,-2), 7),
        ('ALIGN', (0,1),(-1,-2), 'CENTER'),
        ('ALIGN', (4,1),(4,-2), 'LEFT'),
        ('ALIGN', (1,1),(1,-2), 'LEFT'),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [colors.white, GREY]),
        ('BACKGROUND', (0,-1),(-1,-1),NAVY),
        ('TEXTCOLOR', (0,-1),(-1,-1),colors.white),
        ('FONTNAME', (0,-1),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE', (0,-1),(-1,-1),7),
        ('BACKGROUND', (-1,1),(-1,-2),colors.HexColor("#fef3c7")),
        ('TEXTCOLOR', (-1,1),(-1,-2),colors.HexColor("#92400e")),
        ('FONTNAME', (-1,1),(-1,-2),'Helvetica-Bold'),
        ('BOX', (0,0),(-1,-1), 0.8, BLACK),
        ('INNERGRID', (0,0),(-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0),(-1,-1), 3),
        ('BOTTOMPADDING', (0,0),(-1,-1), 3),
        ('LEFTPADDING', (0,0),(-1,-1), 2),
        ('RIGHTPADDING', (0,0),(-1,-1), 2),
        ('VALIGN', (0,0),(-1,-1), 'MIDDLE'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    # Summary Bifurcation
    story.append(Paragraph("<b>Summary Bifurcation</b>",
        ParagraphStyle('SB', fontSize=10, fontName='Helvetica-Bold',
                       textColor=NAVY, spaceAfter=4)))
    stbl = Table([
        ["Total Received","Gross Commission","Total Discount","Net Commission","Total TDS","IN HAND"],
        [f"Rs {tot['received']:,.2f}", f"Rs {tot['gross']:,.2f}",
         f"Rs {tot['disc_amt']:,.2f}", f"Rs {tot['net_comm']:,.2f}",
         f"Rs {tot['tds']:,.2f}", f"Rs {tot['in_hand']:,.2f}"],
    ], colWidths=[30*mm, 30*mm, 28*mm, 30*mm, 24*mm, 28*mm])
    stbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0),(-1,0), NAVY),
        ('TEXTCOLOR', (0,0),(-1,0), colors.white),
        ('FONTNAME', (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0),(-1,-1), 8),
        ('ALIGN', (0,0),(-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1),(-2,1), LTBLUE),
        ('BACKGROUND', (-1,1),(-1,1), GREEN),
        ('TEXTCOLOR', (-1,1),(-1,1), DKGREEN),
        ('FONTNAME', (0,1),(-1,1), 'Helvetica-Bold'),
        ('BOX', (0,0),(-1,-1), 1, NAVY),
        ('INNERGRID', (0,0),(-1,-1), 0.4, colors.HexColor("#93c5fd")),
        ('TOPPADDING', (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(stbl)

    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY, spaceAfter=4))
    story.append(Paragraph(
        "This is a computer-generated statement by FC Infra — FirstChoice Infrastructure.",
        ParagraphStyle('FT', fontSize=7, alignment=TA_CENTER,
                       textColor=colors.HexColor("#94a3b8"))))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------
# 9. STREAMLIT UI
# ---------------------------------------------------------------
st.markdown("### 👤 Step 1 — Partner Select Karo")

exec_names_all = sorted([n for n, d in exec_data_root.items() if isinstance(d, dict)])
if not exec_names_all:
    st.warning("Koi executive nahi mila. Pehle Partner Portal mein add karo.")
    st.stop()

selected_exec = st.selectbox("Partner / Executive:", exec_names_all)

if selected_exec:
    pct, rs_d = get_exec_slab(selected_exec)
    senior = get_exec_senior(selected_exec)
    downlines = get_all_downlines(selected_exec)
    c1, c2, c3 = st.columns(3)
    slab_info = (f"{pct}% (Disc ₹{rs_d:,.0f})" if rs_d > 0 and pct > 0
                  else f"{pct}%" if pct > 0 else f"₹{rs_d:,.0f} Fixed")
    c1.info(f"**Slab:** {slab_info}")
    c2.info(f"**Senior:** {senior if senior else 'Direct (Company)'}")
    c3.info(f"**Total Downlines:** {len(downlines)}")

st.markdown("### 📅 Step 2 — Period Select Karo")
col1, col2 = st.columns(2)
date_from = col1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to = col2.date_input("To Date:", datetime.date.today())

st.divider()
st.markdown("### 🖨️ Step 3 — Statement Type Choose Karo")

b1, b2, b3 = st.columns(3)
self_clicked = b1.button("👤 SELF\n(Sirf Apni Bookings)", use_container_width=True)
group_clicked = b2.button("👥 GROUP\n(Downline Difference Comm)", use_container_width=True)
all_clicked = b3.button("🌐 ALL\n(Self + Group Dono)", use_container_width=True)


def show_statement(records, exec_name, date_from, date_to, mode_label):
    if not records:
        st.warning("⚠️ Is period mein koi record nahi mila.")
        return

    records.sort(key=lambda x: x['date'])
    st.success(f"✅ **{len(records)}** records mile — {mode_label}")

    df = pd.DataFrame(records)
    df_show = df[['project','plot','mauza','customer',
                  'received','date','gross','disc_amt','net_comm','tds','in_hand']].copy()
    df_show.columns = ['Project','Plot','Mauza','Customer',
                       'Received','Date','Gross','Discount','Net Comm','TDS','In Hand']
    df_show.index = range(1, len(df_show)+1)
    df_show.index.name = "Sr"
    for c in ['Received','Gross','Discount','Net Comm','TDS','In Hand']:
        df_show[c] = df_show[c].apply(lambda x: f"₹ {x:,.2f}")
    st.dataframe(df_show, use_container_width=True)

    st.markdown("#### 📊 Summary")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Received", f"₹ {df['received'].sum():,.2f}")
    m2.metric("Gross Comm", f"₹ {df['gross'].sum():,.2f}")
    m3.metric("Discount", f"₹ {df['disc_amt'].sum():,.2f}")
    m4.metric("Net Comm", f"₹ {df['net_comm'].sum():,.2f}")
    m5.metric("💰 In Hand", f"₹ {df['in_hand'].sum():,.2f}")

    st.divider()

    with st.spinner("PDF ban rahi hai..."):
        pdf_bytes = generate_pdf(exec_name, records, str(date_from), str(date_to), mode_label)

    fname = f"Commission_{exec_name.replace(' ','_')}_{mode_label}_{date_from}_to_{date_to}.pdf"
    b64 = base64.b64encode(pdf_bytes).decode()

    col_dl, col_pr = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Download PDF (A4)",
            data=pdf_bytes, file_name=fname,
            mime="application/pdf",
            use_container_width=True)
    with col_pr:
        components.html(f"""
        <script>
        function printPDF() {{
            var b=atob("{b64}"),n=new Array(b.length);
            for(var i=0;i<b.length;i++) n[i]=b.charCodeAt(i);
            var blob=new Blob([new Uint8Array(n)],{{type:'application/pdf'}});
            var win=window.open(URL.createObjectURL(blob),'_blank');
            win.addEventListener('load',function(){{win.print();}});
        }}
        </script>
        <button onclick="printPDF()"
            style="width:100%;background:linear-gradient(90deg,#059669,#10b981);
                   color:white;padding:12px;border-radius:8px;border:none;
                   font-weight:700;font-size:15px;cursor:pointer;">
            🖨️ Print PDF (A4)
        </button>""", height=55)

    st.info("💡 Download karo ya Print karo — dono A4 size mein.")


if self_clicked:
    with st.spinner("Data collect ho raha hai..."):
        records = build_self(selected_exec, date_from, date_to)
    show_statement(records, selected_exec, date_from, date_to, "SELF")

elif group_clicked:
    with st.spinner("Data collect ho raha hai..."):
        records = build_group(selected_exec, date_from, date_to)
    show_statement(records, selected_exec, date_from, date_to, "GROUP")

elif all_clicked:
    with st.spinner("Data collect ho raha hai..."):
        records = build_all(selected_exec, date_from, date_to)
    show_statement(records, selected_exec, date_from, date_to, "ALL")
