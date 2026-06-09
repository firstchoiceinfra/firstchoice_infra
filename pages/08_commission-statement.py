import streamlit as st
import database
import datetime
import pandas as pd

st.set_page_config(layout="wide", page_title="FC Infra - Commission Statement")
database.init_db()
db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# (अपना 'Safe Float', 'Get Downlines', 'Get Diff Deduction' वाला फंक्शन यहाँ पेस्ट करें)

st.title("📊 Advanced Statement & Payout Ledger")

# [यहाँ 'EVERYONE: LIVE STATEMENT LEDGER ENGINE' वाला पूरा कोड पेस्ट करें]
# (वो 'Generate Comprehensive Ledger' बटन वाला पूरा हिस्सा यहाँ आएगा)

# बस 'Generate' बटन के अंत में ये तीन लाइनें जोड़ें:
if 'statement_rows' in locals() and statement_rows:
    df_statement = pd.DataFrame(statement_rows)
    st.dataframe(df_statement, use_container_width=True)
    
    # कैलकुलेशन और बटन (जो हमने पहले फिक्स किए थे)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("⭐ Direct", f"₹ {df_statement[df_statement['Sale Origin'] == '⭐ Direct Sale']['Net Payout (₹)'].sum():,.2f}")
    c2.metric("👥 Team", f"₹ {df_statement[df_statement['Sale Origin'].str.contains('Team')]['Net Payout (₹)'].sum():,.2f}")
    c4.metric("🏆 Grand Total", f"₹ {df_statement['Net Payout (₹)'].sum():,.2f}")
    
    csv = df_statement.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 Export Statement", csv, "Statement.csv", "text/csv")
