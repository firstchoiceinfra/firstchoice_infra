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
# 1. PAGE CONFIG & SECURITY
# ---------------------------------------------------------------
st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please login on the Main Page portal first.")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})
curr_user = st.session_state.get('current_user_name', '')
user_role = st.session_state.get('user_role', 'executive')

# ---------------------------------------------------------------
# 2. THEME
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
# 3. HEADING
# ---------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>💼 FC Infra — Commission Statement</h1>",
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


def get_exec_info(name):
    for k, v in exec_data_root.items():
        if str(k).strip().lower() == str(name).strip().lower():
            return v
    return {}


def get_exec_slab(name):
    """Returns (pct, rs_fixed) from Partner Portal."""
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
    """Get only direct downlines of a manager."""
    mgr = str(manager_name).strip().lower()
    result = []
    for ex, det in exec_data_root.items():
        if not isinstance(det, dict): continue
        senior = str(det.get('senior_name', '')).strip().lower()
        if senior == mgr and not is_top_level(senior):
            result.append(ex)
    return result


def get_all_downlines(manager_name):
    """Recursively get all downlines."""
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
    """
    Company rate = rate_per_sqft saved at booking time.
    This is the original company rate per sqft.
    """
    return sf(plot_info.get('rate_per_sqft', 0.0))


def get_actual_rate(plot_info):
    """
    Actual sold rate = selling_rate / plot_area
    OR if selling_rate > 100000, it's already total value.
    """
    plot_area = sf(plot_info.get('plot_area', 0.0))
    sell_rate = sf(plot_info.get('selling_rate', 0.0))
    rate_sqft = sf(plot_info.get('rate_per_sqft', 0.0))

    if sell_rate > 100000:
        # selling_rate is total deal value
        if plot_area > 0:
            return sell_rate / plot_area
        return rate_sqft
    else:
        # selling_rate is per sqft rate
        return sell_rate


def compute_discount_pct(company_rate, actual_rate):
    """
    Discount % = ((company_rate - actual_rate) / company_rate) × 100
    Returns 0 if no discount or company_rate = 0.
    """
    if company_rate <= 0 or actual_rate >= company_rate:
        return 0.0
    return ((company_rate - actual_rate) / company_rate) * 100.0


def compute_row(received, exec_pct, rs_fixed, comm_type, discount_pct):
    """
    Calculate one payment row.

    % based project:
      Gross = received × exec_pct / 100
      Discount Amt = Gross × discount_pct / 100
      Net Comm = Gross - Discount Amt
      TDS = Net Comm × 2%
      In Hand = Net Comm - TDS

    Rs based project:
      Gross = rs_fixed (fixed amount)
      Discount Amt = 0
      Net Comm = Gross
      TDS = Net Comm × 2%
      In Hand = Net Comm - TDS
    """
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
    """Return all payments in date range."""
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
    """
    Fetch all payment records for exec_name.
    override_pct: if set, use this % instead of exec's own slab
                  (used for difference commission calculation).
    """
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

            payments = get_payments(plot_info, date_from, date_to)
            for pmt in payments:
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


def build_self(exec_name, date_from, date_to):
    """Only exec's own bookings at full slab."""
    return fetch_exec_records(exec_name, date_from, date_to)


def build_group(exec_name, date_from, date_to):
    """
    Own bookings (full slab) +
    Difference commission from downlines (recursive).

    A=23%, B=15% (downline of A), C=10% (downline of B):
    - A gets 23% on own bookings
    - A gets (23-15)=8% on B's bookings
    - A gets (23-10)=13% on C's bookings ... wait —
      Actually: A gets 8% on B, B gets 5% on C, A gets remaining from B's share?

    Correct chain logic:
    - C does booking → C gets 10%
    - B (C's senior, 15%) → B gets (15-10)=5% difference
    - A (B's senior, 23%) → A gets (23-15)=8% difference (on B's bookings level)
    So A gets 8% difference on ALL bookings under B's chain.
    """
    records = fetch_exec_records(exec_name, date_from, date_to) # own

    exec_pct, _ = get_exec_slab(exec_name)

    def add_downline_diff(senior_name, senior_pct, level=0):
        for dl in get_direct_downlines(senior_name):
            dl_pct, dl_rs = get_exec_slab(dl)
            diff_pct = senior_pct - dl_pct
            if diff_pct > 0:
                # Fetch dl's bookings with diff_pct
                dl_recs = fetch_exec_records(dl, date_from, date_to, override_pct=diff_pct)
                for r in dl_recs:
                    r['via'] = dl
                    r['customer']= f"{r['customer']} [{dl}]"
                records.extend(dl_recs)
            # Recurse: A also benefits from C through B's chain
            add_downline_diff(dl, senior_pct, level+1)

    add_downline_diff(exec_name, exec_pct)
    return records


def build_all(exec_name, date_from, date_to):
    """Self + Group combined."""
    # build_group already includes self
    return build_group(exec_name, date_from, date_to)


