import streamlit as st
import pandas as pd
import time

st.set_page_config(page_title="Agreements & Formatting", page_icon="📝", layout="wide")

# 1. Security Check (Admin & Executive Access)
current_role = str(st.session_state.get("user_role", "")).lower()

if not current_role:
    st.warning("🔒 Please login from the Main Page first!")
    st.stop()

if current_role not in ["admin", "executive"]:
    st.error("🔒 This page is restricted to Admin and Executives only!")
    st.stop()

st.title("📝 Master Agreement Configuration")
st.markdown("---")

# 2. Upload Master Template Section
st.subheader("1. Upload Your Master Format")
st.write("Upload your standard agreement format. The system will use this structure to generate new agreements.")

uploaded_template = st.file_uploader("Upload Master Template (PDF, DOCX, JPG, PNG)", type=["pdf", "docx", "jpg", "jpeg", "png"])

if uploaded_template:
    st.success(f"✅ Successfully uploaded format: **{uploaded_template.name}**")
else:
    st.info("ℹ️ Please upload your agreement format to proceed.")

st.markdown("---")

# 3. Fetch Data from Master Ledger / Booking Form
st.subheader("2. Fetch Plot & Customer Details")
st.write("Select the Project and Plot. The system will auto-fetch data from the Master Ledger.")

col1, col2 = st.columns(2)
with col1:
    project_name = st.selectbox("Select Project", [
        "First Choice City 2 (Mohadi)", 
        "First Choice City 3 (Pachgaon)", 
        "Sai Samruddhi (Temsana - Cement Road)", 
        "Other"
    ])
with col2:
    # In live system, these plot numbers will automatically come from your Master Ledger
    plot_number = st.text_input("Enter Plot Number (e.g., Plot 101)")

# Mock Data Fetching Logic (This simulates pulling data from your ledger)
if plot_number:
    with st.spinner("🔄 Searching Master Ledger for Plot Details..."):
        time.sleep(1) # Simulating loading time
        
        # Here we pretend we found the data in the Master Ledger
        fetched_data = {
            "Customer Name": "Auto-Fetched from Ledger",
            "Contact Number": "Auto-Fetched from Ledger",
            "Plot Area (Sq.Ft.)": "1500",
            "Total Agreement Value": "₹ 15,00,000",
            "Advance Amount Paid": "₹ 5,00,000"
        }
        
        st.write("### 📋 Fetched Details from Ledger:")
        st.json(fetched_data)
        st.success("✅ Data linked successfully with the Booking Form!")

st.markdown("---")

# 4. Generate New Agreement Section
st.subheader("3. Generate Final Agreement")
language = st.radio("Select Output Language:", ["English", "Marathi", "Hindi"], horizontal=True)

if st.button("✨ Generate New Agreement", type="primary"):
    if not uploaded_template:
        st.error("⚠️ Please upload your Master Format in Step 1 before generating!")
    elif not plot_number:
        st.error("⚠️ Please enter a Plot Number in Step 2!")
    else:
        with st.spinner(f"Merging Master Ledger data with '{uploaded_template.name}'..."):
            time.sleep(2) # Simulating AI / PDF generation processing
            st.balloons()
            st.success("🎉 Agreement Generated Successfully!")
            
            st.info(f"📄 **Generated For:** {project_name} | {plot_number} | Language: {language}")
            
            # Download Button for the final generated agreement
            st.download_button(
                label="⬇️ Download Final Agreement (PDF)",
                data="This is a dummy PDF file content.", # In future, real PDF data goes here
                file_name=f"Agreement_{project_name}_{plot_number}.pdf",
                mime="application/pdf"
            )
