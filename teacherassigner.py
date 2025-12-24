import streamlit as st
import pandas as pd
import random

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="School Exam Manager", layout="wide")

# --- AUTO-FIX FOR DATA FORMAT ---
# This block checks if your browser is holding onto old data formats
# and clears them to prevent the KeyError.
if 'timetable' in st.session_state and st.session_state.timetable:
    # Check if the first entry is missing the new key 'rev_p'
    if 'rev_p' not in st.session_state.timetable[0]:
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.toast("⚠️ System updated: Old data format cleared.", icon="🔄")
# --------------------------------

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
# 2. GLASS THEME CSS
# ==========================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
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
    h1, h2, h3, h4, p, label, span {
        color: white !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .stDataFrame {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 10px;
        padding: 10px;
    }
    /* Fix for tabs text color */
    button[data-baseweb="tab"] {
        color: white !important;
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
    result = []
    for t in st.session_state.teachers:
        if match_type == "is":
            if subject in t['subjects']:
                result.append(t['name'])
        else:
            if subject not in t['subjects']:
                result.append(t['name'])
    return result

def get_all_teacher_names():
    return [t['name'] for t in st.session_state.teachers]

# ==========================================
# 4. APP LAYOUT
# ==========================================

st.markdown("<div class='glass-container'><h1>🏫 Exam Manager</h1></div>", unsafe_allow_html=True)

# Tabs
tabs = st.tabs(["👨‍🏫 Teachers", "📚 Subjects", "📅 Schedule", "✅ Allocate", "🗓️ Final Matrix", "📊 Stats"])

# --- TAB 1: TEACHERS (Add/Delete) ---
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("<div class='glass-container'><h3>Add Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Name")
        all_subs = get_all_subjects()
        t_subs = st.multiselect("Subjects", all_subs)
        if st.button("Save Teacher"):
            if t_name and t_subs:
                st.session_state.teachers.append({"name": t_name, "subjects": t_subs})
                st.success(f"Added {t_name}")
            else:
                st.error("Enter name and subjects.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='glass-container'><h3>Teacher List</h3>", unsafe_allow_html=True)
        if st.session_state.teachers:
            for idx, t in enumerate(st.session_state.teachers):
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{t['name']}** - {', '.join(t['subjects'])}")
                if c2.button("Delete", key=f"del_{idx}"):
                    st.session_state.teachers.pop(idx)
                    st.rerun()
        else:
            st.info("No teachers added yet.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SUBJECTS ---
with tabs[1]:
    st.markdown("<div class='glass-container'><h3>Add Subject to Class</h3>", unsafe_allow_html=True)
    target_class = st.selectbox("Select Class", list(st.session_state.class_subjects.keys()))
    new_subject = st.text_input("New Subject Name")
    
    if st.button("Add Subject"):
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
    with c2: exam_class = st.selectbox("Class", list(st.session_state.class_subjects.keys()), key="tt_class")
    with c3: exam_subject = st.selectbox("Subject", st.session_state.class_subjects[exam_class], key="tt_sub")
    with c4: exam_slot = st.selectbox("Slot", ["Morning (Exam: 3rd-4th)", "Afternoon (Exam: 7th-8th)"])
    
    if st.button("Add to Timetable"):
        eid = f"{exam_date}_{exam_class}_{exam_slot}"
        rev_periods = "1st-2nd" if "Morning" in exam_slot else "5th-6th"
        exam_periods = "3rd-4th" if "Morning" in exam_slot else "7th-8th"
        
        st.session_state.timetable.append({
            "id": eid, "date": str(exam_date), "class": exam_class, 
            "subject": exam_subject, "slot": exam_slot,
            "rev_p": rev_periods, "exam_p": exam_periods
        })
        st.success("Scheduled!")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("Reset All Data (Clear Cache)"):
        st.session_state.timetable = []
        st.session_state.allocations = {}
        st.rerun()

# --- TAB 4: ALLOCATE ---
with tabs[3]:
    st.markdown("### 🟢 Allocate Teachers")
    if not st.session_state.timetable:
        st.info("No exams scheduled.")
    
    for exam in st.session_state.timetable:
        eid = exam['id']
        
        # Initialize Allocation Logic
        if eid not in st.session_state.allocations:
            # Revision: Subject teachers first
            rev_pool = find_teachers_by_subject(exam['subject'], "is")
            # Invigilation: Non-subject teachers
            inv_pool = find_teachers_by_subject(exam['subject'], "not")
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
                st.info(f"**Revision ({exam['rev_p']})**")
                if data['confirmed_rev']:
                    st.success(f"✅ Assigned: {data['confirmed_rev']}")
                else:
                    pool = data['rev_pool']
                    idx = data['rev_idx']
                    
                    if not pool:
                        st.warning("No subject teacher found.")
                        candidate = st.selectbox("Select Substitute", get_all_teacher_names(), key=f"sub_rev_{eid}")
                        if st.button("Confirm Substitute", key=f"conf_sub_rev_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()
                    elif idx < len(pool):
                        candidate = pool[idx]
                        st.write(f"Candidate: **{candidate}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Avail", key=f"rev_y_{eid}_{idx}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()
                        if c2.button("❌ No", key=f"rev_n_{eid}_{idx}"):
                            data['rev_idx'] += 1
                            st.rerun()
                    else:
                        st.error("All subject teachers unavailable.")
                        candidate = st.selectbox("Select Substitute", get_all_teacher_names(), key=f"sub_rev_man_{eid}")
                        if st.button("Confirm Manually", key=f"conf_man_rev_{eid}"):
                            data['confirmed_rev'] = candidate
                            st.rerun()

            # -- INVIGILATION LOGIC --
            with i_col:
                st.warning(f"**Exam ({exam['exam_p']})**")
                if data['confirmed_inv']:
                    st.success(f"✅ Assigned: {data['confirmed_inv']}")
                else:
                    pool = data['inv_pool']
                    idx = data['inv_idx']
                    
                    if idx < len(pool):
                        candidate = pool[idx]
                        st.write(f"Candidate: **{candidate}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Avail", key=f"inv_y_{eid}_{idx}"):
                            data['confirmed_inv'] = candidate
                            st.rerun()
                        if c2.button("❌ No", key=f"inv_n_{eid}_{idx}"):
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
            
            # Get names or status
            rev_teacher = alloc.get('confirmed_rev', '❓ Pending')
            inv_teacher = alloc.get('confirmed_inv', '❓ Pending')
            
            # Build Row
            row = {
                "Date": exam['date'],
                "Class": exam['class'] + f" ({exam['subject']})",
                "1st-2nd": "---",
                "3rd-4th": "---",
                "5th-6th": "---",
                "7th-8th": "---"
            }
            
            if "Morning" in exam['slot']:
                row["1st-2nd"] = f"Rev: {rev_teacher}"
                row["3rd-4th"] = f"Inv: {inv_teacher}"
            else:
                row["5th-6th"] = f"Rev: {rev_teacher}"
                row["7th-8th"] = f"Inv: {inv_teacher}"
            
            matrix_data.append(row)
        
        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix, use_container_width=True, hide_index=True)
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
            # Count Invigilation
            inv = alloc.get('confirmed_inv')
            if inv and inv in stats:
                stats[inv] += 1
            # Count Revision (Optional - remove if not needed)
            rev = alloc.get('confirmed_rev')
            if rev and rev in stats:
                stats[rev] += 1
                
        stats_df = pd.DataFrame(list(stats.items()), columns=["Teacher Name", "Total Duties Assigned"])
        stats_df = stats_df.sort_values(by="Total Duties Assigned", ascending=False)
        
        st.dataframe(stats_df, use_container_width=True, hide_index=True)
    else:
        st.warning("Add teachers first.")
