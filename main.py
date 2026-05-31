import streamlit as st

# डेटा सेव करने के लिए (Session State)
if 'projects' not in st.session_state: st.session_state.projects = {}
if 'plots' not in st.session_state: st.session_state.plots = {} # {Project_Name: {Plot_No: "Available"}}

def show_inventory(project_name):
    st.title(f"Inventory: {project_name}")
    proj_data = st.session_state.projects[project_name]
    
    # 5 कॉलम का ग्रिड
    cols = st.columns(5)
    for i in range(1, proj_data['total_plots'] + 1):
        plot_status = st.session_state.plots[project_name].get(i, "Available")
        color = "green" if plot_status == "Available" else "red"
        
        # बटन का रंग और क्लिक एक्शन
        if cols[i % 5].button(f"Plot {i}", key=f"p_{i}"):
            if plot_status == "Available":
                st.session_state.selected_plot = i
                st.session_state.selected_project = project_name
                st.rerun() # बुकिंग फॉर्म दिखाने के लिए
            else:
                st.warning(f"Plot {i} is already Booked!")

def main():
    st.title("🏢 Firstchoice Infra ERP")
    
    # प्रोजेक्ट बनाने का फॉर्म
    with st.expander("➕ Add New Project"):
        p_name = st.text_input("Project Name")
        khasra = st.text_input("Khasra No")
        mauza = st.text_input("Mauza")
        total_plots = st.number_input("Total Plots", min_value=1, step=1)
        
        if st.button("Save Project"):
            st.session_state.projects[p_name] = {"khasra": khasra, "mauza": mauza, "total_plots": total_plots}
            st.session_state.plots[p_name] = {i: "Available" for i in range(1, total_plots + 1)}
            st.success(f"Project {p_name} added!")

    # प्रोजेक्ट्स की लिस्ट
    st.subheader("Select Project")
    for p_name in st.session_state.projects.keys():
        if st.button(f"Open: {p_name}"):
            st.session_state.current_page = p_name
            st.rerun()

    # अगर कोई प्रोजेक्ट चुना गया है
    if 'current_page' in st.session_state:
        show_inventory(st.session_state.current_page)

main()
