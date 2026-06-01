import streamlit as st
import requests
import json

# 👇 इनवर्टेड कॉमा (" ") के अंदर अपना लिंक डालें और आख़िर में /erp_data.json ज़रूर लगाएं।
# उदाहरण: "https://firstchoice-infra-default-rtdb.firebaseio.com/erp_data.json"
FIREBASE_URL = "https://firstchoice-infra-default-rtdb.firebaseio.com/erp_data.json
def init_db():
    """ऐप शुरू होते ही क्लाउड (Firebase) से डेटा डाउनलोड करेगा"""
    db_data = {}
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200 and response.json() is not None:
            db_data = response.json()
    except Exception as e:
        print("Cloud load error:", e)

    # मेमोरी में सेट करना
    if 'projects' not in st.session_state: st.session_state.projects = db_data.get('projects', {})
    if 'plot_status' not in st.session_state: st.session_state.plot_status = db_data.get('plot_status', {})
    if 'bookings' not in st.session_state: st.session_state.bookings = db_data.get('bookings', {})
    if 'exec_data' not in st.session_state: st.session_state.exec_data = db_data.get('exec_data', {})

def save_db():
    """डेटा सेव होते ही उसे सीधा Firebase क्लाउड पर लॉक कर देगा"""
    db_data = {
        "projects": st.session_state.get('projects', {}),
        "plot_status": st.session_state.get('plot_status', {}),
        "bookings": st.session_state.get('bookings', {}),
        "exec_data": st.session_state.get('exec_data', {})
    }
    try:
        requests.put(FIREBASE_URL, data=json.dumps(db_data))
    except Exception as e:
        st.error("क्लाउड पर सेव करने में समस्या आ रही है।")
