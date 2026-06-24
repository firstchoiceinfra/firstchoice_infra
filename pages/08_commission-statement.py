import streamlit as st
import pandas as pd
import database
import datetime

# ======================================================
# PAGE CONFIG
# ======================================================
st.set_page_config(
    page_title="FC Infra - Commission Statement",
    layout="wide"
)

# ======================================================
# SECURITY CHECK
# ======================================================
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 Please Login First")
    st.stop()

# ======================================================
# DATABASE INIT
# ======================================================
database.init_db()
db_data = st.session_state.db_projects

# ======================================================
# THEME LOAD
# ======================================================
settings = db_data.get('_app_settings', {})

bg_url = settings.get(
    'bg_url',
    "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=2070&auto=format&fit=crop"
)

p_color = settings.get('primary_color', "#1e3a8a")
s_color = settings.get('secondary_color', "#3b82f6")

st.markdown(f"""
<style>

.stApp {{
background-image:url("{bg_url}");
background-size:cover;
background-attachment:fixed;
}}

.block-container {{
background:rgba(255,255,255,0.88);
backdrop-filter:blur(15px);
padding:2rem;
border-radius:20px;
}}

.main-title {{
text-align:center;
font-size:38px;
font-weight:900;
color:{p_color};
}}

.summary-box {{
background:white;
padding:15px;
border-radius:12px;
box-shadow:0 3px 10px rgba(0,0,0,.10);
margin-bottom:10px;
}}

</style>
""", unsafe_allow_html=True)

# ======================================================
# TITLE
# ======================================================
st.markdown(
    "<div class='main-title'>💰 Executive Commission Statement</div>",
    unsafe_allow_html=True
)

st.write("")

# ======================================================
# EXECUTIVE DATA
# ======================================================
executives = db_data.get("executives", {})

if not executives:
    st.error("No Executive Found")
    st.stop()

# ======================================================
# GET DOWNLINES
# ======================================================
def get_downlines(manager_name):

    result = []

    for ex_name, ex_data in executives.items():

        senior = str(
            ex_data.get("senior_name", "")
        ).strip().lower()

        if senior == str(manager_name).strip().lower():

            result.append(ex_name)

            child = get_downlines(ex_name)

            if child:
                result.extend(child)

    return list(set(result))

# ======================================================
# FILTER SECTION
# ======================================================
st.markdown("### 🔎 Statement Filters")

c1, c2, c3, c4 = st.columns(4)

executive_names = sorted(list(executives.keys()))

selected_exec = c1.selectbox(
    "Executive",
    executive_names
)

start_date = c2.date_input(
    "Start Date",
    datetime.date.today().replace(day=1)
)

end_date = c3.date_input(
    "End Date",
    datetime.date.today()
)

statement_type = c4.selectbox(
    "Statement Type",
    [
        "Self",
        "Group",
        "All"
    ]
)

generate = st.button(
    "🚀 Generate Statement",
    use_container_width=True
)

# ======================================================
# DATA COLLECTION
# ======================================================
if generate:

    rows = []

    sr = 1

    downlines = get_downlines(selected_exec)

    for project_name, project_data in db_data.items():

        if not isinstance(project_data, dict):
            continue

        plots = project_data.get("plots", {})

        if not isinstance(plots, dict):
            continue

        mauza = project_data.get(
            "mauza",
            ""
        )

        for plot_no, plot_data in plots.items():

            if plot_data.get("status") != "Booked":
                continue

            booking_exec = str(
                plot_data.get(
                    "executive_name",
                    ""
                )
            ).strip()

            # =====================================
            # FILTER LOGIC
            # =====================================
            include = False

            if statement_type == "Self":

                if booking_exec == selected_exec:
                    include = True

            elif statement_type == "Group":

                if booking_exec in downlines:
                    include = True

            elif statement_type == "All":

                if (
                    booking_exec == selected_exec
                    or booking_exec in downlines
                ):
                    include = True

            if not include:
                continue

            booking_date = plot_data.get(
                "booking_date",
                ""
            )

            try:

                booking_dt = datetime.datetime.strptime(
                    booking_date,
                    "%Y-%m-%d"
                ).date()

            except:

                booking_dt = None

            if booking_dt:

                if booking_dt < start_date:
                    continue

                if booking_dt > end_date:
                    continue

            # =====================================
            # COLLECTION
            # =====================================
            token_amount = float(
                plot_data.get(
                    "token_amount",
                    0
                )
            )

            emi_total = 0

            partial_payments = plot_data.get(
                "partial_payments",
                []
            )

            for pmt in partial_payments:

                try:
                    emi_total += float(
                        pmt.get(
                            "amount",
                            0
                        )
                    )
                except:
                    pass

            total_collection = (
                token_amount +
                emi_total
            )

            customer_name = plot_data.get(
                "customer_name",
                ""
            )

            rows.append({

                "sr": sr,

                "project_name": project_name,

                "customer_name": customer_name,

                "mauza": mauza,

                "plot_no": plot_no,

                "booking_date": booking_date,

                "executive_name": booking_exec,

                "collection": total_collection

            })

            sr += 1

    if len(rows) == 0:

        st.warning(
            "No Records Found"
        )

        st.stop()

    commission_df = pd.DataFrame(rows)

    st.session_state["commission_df"] = commission_df

    st.success(
        f"{len(rows)} Records Found"
    )

    st.dataframe(
        commission_df,
        use_container_width=True
    )
    # ======================================================
