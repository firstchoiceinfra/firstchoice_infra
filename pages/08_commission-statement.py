import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(
    layout="wide",
    page_title="FC Infra - Commission Management"
)

# --------------------------------------------------
# Security
# --------------------------------------------------

if 'logged_in' not in st.session_state:
    st.warning("Please Login First")
    st.stop()

database.init_db()
db_data = st.session_state.db_projects

if "commission_ledger" not in db_data:
    db_data["commission_ledger"] = []

ledger = db_data["commission_ledger"]

st.title("💰 Commission Management System")

# --------------------------------------------------
# Commission Entry
# --------------------------------------------------

with st.expander("➕ Generate Commission Entry", expanded=True):

    executives = list(
        db_data.get("executives", {}).keys()
    )

    col1,col2,col3 = st.columns(3)

    executive = col1.selectbox(
        "Executive",
        executives
    )

    project = col2.text_input(
        "Project Name"
    )

    sale_amount = col3.number_input(
        "Sale Amount ₹",
        min_value=0.0
    )

    exec_info = db_data["executives"].get(
        executive,
        {}
    )

    direct_pct = exec_info.get(
        "percentage_exec",
        0.0
    )

    senior_name = exec_info.get(
        "senior_name",
        "Direct"
    )

    senior_pct = st.number_input(
        "Senior Commission %",
        min_value=0.0,
        value=10.0
    )

    group_pct = st.number_input(
        "Group Commission %",
        min_value=0.0,
        value=0.0
    )

    if st.button("Generate Commission"):

        direct_comm = (
            sale_amount * direct_pct / 100
        )

        difference_pct = max(
            senior_pct - direct_pct,
            0
        )

        difference_comm = (
            sale_amount *
            difference_pct / 100
        )

        group_comm = (
            sale_amount *
            group_pct / 100
        )

        total_comm = (
            direct_comm +
            difference_comm +
            group_comm
        )

        ledger.append({
            "Date":
            str(datetime.date.today()),

            "Executive":
            executive,

            "Senior":
            senior_name,

            "Project":
            project,

            "Sale":
            sale_amount,

            "Direct":
            direct_comm,

            "Difference":
            difference_comm,

            "Group":
            group_comm,

            "Total":
            total_comm,

            "Paid":
            0,

            "Pending":
            total_comm,

            "Status":
            "Pending"
        })

        database.save_db_data()

        st.success(
            "Commission Generated Successfully"
        )

# --------------------------------------------------
# Dashboard
# --------------------------------------------------

if ledger:

    df = pd.DataFrame(ledger)

    total_direct = df["Direct"].sum()
    total_diff = df["Difference"].sum()
    total_group = df["Group"].sum()
    total_pending = df["Pending"].sum()

    c1,c2,c3,c4 = st.columns(4)

    c1.metric(
        "Direct Commission",
        f"₹{total_direct:,.0f}"
    )

    c2.metric(
        "Difference Commission",
        f"₹{total_diff:,.0f}"
    )

    c3.metric(
        "Group Commission",
        f"₹{total_group:,.0f}"
    )

    c4.metric(
        "Pending",
        f"₹{total_pending:,.0f}"
    )

    st.divider()

# --------------------------------------------------
# Filters
# --------------------------------------------------

    executives = [
        "All"
    ] + list(df["Executive"].unique())

    selected_exec = st.selectbox(
        "Filter Executive",
        executives
    )

    if selected_exec != "All":
        df = df[
            df["Executive"] ==
            selected_exec
        ]

# --------------------------------------------------
# Commission Statement
# --------------------------------------------------

    st.subheader(
        "📋 Commission Statement"
    )

    st.dataframe(
        df,
        use_container_width=True
    )

# --------------------------------------------------
# Download Excel
# --------------------------------------------------

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "📥 Download Statement",
        csv,
        "commission_statement.csv",
        "text/csv"
    )

# --------------------------------------------------
# Print Button
# --------------------------------------------------

    st.markdown(
    """
    <script>
    function printPage() {
        window.print();
    }
    </script>

    <button onclick="printPage()"
    style="
    background:#1e3a8a;
    color:white;
    border:none;
    padding:10px 20px;
    border-radius:8px;
    cursor:pointer;">
    🖨️ Print Statement
    </button>
    """,
    unsafe_allow_html=True
    )

else:

    st.info(
        "No Commission Records Found"
    )
