# database.py
import streamlit as st
import requests
import json

# आपका असली Firebase डेटाबेस URL (जो आपने इमेज 12 में दिखाया था)
# !!! सबसे ज़रूरी !!!: इसके आखिर में /erp_data.json ज़रूर लगाएँ।
FIREBASE_URL = "https://firstchoice-infra-default-rtdb.firebaseio.com/erp_data.json"

# 1. डेटाबेस को शुरू करने का फ़ंक्शन (main.py में लॉगिन के बाद कॉल करें)
def init_db():
    if 'db_projects' not in st.session_state:
        st.session_state.db_projects = {}
    if 'init_call' not in st.session_state:
        load_db_data()
        st.session_state.init_call = True

# 2. क्लाउड (Firebase) से डेटा डाउनलोड करने का फ़ंक्शन
def load_db_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            # यदि डेटाबेस खाली है (None), तो खाली डेटा सेट करें
            st.session_state.db_projects = data if data is not None else {}
        else:
            # यदि डेटा लोड करने में समस्या हो, तो खाली डेटा रखें
            st.session_state.db_projects = {}
    except Exception as e:
        st.error(f"Cloud load error: {e}")
        st.session_state.db_projects = {}

# 3. क्लाउड (Firebase) में डेटा सेव करने का फ़ंक्शन
def save_db_data():
    try:
        # सत्र स्थिति (st.session_state) में रखे डेटा को JSON में बदलें
        json_data = json.dumps(st.session_state.db_projects, indent=4)
        # Firebase को PUT कमांड से धकेलें
        response = requests.put(FIREBASE_URL, data=json_data)
        if response.status_code == 200:
            return True
        else:
            st.error(f"Cloud save error. Status code: {response.status_code}")
            return False
    except Exception as e:
        st.error(f"Cloud save error: {e}")
        return False