# PART 2
# COMMISSION CALCULATION ENGINE
# ======================================================

if "commission_df" in st.session_state:

    commission_df = st.session_state["commission_df"]

    # ==========================================
    # EXECUTIVE LOOKUP FUNCTIONS
    # ==========================================
    def get_exec_percent(exec_name):

        try:
            return float(
                executives
                .get(exec_name, {})
                .get("percentage_exec", 0)
            )
        except:
            return 0.0


    def get_senior(exec_name):

        return (
            executives
            .get(exec_name, {})
            .get("senior_name", "")
        )


    # ==========================================
    # BUILD COMMISSION DATA
    # ==========================================
    final_rows = []

    total_collection = 0
    total_direct = 0
    total_difference = 0
    total_gross = 0
    total_tds = 0
    total_final = 0

    for _, row in commission_df.iterrows():

        customer_name = row["customer_name"]
        plot_no = row["plot_no"]
        mauza = row["mauza"]

        booking_exec = row["executive_name"]

        collection = float(
            row["collection"]
        )

        booking_date = row["booking_date"]

        # ======================================
        # DIRECT EXECUTIVE
        # ======================================
        direct_pct = get_exec_percent(
            booking_exec
        )

        direct_commission = (
            collection *
            direct_pct /
            100
        )

        # ======================================
        # DIFFERENCE COMMISSION
        # ======================================
        senior_name = get_senior(
            booking_exec
        )

        senior_pct = 0
        diff_pct = 0
        diff_commission = 0

        if (
            senior_name
            and
            senior_name in executives
        ):

            senior_pct = get_exec_percent(
                senior_name
            )

            diff_pct = max(
                0,
                senior_pct -
                direct_pct
            )

            diff_commission = (
                collection *
                diff_pct /
                100
            )

        # ======================================
        # TOTAL
        # ======================================
        gross_commission = (
            direct_commission +
            diff_commission
        )

        tds = (
            gross_commission *
            0.02
        )

        final_payable = (
            gross_commission -
            tds
        )

        # ======================================
        # GRAND TOTALS
        # ======================================
        total_collection += collection
        total_direct += direct_commission
        total_difference += diff_commission
        total_gross += gross_commission
        total_tds += tds
        total_final += final_payable

        final_rows.append({

            "Sr No":
            len(final_rows)+1,

            "Customer Name":
            customer_name,

            "Mauza":
            mauza,

            "Plot No":
            plot_no,

            "Booking Date":
            booking_date,

            "Collection":
            round(collection,2),

            "Executive":
            booking_exec,

            "Direct %":
            direct_pct,

            "Direct Commission":
            round(direct_commission,2),

            "Senior":
            senior_name,

            "Senior %":
            senior_pct,

            "Difference %":
            diff_pct,

            "Difference Commission":
            round(diff_commission,2),

            "Gross Commission":
            round(gross_commission,2),

            "TDS 2%":
            round(tds,2),

            "Final Payable":
            round(final_payable,2)

        })

    # ==========================================
    # FINAL DATAFRAME
    # ==========================================
    final_df = pd.DataFrame(
        final_rows
    )

    st.session_state[
        "commission_final_df"
    ] = final_df

    # ==========================================
    # SUMMARY
    # ==========================================
    st.markdown("## 📊 Commission Summary")

    s1,s2,s3,s4,s5,s6 = st.columns(6)

    s1.metric(
        "Collection",
        f"₹ {total_collection:,.0f}"
    )

    s2.metric(
        "Direct",
        f"₹ {total_direct:,.0f}"
    )

    s3.metric(
        "Difference",
        f"₹ {total_difference:,.0f}"
    )

    s4.metric(
        "Gross",
        f"₹ {total_gross:,.0f}"
    )

    s5.metric(
        "TDS",
        f"₹ {total_tds:,.0f}"
    )

    s6.metric(
        "Final Payable",
        f"₹ {total_final:,.0f}"
    )

    st.write("")

    st.markdown("## 📋 Statement Preview")

    st.dataframe(
        final_df,
        use_container_width=True,
        hide_index=True
    )

    # ==========================================
    # SAVE TOTALS
    # ==========================================
    st.session_state["total_collection"] = total_collection
    st.session_state["total_direct"] = total_direct
    st.session_state["total_difference"] = total_difference
    st.session_state["total_gross"] = total_gross
    st.session_state["total_tds"] = total_tds
    st.session_state["total_final"] = total_final
    # ======================================================