# ---------------------------------------------------------------
# 5. PDF GENERATOR (A4 Portrait)
# ---------------------------------------------------------------
def generate_pdf(exec_name, records, date_from, date_to, mode_label):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                rightMargin=12*mm, leftMargin=12*mm,
                topMargin=10*mm, bottomMargin=10*mm)
    BLACK = colors.black
    NAVY = colors.HexColor("#1e3a8a")
    LTBLUE = colors.HexColor("#e0f2fe")
    GREY = colors.HexColor("#f8fafc")
    GREEN = colors.HexColor("#d1fae5")
    DKGREEN = colors.HexColor("#065f46")
    story = []

    # ── Company Header ──────────────────────────────────────────
    story.append(Paragraph(
        "<b>FIRSTCHOICE INFRA</b>",
        ParagraphStyle('TT', fontSize=20, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=3)))
    story.append(Paragraph(
        "<i>Symbol Of Trust...</i>",
        ParagraphStyle('ST', fontSize=9, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph(
        "Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034",
        ParagraphStyle('AD', fontSize=8, alignment=TA_CENTER, spaceAfter=5)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=4))
    story.append(Paragraph(
        f"<b>Executive Commission Statement — {mode_label}</b>",
        ParagraphStyle('ES', fontSize=12, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=0.5, color=NAVY, spaceAfter=6))

    # ── Partner (left) + Period (right) ────────────────────────
    exec_info = get_exec_info(exec_name)
    senior_nm = exec_info.get('senior_name', 'Direct')
    pct, rs_d = get_exec_slab(exec_name)
    slab_str = (f"{pct}% (Disc: Rs {rs_d:,.0f})" if pct > 0 and rs_d > 0
                 else f"{pct}%" if pct > 0 else f"Rs {rs_d:,.0f} Fixed")

    hdr_tbl = Table([
        [Paragraph(f"<b>Partner:</b> {exec_name}",
                   ParagraphStyle('PL', fontSize=9, fontName='Helvetica')),
         Paragraph(f"<b>Period:</b> {date_from} to {date_to}",
                   ParagraphStyle('PR', fontSize=9, fontName='Helvetica',
                                  alignment=TA_RIGHT))],
        [Paragraph(f"<b>Senior:</b> {senior_nm} | <b>Slab:</b> {slab_str}",
                   ParagraphStyle('SL', fontSize=8)),
         Paragraph(f"<b>Generated:</b> {datetime.date.today()}",
                   ParagraphStyle('GR', fontSize=8, alignment=TA_RIGHT))],
    ], colWidths=[95*mm, 75*mm])
    hdr_tbl.setStyle(TableStyle([
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('BOTTOMPADDING',(0,0),(-1,-1), 3),
    ]))
    story.append(hdr_tbl)
    story.append(Spacer(1, 5))

    # ── Main Table ──────────────────────────────────────────────
    headers = ["Sr\nNo", "Project", "Plot\nNo", "Mauza", "Client Name",
               "Received\nAmt (Rs)", "Received\nDate",
               "Gross\nComm", "Discount\nAmt", "Net\nComm", "TDS\n2%", "In\nHand"]
    cw = [8*mm, 28*mm, 10*mm, 18*mm, 32*mm,
          18*mm, 18*mm, 16*mm, 16*mm, 16*mm, 12*mm, 16*mm]

    tdata = [headers]
    tot = {k: 0.0 for k in ['received','gross','disc_amt','net_comm','tds','in_hand']}

    for idx, r in enumerate(records, 1):
        tdata.append([
            str(idx),
            r['project'],
            str(r['plot']),
            r['mauza'],
            r['customer'],
            f"{r['received']:,.2f}",
            r['date'],
            f"{r['gross']:,.2f}",
            f"{r['disc_amt']:,.2f}",
            f"{r['net_comm']:,.2f}",
            f"{r['tds']:,.2f}",
            f"{r['in_hand']:,.2f}",
        ])
        for k in tot: tot[k] += r[k]

    # Totals row
    tdata.append([
        "TOTAL", "", "", "", "",
        f"{tot['received']:,.2f}", "",
        f"{tot['gross']:,.2f}",
        f"{tot['disc_amt']:,.2f}",
        f"{tot['net_comm']:,.2f}",
        f"{tot['tds']:,.2f}",
        f"{tot['in_hand']:,.2f}",
    ])

    tbl = Table(tdata, colWidths=cw, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 7),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        # Body
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-2), 7),
        ('ALIGN', (0,1), (-1,-2), 'CENTER'),
        ('ALIGN', (4,1), (4,-2), 'LEFT'), # Client name left
        ('ALIGN', (1,1), (1,-2), 'LEFT'), # Project left
        ('ROWBACKGROUNDS',(0,1), (-1,-2), [colors.white, GREY]),
        # Totals row
        ('BACKGROUND', (0,-1),(-1,-1), NAVY),
        ('TEXTCOLOR', (0,-1),(-1,-1), colors.white),
        ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1),(-1,-1), 7),
        # In Hand column highlight
        ('BACKGROUND', (-1,1),(-1,-2), colors.HexColor("#fef3c7")),
        ('TEXTCOLOR', (-1,1),(-1,-2), colors.HexColor("#92400e")),
        ('FONTNAME', (-1,1),(-1,-2), 'Helvetica-Bold'),
        # Grid
        ('BOX', (0,0), (-1,-1), 0.8, BLACK),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 2),
        ('RIGHTPADDING', (0,0), (-1,-1), 2),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 8))

    # ── Summary Bifurcation Box ──────────────────────────────────
    story.append(Paragraph("<b>Summary Bifurcation</b>",
        ParagraphStyle('SB', fontSize=10, fontName='Helvetica-Bold',
                       textColor=NAVY, spaceAfter=4)))

    sum_data = [
        ["Total Received", "Gross Commission", "Total Discount", "Net Commission", "Total TDS", "IN HAND"],
        [f"Rs {tot['received']:,.2f}",
         f"Rs {tot['gross']:,.2f}",
         f"Rs {tot['disc_amt']:,.2f}",
         f"Rs {tot['net_comm']:,.2f}",
         f"Rs {tot['tds']:,.2f}",
         f"Rs {tot['in_hand']:,.2f}"],
    ]
    s_cw = [30*mm, 30*mm, 28*mm, 30*mm, 24*mm, 28*mm]
    stbl = Table(sum_data, colWidths=s_cw)
    stbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-2,1), LTBLUE),
        ('BACKGROUND', (-1,1),(-1,1), GREEN),
        ('TEXTCOLOR', (-1,1),(-1,1), DKGREEN),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('BOX', (0,0), (-1,-1), 1, NAVY),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#93c5fd")),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(stbl)

    # ── Footer ───────────────────────────────────────────────────
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
# 6. STREAMLIT UI
# ---------------------------------------------------------------
st.markdown("### 👤 Step 1 — Partner Select Karo")

