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
# 2. DARK MODE + SUPER WHITE TEXT CSS
# ==========================================
st.markdown("""
<style>
    /* 1. Main Background - Deep Dark Blue Gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    /* 2. Glass Container - Dark & Transparent */
    .glass-container {
        background: rgba(0, 0, 0, 0.6); /* Dark background */
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
    }

    /* 3. SUPER WHITE TEXT for Headlines & Labels */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff !important;
        font-weight: 800 !important; /* Extra Bold */
        text-shadow: 0px 2px 4px rgba(0,0,0,0.8);
    }
    
    p, label, span, div[data-testid="stMarkdownContainer"] p {
        color: #ffffff !important;
        font-weight: 600 !important; /* Semi-Bold */
    }
    
    /* 4. Input Fields & Dropdowns - High Contrast (White Box, Black Text) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div, .stDateInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 8px !important;
        font-weight: bold !important;
        border: 2px solid rgba(255,255,255,0.5) !important;
    }
    
    /* Fix Dropdown Menu Items (Pop-up list) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], li[data-baseweb="option"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        font-weight: bold !important;
    }
    
    /* 5. Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(0,0,0,0.3);
        padding: 10px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #cccccc !important; /* Grey when inactive */
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #000000 !important; /* Black text on selected tab */
        font-weight: 900 !important;
        border-radius: 8px;
    }

    /* 6. Buttons - Neon Pop */
    .stButton button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%) !important;
        color: white !important;
        font-weight: bold !important;
        border: none !important;
        padding: 0.6rem 1.2rem !important;
        border-radius: 8px !important;
        box-shadow: 0px 4px 15px rgba(0, 210, 255, 0.4);
    }
    .stButton button:hover {
        transform: scale(1.02);
        box-shadow: 0px 6px 20px rgba(0, 210, 255, 0.6);
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
            for idx, t in enumerate(st.session_state.teachers):
                with st.expander(f"👤 {t['name']}"):
                    st.write(f"**Subjects:** {', '.join(t['subjects'])}")
                    st.write(f"**Classes:** {', '.join(t['classes'])}")
                    if st.button("Delete", key=f"del_{idx}"):
                        st.session_state.teachers.pop(idx)
                        st.rerun()
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