# PART 3
# A4 PRINTABLE COMMISSION STATEMENT
# ======================================================

if "commission_final_df" in st.session_state:

    final_df = st.session_state["commission_final_df"]

    total_collection = st.session_state.get("total_collection",0)
    total_direct = st.session_state.get("total_direct",0)
    total_difference = st.session_state.get("total_difference",0)
    total_gross = st.session_state.get("total_gross",0)
    total_tds = st.session_state.get("total_tds",0)
    total_final = st.session_state.get("total_final",0)

    st.markdown("---")
    st.markdown("## 🖨️ Print Ready Statement")

    html_table = final_df.to_html(
        index=False,
        classes="statement-table"
    )

    html_report = f"""
    <html>

    <head>

    <style>

    @page {{
        size:A4 portrait;
        margin:10mm;
    }}

    body {{
        font-family:Arial;
        padding:10px;
    }}

    .header {{
        text-align:center;
        margin-bottom:20px;
    }}

    .company {{
        font-size:28px;
        font-weight:bold;
        color:#1e3a8a;
    }}

    .title {{
        font-size:18px;
        margin-top:5px;
        font-weight:bold;
    }}

    .info {{
        margin-top:15px;
        margin-bottom:15px;
        font-size:14px;
    }}

    table {{
        width:100%;
        border-collapse:collapse;
        font-size:11px;
    }}

    th {{
        background:#1e3a8a;
        color:white;
        border:1px solid #000;
        padding:5px;
    }}

    td {{
        border:1px solid #000;
        padding:4px;
        text-align:center;
    }}

    .totals {{
        margin-top:20px;
        width:350px;
        float:right;
    }}

    .totals table {{
        font-size:13px;
    }}

    .totals td {{
        text-align:right;
        padding:6px;
    }}

    </style>

    </head>

    <body>

    <div class="header">

        <div class="company">
            FIRSTCHOICE INFRA
        </div>

        <div class="title">
            EXECUTIVE COMMISSION STATEMENT
        </div>

    </div>

    <div class="info">

        <b>Executive :</b>
        {selected_exec}

        <br>

        <b>Statement Type :</b>
        {statement_type}

        <br>

        <b>Period :</b>
        {start_date} To {end_date}

    </div>

    {html_table}

    <div class="totals">

    <table>

        <tr>
            <td><b>Total Collection</b></td>
            <td>₹ {total_collection:,.2f}</td>
        </tr>

        <tr>
            <td><b>Total Direct Commission</b></td>
            <td>₹ {total_direct:,.2f}</td>
        </tr>

        <tr>
            <td><b>Total Difference Commission</b></td>
            <td>₹ {total_difference:,.2f}</td>
        </tr>

        <tr>
            <td><b>Gross Commission</b></td>
            <td>₹ {total_gross:,.2f}</td>
        </tr>

        <tr>
            <td><b>TDS 2%</b></td>
            <td>₹ {total_tds:,.2f}</td>
        </tr>

        <tr>
            <td><b>Final Payable</b></td>
            <td><b>₹ {total_final:,.2f}</b></td>
        </tr>

    </table>

    </div>

    </body>
    </html>
    """

    st.components.v1.html(
        html_report,
        height=900,
        scrolling=True
    )

    st.markdown("### 🖨️ Print Statement")

    st.components.v1.html(
        f"""
        <button
        onclick="window.print()"
        style="
        background:#1e3a8a;
        color:white;
        padding:12px 25px;
        border:none;
        border-radius:8px;
        font-size:16px;
        font-weight:bold;
        cursor:pointer;">
        🖨️ Print Commission Statement
        </button>
        """,
        height=70
    )

    st.success(
        f"Statement Generated Successfully for {selected_exec}"
)
