import streamlit as st
import pickle
import os

DB_FILE = "firstchoice_infra_master_db.pkl"

def init_db():
    db_data = {}
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "rb") as f:
                db_data = pickle.load(f)
        except:
            db_data = {}

    if 'projects' not in st.session_state: st.session_state.projects = db_data.get('projects', {})
    if 'plot_status' not in st.session_state: st.session_state.plot_status = db_data.get('plot_status', {})
    if 'bookings' not in st.session_state: st.session_state.bookings = db_data.get('bookings', {})
    if 'exec_data' not in st.session_state: st.session_state.exec_data = db_data.get('exec_data', {})

def save_db():
    db_data = {
        "projects": st.session_state.get('projects', {}),
        "plot_status": st.session_state.get('plot_status', {}),
        "bookings": st.session_state.get('bookings', {}),
        "exec_data": st.session_state.get('exec_data', {})
    }
    with open(DB_FILE, "wb") as f:
        pickle.dump(db_data, f)