exec_names_all = sorted([n for n, d in exec_data_root.items() if isinstance(d, dict)])
exec_options = exec_names_all if user_role == 'admin' else [curr_user]

if not exec_options:
    st.warning("Koi executive nahi mila. Pehle Partner Portal mein add karo.")
    st.stop()

selected_exec = st.selectbox("Partner / Executive:", exec_options)

# Info row
if selected_exec:
    pct, rs_d = get_exec_slab(selected_exec)
    senior = get_exec_senior(selected_exec)
    downlines = get_all_downlines(selected_exec)
    c1, c2, c3 = st.columns(3)
    slab_info = (f"{pct}% (Disc ₹{rs_d:,.0f})" if rs_d > 0 and pct > 0
                  else f"{pct}%" if pct > 0 else f"₹{rs_d:,.0f} Fixed")
    c1.info(f"**Slab:** {slab_info}")
    c2.info(f"**Senior:** {senior if senior else 'Direct (Company)'}")
    c3.info(f"**Downlines:** {len(downlines)}")

st.markdown("### 📅 Step 2 — Period Select Karo")
col1, col2 = st.columns(2)
date_from = col1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to = col2.date_input("To Date:", datetime.date.today())

st.divider()
st.markdown("### 🖨️ Step 3 — Statement Type Choose Karo")

# ── 3 Buttons: SELF | GROUP | ALL ────────────────────────────
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

    # Preview
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

    # Summary
    st.markdown("#### 📊 Summary")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total Received", f"₹ {df['received'].sum():,.2f}")
    m2.metric("Gross Comm", f"₹ {df['gross'].sum():,.2f}")
    m3.metric("Discount", f"₹ {df['disc_amt'].sum():,.2f}")
    m4.metric("Net Comm", f"₹ {df['net_comm'].sum():,.2f}")
    m5.metric("💰 In Hand", f"₹ {df['in_hand'].sum():,.2f}")

    st.divider()

    # PDF
    with st.spinner("PDF ban rahi hai..."):
        pdf_bytes = generate_pdf(exec_name, records, str(date_from), str(date_to), mode_label)

    fname = f"Commission_{exec_name.replace(' ','_')}_{mode_label}_{date_from}_to_{date_to}.pdf"
    b64 = base64.b64encode(pdf_bytes).decode()

    col_dl, col_pr = st.columns(2)
    with col_dl:
        st.download_button(
            label="📥 Download PDF (A4)",
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
            var url = URL.createObjectURL(blob);
            var win = window.open(url,'_blank');
            win.addEventListener('load', function(){{ win.print(); }});
        }}
        </script>
        <button onclick="printPDF()"
            style="width:100%;background:linear-gradient(90deg,#059669,#10b981);
                   color:white;padding:12px;border-radius:8px;border:none;
                   font-weight:700;font-size:15px;cursor:pointer;
                   box-shadow:0 4px 12px rgba(5,150,105,0.4);">
            🖨️ Print PDF (A4)
        </button>
        """, height=55)

    st.info("💡 Download karo ya Print karo — dono A4 size mein honge.")


# Trigger buttons
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

