import streamlit as st
import requests
import json

# आपका असली Firebase डेटाबेस URL (इसमें आख़िर में /erp_data.json ज़रूर लगा है)
FIREBASE_URL = "https://firstchoice-infra-default-rtdb.firebaseio.com/erp_data.json"

# 1. डेटाबेस को शुरू करने का फ़ंक्शन
def init_db():
    # यदि session_state में डेटा नहीं है, तो उसे बनाएँ
    if 'db_projects' not in st.session_state:
        st.session_state.db_projects = {}
    # यदि पहली बार कॉल हो रहा है, तो क्लाउड से लोड करें
    if 'init_done' not in st.session_state:
        load_db_data()
        st.session_state.init_done = True

# 2. क्लाउड (Firebase) से डेटा डाउनलोड करने का फ़ंक्शन
def load_db_data():
    try:
        response = requests.get(FIREBASE_URL, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # यदि डेटाबेस खाली है (None), तो खाली डिक्शनरी रखें
            st.session_state.db_projects = data if data is not None else {}
        else:
            st.session_state.db_projects = {}
    except Exception as e:
        st.error(f"क्लाउड लोड एरर (Check Internet): {e}")
        st.session_state.db_projects = {}

# 3. क्लाउड (Firebase) में डेटा सेव करने का फ़ंक्शन
def save_db_data():
    try:
        # डेटा को JSON फॉर्मेट में बदलें
        json_data = json.dumps(st.session_state.db_projects, indent=4)
        # Firebase को PUT कमांड से भेजें (यह पुराने डेटा को नए से बदल देता है)
        response = requests.put(FIREBASE_URL, data=json_data, timeout=10)
        if response.status_code == 200:
            return True
        else:
            st.error(f"सेव फेल हुआ। स्टेटस कोड: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"क्लाउड सेव एरर: {e}")
        return False
