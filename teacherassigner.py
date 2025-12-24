import streamlit as st
import pandas as pd
import random
from datetime import datetime

# ==========================================
# 1. CONFIGURATION & STATE MANAGEMENT
# ==========================================
st.set_page_config(page_title="School Exam Manager", layout="wide")

# Initialize Session State for Data Persistence
if 'teachers' not in st.session_state:
    st.session_state.teachers = [
        {"name": "Alice (Math)", "subjects": ["Maths"]},
        {"name": "Bob (Eng)", "subjects": ["English"]},
        {"name": "Charlie (Sci)", "subjects": ["EVS", "Physics"]},
        {"name": "David (Tel)", "subjects": ["Telugu"]},
        {"name": "Eve (Comp)", "subjects": ["Computer", "AI"]},
        {"name": "Frank (Hin)", "subjects": ["Hindi"]},
        {"name": "Grace (Bio)", "subjects": ["Biology"]},
        {"name": "Heidi (Chem)", "subjects": ["Chemistry"]},
        {"name": "Ivan (Comm)", "subjects": ["Business Studies", "Accounts"]},
        {"name": "Judy (EHV)", "subjects": ["EHV"]}
    ]

if 'timetable' not in st.session_state:
    st.session_state.timetable = []

if 'allocations' not in st.session_state:
    st.session_state.allocations = {}  # Key: Exam_ID, Value: {status, current_invigilator_index}

