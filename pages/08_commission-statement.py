import streamlit as st
import pandas as pd
import database
import datetime

# ==================================================
# PAGE CONFIG
# ==================================================
st.set_page_config(
    page_title="FC Infra - Commission Statement",
    layout="wide"
)

# ==================================================
# LOGIN CHECK
# ==================================================
if 'logged_in' not in st.session_state:
    st.warning("Please Login First")
    st.stop()

# ==================================================
# DATABASE
# ==================================================
database.init_db()
db_data = st.session_state.db_projects

# ==================================================
# EXECUTIVES
# ==================================================
executives = db_data.get("executives", {})

if not executives:
    st.error("No Executive Found")
    st.stop()

# ==================================================
# TITLE
# ==================================================
st.title("💰 Executive Commission Statement")

# ==================================================
# HIERARCHY ENGINE
# ==================================================
def get_downlines(manager_name):

    result = []

    for ex_name, ex_data in executives.items():

        senior = str(
            ex_data.get(
                "senior_name",
                ""
            )
        ).strip().lower()

        if senior == str(manager_name).strip().lower():

            result.append(ex_name)

            child = get_downlines(ex_name)

            if child:
                result.extend(child)

    return list(set(result))

# ==================================================
# FILTERS
# ==================================================
c1, c2, c3, c4 = st.columns(4)

selected_exec = c1.selectbox(
    "Executive",
    sorted(list(executives.keys()))
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

# ==================================================
# TEST DATA
# ==================================================
if generate:

    st.success("Commission Engine Started")

    st.write("Executive:", selected_exec)

    st.write(
        "Downlines:",
        get_downlines(selected_exec)
    )

    st.write(
        "Projects Found:"
    )

    for key in db_data.keys():

        st.write(key)
        # ==================================================
# COLLECTION EXTRACTION ENGINE
# ==================================================

if generate:

    rows = []

    sr = 1

    downlines = get_downlines(selected_exec)

    def safe_float(val):
        try:
            return float(val)
        except:
            return 0.0

    for project_name, project_data in db_data.items():

        if not isinstance(project_data, dict):
            continue

        if "plots" not in project_data:
            continue

        plots = project_data.get("plots", {})

        # LIST TO DICT FIX
        if isinstance(plots, list):

            plots = {
                str(i): p
                for i, p in enumerate(plots)
                if p is not None
            }

        if not isinstance(plots, dict):
            continue

        mauza = project_data.get(
            "mauza",
            "N/A"
        )

        for plot_no, plot_data in plots.items():

            if not isinstance(plot_data, dict):
                continue

            if plot_data.get("status") != "Booked":
                continue

            booking_exec = str(
                plot_data.get(
                    "executive_name",
                    ""
                )
            ).strip()

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

            customer_name = plot_data.get(
                "customer_name",
                ""
            )

            # ===================================
            # TOKEN COLLECTION
            # ===================================

            token_amount = safe_float(
                plot_data.get(
                    "token_amount",
                    0
                )
            )

            token_date = plot_data.get(
                "receipt_date",
                plot_data.get(
                    "booking_date",
                    ""
                )
            )

            try:

                token_dt = datetime.datetime.strptime(
                    token_date,
                    "%Y-%m-%d"
                ).date()

                if (
                    token_dt >= start_date
                    and token_dt <= end_date
                    and token_amount > 0
                ):

                    rows.append({

                        "Sr": sr,
                        "Customer": customer_name,
                        "Mauza": mauza,
                        "Plot": plot_no,
                        "Date": token_date,
                        "Collection Type": "Token",
                        "Slip No": plot_data.get(
                            "token_slip_no",
                            ""
                        ),
                        "Collection": token_amount,
                        "Executive": booking_exec

                    })

                    sr += 1

            except:
                pass

            # ===================================
            # EMI COLLECTIONS
            # ===================================

            partial_payments = plot_data.get(
                "partial_payments",
                []
            )

            for emi in partial_payments:

                emi_amount = safe_float(
                    emi.get(
                        "amount",
                        0
                    )
                )

                emi_date = emi.get(
                    "date",
                    ""
                )

                try:

                    emi_dt = datetime.datetime.strptime(
                        emi_date,
                        "%Y-%m-%d"
                    ).date()

                    if (
                        emi_dt >= start_date
                        and emi_dt <= end_date
                        and emi_amount > 0
                    ):

                        rows.append({

                            "Sr": sr,
                            "Customer": customer_name,
                            "Mauza": mauza,
                            "Plot": plot_no,
                            "Date": emi_date,
                            "Collection Type": "EMI",
                            "Slip No": emi.get(
                                "slip_no",
                                ""
                            ),
                            "Collection": emi_amount,
                            "Executive": booking_exec

                        })

                        sr += 1

                except:
                    pass

    commission_df = pd.DataFrame(rows)

    if commission_df.empty:

        st.warning(
            "No Collection Found"
        )

    else:

        st.success(
            f"{len(commission_df)} Collection Records Found"
        )

        st.dataframe(
            commission_df,
            use_container_width=True
        )

        st.session_state[
            "commission_df"
        ] = commission_df
        # =========================================
# COMMISSION FUNCTIONS
# =========================================

def get_exec_percent(exec_name):

    try:

        return float(
            executives.get(
                exec_name,
                {}
            ).get(
                "percentage_exec",
                0
            )
        )

    except:

        return 0.0


def get_senior_percent(exec_name):

    try:

        senior_name = executives.get(
            exec_name,
            {}
        ).get(
            "senior_name",
            ""
        )

        return float(
            executives.get(
                senior_name,
                {}
            ).get(
                "percentage_exec",
                0
            )
        )

    except:

        return 0.0
        Sr
Customer
Mauza
Plot
Date
Collection Type
Slip No
Collection
Executive
Exec %
Senior %
Direct Comm
Diff Comm
Gross Comm
TDS
Final Payable
    Total Collection
Direct Commission
Difference Commission
Gross Commission
TDS
Net Payable
