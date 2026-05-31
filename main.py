import streamlit as st

# डेटा को सुरक्षित रखने के लिए बेसिक सेटअप
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'executives' not in st.session_state: st.session_state.executives = {"8317259986": "shubham dekate"}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'role' not in st.session_state: st.session_state.role = None

def login():
    st.title("🔐 Firstchoice Infra - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.logged_in = True
            st.session_state.role = "admin"
            st.rerun()
        elif username in st.session_state.executives.values() and password in st.session_state.executives.keys():
            st.session_state.logged_in = True
            st.session_state.role = "executive"
            st.rerun()
        else: st.error("Invalid Login!")

if not st.session_state.logged_in:
    login()
else:
    st.sidebar.button("Log out", on_click=lambda: st.session_state.update({'logged_in': False}))
    
    # एडमिन सेक्शन
    if st.session_state.role == "admin":
        st.title("🏢 Admin Panel")
        with st.expander("➕ Add New Executive"):
            n = st.text_input("Executive Name")
            m = st.text_input("Mobile No")
            if st.button("Save Executive"):
                st.session_state.executives[m] = n
        
        with st.expander("➕ Add New Project"):
            p_name = st.text_input("Project Name")
            plots = st.number_input("Total Plots", min_value=1)
            if st.button("Save Project"):
                st.session_state.projects[p_name] = {"total_plots": plots}
                st.success(f"Project {p_name} saved!")

    # डैशबोर्ड (सबके लिए)
    st.title("📊 Projects Dashboard")
    for p_name, data in st.session_state.projects.items():
        if st.button(f"Open: {p_name}"):
            st.session_state.current_project = p_name
            
    if 'current_project' in st.session_state:
        st.subheader(f"Inventory: {st.session_state.current_project}")
        cols = st.columns(5)
        for i in range(1, st.session_state.projects[st.session_state.current_project]['total_plots'] + 1):
            if cols[i%5].button(f"Plot {i}"):
                st.info(f"Booking form for {st.session_state.current_project} - Plot {i} will open here.")
