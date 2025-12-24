import streamlit as st
import pandas as pd
import random
import io

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="School Exam Manager", layout="wide")

# --- AUTO-FIX FOR DATA FORMAT ---
# Clears old data if structure changes to prevent crashes
if 'teachers' in st.session_state and st.session_state.teachers:
    if 'classes' not in st.session_state.teachers[0]: # New field check
        st.session_state.teachers = []
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.toast("⚠️ System updated: Teacher data structure changed. Old data cleared.", icon="🔄")

# Initialize Session State
if 'teachers' not in st.session_state:
    st.session_state.teachers = [] 

if 'timetable' not in st.session_state:
    st.session_state.timetable = []

if 'allocations' not in st.session_state:
    st.session_state.allocations = {} 

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
# 2. GLASS THEME CSS (IMPROVED VISIBILITY)
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .glass-container {
        background: rgba(255, 255, 255, 0.95); /* More opaque for better contrast */
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.18);
        padding: 20px;
        margin-bottom: 20px;
        color: #333; /* Dark text for readability */
    }
    h1, h2, h3, h4 {
        color: white !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    /* Button Styling - Bigger & Better Contrast */
    .stButton button {
        background-color: #ffffff !important;
        color: #764ba2 !important;
        font-weight: bold !important;
        border: 2px solid #764ba2 !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-size: 16px !important;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #764ba2 !important;
        color: white !important;
        transform: scale(1.02);
    }
    /* Table Styling */
    div[data-testid="stDataFrame"] {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
    p, label, span, div {
        color: #white;
    }
    /* Input field text color fix */
    .stTextInput input, .stSelectbox div, .stMultiSelect div {
        color: #333 !important;
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
    """
    Finds teachers based on Subject AND Class match.
    role_type="revision": Returns teachers who teach Subject X to Class Y.
    role_type="invigilator": Returns teachers who do NOT teach Subject X (regardless of class).
    """
    result = []
    for t in st.session_state.teachers:
        # Check if teacher handles the target class
        teaches_class = target_class in t['classes']
        # Check if teacher teaches the subject
        teaches_subject = subject in t['subjects']

        if role_type == "revision":
            # MUST teach this subject to this specific class
            if teaches_subject and teaches_class:
                result.append(t['name'])
        
        elif role_type == "invigilator":
            # MUST NOT teach this subject at all (to avoid conflict of interest)
            # Standard rule: Subject teacher shouldn't invigilate their own subject exam
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

# Tabs
tabs = st.tabs(["👨‍🏫 Teachers", "📚 Subjects", "📅 Schedule", "✅ Allocate", "🗓️ Final Matrix", "📊 Stats"])

# --- TAB 1: TEACHERS (Add/Delete) ---
with tabs[0]:
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("<div class='glass-container'><h3>Add Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Teacher Name")
        all_subs = get_all_subjects()
        t_subs = st.multiselect("Subjects Taught", all_subs)
        all_classes = get_all_classes()
        t_classes = st.multiselect("Classes Taught", all_classes)
        
        if st.button("Save Teacher", use_container_width=True):
            if t_name and t_subs and t_classes:
                st.session_state.teachers.append({
                    "name": t_name, 
                    "subjects": t_subs,
                    "classes": t_classes
                })
                st.success(f"Added {t_name}")
            else:
                st.error("Please fill in Name, Subjects, and Classes.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-container'><h3>Teacher List</h3>", unsafe_allow_html=True)
        if st.session_state.teachers:
            for idx, t in enumerate(st.session_state.teachers):
                with st.expander(f"{t['name']}"):
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
    target_class = st.selectbox("Select Class", get_all_classes())
    new_subject = st.text_input("New Subject Name")
    
    if st.button("Add Subject", use_container_width=True):
        if new_subject:
            if new_subject not in st.session_state.class_subjects[target_class]:
                st.session_state.class_subjects[target_class].append(new_subject)
                st.success(f"Added {new_subject} to {target_class}")
            else:
                st.warning("Subject exists.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: SCHEDULE ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Create Exam Schedule</h3>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1: exam_date = st.date_input("Date")
    with c2: exam_class = st.selectbox("Class", get_all_classes(), key="tt_class")
    with c3: exam_subject = st.selectbox("Subject", st.session_state.class_subjects[exam_class], key="tt_sub")
    with c4: exam_slot = st.selectbox("Slot", ["Morning (Exam: 3rd-4th)", "Afternoon (Exam: 7th-8th)"])
    
    if st.button("Add Exam", use_container_width=True):
        eid = f"{exam_date}_{exam_class}_{exam_slot}"
        rev_periods = "1st-2nd" if "Morning" in exam_slot else "5th-6th"
        exam_periods = "3rd-4th" if "Morning" in exam_slot else "7th-8th"
        
        st.session_state.timetable.append({
            "id": eid, "date": str(exam_date), "class": exam_class, 
            "subject": exam_subject, "slot": exam_slot,
            "rev_p": rev_periods, "exam_p": exam_periods
        })
        st.success("Scheduled!")
        
    if st.button("Reset All Data", type="primary"):
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: ALLOCATE ---
with tabs[3]:
    st.markdown("### 🟢 Allocate Teachers")
    if not st.session_state.timetable:
        st.info("No exams scheduled.")
    
    for exam in st.session_state.timetable:
        eid = exam['id']
        
        # Initialize Allocation Logic
        if eid not in st.session_state.allocations:
            # Revision: Specific Teacher for Subject AND Class
            rev_pool = find_teachers(exam['subject'], exam['class'], "revision")
            
            # Invigilation: Anyone NOT teaching that Subject
            inv_pool = find_teachers(exam['subject'], exam['class'], "invigilator")
            random.shuffle(inv_pool)
            
            st.session_state.allocations[eid] = {
                "rev_pool": rev_pool, "rev_idx": 0, "confirmed_rev": None,
                "inv_pool": inv_pool, "inv_idx": 0, "confirmed_inv": None
            }
            
        data = st.session_state.allocations[eid]
        
        with st.expander(f"{exam['date']} | {exam['class']} | {exam['subject']}", expanded=True):
            r_col, i_col = st.columns(2)
            
            # -- REVISION LOGIC --
            with r_col:
                st.markdown(f"#### Revision ({exam['rev_p']})")
                if data['confirmed_rev']:
                    st.success(f"✅ Assigned: **{data['confirmed_rev']}**")
                else:
                    pool = data['rev_pool']
                    idx = data['rev_idx']
                    
                    if not pool:
                        st.warning("No teacher found for this Class & Subject.")
                        candidate = st.selectbox("Select Substitute", get_all_teacher_names(), key=f"sub_rev_{eid}")
                        if st.button("Confirm Substitute", key=f"conf_sub_rev_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()
                    elif idx < len(pool):
                        candidate = pool[idx]
                        st.info(f"Candidate: **{candidate}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Available", key=f"rev_y_{eid}_{idx}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()
                        if c2.button("❌ Not Available", key=f"rev_n_{eid}_{idx}"):
                            data['rev_idx'] += 1
                            st.rerun()
                    else:
                        st.error("All assigned teachers unavailable.")
                        candidate = st.selectbox("Select Substitute", get_all_teacher_names(), key=f"sub_rev_man_{eid}")
                        if st.button("Confirm Manually", key=f"conf_man_rev_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()

            # -- INVIGILATION LOGIC --
            with i_col:
                st.markdown(f"#### Exam ({exam['exam_p']})")
                if data['confirmed_inv']:
                    st.success(f"✅ Assigned: **{data['confirmed_inv']}**")
                else:
                    pool = data['inv_pool']
                    idx = data['inv_idx']
                    
                    if idx < len(pool):
                        candidate = pool[idx]
                        st.info(f"Backup: **{candidate}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Available", key=f"inv_y_{eid}_{idx}"):
                            data['confirmed_inv'] = candidate
                            st.rerun()
                        if c2.button("❌ Not Available", key=f"inv_n_{eid}_{idx}"):
                            data['inv_idx'] += 1
                            st.rerun()
                    else:
                        st.error("No backup teachers left.")
                        candidate = st.selectbox("Select Manually", get_all_teacher_names(), key=f"man_inv_{eid}")
                        if st.button("Confirm", key=f"conf_man_inv_{eid}"):
                            data['confirmed_inv'] = candidate
                            st.rerun()

# --- TAB 5: FINAL TIMETABLE MATRIX ---
with tabs[4]:
    st.markdown("<div class='glass-container'><h3>🗓️ Final Timetable Matrix</h3></div>", unsafe_allow_html=True)
    
    if st.session_state.timetable:
        matrix_data = []
        for exam in st.session_state.timetable:
            eid = exam['id']
            alloc = st.session_state.allocations.get(eid, {})
            
            rev_teacher = alloc.get('confirmed_rev', 'Pending')
            inv_teacher = alloc.get('confirmed_inv', 'Pending')
            
            row = {
                "Date": exam['date'],
                "Class": exam['class'],
                "Subject": exam['subject'],
                "1st-2nd (Rev)": "---",
                "3rd-4th (Exam/Rev)": "---",
                "5th-6th (Rev)": "---",
                "7th-8th (Exam)": "---"
            }
            
            if "Morning" in exam['slot']:
                row["1st-2nd (Rev)"] = rev_teacher
                row["3rd-4th (Exam/Rev)"] = f"EXAM (Inv: {inv_teacher})"
            else:
                row["5th-6th (Rev)"] = rev_teacher
                row["7th-8th (Exam)"] = f"EXAM (Inv: {inv_teacher})"
            
            matrix_data.append(row)
        
        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)
        
        # DOWNLOAD BUTTON
        excel_data = convert_df_to_excel(df_matrix)
        st.download_button(
            label="📥 Download Timetable as Excel",
            data=excel_data,
            file_name='exam_timetable.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )

    else:
        st.info("No data available.")

# --- TAB 6: TEACHER STATS ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>📊 Teacher Workload</h3></div>", unsafe_allow_html=True)
    
    if st.session_state.teachers:
        stats = {}
        all_teachers = get_all_teacher_names()
        for t in all_teachers:
            stats[t] = 0
            
        for alloc in st.session_state.allocations.values():
            inv = alloc.get('confirmed_inv')
            if inv and inv in stats:
                stats[inv] += 1
            rev = alloc.get('confirmed_rev')
            if rev and rev in stats:
                stats[rev] += 1
                
        stats_df = pd.DataFrame(list(stats.items()), columns=["Teacher Name", "Total Duties"])
        stats_df = stats_df.sort_values(by="Total Duties", ascending=False)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(stats_df, use_container_width=True, hide_index=True)
            
        with col2:
            st.markdown("#### Workload Graph")
            st.bar_chart(stats_df.set_index("Teacher Name"))
            
    else:
        st.warning("Add teachers first.")
