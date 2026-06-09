import streamlit as st
import database
import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Commission Statement", layout="wide")

# 1. डेटाबेस सिंक - यह लाइन सबसे जरूरी है
database.init_db()
# यह सुनिश्चित करता है कि डेटा डैशबोर्ड से सिंक हो रहा है
if 'db_projects' not in st.session_state:
    st.error("🚨 डेटाबेस लोड नहीं हो पाया है। कृपया इन्वेंटरी डैशबोर्ड से चेक करें।")
    st.stop()

db_data = st.session_state.db_projects
exec_data_root = db_data.get('executives', {})

# 2. प्रोजेक्ट्स लोड करने का सही तरीका
# हम उन सभी कीज़ को लेंगे जिनमें 'plots' मौजूद है
project_names = [name for name, data in db_data.items() if isinstance(data, dict) and 'plots' in data]

# अब आगे का आपका लूपिंग लॉजिक जो 'statement_rows' बनाता है
# ... [अपना पुराना लूपिंग कोड यहाँ पेस्ट करें] ...

# 3. अंत में यह चेक करें
if 'statement_rows' in locals() and len(statement_rows) > 0:
    # अपना टेबल और ग्राफ दिखाने वाला कोड यहाँ रखें
    st.success(f"कुल {len(statement_rows)} बुकिंग्स मिलीं!")
else:
    st.info("डेटा सिंक है, लेकिन चुनी गई तारीख या एग्जीक्यूटिव के लिए कोई 'Booked' बुकिंग नहीं मिली।")
    st.write(f"उपलब्ध प्रोजेक्ट्स: {project_names}") # यह आपको बताएगा कि क्या उसे प्रोजेक्ट मिल रहे हैं
