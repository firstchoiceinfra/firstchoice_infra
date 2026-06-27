import streamlit as st
import pandas as pd
import database
import datetime
import io

# ReportLab PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
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
c_bg = "rgba(255, 255, 255, 0.92)"

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
h1, h2, h3, h4 {{
    color: {p_color} !important;
    font-weight: 900;
}}
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
.comm-summary-box {{
    background: linear-gradient(135deg, #e0f2fe 0%, #bfdbfe 100%);
    border-left: 6px solid {p_color};
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
}}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# 3. HEADING
# ---------------------------------------------------------------
st.markdown(
    f"<h1 style='text-align:center;'>💼 FC Infra — Commission Statement Generator</h1>",
    unsafe_allow_html=True
)
st.markdown(
    "<p style='text-align:center; color:#475569; font-size:16px;'>"
    "Select an executive and generate a professional PDF commission statement.</p>",
    unsafe_allow_html=True
)
st.divider()

# ---------------------------------------------------------------
# 4. HELPER FUNCTIONS
# ---------------------------------------------------------------
def safe_float(val, default=0.0):
    try:
        if val is None or str(val).strip() == "":
            return float(default)
        return float(val)
    except:
        return float(default)


def get_all_downlines(manager_name):
    """Recursively get all downline executive names under a manager."""
    manager_clean = str(manager_name).strip().lower()
    downlines = []
    for ex_name, details in exec_data_root.items():
        if str(details.get('senior_name', '')).strip().lower() == manager_clean:
            downlines.append(ex_name)
            downlines.extend(get_all_downlines(ex_name))
    return list(set(downlines))


def get_commission_for_exec(exec_name):
    """Return (percentage, fixed_rupees) for an executive from Partner Portal data."""
    for key, val in exec_data_root.items():
        if str(key).strip().lower() == str(exec_name).strip().lower():
            pct = safe_float(val.get('percentage_exec', 0.0))
            rs = safe_float(val.get('rupees_exec', 0.0))
            return pct, rs
    return 0.0, 0.0


def calculate_commission(total_deal_value, pct, rs_fixed):
    """
    If percentage is set → use percentage.
    If only fixed rupees → use fixed.
    If both → add both.
    """
    comm = 0.0
    if pct > 0:
        comm += (pct / 100.0) * total_deal_value
    if rs_fixed > 0:
        comm += rs_fixed
    return comm


def get_bookings_for_exec(exec_name):
    """Return list of booking dicts for a given executive name."""
    records = []
    project_names = [
        name for name, data in db_data.items()
        if isinstance(data, dict) and ('plots' in data or 'total_plots' in data)
    ]
    for p_name in project_names:
        p_info = db_data[p_name]
        p_plots = p_info.get('plots', {})
        if isinstance(p_plots, list):
            p_plots = {str(i): p for i, p in enumerate(p_plots) if p is not None}

        for plot_id, plot_info in p_plots.items():
            if not isinstance(plot_info, dict):
                continue
            status = str(plot_info.get('status', '')).strip().lower()
            plot_exec = str(plot_info.get('executive_name', '')).strip().lower()

            # Only primary bookings for this executive
            if status != 'booked':
                continue
            if plot_info.get('is_primary', True) is False:
                continue
            if plot_exec != str(exec_name).strip().lower():
                continue

            # Calculate deal value
            plot_area = safe_float(plot_info.get('plot_area', 0.0))
            sell_rate = safe_float(plot_info.get('selling_rate', 0.0))
            rate_sqft = safe_float(plot_info.get('rate_per_sqft', 0.0))

            if sell_rate > 100000:
                total_deal = sell_rate
                r_sqft = rate_sqft if rate_sqft > 0 else 0.0
            else:
                total_deal = plot_area * sell_rate
                r_sqft = sell_rate

            if total_deal <= 0:
                continue

            # Payments
            token_amt = safe_float(plot_info.get('token_amount', 0.0))
            partial_pmts = plot_info.get('partial_payments', [])
            total_emi_paid = sum(safe_float(p.get('amount', 0.0)) for p in partial_pmts)
            total_paid = token_amt + total_emi_paid
            net_pending = max(0.0, total_deal - total_paid)

            # Commission
            pct, rs_fixed = get_commission_for_exec(exec_name)
            commission_amt = calculate_commission(total_deal, pct, rs_fixed)
            comm_label = f"{pct}%" if pct > 0 and rs_fixed == 0 else (
                             f"Rs {rs_fixed:,.0f}" if rs_fixed > 0 and pct == 0 else
                             f"{pct}% + Rs {rs_fixed:,.0f}")

            records.append({
                "Project" : p_name,
                "Plot(s)" : f"P-{plot_info.get('booked_plots_str', plot_id)}",
                "Customer Name" : str(plot_info.get('customer_name', 'N/A')).title(),
                "Booking Date" : plot_info.get('booking_date', 'N/A'),
                "Plot Area (Sq.Ft)": plot_area,
                "Rate (Rs/Sq.Ft)" : r_sqft,
                "Total Deal Value" : total_deal,
                "Total Paid" : total_paid,
                "Net Pending" : net_pending,
                "Comm Slab" : comm_label,
                "Commission (Rs)" : commission_amt,
            })
    return records


# ---------------------------------------------------------------
# 5. PDF GENERATOR
# ---------------------------------------------------------------
def generate_commission_pdf(exec_name, records, date_from, date_to):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm
    )

    styles = getSampleStyleSheet()
    PRIMARY = colors.HexColor("#1e3a8a")
    ACCENT = colors.HexColor("#3b82f6")
    LIGHT = colors.HexColor("#e0f2fe")
    DARK = colors.HexColor("#0f172a")

    # Custom styles
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=22, textColor=PRIMARY,
        spaceAfter=4, alignment=TA_CENTER, fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'Sub', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor("#475569"),
        spaceAfter=2, alignment=TA_CENTER
    )
    heading2 = ParagraphStyle(
        'H2', parent=styles['Heading2'],
        fontSize=13, textColor=PRIMARY,
        spaceBefore=12, spaceAfter=4, fontName='Helvetica-Bold'
    )
    normal = ParagraphStyle(
        'N', parent=styles['Normal'],
        fontSize=9, textColor=DARK, leading=14
    )
    bold_center = ParagraphStyle(
        'BC', parent=styles['Normal'],
        fontSize=9, fontName='Helvetica-Bold',
        alignment=TA_CENTER, textColor=DARK
    )

    story = []

    # ── HEADER ──────────────────────────────────────────────────
    story.append(Paragraph("🏗 FC Infra — FirstChoice Infrastructure", title_style))
    story.append(Paragraph("Premium Real Estate | Plot Development & Sales", sub_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceAfter=6))
    story.append(Paragraph("<b>COMMISSION STATEMENT</b>", ParagraphStyle(
        'CS', fontSize=15, textColor=ACCENT, alignment=TA_CENTER,
        fontName='Helvetica-Bold', spaceAfter=4
    )))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=10))

    # ── EXECUTIVE INFO ───────────────────────────────────────────
    pct, rs_fixed = get_commission_for_exec(exec_name)
    ex_details = exec_data_root.get(exec_name, {})
    senior_name = ex_details.get('senior_name', 'N/A')
    mobile = ex_details.get('mobile', 'N/A')

    info_data = [
        ["Executive Name:", exec_name, "Senior / Upline:", senior_name],
        ["Mobile:", mobile, "Commission Slab:",
         f"{pct}% + Rs {rs_fixed:,.0f}" if pct > 0 and rs_fixed > 0
         else (f"{pct}%" if pct > 0 else f"Rs {rs_fixed:,.0f}")],
        ["Statement Period:", f"{date_from} to {date_to}",
         "Generated On:", str(datetime.date.today())],
    ]
    info_table = Table(info_data, colWidths=[38*mm, 52*mm, 38*mm, 52*mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('TEXTCOLOR', (0,0), (0,-1), PRIMARY),
        ('TEXTCOLOR', (2,0), (2,-1), PRIMARY),
        ('BACKGROUND',(0,0), (-1,-1), LIGHT),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [LIGHT, colors.white]),
        ('BOX', (0,0), (-1,-1), 0.5, PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING',(0,0), (-1,-1), 5),
        ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ('LEFTPADDING',(0,0), (-1,-1), 6),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ── BOOKING TABLE ─────────────────────────────────────────────
    story.append(Paragraph("Booking & Commission Details", heading2))

    col_headers = [
        "Project", "Plot(s)", "Customer", "Date",
        "Area\n(Sq.Ft)", "Deal Value\n(Rs)", "Paid\n(Rs)", "Pending\n(Rs)",
        "Slab", "Commission\n(Rs)"
    ]
    col_widths = [28*mm, 18*mm, 30*mm, 18*mm, 15*mm, 22*mm, 20*mm, 20*mm, 16*mm, 23*mm]

    table_data = [col_headers]
    total_commission = 0.0
    total_deal_sum = 0.0
    total_paid_sum = 0.0

    for r in records:
        table_data.append([
            r["Project"],
            r["Plot(s)"],
            r["Customer Name"],
            str(r["Booking Date"]),
            f"{r['Plot Area (Sq.Ft)']:,.0f}",
            f"Rs {r['Total Deal Value']:,.0f}",
            f"Rs {r['Total Paid']:,.0f}",
            f"Rs {r['Net Pending']:,.0f}",
            r["Comm Slab"],
            f"Rs {r['Commission (Rs)']:,.0f}",
        ])
        total_commission += r["Commission (Rs)"]
        total_deal_sum += r["Total Deal Value"]
        total_paid_sum += r["Total Paid"]

    # Totals row
    table_data.append([
        "TOTAL", f"{len(records)} Plots", "", "",
        "",
        f"Rs {total_deal_sum:,.0f}",
        f"Rs {total_paid_sum:,.0f}",
        f"Rs {(total_deal_sum - total_paid_sum):,.0f}",
        "",
        f"Rs {total_commission:,.0f}",
    ])

    booking_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    booking_table.setStyle(TableStyle([
        # Header row
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('ALIGN', (0,0), (-1,0), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        # Body rows
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTSIZE', (0,1), (-1,-2), 8),
        ('ROWBACKGROUNDS',(0,1),(-1,-2), [colors.white, colors.HexColor("#f1f5f9")]),
        # Totals row
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#1e3a8a")),
        ('TEXTCOLOR', (0,-1), (-1,-1), colors.white),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,-1), (-1,-1), 8),
        # Commission column highlight
        ('BACKGROUND', (-1,1), (-1,-2), colors.HexColor("#fef3c7")),
        ('TEXTCOLOR', (-1,1), (-1,-2), colors.HexColor("#b45309")),
        ('FONTNAME', (-1,1), (-1,-2), 'Helvetica-Bold'),
        # Grid
        ('BOX', (0,0), (-1,-1), 0.8, PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.3, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(booking_table)
    story.append(Spacer(1, 12))

    # ── SUMMARY BOX ──────────────────────────────────────────────
    story.append(Paragraph("Commission Summary", heading2))
    summary_data = [
        ["Total Bookings", "Total Deal Value", "Total Amount Collected", "Total Pending", "NET COMMISSION EARNED"],
        [
            str(len(records)),
            f"Rs {total_deal_sum:,.2f}",
            f"Rs {total_paid_sum:,.2f}",
            f"Rs {(total_deal_sum - total_paid_sum):,.2f}",
            f"Rs {total_commission:,.2f}",
        ]
    ]
    summary_table = Table(summary_data, colWidths=[30*mm, 38*mm, 42*mm, 35*mm, 45*mm])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BACKGROUND', (0,1), (-2,1), LIGHT),
        ('BACKGROUND', (-1,1),(-1,1), colors.HexColor("#d1fae5")),
        ('TEXTCOLOR', (-1,1),(-1,1), colors.HexColor("#065f46")),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (-1,1), 10),
        ('BOX', (0,0), (-1,-1), 1, PRIMARY),
        ('INNERGRID', (0,0), (-1,-1), 0.4, colors.HexColor("#93c5fd")),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING',(0,0), (-1,-1), 7),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # ── FOOTER ───────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=6))
    story.append(Paragraph(
        "This is a computer-generated commission statement by FC Infra — FirstChoice Infrastructure. "
        "For queries, contact the Admin Desk.",
        ParagraphStyle('Footer', fontSize=8, textColor=colors.HexColor("#94a3b8"),
                       alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ---------------------------------------------------------------
# 6. STREAMLIT UI
# ---------------------------------------------------------------

# ── Select Executive ──────────────────────────────────────────
st.markdown("### 👤 Step 1 — Select Executive")

exec_names_all = sorted([
    name for name, det in exec_data_root.items()
    if isinstance(det, dict)
])

if user_role == 'admin':
    exec_options = exec_names_all
else:
    exec_options = [curr_user]

if not exec_options:
    st.warning("No executives found. Please add partners via the Partner Portal first.")
    st.stop()

selected_exec = st.selectbox("Select Executive / Partner:", exec_options)

# Include downlines toggle
include_downlines = st.checkbox(
    "📥 Include downline executives' bookings in this statement",
    value=False
)

# ── Date Filter ───────────────────────────────────────────────
st.markdown("### 📅 Step 2 — Select Statement Period")
col_d1, col_d2 = st.columns(2)
date_from = col_d1.date_input("From Date:", datetime.date(datetime.date.today().year, 1, 1))
date_to = col_d2.date_input("To Date:", datetime.date.today())

st.divider()

# ── Generate Button ───────────────────────────────────────────
st.markdown("### 🖨️ Step 3 — Generate Statement")

if st.button("🖨️ Generate Commission Statement PDF", use_container_width=True, type="primary"):

    # Collect all executives to include
    execs_to_include = [selected_exec]
    if include_downlines:
        downlines = get_all_downlines(selected_exec)
        execs_to_include.extend(downlines)
    execs_to_include = list(set(execs_to_include))

    # Collect all records
    all_records = []
    for ex in execs_to_include:
        recs = get_bookings_for_exec(ex)
        # Date filter
        filtered = []
        for r in recs:
            try:
                b_date = datetime.date.fromisoformat(str(r["Booking Date"]))
                if date_from <= b_date <= date_to:
                    filtered.append(r)
            except:
                filtered.append(r) # include if date parse fails
        all_records.extend(filtered)

    if not all_records:
        st.warning("⚠️ No bookings found for the selected executive and period.")
    else:
        # ── Preview Table ─────────────────────────────────────
        st.success(f"✅ Found **{len(all_records)}** booking(s) for the selected period.")

        df_preview = pd.DataFrame(all_records)
        df_show = df_preview[[
            "Project", "Plot(s)", "Customer Name", "Booking Date",
            "Total Deal Value", "Total Paid", "Net Pending", "Comm Slab", "Commission (Rs)"
        ]].copy()

        for col in ["Total Deal Value", "Total Paid", "Net Pending", "Commission (Rs)"]:
            df_show[col] = df_show[col].apply(lambda x: f"Rs {x:,.2f}")

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # Summary
        total_comm = sum(r["Commission (Rs)"] for r in all_records)
        total_deal = sum(r["Total Deal Value"] for r in all_records)

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Bookings", len(all_records))
        c2.metric("Total Deal Value", f"Rs {total_deal:,.2f}")
        c3.metric("💰 Net Commission", f"Rs {total_comm:,.2f}")

        st.divider()

        # ── PDF Generation & Download ─────────────────────────
        label = selected_exec
        if include_downlines:
            label += " + Downlines"

        with st.spinner("Generating PDF..."):
            pdf_buffer = generate_commission_pdf(
                exec_name = selected_exec,
                records = all_records,
                date_from = str(date_from),
                date_to = str(date_to)
            )

        fname = f"Commission_{selected_exec.replace(' ','_')}_{date_from}_to_{date_to}.pdf"
        st.download_button(
            label = "📥 Download Commission Statement (PDF)",
            data = pdf_buffer,
            file_name = fname,
            mime = "application/pdf",
            use_container_width = True
        )
        st.info("💡 Click the button above to download and print your PDF statement.")

