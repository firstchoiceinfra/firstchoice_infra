import streamlit as st
import pandas as pd
import database
import datetime
import io
import base64

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
import streamlit.components.v1 as components

# ---------------------------------------------------------------
# 1. PAGE CONFIG & SECURITY
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

database.init_db()
db_data        = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
curr_user      = st.session_state.get('current_user_name', '')
user_role      = st.session_state.get('user_role', 'executive')

# ---------------------------------------------------------------
# 2. THEME
# ---------------------------------------------------------------
bg_url  = "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
p_color = "#1e3a8a"
s_color = "#3b82f6"
c_bg    = "rgba(255,255,255,0.92)"

if '_app_settings' in db_data:
    gs      = db_data['_app_settings']
    bg_url  = gs.get('bg_url',          bg_url)
    p_color = gs.get('primary_color',   p_color)
    s_color = gs.get('secondary_color', s_color)
    c_bg    = gs.get('card_bg',         c_bg)

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
.stButton>button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(59,130,246,0.6);
}}
.self-btn button {{
    background: linear-gradient(90deg,#1e3a8a,#3b82f6) !important;
}}
.group-btn button {{
    background: linear-gradient(90deg,#065f46,#10b981) !important;
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# 3. HEADING
# ---------------------------------------------------------------
st.markdown(
    "<h1 style='text-align:center;'>💼 FC Infra — Commission Statement</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<p style='text-align:center;color:#475569;font-size:15px;'>"
    "Executive select karo, period choose karo aur PDF generate karo.</p>",
    unsafe_allow_html=True)
st.divider()

# ---------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------
def sf(val, default=0.0):
    try:
        if val is None or str(val).strip() == "": return float(default)
        return float(val)
    except: return float(default)


def get_exec_info(exec_name):
    for k, v in exec_data_root.items():
        if str(k).strip().lower() == str(exec_name).strip().lower():
            return v
    return {}


def get_exec_slab(exec_name):
    """Return (pct, rs_discount) from Partner Portal."""
    info = get_exec_info(exec_name)
    return sf(info.get('percentage_exec', 0.0)), sf(info.get('rupees_exec', 0.0))


def get_exec_senior(exec_name):
    info = get_exec_info(exec_name)
    s = info.get('senior_name', '')
    if not s or str(s).strip().lower() in ['', 'direct', 'none']:
        return None
    return str(s).strip()


def get_project_comm_type(project_name):
    p = db_data.get(project_name, {})
    return p.get('comm_type', 'Percentage (%)')


def get_project_mauza(project_name):
    p = db_data.get(project_name, {})
    return p.get('mauza', project_name)


def get_all_downlines(manager_name):
    mgr = str(manager_name).strip().lower()
    result = []
    for ex, det in exec_data_root.items():
        if isinstance(det, dict) and str(det.get('senior_name', '')).strip().lower() == mgr:
            result.append(ex)
            result.extend(get_all_downlines(ex))
    return list(set(result))


def compute_comm(received, exec_pct, rs_discount, comm_type, diff_only=False, downline_pct=0.0):
    """
    Commission formula:

    If project is % based:
      effective_pct  = exec_pct  (or exec_pct - downline_pct for diff)
      Gross          = received × effective_pct / 100
      discount_%     = (rs_discount / received) × 100        ← Rs converted to %
      Discount_amt   = Gross × discount_% / 100
                     = Gross × rs_discount / received
                     = (received × eff_pct/100) × (rs_discount/received)
                     = eff_pct/100 × rs_discount              ← simplified
      Net Comm       = Gross − Discount_amt
      TDS            = Net Comm × 2%
      In Hand        = Net Comm − TDS

    If project is Rs based:
      Gross = rs_discount  (fixed amount)
      No discount conversion needed
      TDS = Gross × 2%
      In Hand = Gross − TDS
    """
    if received <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    is_pct = 'percentage' in str(comm_type).lower() or '%' in str(comm_type)

    if is_pct:
        eff_pct = (exec_pct - downline_pct) if diff_only else exec_pct
        if eff_pct <= 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0

        gross        = received * eff_pct / 100.0
        # Rs discount → converted to % of received → applied on gross
        discount_amt = (eff_pct / 100.0 * rs_discount) if rs_discount > 0 else 0.0
        net_comm     = max(0.0, gross - discount_amt)
        tds          = net_comm * 0.02
        in_hand      = net_comm - tds
        return gross, discount_amt, net_comm, tds, in_hand

    else:
        # Fixed Rs commission
        gross    = rs_discount
        net_comm = gross
        tds      = net_comm * 0.02
        in_hand  = net_comm - tds
        return gross, 0.0, net_comm, tds, in_hand


def get_all_received_payments(plot_info):
    payments = []
    tok_amt  = sf(plot_info.get('token_amount', 0.0))
    tok_date = plot_info.get('receipt_date', plot_info.get('booking_date', str(datetime.date.today())))
    if tok_amt > 0:
        payments.append({'date': tok_date, 'amount': tok_amt})
    for p in plot_info.get('partial_payments', []):
        amt = sf(p.get('amount', 0.0))
        dt  = p.get('date', str(datetime.date.today()))
        if amt > 0:
            payments.append({'date': dt, 'amount': amt})
    return payments


def fetch_records(exec_name, date_from, date_to, diff_only=False, downline_pct=0.0, via_name=''):
    """Fetch payment rows for one executive."""
    exec_pct, rs_disc = get_exec_slab(exec_name)
    records = []
    project_names = [n for n, d in db_data.items()
                     if isinstance(d, dict) and ('plots' in d or 'total_plots' in d)]

    for p_name in project_names:
        p_info  = db_data[p_name]
        p_plots = p_info.get('plots', {})
        if isinstance(p_plots, list):
            p_plots = {str(i): p for i, p in enumerate(p_plots) if p is not None}

        comm_type = get_project_comm_type(p_name)
        mauza     = get_project_mauza(p_name)

        for plot_id, plot_info in p_plots.items():
            if not isinstance(plot_info, dict): continue
            if str(plot_info.get('status', '')).lower() != 'booked': continue
            if plot_info.get('is_primary', True) is False: continue
            if str(plot_info.get('executive_name', '')).strip().lower() != str(exec_name).strip().lower():
                continue

            customer   = str(plot_info.get('customer_name', 'N/A')).title()
            booked_str = plot_info.get('booked_plots_str', plot_id)
            payments   = get_all_received_payments(plot_info)

            for pmt in payments:
                try:
                    pmt_date = datetime.date.fromisoformat(str(pmt['date'])[:10])
                except:
                    pmt_date = datetime.date.today()

                if not (date_from <= pmt_date <= date_to):
                    continue

                received = pmt['amount']
                gross, disc, net_comm, tds, in_hand = compute_comm(
                    received, exec_pct, rs_disc, comm_type, diff_only, downline_pct)

                if gross <= 0:
                    continue

                is_pct = 'percentage' in str(comm_type).lower() or '%' in str(comm_type)
                if diff_only:
                    eff = exec_pct - downline_pct
                    lbl = f"Diff {eff:.1f}% (via {via_name})"
                elif is_pct:
                    lbl = f"{exec_pct}%" + (f" − ₹{rs_disc:.0f}" if rs_disc > 0 else "")
                else:
                    lbl = f"₹{rs_disc:,.0f} Fixed"

                records.append({
                    'Project'   : p_name,
                    'Plot'      : booked_str,
                    'Customer'  : customer,
                    'Comm Slab' : lbl,
                    'Received'  : received,
                    'Date'      : str(pmt_date),
                    'Gross'     : gross,
                    'Discount'  : disc,
                    'Net Comm'  : net_comm,
                    'TDS'       : tds,
                    'In Hand'   : in_hand,
                    'Mauja'     : mauza,
                })
    return records


def build_self_records(exec_name, date_from, date_to):
    """Only own bookings."""
    return fetch_records(exec_name, date_from, date_to)


def build_group_records(exec_name, date_from, date_to):
    """Own bookings + difference commission from all direct downlines."""
    all_rec = fetch_records(exec_name, date_from, date_to)  # own

    exec_pct, _ = get_exec_slab(exec_name)
    for ex, det in exec_data_root.items():
        if not isinstance(det, dict): continue
        if str(det.get('senior_name', '')).strip().lower() != str(exec_name).strip().lower():
            continue
        dl_pct, _ = get_exec_slab(ex)
        if exec_pct > dl_pct:
            diff_recs = fetch_records(ex, date_from, date_to,
                                      diff_only=True, downline_pct=dl_pct, via_name=ex)
            for r in diff_recs:
                r['Customer'] = f"{r['Customer']} [{ex}]"
            all_rec.extend(diff_recs)
    return all_rec


# ---------------------------------------------------------------
# 5. PDF GENERATOR
# ---------------------------------------------------------------
def generate_pdf(exec_name, records, date_from, date_to, mode_label):
    buffer  = io.BytesIO()
    doc     = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                rightMargin=12*mm, leftMargin=12*mm,
                topMargin=10*mm, bottomMargin=10*mm)
    BLACK   = colors.black
    GREY_LT = colors.HexColor("#f8fafc")
    story   = []

    # Header
    story.append(Paragraph("<b>FIRSTCHOICE INFRA</b>",
        ParagraphStyle('TT', fontSize=24, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=3)))
    story.append(Paragraph("<i>Symbol Of Trust...</i>",
        ParagraphStyle('ST', fontSize=10, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph(
        "Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034",
        ParagraphStyle('AD', fontSize=9, alignment=TA_CENTER, spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceAfter=5))
    story.append(Paragraph(
        f"<b>Executive Commission Statement — {mode_label}</b>",
        ParagraphStyle('ES', fontSize=14, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=8)))

    # Partner + Period info row
    exec_info = get_exec_info(exec_name)
    senior_nm = exec_info.get('senior_name', 'Direct')
    pct, rs_d = get_exec_slab(exec_name)
    slab_str  = (f"{pct}% (Disc: Rs {rs_d:,.0f})" if pct > 0 and rs_d > 0
                 else f"{pct}%" if pct > 0 else f"Rs {rs_d:,.0f} Fixed")

    info_t = Table([[
        f"Partner: {exec_name}",
        f"Senior: {senior_nm}  |  Slab: {slab_str}",
        f"Period: {date_from} to {date_to}"
    ]], colWidths=[85*mm, 90*mm, 82*mm])
    info_t.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(0,0),'Helvetica-Bold'),
        ('FONTNAME',  (2,0),(2,0),'Helvetica-Bold'),
        ('ALIGN',     (2,0),(2,0),'RIGHT'),
        ('FONTSIZE',  (0,0),(-1,-1), 9),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 4))

    # Main table
    headers    = ["S.No.", "Project", "Plot", "Customer", "Comm Slab",
                  "Received", "Date", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]
    col_widths = [10*mm, 36*mm, 12*mm, 44*mm, 26*mm,
                  22*mm, 20*mm, 20*mm, 18*mm, 20*mm, 14*mm, 21*mm]

    tdata = [headers]
    tot_recv = tot_gross = tot_disc = tot_net = tot_tds = tot_ih = 0.0

    for idx, r in enumerate(records, 1):
        tdata.append([
            str(idx),
            r['Project'], str(r['Plot']), r['Customer'], r['Comm Slab'],
            f"{r['Received']:,.2f}",
            r['Date'],
            f"{r['Gross']:,.2f}",
            f"{r['Discount']:,.2f}",
            f"{r['Net Comm']:,.2f}",
            f"{r['TDS']:,.2f}",
            f"{r['In Hand']:,.2f}",
        ])
        tot_recv  += r['Received']
        tot_gross += r['Gross']
        tot_disc  += r['Discount']
        tot_net   += r['Net Comm']
        tot_tds   += r['TDS']
        tot_ih    += r['In Hand']

    tdata.append(["TOTAL","","","","",
        f"{tot_recv:,.2f}","",
        f"{tot_gross:,.2f}", f"{tot_disc:,.2f}",
        f"{tot_net:,.2f}",  f"{tot_tds:,.2f}", f"{tot_ih:,.2f}"])

    tbl = Table(tdata, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONTNAME',      (0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',      (0,0),(-1,0), 8),
        ('ALIGN',         (0,0),(-1,0),'CENTER'),
        ('FONTNAME',      (0,1),(-1,-2),'Helvetica'),
        ('FONTSIZE',      (0,1),(-1,-2), 8),
        ('ALIGN',         (0,1),(-1,-2),'CENTER'),
        ('ALIGN',         (3,1),(3,-2),'LEFT'),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[colors.white, GREY_LT]),
        ('FONTNAME',      (0,-1),(-1,-1),'Helvetica-Bold'),
        ('FONTSIZE',      (0,-1),(-1,-1), 8),
        ('BOX',           (0,0),(-1,-1), 0.8, BLACK),
        ('INNERGRID',     (0,0),(-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 3),
        ('VALIGN',        (0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(tbl)

    # Summary box
    story.append(Spacer(1, 8))
    s_tbl = Table([
        ["Total Payments","Total Received","Total Gross","Net Commission","Total TDS","IN HAND"],
        [str(len(records)),
         f"Rs {tot_recv:,.2f}", f"Rs {tot_gross:,.2f}",
         f"Rs {tot_net:,.2f}",  f"Rs {tot_tds:,.2f}",
         f"Rs {tot_ih:,.2f}"],
    ], colWidths=[30*mm, 38*mm, 34*mm, 34*mm, 28*mm, 36*mm])
    s_tbl.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,0), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR',    (0,0),(-1,0), colors.white),
        ('FONTNAME',     (0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',     (0,0),(-1,-1), 9),
        ('ALIGN',        (0,0),(-1,-1),'CENTER'),
        ('BACKGROUND',   (0,1),(-2,1), colors.HexColor("#e0f2fe")),
        ('BACKGROUND',   (-1,1),(-1,1),colors.HexColor("#d1fae5")),
        ('TEXTCOLOR',    (-1,1),(-1,1),colors.HexColor("#065f46")),
        ('FONTNAME',     (0,1),(-1,1),'Helvetica-Bold'),
        ('BOX',          (0,0),(-1,-1), 1, colors.HexColor("#1e3a8a")),
        ('INNERGRID',    (0,0),(-1,-1), 0.4, colors.HexColor("#93c5fd")),
        ('TOPPADDING',   (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
    ]))
    story.append(s_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ---------------------------------------------------------------
# 6. STREAMLIT UI
# ---------------------------------------------------------------
st.markdown("### 👤 Step 1 — Executive Select Karo")

exec_names_all = sorted([n for n, d in exec_data_root.items() if isinstance(d, dict)])
exec_options   = exec_names_all if user_role == 'admin' else [curr_user]

if not exec_options:
    st.warning("Koi executive nahi mila. Pehle Partner Portal mein add karo.")
    st.stop()

selected_exec = st.selectbox("Executive / Partner:", exec_options)

if selected_exec:
    pct, rs_d  = get_exec_slab(selected_exec)
    senior     = get_exec_senior(selected_exec)
    downlines  = get_all_downlines(selected_exec)
    c1, c2, c3 = st.columns(3)
    slab_info  = (f"{pct}% (Disc ₹{rs_d:,.0f})" if rs_d > 0 else f"{pct}%") if pct > 0 else f"₹{rs_d:,.0f} Fixed"
    c1.info(f"**Commission Slab:** {slab_info}")
    c2.info(f"**Senior / Upline:** {senior if senior else 'Direct (Company)'}")
    c3.info(f"**Total Downlines:** {len(downlines)}")

st.markdown("### 📅 Step 2 — Statement Period")
col1, col2 = st.columns(2)
date_from = col1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to   = col2.date_input("To Date:",   datetime.date.today())

st.divider()
st.markdown("### 🖨️ Step 3 — Statement Type Chunno aur Generate Karo")

# ── SELF / GROUP BUTTONS ──────────────────────────────────────
col_self, col_group = st.columns(2)

with col_self:
    st.markdown('<div class="self-btn">', unsafe_allow_html=True)
    self_clicked = st.button(
        "👤 SELF Statement\n(Sirf Apni Bookings)",
        use_container_width=True, key="btn_self")
    st.markdown('</div>', unsafe_allow_html=True)

with col_group:
    st.markdown('<div class="group-btn">', unsafe_allow_html=True)
    group_clicked = st.button(
        "👥 GROUP Statement\n(Apni + Downline Difference)",
        use_container_width=True, key="btn_group")
    st.markdown('</div>', unsafe_allow_html=True)


def show_statement(records, exec_name, date_from, date_to, mode_label):
    if not records:
        st.warning("⚠️ Is period mein koi payment record nahi mila.")
        return

    records.sort(key=lambda x: x['Date'])
    st.success(f"✅ **{len(records)}** payment record(s) mile — {mode_label}")

    # Preview table
    df = pd.DataFrame(records)
    df_show = df[['Project','Plot','Customer','Comm Slab',
                  'Received','Date','Gross','Discount','Net Comm','TDS','In Hand']].copy()
    df_show.index = range(1, len(df_show)+1)
    df_show.index.name = "S.No."
    for c in ['Received','Gross','Discount','Net Comm','TDS','In Hand']:
        df_show[c] = df_show[c].apply(lambda x: f"₹ {x:,.2f}")
    st.dataframe(df_show, use_container_width=True)

    # Summary metrics
    st.markdown("#### 📊 Summary")
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("Payments",       len(records))
    m2.metric("Total Received", f"₹ {df['Received'].sum():,.2f}")
    m3.metric("Gross Comm",     f"₹ {df['Gross'].sum():,.2f}")
    m4.metric("Net Comm",       f"₹ {df['Net Comm'].sum():,.2f}")
    m5.metric("💰 In Hand",      f"₹ {df['In Hand'].sum():,.2f}")

    st.divider()

    # PDF
    with st.spinner("PDF ban rahi hai..."):
        pdf_bytes = generate_pdf(exec_name, records, str(date_from), str(date_to), mode_label)

    fname = f"Commission_{exec_name.replace(' ','_')}_{mode_label}_{date_from}_to_{date_to}.pdf"
    b64   = base64.b64encode(pdf_bytes).decode()

    col_dl, col_pr = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Download PDF",
            data=pdf_bytes,
            file_name=fname,
            mime="application/pdf",
            use_container_width=True,
        )
    with col_pr:
        components.html(f"""
        <script>
        function printPDF() {{
            var b = atob("{b64}");
            var n = new Array(b.length);
            for(var i=0;i<b.length;i++) n[i]=b.charCodeAt(i);
            var blob = new Blob([new Uint8Array(n)],{{type:'application/pdf'}});
            var url  = URL.createObjectURL(blob);
            var win  = window.open(url,'_blank');
            win.addEventListener('load', function(){{ win.print(); }});
        }}
        </script>
        <button onclick="printPDF()"
            style="width:100%;background:linear-gradient(90deg,#059669,#10b981);
                   color:white;padding:12px;border-radius:8px;border:none;
                   font-weight:700;font-size:15px;cursor:pointer;
                   box-shadow:0 4px 12px rgba(5,150,105,0.4);">
            🖨️ Print PDF
        </button>
        """, height=55)

    st.info("💡 'Download PDF' se save karo ya '🖨️ Print PDF' se seedha print dialog khulega.")


# Trigger
if self_clicked:
    with st.spinner("Data collect ho raha hai..."):
        records = build_self_records(selected_exec, date_from, date_to)
    show_statement(records, selected_exec, date_from, date_to, "SELF")

if group_clicked:
    with st.spinner("Data collect ho raha hai..."):
        records = build_group_records(selected_exec, date_from, date_to)
    show_statement(records, selected_exec, date_from, date_to, "GROUP")


