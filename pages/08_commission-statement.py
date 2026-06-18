import streamlit as st
import pandas as pd
import database
import datetime

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Commission Statement", layout="wide")

# =========================
# SECURITY CHECK
# =========================
if not st.session_state.get("logged_in", False):
    st.warning("🔒 Please login first")
    st.stop()

user_role = st.session_state.get("user_role", "executive")
current_user = st.session_state.get("current_user_name", "")

# =========================
# DB LOAD
# =========================
database.init_db()
db_data = st.session_state.db_projects
exec_data = db_data.get("executives", {})

# =========================
# THEME (optional)
# =========================
st.title("💰 Commission Statement Dashboard")
st.markdown("---")

# =========================
# HELPER FUNCTIONS
# =========================
def safe_float(v):
    try:
        return float(v)
    except:
        return 0.0

def get_downlines(manager):
    manager = manager.lower().strip()
    down = []
    for ex, data in exec_data.items():
        if str(data.get("senior_name","")).lower().strip() == manager:
            down.append(ex)
            down.extend(get_downlines(ex))
    return list(set(down))

# =========================
# INPUT FILTER
# =========================
col1, col2 = st.columns(2)

with col1:
    selected_exec = st.selectbox(
        "Select Executive",
        ["All"] + list(exec_data.keys())
    )

with col2:
    selected_project = st.selectbox(
        "Select Project",
        ["All"] + [p for p in db_data.keys() if isinstance(db_data[p], dict)]
    )

# =========================
# MAIN CALCULATION ENGINE
# =========================
commission_rows = []
total_commission = 0.0

for p_name, p_info in db_data.items():
    if not isinstance(p_info, dict) or "plots" not in p_info:
        continue

    plots = p_info.get("plots", {})

    if isinstance(plots, list):
        plots = {str(i): v for i, v in enumerate(plots)}

    for plot_id, plot in plots.items():
        if not isinstance(plot, dict):
            continue

        if plot.get("status") != "Booked":
            continue

        exec_name = plot.get("executive_name", "Direct")
        if selected_exec != "All" and exec_name != selected_exec:
            continue

        if selected_project != "All" and p_name != selected_project:
            continue

        # =========================
        # VALUE CALCULATION
        # =========================
        area = safe_float(plot.get("plot_area", 0))
        rate = safe_float(plot.get("selling_rate", 0))

        if rate > 100000:
            total_value = rate
        else:
            total_value = area * rate

        token = safe_float(plot.get("token_amount", 0))

        emi = sum(safe_float(p.get("amount", 0)) for p in plot.get("partial_payments", []))

        collected = token + emi

        # =========================
        # COMMISSION LOGIC
        # =========================
        exec_info = exec_data.get(exec_name, {})
        percent = safe_float(exec_info.get("percentage_exec", 0))
        fixed = safe_float(exec_info.get("rupees_exec", 0))

        commission = (total_value * percent / 100) + fixed

        total_commission += commission

        commission_rows.append({
            "Project": p_name,
            "Plot": plot_id,
            "Customer": plot.get("customer_name", "N/A"),
            "Executive": exec_name,
            "Total Value": total_value,
            "Collected": collected,
            "Commission %": percent,
            "Fixed Commission": fixed,
            "Total Commission": commission
        })

# =========================
# DASHBOARD
# =========================
if commission_rows:
    df = pd.DataFrame(commission_rows)

    st.subheader("📊 Commission Summary")

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Records", len(df))
    c2.metric("Total Commission", f"₹ {total_commission:,.2f}")
    c3.metric("Avg Commission", f"₹ {df['Total Commission'].mean():,.2f}")

    st.write("---")

    st.subheader("📋 Detailed Statement")
    st.dataframe(df, use_container_width=True)

    # =========================
    # DOWNLOAD
    # =========================
    csv = df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "📥 Download Commission Report",
        data=csv,
        file_name=f"commission_statement_{datetime.date.today()}.csv",
        mime="text/csv"
    )

else:
    st.info("No commission data found for selected filters.")
