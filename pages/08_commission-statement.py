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
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

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
    "Select executive, period and generate a professional PDF commission statement.</p>",
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
    """Return full dict of executive from Partner Portal."""
    for k, v in exec_data_root.items():
        if str(k).strip().lower() == str(exec_name).strip().lower():
            return v
    return {}


def get_exec_slab(exec_name):
    """Return (pct, rs_discount) for executive."""
    info = get_exec_info(exec_name)
    return sf(info.get('percentage_exec', 0.0)), sf(info.get('rupees_exec', 0.0))


def get_exec_senior(exec_name):
    """Return senior/upline name of executive."""
    info = get_exec_info(exec_name)
    senior = info.get('senior_name', 'Direct')
    if not senior or str(senior).strip().lower() in ['', 'direct', 'none']:
        return None
    return str(senior).strip()


def get_project_comm_type(project_name):
    """
    Return comm_type for a project: 'Percentage (%)' or 'Rupees (₹)'
    from Admin Panel data.
    """
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


def compute_commission_row(received_amt, exec_pct, exec_rs_discount, comm_type,
                           downline_pct=0.0):
    """
    Commission calculation:

    CASE A — Project comm_type = Percentage (%):
      → Use executive's percentage slab
      → Gross        = received × exec_pct / 100
      → Discount_amt = exec_rs_discount × exec_pct / 100  (Rs discount converted to % impact)
      → Net Comm     = Gross − Discount_amt
      → TDS          = Net Comm × 2%
      → In Hand      = Net Comm − TDS
      → If downline exists:
            Senior Gross    = received × (exec_pct − downline_pct) / 100
            (same discount & TDS logic on senior's gross)

    CASE B — Project comm_type = Rupees (₹):
      → Use executive's fixed Rs slab directly as commission
      → Gross        = exec_rs_discount  (the fixed Rs amount IS the commission here)
      → Discount_amt = 0  (no % discount applicable)
      → Net Comm     = Gross
      → TDS          = Net Comm × 2%
      → In Hand      = Net Comm − TDS
    """
    if received_amt <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

    is_pct_project = 'percentage' in str(comm_type).lower() or '%' in str(comm_type)

    if is_pct_project:
        # Executive's own commission
        gross        = received_amt * exec_pct / 100.0
        discount_amt = (exec_rs_discount * exec_pct / 100.0) if exec_rs_discount > 0 else 0.0
        net_comm     = max(0.0, gross - discount_amt)
        tds          = net_comm * 0.02
        in_hand      = net_comm - tds

        # Downline difference commission (only for senior on downline's booking)
        if downline_pct > 0 and exec_pct > downline_pct:
            diff_pct        = exec_pct - downline_pct
            diff_gross      = received_amt * diff_pct / 100.0
            diff_discount   = (exec_rs_discount * diff_pct / 100.0) if exec_rs_discount > 0 else 0.0
            diff_net        = max(0.0, diff_gross - diff_discount)
            diff_tds        = diff_net * 0.02
            diff_in_hand    = diff_net - diff_tds
        else:
            diff_gross = diff_discount = diff_net = diff_tds = diff_in_hand = 0.0

        return gross, discount_amt, net_comm, tds, in_hand, diff_gross, diff_discount, diff_net, diff_tds

    else:
        # Rs-based project — fixed commission amount
        gross    = exec_rs_discount   # fixed Rs IS the commission
        net_comm = gross
        tds      = net_comm * 0.02
        in_hand  = net_comm - tds
        return gross, 0.0, net_comm, tds, in_hand, 0.0, 0.0, 0.0, 0.0


def get_all_received_payments(plot_info):
    """Return list of {date, amount} for every received payment."""
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


