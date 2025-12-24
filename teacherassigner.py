import streamlit as st
import pandas as pd
import random
import io

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="School Exam Manager", layout="wide")

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
# 2. FIXED UI CSS
# ==========================================
st.markdown("""
<style>
    /* Gradient Background for the whole app */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* The Glass Container */
    .glass-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 25px;
        margin-bottom: 20px;
        color: #1f1f1f; /* Dark text for visibility */
    }

    /* Headers inside the app */
    h1 { color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
    h2, h3, h4 { color: #333 !important; }

    /* Input Fields - FORCE BLACK TEXT */
    .stTextInput input, .stDateInput input, .stSelectbox div, .stMultiSelect div {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Make dropdown text visible */
    div[data-baseweb="select"] span {
        color: #000000 !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #764ba2 !important;
        color: white !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: bold !important;
    }
    .stButton button:hover {
        background-color: #5a387e !important;
    }
    
    /* Tab text color fix */
    button[data-baseweb="tab"] {
        background-color: rgba(255,255,255, 0.2) !important;
        color: white !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: white !important;
        color: #764ba2 !important;
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
            # Must NOT teach this subject (general rule to avoid cheating)
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

st.markdown("<h1>🏫 School Exam Manager</h1>", unsafe_allow_html=True)

tabs = st.tabs(["👨‍🏫 Teachers", "📚 Subjects", "📅 Schedule", "✅ Allocate", "🗓️ Final Matrix", "📊 Stats"])

# --- TAB 1: TEACHERS ---
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='glass-container'><h3>Add New Teacher</h3>", unsafe_allow_html=True)
        
        # USE FORM TO CLEAR INPUTS AUTOMATICALLY
        with st.form("add_teacher_form", clear_on_submit=True):
            t_name = st.text_input("Teacher Name")
            t_subs = st.multiselect("Subjects Taught", get_all_subjects())
            t_classes = st.multiselect("Classes Taught", get_all_classes())
            
            submitted = st.form_submit_button("Save Teacher")
            
            if submitted:
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
        st.markdown("<div class='glass-container'><h3>Teacher List</h3>", unsafe_allow_html=True)
        if st.session_state.teachers:
            for idx, t in enumerate(st.session_state.teachers):
                with st.expander(f"👤 {t['name']}"):
                    st.write(f"**Subjects:** {', '.join(t['subjects'])}")
                    st.write(f"**Classes:** {', '.join(t['classes'])}")
                    if st.button("Delete Teacher", key=f"del_{idx}"):
                        st.session_state.teachers.pop(idx)
                        st.rerun()
        else:
            st.info("No teachers added yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SUBJECTS ---
with tabs[1]:
    st.markdown("<div class='glass-container'><h3>Add Subject to Class</h3>", unsafe_allow_html=True)
    
    with st.form("add_subject_form", clear_on_submit=True):
        target_class = st.selectbox("Select Class", get_all_classes())
        new_subject = st.text_input("New Subject Name")
        sub_submit = st.form_submit_button("Add Subject")
        
        if sub_submit:
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
    
    with st.form("schedule_form", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        with c1: exam_date = st.date_input("Date")
        with c2: exam_class = st.selectbox("Class", get_all_classes())
        with c3: exam_subject = st.selectbox("Subject", st.session_state.class_subjects.get(exam_class, []))
        with c4: exam_slot = st.selectbox("Slot", ["Morning (Exam: 3rd-4th)", "Afternoon (Exam: 7th-8th)"])
        
        schedule_btn = st.form_submit_button("Add Exam")
        
        if schedule_btn:
            eid = f"{exam_date}_{exam_class}_{exam_slot}"
            rev_periods = "1st-2nd" if "Morning" in exam_slot else "5th-6th"
            exam_periods = "3rd-4th" if "Morning" in exam_slot else "7th-8th"
            
            st.session_state.timetable.append({
                "id": eid, "date": str(exam_date), "class": exam_class, 
                "subject": exam_subject, "slot": exam_slot,
                "rev_p": rev_periods, "exam_p": exam_periods
            })
            st.success("Exam Scheduled!")
            
    if st.button("Reset All Timetable Data", type="primary"):
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: ALLOCATE ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>Allocation</h3></div>", unsafe_allow_html=True)
    if not st.session_state.timetable:
        st.info("No exams scheduled.")
    
    for exam in st.session_state.timetable:
        eid = exam['id']
        
        # Initialize Logic
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
                        st.warning("No subject teacher found.")
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
                        st.error("All unavailable.")
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
                        st.error("No backups left.")
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

# --- TAB 6: STATS ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>📊 Statistics</h3></div>", unsafe_allow_html=True)
    if st.session_state.teachers:
        stats = {t: 0 for t in get_all_teacher_names()}
        for alloc in st.session_state.allocations.values():
            if alloc.get('confirmed_inv') in stats: stats[alloc['confirmed_inv']] += 1
            if alloc.get('confirmed_rev') in stats: stats[alloc['confirmed_rev']] += 1
            
        df_stats = pd.DataFrame(list(stats.items()), columns=["Teacher", "Duties"])
        st.bar_chart(df_stats.set_index("Teacher"))
