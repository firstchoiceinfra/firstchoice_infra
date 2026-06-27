import streamlit as st
import pandas as pd
import database
import datetime
import io

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
.stButton>button:hover {{
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(59,130,246,0.6);
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# 3. HEADING
# ---------------------------------------------------------------
st.markdown("<h1 style='text-align:center;'>💼 FC Infra — Commission Statement</h1>",
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


def get_all_downlines(manager_name):
    mgr = str(manager_name).strip().lower()
    result = []
    for ex, det in exec_data_root.items():
        if str(det.get('senior_name', '')).strip().lower() == mgr:
            result.append(ex)
            result.extend(get_all_downlines(ex))
    return list(set(result))


def get_exec_slab(exec_name):
    """Return (pct, rs_discount) from Partner Portal for this executive."""
    for k, v in exec_data_root.items():
        if str(k).strip().lower() == str(exec_name).strip().lower():
            return sf(v.get('percentage_exec', 0.0)), sf(v.get('rupees_exec', 0.0))
    return 0.0, 0.0


def compute_commission_row(received_amt, pct, rs_discount):
    """
    Logic as per user requirement:
    - Gross = received × pct/100
    - Discount = convert rs_discount to % of received, then apply on gross
                 i.e. discount_pct = (rs_discount / received) * 100
                        discount_amt = gross × discount_pct / 100 = rs_discount × pct/100
                 Simplified: discount_amt = rs_discount * pct / 100
    - Net Comm = Gross - Discount
    - TDS = Net Comm × 2%
    - In Hand = Net Comm - TDS
    """
    if received_amt <= 0 or pct <= 0:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    gross = received_amt * pct / 100.0
    # rs_discount is a flat rupee amount → its proportional impact on commission:
    discount_amt = rs_discount * pct / 100.0 if rs_discount > 0 else 0.0
    net_comm = max(0.0, gross - discount_amt)
    tds = net_comm * 0.02
    in_hand = net_comm - tds
    return gross, discount_amt, net_comm, tds, in_hand


def get_all_received_payments(plot_info):
    """
    Returns list of (date, amount) for every received payment in a booking:
    token + each partial payment.
    """
    payments = []
    tok_amt = sf(plot_info.get('token_amount', 0.0))
    tok_date = plot_info.get('receipt_date', plot_info.get('booking_date', str(datetime.date.today())))
    if tok_amt > 0:
        payments.append({'date': tok_date, 'amount': tok_amt})
    for p in plot_info.get('partial_payments', []):
        amt = sf(p.get('amount', 0.0))
        dt = p.get('date', str(datetime.date.today()))
        if amt > 0:
            payments.append({'date': dt, 'amount': amt})
    return payments


def get_project_mauza(project_name):
    p = db_data.get(project_name, {})
    return p.get('mauza', project_name)


def collect_records(exec_name, date_from, date_to):
    """
    Collect one row per PAYMENT (not per booking) for the executive,
    filtered by date range. Commission is on received amount.
    """
    pct, rs_discount = get_exec_slab(exec_name)
    records = []

    project_names = [
        n for n, d in db_data.items()
        if isinstance(d, dict) and ('plots' in d or 'total_plots' in d)
    ]

    for p_name in project_names:
        p_info = db_data[p_name]
        p_plots = p_info.get('plots', {})
        if isinstance(p_plots, list):
            p_plots = {str(i): p for i, p in enumerate(p_plots) if p is not None}

        mauza = get_project_mauza(p_name)

        for plot_id, plot_info in p_plots.items():
            if not isinstance(plot_info, dict): continue
            if str(plot_info.get('status', '')).lower() != 'booked': continue
            if plot_info.get('is_primary', True) is False: continue
            if str(plot_info.get('executive_name', '')).strip().lower() != str(exec_name).strip().lower():
                continue

            customer = str(plot_info.get('customer_name', 'N/A')).title()
            booked_str = plot_info.get('booked_plots_str', plot_id)
            payments = get_all_received_payments(plot_info)

            for pmt in payments:
                try:
                    pmt_date = datetime.date.fromisoformat(str(pmt['date'])[:10])
                except:
                    pmt_date = datetime.date.today()

                if not (date_from <= pmt_date <= date_to):
                    continue

                received = pmt['amount']
                gross, discount_amt, net_comm, tds, in_hand = compute_commission_row(
                    received, pct, rs_discount)

                records.append({
                    'Mauja' : mauza,
                    'Project' : p_name,
                    'Plot' : booked_str,
                    'Customer' : customer,
                    'Received' : received,
                    'Date' : str(pmt_date),
                    'Gross' : gross,
                    'Discount' : discount_amt,
                    'Net Comm' : net_comm,
                    'TDS' : tds,
                    'In Hand' : in_hand,
                    '_exec' : exec_name,
                    '_pct' : pct,
                    '_disc_rs' : rs_discount,
                })
    return records


# ---------------------------------------------------------------
# 5. PDF GENERATOR (landscape A4, exact sample format)
# ---------------------------------------------------------------
def generate_pdf(exec_name, records, date_from, date_to, include_downlines, downline_names):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4),
        rightMargin=12*mm, leftMargin=12*mm,
        topMargin=10*mm, bottomMargin=10*mm)

    BLACK = colors.black
    GREY_LT = colors.HexColor("#f8fafc")
    GREY_HD = colors.HexColor("#e2e8f0")
    story = []

    # ── Company Header ──────────────────────────────────────────
    story.append(Paragraph(
        "<b>FIRSTCHOICE INFRA</b>",
        ParagraphStyle('TT', fontSize=24, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=4)))
    story.append(Paragraph(
        "<i>Symbol Of Trust...</i>",
        ParagraphStyle('ST', fontSize=10, alignment=TA_CENTER, spaceAfter=4)))
    story.append(Paragraph(
        "Plot No. 06, Shop No.106, Motilal Nagar, Gonhi(Sim) Bahadura, Nagpur-440034",
        ParagraphStyle('AD', fontSize=9, alignment=TA_CENTER, spaceAfter=8)))
    story.append(HRFlowable(width="100%", thickness=1, color=BLACK, spaceAfter=6))

    story.append(Paragraph(
        "<b>Executive Commission Statement</b>",
        ParagraphStyle('ES', fontSize=14, alignment=TA_CENTER,
                       fontName='Helvetica-Bold', spaceAfter=10)))

    # ── Partner + Period info ───────────────────────────────────
    partner_label = exec_name
    if include_downlines and downline_names:
        partner_label += f" + Team ({', '.join(downline_names[:3])}{'...' if len(downline_names)>3 else ''})"

    pct, rs_disc = get_exec_slab(exec_name)
    slab_str = (f"{pct}%" if pct > 0 and rs_disc == 0 else
                f"Rs {rs_disc:,.0f} discount" if rs_disc > 0 and pct == 0 else
                f"{pct}% (Disc: Rs {rs_disc:,.0f})")

    info_data = [[
        f"Partner: {partner_label}",
        f"Commission Slab: {slab_str}",
        f"Period: {date_from} to {date_to}"
    ]]
    info_t = Table(info_data, colWidths=[90*mm, 80*mm, 87*mm])
    info_t.setStyle(TableStyle([
        ('FONTNAME', (0,0),(0,0), 'Helvetica-Bold'),
        ('FONTNAME', (1,0),(1,0), 'Helvetica'),
        ('FONTNAME', (2,0),(2,0), 'Helvetica-Bold'),
        ('ALIGN', (2,0),(2,0), 'RIGHT'),
        ('FONTSIZE', (0,0),(-1,-1), 9),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
    ]))
    story.append(info_t)
    story.append(Spacer(1, 4))

    # ── Main Table ──────────────────────────────────────────────
    headers = ["S.No.", "Mauja", "Project", "Plot", "Customer",
                "Received", "Date", "Gross", "Discount", "Net Comm", "TDS", "In Hand"]
    col_widths = [10*mm, 18*mm, 36*mm, 12*mm, 48*mm,
                  22*mm, 22*mm, 20*mm, 18*mm, 20*mm, 15*mm, 20*mm]

    table_data = [headers]
    tot_received = tot_gross = tot_disc = tot_net = tot_tds = tot_inhand = 0.0

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
        tot_received += r['Received']
        tot_gross += r['Gross']
        tot_disc += r['Discount']
        tot_net += r['Net Comm']
        tot_tds += r['TDS']
        tot_inhand += r['In Hand']

    # Totals row
    table_data.append([
        "TOTAL", "", "", "", "",
        f"{tot_received:,.2f}", "",
        f"{tot_gross:,.2f}",
        f"{tot_disc:,.2f}",
        f"{tot_net:,.2f}",
        f"{tot_tds:,.2f}",
        f"{tot_inhand:,.2f}",
    ])

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Header
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), colors.white),
        ('BOX', (0,0), (-1,0), 0.8, BLACK),
        # Body
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-2), 8),
        ('ALIGN', (0,1), (-1,-2), 'CENTER'),
        ('ALIGN', (4,1), (4,-2), 'LEFT'), # Customer left-align
        ('ROWBACKGROUNDS',(0,1), (-1,-2), [colors.white, GREY_LT]),
        # Totals row
        ('FONTNAME', (0,-1),(-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1),(-1,-1), 8),
        ('ALIGN', (0,-1),(-1,-1), 'CENTER'),
        # Full grid
        ('BOX', (0,0), (-1,-1), 0.8, BLACK),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer


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

