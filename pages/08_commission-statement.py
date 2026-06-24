import streamlit as st
import pandas as pd
import datetime
import database

st.set_page_config(
    page_title="Commission Statement",
    layout="wide"
)

# -------------------------------------------------
# LOGIN CHECK
# -------------------------------------------------

if 'logged_in' not in st.session_state:
    st.warning("Please Login First")
    st.stop()

database.init_db()

db_data = st.session_state.db_projects
executives = db_data.get("executives", {})

# -------------------------------------------------
# DOWNLINE FINDER
# -------------------------------------------------

def get_all_downlines(manager_name):
    downlines = []

    for ex_name, details in executives.items():

        senior = str(
            details.get("senior_name", "")
        ).strip().lower()

        if senior == manager_name.strip().lower():
            downlines.append(ex_name)
            downlines.extend(
                get_all_downlines(ex_name)
            )

    return list(set(downlines))

# -------------------------------------------------
# PAGE HEADER
# -------------------------------------------------

st.title("💰 Commission Statement Generator")

executive_names = sorted(
    list(executives.keys())
)

if not executive_names:
    st.error("No Executives Found")
    st.stop()

col1,col2,col3,col4 = st.columns(4)

selected_exec = col1.selectbox(
    "Executive",
    executive_names
)

comm_type = col2.selectbox(
    "Commission Type",
    ["Self","Group","All"]
)

start_date = col3.date_input(
    "Start Date",
    datetime.date.today().replace(day=1)
)

end_date = col4.date_input(
    "End Date",
    datetime.date.today()
)

generate = st.button(
    "📊 Generate Statement",
    use_container_width=True
)

# -------------------------------------------------
# GENERATE
# -------------------------------------------------

if generate:

    rows = []

    self_exec = selected_exec

    group_execs = get_all_downlines(
        selected_exec
    )

    all_execs = [self_exec] + group_execs

    project_names = [
        name
        for name,data in db_data.items()
        if isinstance(data,dict)
        and ("plots" in data)
    ]

    total_commission = 0

    for project in project_names:

        plots = db_data[project].get(
            "plots",
            {}
        )

        if isinstance(plots,list):
            plots = {
                str(i):p
                for i,p in enumerate(plots)
                if p
            }

        for plot_no,plot in plots.items():

            if not isinstance(plot,dict):
                continue

            if str(
                plot.get("status","")
            ).lower() != "booked":
                continue

            exec_name = str(
                plot.get(
                    "executive_name",
                    ""
                )
            ).strip()

            include = False

            if comm_type == "Self":
                include = (
                    exec_name.lower()
                    ==
                    self_exec.lower()
                )

            elif comm_type == "Group":
                include = (
                    exec_name in group_execs
                )

            elif comm_type == "All":
                include = (
                    exec_name in all_execs
                )

            if not include:
                continue

            booking_date = str(
                plot.get(
                    "booking_date",
                    ""
                )
            )

            try:
                booking_dt = datetime.datetime.strptime(
                    booking_date,
                    "%Y-%m-%d"
                ).date()
            except:
                continue

            if not (
                start_date
                <=
                booking_dt
                <=
                end_date
            ):
                continue

            sale_value = float(
                plot.get(
                    "selling_rate",
                    0
                )
            )

            exec_info = executives.get(
                exec_name,
                {}
            )

            pct = float(
                exec_info.get(
                    "percentage_exec",
                    0
                )
            )

            commission = (
                sale_value * pct / 100
            )

            total_commission += commission

            rows.append({
                "Date":
                booking_dt.strftime(
                    "%d-%m-%Y"
                ),

                "Customer":
                plot.get(
                    "customer_name",
                    ""
                ),

                "Project":
                project,

                "Plot":
                plot_no,

                "Executive":
                exec_name,

                "Sale Value":
                sale_value,

                "Comm %":
                pct,

                "Commission":
                commission
            })

    if rows:

        df = pd.DataFrame(rows)

        st.success(
            f"{len(df)} Records Found"
        )

        st.metric(
            "Total Commission",
            f"₹ {total_commission:,.2f}"
        )

        st.dataframe(
            df,
            use_container_width=True
        )

        csv = df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "📥 Download Excel",
            csv,
            "Commission_Statement.csv",
            "text/csv"
        )

        table_html = df.to_html(
            index=False
        )

        html_statement = f"""
        <div id="printArea"
        style="
        width:210mm;
        min-height:297mm;
        background:white;
        color:black;
        padding:15mm;
        margin:auto;">

        <h2 style="text-align:center;">
        FIRSTCHOICE INFRA
        </h2>

        <h3 style="text-align:center;">
        COMMISSION STATEMENT
        </h3>

        <hr>

        <p>
        <b>Executive :</b>
        {selected_exec}<br>

        <b>Commission Type :</b>
        {comm_type}<br>

        <b>Period :</b>
        {start_date}
        To
        {end_date}
        </p>

        {table_html}

        <hr>

        <h2>
        Total Commission :
        ₹ {total_commission:,.2f}
        </h2>

        </div>
        """

        st.markdown(
            html_statement,
            unsafe_allow_html=True
        )

        st.markdown(
        """
        <script>
        function printPage(){
            window.print();
        }
        </script>

        <button onclick="printPage()"
        style="
        background:#1e3a8a;
        color:white;
        padding:12px 25px;
        border:none;
        border-radius:8px;
        font-size:16px;
        cursor:pointer;">
        🖨️ Print Statement
        </button>
        """,
        unsafe_allow_html=True
        )

    else:

        st.warning(
            "No Commission Records Found"
        )
