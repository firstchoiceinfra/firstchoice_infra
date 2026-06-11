import streamlit as st
import database
import pandas as pd
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# (अपना डेटाबेस और बाकी कोड यहाँ रखें...)

# PDF जनरेटर फंक्शन
def create_pdf(df, search_exec, start, end):
    pdf_file = f"Statement_{search_exec}.pdf"
    c = canvas.Canvas(pdf_file, pagesize=A4)
    # प्रीमियम लेआउट
    c.setFont("Helvetica-Bold", 24)
    c.drawString(150, 800, "FIRSTCHOICE INFRA")
    c.setFont("Helvetica-Oblique", 12)
    c.drawString(250, 780, "Symbol Of Trust...")
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, 740, "Business Partner Commission Statement")
    
    # डिटेल्स
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Partner: {search_exec}")
    c.drawString(350, 700, f"Period: {start} to {end}")
    
    # टेबल डेटा (सिंपल लूप)
    y = 650
    for index, row in df.iterrows():
        c.drawString(50, y, f"{row['Customer']} | {row['Plot']} | ₹{row['Received Amt']:,.2f}")
        y -= 20
    
    # फाइनेंशियल समरी
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y-50, f"Total Net Payout: ₹{df['Net In Hand'].sum():,.2f}")
    c.save()
    return pdf_file

# बटन लॉजिक
if 'df_statement' in st.session_state:
    df = st.session_state.df_statement
    
    if st.button("📄 Generate PDF for WhatsApp/Print"):
        pdf_path = create_pdf(df, search_exec, start, end)
        
        # डाउनलोड बटन
        with open(pdf_path, "rb") as f:
            st.download_button("📥 Download A4 PDF", f, file_name="Commission_Statement.pdf")
            
        st.success("PDF तैयार है! अब आप इसे WhatsApp पर शेयर कर सकते हैं।")