def collect_records(exec_name, date_from, date_to, is_downline_view=False, downline_exec_pct=0.0):
    """
    Collect one row per PAYMENT for the executive.
    If is_downline_view=True → calculate only DIFFERENCE commission for senior.
    """
    exec_pct, exec_rs_disc = get_exec_slab(exec_name)
    records = []

    project_names = [
        n for n, d in db_data.items()
        if isinstance(d, dict) and ('plots' in d or 'total_plots' in d)
    ]

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

            plot_exec = str(plot_info.get('executive_name', '')).strip().lower()
            if plot_exec != str(exec_name).strip().lower():
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
                (gross, disc, net_comm, tds, in_hand,
                 diff_gross, diff_disc, diff_net, diff_tds) = compute_commission_row(
                    received, exec_pct, exec_rs_disc, comm_type, downline_exec_pct)

                is_pct = 'percentage' in str(comm_type).lower() or '%' in str(comm_type)

                if is_downline_view:
                    # Senior earns only the DIFFERENCE
                    use_gross   = diff_gross
                    use_disc    = diff_disc
                    use_net     = diff_net
                    use_tds     = diff_tds
                    use_inhand  = max(0.0, diff_net - diff_tds)
                    comm_label  = f"Diff {exec_pct - downline_exec_pct:.1f}%"
                else:
                    use_gross   = gross
                    use_disc    = disc
                    use_net     = net_comm
                    use_tds     = tds
                    use_inhand  = in_hand
                    if is_pct:
                        comm_label = f"{exec_pct}%"
                        if exec_rs_disc > 0:
                            comm_label += f" (Disc ₹{exec_rs_disc:,.0f})"
                    else:
                        comm_label = f"₹{exec_rs_disc:,.0f} Fixed"

                if use_gross <= 0:
                    continue

                records.append({
                    'Mauja'      : mauza,
                    'Project'    : p_name,
                    'Plot'       : booked_str,
                    'Customer'   : customer,
                    'Received'   : received,
                    'Date'       : str(pmt_date),
                    'Gross'      : use_gross,
                    'Discount'   : use_disc,
                    'Net Comm'   : use_net,
                    'TDS'        : use_tds,
                    'In Hand'    : use_inhand,
                    'Comm Label' : comm_label,
                    '_exec'      : exec_name,
                })
    return records


def collect_all_records_for_exec(exec_name, date_from, date_to):
    """
    Collect:
    1. Executive's own bookings (own commission)
    2. Difference commission from each direct downline
    """
    all_records = []

    # Own bookings
    own = collect_records(exec_name, date_from, date_to,
                          is_downline_view=False, downline_exec_pct=0.0)
    all_records.extend(own)

    # Downline difference commission
    exec_pct, _ = get_exec_slab(exec_name)
    direct_downlines = []
    for ex, det in exec_data_root.items():
        if isinstance(det, dict):
            senior = str(det.get('senior_name', '')).strip().lower()
            if senior == str(exec_name).strip().lower():
                direct_downlines.append(ex)

    for dl_name in direct_downlines:
        dl_pct, _ = get_exec_slab(dl_name)
        if exec_pct > dl_pct:
            dl_records = collect_records(dl_name, date_from, date_to,
                                         is_downline_view=True,
                                         downline_exec_pct=dl_pct)
            for r in dl_records:
                r['Customer'] = f"{r['Customer']} (via {dl_name})"
                r['Comm Label'] = f"Diff {exec_pct - dl_pct:.1f}% on {dl_name}"
            all_records.extend(dl_records)

    return all_records


