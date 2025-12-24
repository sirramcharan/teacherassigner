import streamlit as st
import pandas as pd
import random
import io

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="Exam Manager", layout="wide")

# --- DATA SAFETY CHECK ---
if 'teachers' in st.session_state and st.session_state.teachers:
    if 'classes' not in st.session_state.teachers[0]: 
        st.session_state.teachers = []
        st.session_state.timetable = []
        st.session_state.allocations = {}

# Initialize Session State
if 'teachers' not in st.session_state: st.session_state.teachers = [] 
if 'timetable' not in st.session_state: st.session_state.timetable = []
if 'allocations' not in st.session_state: st.session_state.allocations = {} 

# Default Subjects
if 'class_subjects' not in st.session_state:
    st.session_state.class_subjects = {
        "Class 1": ["EVS", "English", "Telugu", "EHV", "Maths"],
        "Class 2": ["EVS", "English", "Telugu", "EHV", "Maths"],
        "Class 3": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi"],
        "Class 4": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi"],
        "Class 5": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi", "Computer"],
        "Class 6": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi", "Computer"],
        "Class 7": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi", "Computer"],
        "Class 8": ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi", "Computer"],
        "Class 9": ["AI", "EVS", "English", "Telugu", "EHV", "Maths"],
        "Class 10": ["AI", "EVS", "English", "Telugu", "EHV", "Maths"],
        "Class 11 (MPC)": ["English", "Telugu", "EHV", "Maths", "Physics", "Chemistry"],
        "Class 11 (BPC)": ["English", "Telugu", "EHV", "Biology", "Physics", "Chemistry"],
        "Class 11 (CAE)": ["English", "Telugu", "EHV", "Business Studies", "Accounts", "Economics"],
        "Class 12 (MPC)": ["English", "Telugu", "EHV", "Maths", "Physics", "Chemistry"],
        "Class 12 (BPC)": ["English", "Telugu", "EHV", "Biology", "Physics", "Chemistry"],
        "Class 12 (CAE)": ["English", "Telugu", "EHV", "Business Studies", "Accounts", "Economics"],
    }