# Default Class Subjects Structure
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
# 2. GLASS THEME CSS
# ==========================================
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Glass Container */
    .glass-container {
        background: rgba(255, 255, 255, 0.25);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        backdrop-filter: blur(4px);
        -webkit-backdrop-filter: blur(4px);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        margin-bottom: 20px;
        color: white;
    }
    
    /* Text Colors */
    h1, h2, h3, p, label {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    
    /* Input Fields */
    .stTextInput input, .stSelectbox div, .stDateInput input {
        background-color: rgba(255, 255, 255, 0.9) !important;
        color: black !important;
        border-radius: 5px;
    }
    
    /* Buttons */
    .stButton button {
        background-color: rgba(255, 255, 255, 0.3) !important;
        color: white !important;
        border: 1px solid white !important;
        transition: 0.3s;
    }
    .stButton button:hover {
        background-color: white !important;
        color: #764ba2 !important;
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
        color: black;
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

def find_teachers_by_subject(subject, match_type="is"):
    """
    match_type 'is': returns teachers teaching this subject.
    match_type 'not': returns teachers NOT teaching this subject.
    """
    result = []
    for t in st.session_state.teachers:
        if match_type == "is":
            if subject in t['subjects']:
                result.append(t['name'])
        else:
            if subject not in t['subjects']:
                result.append(t['name'])
    return result

# ==========================================
# 4. APP LAYOUT
# ==========================================

st.markdown("<div class='glass-container'><h1>🏫 Exam & Invigilation Manager</h1></div>", unsafe_allow_html=True)

# Tabs for navigation
tab1, tab2, tab3 = st.tabs(["📝 Manage Data", "📅 Create Timetable", "✅ Allocations & Availability"])

# --- TAB 1: MANAGE DATA ---
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='glass-container'><h3>Add New Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Teacher Name")
        all_subs = get_all_subjects()
        t_subs = st.multiselect("Subjects Taught", all_subs)
        
        if st.button("Add Teacher"):
            if t_name and t_subs:
                st.session_state.teachers.append({"name": t_name, "subjects": t_subs})
                st.success(f"Added {t_name}")
            else:
                st.error("Please enter name and select subjects.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Display Teachers
        st.markdown("#### Current Teachers")
        teacher_df = pd.DataFrame(st.session_state.teachers)
        st.dataframe(teacher_df, hide_index=True)

    with col2:
        st.markdown("<div class='glass-container'><h3>Add Subject to Class</h3>", unsafe_allow_html=True)
        target_class = st.selectbox("Select Class", list(st.session_state.class_subjects.keys()))
        new_subject = st.text_input("New Subject Name (e.g., Robotics)")
        
        if st.button("Add Subject"):
            if new_subject:
                if new_subject not in st.session_state.class_subjects[target_class]:
                    st.session_state.class_subjects[target_class].append(new_subject)
                    st.success(f"Added {new_subject} to {target_class}")
                else:
                    st.warning("Subject already exists.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: CREATE TIMETABLE ---
with tab2:
    st.markdown("<div class='glass-container'><h3>Schedule an Exam</h3>", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        exam_date = st.date_input("Date")
    with c2:
        exam_class = st.selectbox("Class", list(st.session_state.class_subjects.keys()), key="tt_class")
    with c3:
        # Dynamic subjects based on class
        avail_subjects = st.session_state.class_subjects[exam_class]
        exam_subject = st.selectbox("Subject", avail_subjects, key="tt_subject")
    with c4:
        exam_slot = st.selectbox("Time Slot", ["Morning (Exam: 3rd-4th)", "Afternoon (Exam: 7th-8th)"])
    
    if st.button("Add to Timetable"):
        # Generate unique ID for this exam
        exam_id = f"{exam_date}_{exam_class}_{exam_slot}"
        
        # Determine Periods
        if "Morning" in exam_slot:
            rev_periods = "1st - 2nd"
            exam_periods = "3rd - 4th"
        else:
            rev_periods = "5th - 6th"
            exam_periods = "7th - 8th"
            
        entry = {
            "id": exam_id,
            "date": str(exam_date),
            "class": exam_class,
            "subject": exam_subject,
            "slot": exam_slot,
            "revision_time": rev_periods,
            "exam_time": exam_periods
        }
        st.session_state.timetable.append(entry)
        st.success("Exam Scheduled!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.timetable:
        st.markdown("#### Scheduled Exams")
        st.dataframe(pd.DataFrame(st.session_state.timetable).drop(columns=['id']), hide_index=True)

# --- TAB 3: ALLOCATIONS ---
with tab3:
    st.markdown("<div class='glass-container'><h3>Teacher Allocations</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.timetable:
        st.info("No exams scheduled yet. Go to the Timetable tab.")
    
    for i, exam in enumerate(st.session_state.timetable):
        eid = exam['id']
        
        # Initialize allocation state for this exam if not exists
        if eid not in st.session_state.allocations:
            # 1. Revision Teacher (Must be subject teacher)
            rev_teachers = find_teachers_by_subject(exam['subject'], "is")
            
            # 2. Invigilator (Must NOT be subject teacher)
            inv_pool = find_teachers_by_subject(exam['subject'], "not")
            random.shuffle(inv_pool) # Shuffle to randomize backups
            
            st.session_state.allocations[eid] = {
                "rev_teacher": rev_teachers[0] if rev_teachers else "None Available",
                "inv_list": inv_pool,
                "current_inv_idx": 0,
                "confirmed_inv": None
            }
            
        alloc_data = st.session_state.allocations[eid]
        
        # UI for this Exam
        with st.expander(f"{exam['date']} | {exam['class']} | {exam['subject']} ({exam['slot']})", expanded=True):
            col_rev, col_inv = st.columns(2)
            
            # --- Revision Section ---
            with col_rev:
                st.info(f"**Revision ({exam['revision_time']})**")
                st.write(f"**Teacher:** {alloc_data['rev_teacher']}")
                st.caption(f"*Rule: Must be {exam['subject']} teacher.*")
                
            # --- Invigilation Section ---
            with col_inv:
                st.warning(f"**Exam Invigilation ({exam['exam_time']})**")
                
                # Get current candidate from pool
                pool = alloc_data['inv_list']
                idx = alloc_data['current_inv_idx']
                
                if not pool:
                    st.error("No eligible teachers found (everyone teaches this subject!).")
                elif idx >= len(pool):
                    st.error("All backup teachers marked unavailable!")
                else:
                    current_candidate = pool[idx]
                    st.write(f"**Assigned Invigilator:** 🧑‍🏫 {current_candidate}")
                    st.caption(f"*Rule: Must NOT teach {exam['subject']}.*")
                    
                    # Availability Check
                    st.write("Is this teacher available?")
                    c1, c2 = st.columns(2)
                    
                    if c1.button("✅ Yes, Confirm", key=f"yes_{eid}_{idx}"):
                        alloc_data['confirmed_inv'] = current_candidate
                        st.rerun()
                        
                    if c2.button("❌ No, Next Backup", key=f"no_{eid}_{idx}"):
                        alloc_data['current_inv_idx'] += 1
                        st.rerun()
            
            # Final Status Bar
            if alloc_data.get('confirmed_inv'):
                st.success(f"**FINAL ASSIGNMENT LOCKED:** Revision: {alloc_data['rev_teacher']} | Exam: {alloc_data['confirmed_inv']}")