# ---------------------------------------------------------------
# 5. PDF GENERATOR
# ---------------------------------------------------------------
def generate_pdf(exec_name, records, date_from, date_to):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=10*mm, bottomMargin=10*mm)

    BLACK   = colors.black
    GREY_LT = colors.HexColor("#f8fafc")
    story   = []

    # ── Company Header ──────────────────────────────────────────
    story.append(Paragraph(
        "<b>FIRSTCHOICE INFRA</b>",
        ParagraphStyle('TT', fontSize=24, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=3)))
    story.append(Paragraph(
        "<i>Symbol Of Trust...</i>",
        ParagraphStyle('ST', fontSize=10, alignment=TA_CENTER, spaceAfter=3)))
    story.append(Paragraph(
        "Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034",
        ParagraphStyle('AD', fontSize=9, alignment=TA_CENTER, spaceAfter=6)))
    story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceAfter=5))
    story.append(Paragraph(
        "<b>Executive Commission Statement</b>",
        ParagraphStyle('ES', fontSize=14, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=8)))

    # ── Partner + Period ────────────────────────────────────────
    exec_info  = get_exec_info(exec_name)
    senior_nm  = exec_info.get('senior_name', 'Direct')
    pct, rs_d  = get_exec_slab(exec_name)
    slab_str   = (f"{pct}% (Disc: Rs {rs_d:,.0f})" if pct > 0 and rs_d > 0
                  else f"{pct}%" if pct > 0 else f"Rs {rs_d:,.0f} Fixed")

    info_data = [[
        f"Partner: {exec_name}",
        f"Senior: {senior_nm}  |  Slab: {slab_str}",
        f"Period: {date_from} to {date_to}"
    ]]
    info_t = Table(info_data, colWidths=[85*mm, 90*mm, 82*mm])
    info_t.setStyle(TableStyle([
        ('FONTNAME',  (0,0),(0,0), 'Helvetica-Bold'),
        ('FONTNAME',  (2,0),(2,0), 'Helvetica-Bold'),
        ('ALIGN',     (2,0),(2,0), 'RIGHT'),
        ('FONTSIZE',  (0,0),(-1,-1), 9),
        ('BOTTOMPADDING', (0,0),(-1,-1), 5),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 4))

    # ── Main Table ──────────────────────────────────────────────
    headers    = ["S.No.", "Mauja", "Project", "Plot", "Customer",
                  "Received", "Date", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]
    col_widths = [10*mm, 18*mm, 34*mm, 12*mm, 48*mm,
                  22*mm, 20*mm, 20*mm, 18*mm, 20*mm, 14*mm, 21*mm]

    table_data = [headers]
    tot_recv = tot_gross = tot_disc = tot_net = tot_tds = tot_ih = 0.0

    for idx, r in enumerate(records, 1):
        table_data.append([
            str(idx),
            r['Mauja'],
            r['Project'],
            str(r['Plot']),
            r['Customer'],
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

    table_data.append([
        "TOTAL", "", "", "", "",
        f"{tot_recv:,.2f}", "",
        f"{tot_gross:,.2f}",
        f"{tot_disc:,.2f}",
        f"{tot_net:,.2f}",
        f"{tot_tds:,.2f}",
        f"{tot_ih:,.2f}",
    ])

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        ('FONTNAME',       (0,0),  (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',       (0,0),  (-1,0),  8),
        ('ALIGN',          (0,0),  (-1,0),  'CENTER'),
        ('BACKGROUND',     (0,0),  (-1,0),  colors.white),
        ('FONTNAME',       (0,1),  (-1,-2), 'Helvetica'),
        ('FONTSIZE',       (0,1),  (-1,-2), 8),
        ('ALIGN',          (0,1),  (-1,-2), 'CENTER'),
        ('ALIGN',          (4,1),  (4,-2),  'LEFT'),
        ('ROWBACKGROUNDS', (0,1),  (-1,-2), [colors.white, GREY_LT]),
        ('FONTNAME',       (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE',       (0,-1), (-1,-1), 8),
        ('ALIGN',          (0,-1), (-1,-1), 'CENTER'),
        ('BOX',            (0,0),  (-1,-1), 0.8, BLACK),
        ('INNERGRID',      (0,0),  (-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING',     (0,0),  (-1,-1), 4),
        ('BOTTOMPADDING',  (0,0),  (-1,-1), 4),
        ('LEFTPADDING',    (0,0),  (-1,-1), 3),
        ('RIGHTPADDING',   (0,0),  (-1,-1), 3),
        ('VALIGN',         (0,0),  (-1,-1), 'MIDDLE'),
    ]))
    story.append(tbl)

    # ── Summary Box ─────────────────────────────────────────────
    story.append(Spacer(1, 8))
    summary_data = [
        ["Total Payments", "Total Received", "Total Gross", "Total Net Comm", "Total TDS", "Total IN HAND"],
        [str(len(records)),
         f"Rs {tot_recv:,.2f}",
         f"Rs {tot_gross:,.2f}",
         f"Rs {tot_net:,.2f}",
         f"Rs {tot_tds:,.2f}",
         f"Rs {tot_ih:,.2f}"],
    ]
    s_tbl = Table(summary_data, colWidths=[30*mm, 38*mm, 34*mm, 34*mm, 28*mm, 36*mm])
    s_tbl.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,0),  colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR',     (0,0), (-1,0),  colors.white),
        ('FONTNAME',      (0,0), (-1,0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0,0), (-1,-1), 9),
        ('ALIGN',         (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND',    (0,1), (-2,1),  colors.HexColor("#e0f2fe")),
        ('BACKGROUND',    (-1,1),(-1,1),  colors.HexColor("#d1fae5")),
        ('TEXTCOLOR',     (-1,1),(-1,1),  colors.HexColor("#065f46")),
        ('FONTNAME',      (0,1), (-1,1),  'Helvetica-Bold'),
        ('BOX',           (0,0), (-1,-1), 1, colors.HexColor("#1e3a8a")),
        ('INNERGRID',     (0,0), (-1,-1), 0.4, colors.HexColor("#93c5fd")),
        ('TOPPADDING',    (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
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

if user_role == 'admin':
    exec_options = exec_names_all
else:
    exec_options = [curr_user]

if not exec_options:
    st.warning("Koi executive nahi mila. Pehle Partner Portal mein add karo.")
    st.stop()

selected_exec = st.selectbox("Executive / Partner:", exec_options)

# Show executive info
if selected_exec:
    pct, rs_d = get_exec_slab(selected_exec)
    senior    = get_exec_senior(selected_exec)
    downlines = get_all_downlines(selected_exec)

    c1, c2, c3 = st.columns(3)
    c1.info(f"**Commission Slab:** {pct}% + ₹{rs_d:,.0f} discount" if rs_d > 0
            else f"**Commission Slab:** {pct}%" if pct > 0
            else f"**Commission Slab:** ₹{rs_d:,.0f} Fixed")
    c2.info(f"**Senior / Upline:** {senior if senior else 'Direct (Company)'}")
    c3.info(f"**Total Downlines:** {len(downlines)}")

st.markdown("### 📅 Step 2 — Statement Period")
col1, col2 = st.columns(2)
date_from = col1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to   = col2.date_input("To Date:",   datetime.date.today())

st.divider()
st.markdown("### 🖨️ Step 3 — Statement Generate Karo")

if st.button("🖨️ Generate Commission Statement PDF", use_container_width=True, type="primary"):

    with st.spinner("Data collect ho raha hai..."):
        all_records = collect_all_records_for_exec(selected_exec, date_from, date_to)
        all_records.sort(key=lambda x: x['Date'])

    if not all_records:
        st.warning("⚠️ Is period mein koi payment record nahi mila.")
    else:
        st.success(f"✅ **{len(all_records)}** payment record(s) mile.")

        # ── Preview Table ─────────────────────────────────────
        df = pd.DataFrame(all_records)
        df_show = df[['Mauja','Project','Plot','Customer','Comm Label',
                       'Received','Date','Gross','Discount','Net Comm','TDS','In Hand']].copy()
        for c in ['Received','Gross','Discount','Net Comm','TDS','In Hand']:
            df_show[c] = df_show[c].apply(lambda x: f"₹ {x:,.2f}")
        df_show.index = range(1, len(df_show)+1)
        df_show.index.name = "S.No."
        st.dataframe(df_show, use_container_width=True)

        # ── Summary ───────────────────────────────────────────
        st.markdown("#### 📊 Summary")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Total Payments",  len(all_records))
        m2.metric("Total Received",  f"₹ {df['Received'].sum():,.2f}")
        m3.metric("Gross Comm",      f"₹ {df['Gross'].sum():,.2f}")
        m4.metric("Net Comm",        f"₹ {df['Net Comm'].sum():,.2f}")
        m5.metric("💰 In Hand",       f"₹ {df['In Hand'].sum():,.2f}")

        st.divider()

        # ── PDF Generate ──────────────────────────────────────
        with st.spinner("PDF ban rahi hai..."):
            pdf_bytes = generate_pdf(
                exec_name = selected_exec,
                records   = all_records,
                date_from = str(date_from),
                date_to   = str(date_to),
            )

        fname = f"Commission_{selected_exec.replace(' ','_')}_{date_from}_to_{date_to}.pdf"
        b64   = base64.b64encode(pdf_bytes).decode()

        # ── Download + Print Buttons ──────────────────────────
        col_dl, col_pr = st.columns(2)

        with col_dl:
            st.download_button(
                label               = "📥 Download PDF",
                data                = pdf_bytes,
                file_name           = fname,
                mime                = "application/pdf",
                use_container_width = True,
            )

        with col_pr:
            # JavaScript print — opens PDF in new tab and triggers print dialog
            print_html = f"""
            <script>
            function printPDF() {{
                var byteCharacters = atob("{b64}");
                var byteNumbers = new Array(byteCharacters.length);
                for (var i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                var byteArray = new Uint8Array(byteNumbers);
                var blob = new Blob([byteArray], {{type: 'application/pdf'}});
                var blobUrl = URL.createObjectURL(blob);
                var win = window.open(blobUrl, '_blank');
                win.onload = function() {{
                    win.print();
                }};
            }}
            </script>
            <button onclick="printPDF()"
                style="width:100%; background:linear-gradient(90deg,#059669,#10b981);
                       color:white; padding:12px; border-radius:8px; border:none;
                       font-weight:700; font-size:15px; cursor:pointer;
                       box-shadow:0 4px 12px rgba(5,150,105,0.4);">
                🖨️ Print PDF
            </button>
            """
            st.components.v1.html(print_html, height=55)

        st.info("💡 'Download PDF' se save karo ya '🖨️ Print PDF' se seedha print dialog khulega.")