include_downlines = st.checkbox("📥 Downline executives ke bookings bhi include karo", value=False)

st.markdown("### 📅 Step 2 — Statement Period")
col1, col2 = st.columns(2)
date_from = col1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to = col2.date_input("To Date:", datetime.date.today())

st.divider()
st.markdown("### 🖨️ Step 3 — Statement Generate Karo")

if st.button("🖨️ Generate Commission Statement PDF", use_container_width=True, type="primary"):

    execs_to_use = [selected_exec]
    downline_names = []
    if include_downlines:
        downline_names = get_all_downlines(selected_exec)
        execs_to_use.extend(downline_names)
    execs_to_use = list(set(execs_to_use))

    all_records = []
    for ex in execs_to_use:
        all_records.extend(collect_records(ex, date_from, date_to))

    # Sort by date
    all_records.sort(key=lambda x: x['Date'])

    if not all_records:
        st.warning("⚠️ Is period mein koi payment record nahi mila.")
    else:
        st.success(f"✅ **{len(all_records)}** payment record(s) mile.")

        # ── Preview Table ─────────────────────────────────────
        df = pd.DataFrame(all_records)
        df_show = df[['Mauja','Project','Plot','Customer','Received','Date',
                       'Gross','Discount','Net Comm','TDS','In Hand']].copy()
        for c in ['Received','Gross','Discount','Net Comm','TDS','In Hand']:
            df_show[c] = df_show[c].apply(lambda x: f"₹ {x:,.2f}")
        df_show.index = range(1, len(df_show)+1)
        df_show.index.name = "S.No."
        st.dataframe(df_show, use_container_width=True)

        # ── Summary Metrics ───────────────────────────────────
        st.markdown("#### 📊 Summary")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Received", f"₹ {df['Received'].sum():,.2f}")
        m2.metric("Gross Commission", f"₹ {df['Gross'].sum():,.2f}")
        m3.metric("Net Commission", f"₹ {df['Net Comm'].sum():,.2f}")
        m4.metric("💰 In Hand", f"₹ {df['In Hand'].sum():,.2f}")

        st.divider()

        # ── PDF Download + Print ──────────────────────────────
        with st.spinner("PDF generate ho rahi hai..."):
            pdf_buf = generate_pdf(
                exec_name = selected_exec,
                records = all_records,
                date_from = str(date_from),
                date_to = str(date_to),
                include_downlines = include_downlines,
                downline_names = downline_names,
            )
            pdf_bytes = pdf_buf.read()

        fname = f"Commission_{selected_exec.replace(' ','_')}_{date_from}_to_{date_to}.pdf"

        col_dl, col_pr = st.columns(2)

        with col_dl:
            st.download_button(
                label = "📥 Download PDF",
                data = pdf_bytes,
                file_name = fname,
                mime = "application/pdf",
                use_container_width = True,
            )

        with col_pr:
            # Embed PDF in iframe with print button
            import base64
            b64 = base64.b64encode(pdf_bytes).decode()
            st.markdown(f"""
            <a href="data:application/pdf;base64,{b64}" target="_blank"
               style="display:block; width:100%; background:linear-gradient(90deg,#059669,#10b981);
                      color:white; text-align:center; padding:12px; border-radius:8px;
                      font-weight:700; font-size:15px; text-decoration:none;
                      box-shadow:0 4px 12px rgba(5,150,105,0.4);">
                🖨️ Open & Print PDF
            </a>
            """, unsafe_allow_html=True)

        st.info("💡 'Download PDF' se save karo ya 'Open & Print PDF' se seedha print karo.")