# ==========================================
# 2. CSS STYLING
# ==========================================
st.markdown("""
<style>
    /* 1. Main Background */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Segoe UI', sans-serif;
    }

    /* 2. Glass Container */
    .glass-container {
        background: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* 3. Text Colors */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800 !important; }
    p, label, span, div[data-testid="stMarkdownContainer"] p { 
        color: #ffffff !important; 
    }

    /* 4. TAB STYLING (FIXED) */
    /* Unselected Tabs */
    button[data-baseweb="tab"] {
        color: #cccccc !important; 
        background-color: transparent !important;
    }
    /* Selected Tab - Force BLACK Text */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] > div {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* 5. Inputs & Dropdowns */
    .stTextInput input, .stDateInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 5px;
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .stSelectbox div[data-baseweb="select"] div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
    }
    li[data-baseweb="option"] {
        color: #000000 !important;
        background-color: #ffffff !important;
    }

    /* 6. Buttons */
    .stButton button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px;
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0 0 15px rgba(0, 201, 255, 0.7);
    }
    
    /* 7. DataFrame/Table styling */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255,255,255, 0.9);
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_all_subjects():
    subjects = set()
    for s_list in st.session_state.class_subjects.values():
        subjects.update(s_list)
    return sorted(list(subjects))

def get_all_classes():
    return list(st.session_state.class_subjects.keys())

def find_teachers(subject, target_class, role_type):
    result = []
    for t in st.session_state.teachers:
        teaches_class = target_class in t['classes']
        teaches_subject = subject in t['subjects']

        if role_type == "revision":
            # Must teach THIS subject to THIS class
            if teaches_subject and teaches_class:
                result.append(t['name'])
        
        elif role_type == "invigilator":
            # Must NOT teach this subject (general rule)
            if not teaches_subject: 
                result.append(t['name'])
    return result

def get_all_teacher_names():
    return [t['name'] for t in st.session_state.teachers]

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# ==========================================
# 4. APP LAYOUT
# ==========================================

st.markdown("<h1>🏫 Exam & Invigilation Manager</h1>", unsafe_allow_html=True)

tabs = st.tabs(["Teachers", "Subjects", "Schedule", "Allocation", "Timetable", "Stats"])

# --- TAB 1: TEACHERS ---
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='glass-container'><h3>Add New Teacher</h3>", unsafe_allow_html=True)
        with st.form("add_teacher_form", clear_on_submit=True):
            t_name = st.text_input("Full Name")
            t_subs = st.multiselect("Subjects Taught", get_all_subjects())
            t_classes = st.multiselect("Classes Taught", get_all_classes())
            
            if st.form_submit_button("Save Teacher"):
                if t_name and t_subs and t_classes:
                    st.session_state.teachers.append({
                        "name": t_name, 
                        "subjects": t_subs,
                        "classes": t_classes
                    })
                    st.success(f"Added {t_name}")
                else:
                    st.error("Please fill all fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-container'><h3>Teacher Directory</h3>", unsafe_allow_html=True)
        
        if st.session_state.teachers:
            # PREPARE DATA FOR TABLE
            table_data = []
            for t in st.session_state.teachers:
                table_data.append({
                    "Name": t['name'],
                    "Subjects": ", ".join(t['subjects']), # Convert list to string
                    "Classes": ", ".join(t['classes'])    # Convert list to string
                })
            
            df_teachers = pd.DataFrame(table_data)
            st.dataframe(df_teachers, use_container_width=True, hide_index=True)
            
            # REMOVE TEACHER SECTION
            st.markdown("#### Remove Teacher")
            c1, c2 = st.columns([3, 1])
            with c1:
                t_to_del = st.selectbox("Select Teacher to Remove", [t['name'] for t in st.session_state.teachers], label_visibility="collapsed")
            with c2:
                if st.button("Delete"):
                    # Find index and remove
                    for i, t in enumerate(st.session_state.teachers):
                        if t['name'] == t_to_del:
                            st.session_state.teachers.pop(i)
                            st.rerun()
                            break
        else:
            st.info("No teachers added yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SUBJECTS ---
with tabs[1]:
    st.markdown("<div class='glass-container'><h3>Manage Class Subjects</h3>", unsafe_allow_html=True)
    
    with st.form("add_subject_form", clear_on_submit=True):
        target_class = st.selectbox("Select Class", get_all_classes())
        new_subject = st.text_input("New Subject Name (e.g., Robotics)")
        
        if st.form_submit_button("Add Subject"):
            if new_subject:
                if new_subject not in st.session_state.class_subjects[target_class]:
                    st.session_state.class_subjects[target_class].append(new_subject)
                    st.success(f"Added {new_subject} to {target_class}")
                else:
                    st.warning("Subject already exists.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: SCHEDULE ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Create Exam Schedule</h3>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        exam_date = st.date_input("Exam Date")
        exam_class = st.selectbox("Select Class", get_all_classes(), key="tt_class_selector")
    
    with c2:
        available_subjects = st.session_state.class_subjects.get(exam_class, [])
        exam_subject = st.selectbox("Select Subject", available_subjects, key="tt_sub_selector")
        exam_slot = st.selectbox("Time Slot", ["Morning (Exam: 3rd-4th)", "Afternoon (Exam: 7th-8th)"])

    st.markdown("---")
    
    if st.button("Add Exam to Schedule"):
        eid = f"{exam_date}_{exam_class}_{exam_slot}"
        rev_periods = "1st-2nd" if "Morning" in exam_slot else "5th-6th"
        exam_periods = "3rd-4th" if "Morning" in exam_slot else "7th-8th"
        
        st.session_state.timetable.append({
            "id": eid, "date": str(exam_date), "class": exam_class, 
            "subject": exam_subject, "slot": exam_slot,
            "rev_p": rev_periods, "exam_p": exam_periods
        })
        st.success(f"Scheduled {exam_subject} for {exam_class}!")

    if st.button("🗑️ Clear All Timetable Data", type="secondary"):
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.rerun()
        
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: ALLOCATE ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>Teacher Allocation</h3></div>", unsafe_allow_html=True)
    if not st.session_state.timetable:
        st.info("No exams scheduled. Go to the 'Schedule' tab first.")
    
    for exam in st.session_state.timetable:
        eid = exam['id']
        
        if eid not in st.session_state.allocations:
            rev_pool = find_teachers(exam['subject'], exam['class'], "revision")
            inv_pool = find_teachers(exam['subject'], exam['class'], "invigilator")
            random.shuffle(inv_pool)
            
            st.session_state.allocations[eid] = {
                "rev_pool": rev_pool, "rev_idx": 0, "confirmed_rev": None,
                "inv_pool": inv_pool, "inv_idx": 0, "confirmed_inv": None
            }
            
        data = st.session_state.allocations[eid]
        
        with st.expander(f"{exam['date']} | {exam['class']} | {exam['subject']}", expanded=True):
            r_col, i_col = st.columns(2)
            
            # REVISION
            with r_col:
                st.markdown(f"#### 📖 Revision ({exam['rev_p']})")
                if data['confirmed_rev']:
                    st.success(f"Assigned: **{data['confirmed_rev']}**")
                else:
                    pool = data['rev_pool']
                    idx = data['rev_idx']
                    if not pool:
                        st.warning("No teacher found.")
                        candidate = st.selectbox("Substitute", get_all_teacher_names(), key=f"s_r_{eid}")
                        if st.button("Confirm", key=f"c_s_r_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()
                    elif idx < len(pool):
                        cand = pool[idx]
                        st.info(f"Draft: **{cand}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Yes", key=f"y_r_{eid}_{idx}"):
                            data['confirmed_rev'] = cand
                            st.rerun()
                        if c2.button("❌ No", key=f"n_r_{eid}_{idx}"):
                            data['rev_idx'] += 1
                            st.rerun()
                    else:
                        st.error("All Unavailable.")
                        candidate = st.selectbox("Substitute", get_all_teacher_names(), key=f"m_r_{eid}")
                        if st.button("Confirm", key=f"m_c_r_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()

            # INVIGILATION
            with i_col:
                st.markdown(f"#### 📝 Exam ({exam['exam_p']})")
                if data['confirmed_inv']:
                    st.success(f"Assigned: **{data['confirmed_inv']}**")
                else:
                    pool = data['inv_pool']
                    idx = data['inv_idx']
                    if idx < len(pool):
                        cand = pool[idx]
                        st.info(f"Backup: **{cand}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Yes", key=f"y_i_{eid}_{idx}"):
                            data['confirmed_inv'] = cand
                            st.rerun()
                        if c2.button("❌ No", key=f"n_i_{eid}_{idx}"):
                            data['inv_idx'] += 1
                            st.rerun()
                    else:
                        st.error("No Backups.")
                        candidate = st.selectbox("Manual", get_all_teacher_names(), key=f"m_i_{eid}")
                        if st.button("Confirm", key=f"c_m_i_{eid}"):
                            data['confirmed_inv'] = candidate
                            st.rerun()

# --- TAB 5: FINAL MATRIX ---
with tabs[4]:
    st.markdown("<div class='glass-container'><h3>🗓️ Final Timetable</h3></div>", unsafe_allow_html=True)
    if st.session_state.timetable:
        rows = []
        for exam in st.session_state.timetable:
            eid = exam['id']
            alloc = st.session_state.allocations.get(eid, {})
            r_t = alloc.get('confirmed_rev', 'Pending')
            i_t = alloc.get('confirmed_inv', 'Pending')
            
            row = {
                "Date": exam['date'], "Class": exam['class'], "Subject": exam['subject'],
                "1st-2nd": r_t if "Morning" in exam['slot'] else "---",
                "3rd-4th": f"Exam ({i_t})" if "Morning" in exam['slot'] else "---",
                "5th-6th": r_t if "Afternoon" in exam['slot'] else "---",
                "7th-8th": f"Exam ({i_t})" if "Afternoon" in exam['slot'] else "---",
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.download_button("📥 Download Excel", convert_df_to_excel(df), "timetable.xlsx")
    else:
        st.info("No data available.")

# --- TAB 6: STATS ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>📊 Workload Statistics</h3></div>", unsafe_allow_html=True)
    if st.session_state.teachers:
        stats = {t: 0 for t in get_all_teacher_names()}
        for alloc in st.session_state.allocations.values():
            if alloc.get('confirmed_inv') in stats: stats[alloc['confirmed_inv']] += 1
            if alloc.get('confirmed_rev') in stats: stats[alloc['confirmed_rev']] += 1
            
        df_stats = pd.DataFrame(list(stats.items()), columns=["Teacher", "Duties"])
        st.bar_chart(df_stats.set_index("Teacher"))
    else:
        st.warning("Add teachers first.")
