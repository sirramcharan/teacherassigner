import streamlit as st
import pandas as pd
import random
import io
import json

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="Exam Manager", layout="wide")

# --- INITIALIZE SESSION STATE ---
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
        background: rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
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

    /* 4. TABS */
    button[data-baseweb="tab"] {
        color: #ffffff !important; 
        background-color: transparent !important;
        font-weight: 600 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        border-radius: 8px;
    }
    button[data-baseweb="tab"][aria-selected="true"] > div,
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* 5. INPUTS & DROPDOWNS (High Contrast) */
    .stTextInput input, .stDateInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 5px;
    }
    .stSelectbox div[data-baseweb="select"] > div, .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .stSelectbox div[data-baseweb="select"] div, .stMultiSelect div[data-baseweb="select"] div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
    }
    /* Dropdown Menu */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    li[data-baseweb="option"] {
        color: #000000 !important;
        background-color: #ffffff !important;
    }

    /* 6. BUTTONS */
    .stButton button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px;
    }
    
    /* 7. TABLES */
    div[data-testid="stDataFrame"] {
        background-color: rgba(255,255,255, 0.95);
        padding: 10px;
        border-radius: 10px;
        color: black !important;
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
    # Sort naturally if possible, otherwise alphabetical
    return sorted(list(st.session_state.class_subjects.keys()))

def find_teachers(subject, target_class, role_type):
    result = []
    for t in st.session_state.teachers:
        teaches_class = target_class in t['classes']
        teaches_subject = subject in t['subjects']

        if role_type == "revision":
            if teaches_subject and teaches_class:
                result.append(t['name'])
        elif role_type == "invigilator":
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
# 4. SIDEBAR: DATA BACKUP
# ==========================================
with st.sidebar:
    st.header("💾 Data Backup")
    st.info("Download your data as a JSON file to save it. Upload it later to restore everything.")
    
    # 1. Download
    current_data = {
        "teachers": st.session_state.teachers,
        "timetable": st.session_state.timetable,
        "allocations": st.session_state.allocations,
        "class_subjects": st.session_state.class_subjects
    }
    json_str = json.dumps(current_data, indent=4)
    st.download_button(
        label="⬇️ Download Backup (JSON)",
        data=json_str,
        file_name="school_data_backup.json",
        mime="application/json",
    )
    
    # 2. Upload
    st.markdown("---")
    uploaded_file = st.file_uploader("⬆️ Restore Data", type=["json"])
    if uploaded_file is not None:
        try:
            data = json.load(uploaded_file)
            st.session_state.teachers = data.get("teachers", [])
            st.session_state.timetable = data.get("timetable", [])
            st.session_state.allocations = data.get("allocations", {})
            st.session_state.class_subjects = data.get("class_subjects", st.session_state.class_subjects)
            st.success("Data Restored Successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error restoring data: {e}")

# ==========================================
# 5. MAIN APP
# ==========================================

st.markdown("<h1>🏫 Exam Manager</h1>", unsafe_allow_html=True)

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
            table_data = []
            for t in st.session_state.teachers:
                table_data.append({
                    "Name": t['name'],
                    "Subjects": ", ".join(t['subjects']),
                    "Classes": ", ".join(t['classes'])
                })
            df_teachers = pd.DataFrame(table_data)
            st.dataframe(df_teachers, use_container_width=True, hide_index=True)
            
            st.markdown("#### Remove Teacher")
            c1, c2 = st.columns([3, 1])
            with c1:
                t_to_del = st.selectbox("Select Teacher", [t['name'] for t in st.session_state.teachers], label_visibility="collapsed")
            with c2:
                if st.button("Delete"):
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
    st.markdown("<div class='glass-container'><h3>Add Subject to Multiple Classes</h3>", unsafe_allow_html=True)
    
    with st.form("add_subject_form", clear_on_submit=True):
        # CHANGED: Multi-select for classes
        target_classes = st.multiselect("Select Classes", get_all_classes())
        new_subject = st.text_input("New Subject Name (e.g., Robotics)")
        
        if st.form_submit_button("Add Subject"):
            if new_subject and target_classes:
                added_count = 0
                for cls in target_classes:
                    if new_subject not in st.session_state.class_subjects[cls]:
                        st.session_state.class_subjects[cls].append(new_subject)
                        added_count += 1
                
                if added_count > 0:
                    st.success(f"Added '{new_subject}' to {added_count} classes.")
                else:
                    st.warning("Subject already exists in selected classes.")
            else:
                st.error("Please select classes and enter a subject name.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: SCHEDULE ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Create Exam Schedule</h3>", unsafe_allow_html=True)
    
    # 1. ADDING EXAMS
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
        # CONFLICT CHECK
        conflict = False
        for ex in st.session_state.timetable:
            if ex['date'] == str(exam_date) and ex['class'] == exam_class and ex['slot'] == exam_slot:
                conflict = True
                break
        
        if conflict:
            st.error(f"⚠️ Conflict! {exam_class} already has an exam on {exam_date} in the {exam_slot} slot.")
        else:
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

    # 2. MANAGING (EDIT/DELETE) EXAMS
    if st.session_state.timetable:
        st.markdown("<div class='glass-container'><h3>Manage Scheduled Exams</h3>", unsafe_allow_html=True)
        # Sort by date for easier management
        sorted_exams = sorted(st.session_state.timetable, key=lambda x: (x['date'], x['class']))
        
        for idx, ex in enumerate(sorted_exams):
            with st.expander(f"{ex['date']} | {ex['class']} | {ex['subject']}"):
                col_a, col_b = st.columns([3, 1])
                
                # Edit Section
                with col_a:
                    st.write("**Edit Information:**")
                    new_sub = st.selectbox(f"Subject ({ex['id']})", st.session_state.class_subjects[ex['class']], index=st.session_state.class_subjects[ex['class']].index(ex['subject']) if ex['subject'] in st.session_state.class_subjects[ex['class']] else 0)
                    
                    if st.button("Update Info", key=f"upd_{ex['id']}"):
                        # Find original index in session state to update
                        real_idx = st.session_state.timetable.index(ex)
                        st.session_state.timetable[real_idx]['subject'] = new_sub
                        # Reset allocation for this exam as subject changed
                        if ex['id'] in st.session_state.allocations:
                            del st.session_state.allocations[ex['id']]
                        st.success("Updated! Allocations reset for this exam.")
                        st.rerun()

                # Delete Section
                with col_b:
                    st.write("**Actions:**")
                    if st.button("❌ Delete Exam", key=f"del_ex_{ex['id']}"):
                         # Find original index in session state to delete
                        real_idx = st.session_state.timetable.index(ex)
                        st.session_state.timetable.pop(real_idx)
                        if ex['id'] in st.session_state.allocations:
                            del st.session_state.allocations[ex['id']]
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: ALLOCATE ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>Teacher Allocation</h3></div>", unsafe_allow_html=True)
    if not st.session_state.timetable:
        st.info("No exams scheduled.")
    
    # Process allocations
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
            
            # --- REVISION ---
            with r_col:
                st.markdown(f"#### 📖 Revision ({exam['rev_p']})")
                if data['confirmed_rev']:
                    st.success(f"✅ Assigned: **{data['confirmed_rev']}**")
                    if st.button("🔄 Unassign", key=f"un_r_{eid}"):
                        data['confirmed_rev'] = None
                        st.rerun()
                else:
                    pool = data['rev_pool']
                    idx = data['rev_idx']
                    if not pool:
                        st.warning("No teacher found.")
                        c = st.selectbox("Substitute", get_all_teacher_names(), key=f"s_r_{eid}")
                        if st.button("Confirm", key=f"c_s_r_{eid}"):
                            data['confirmed_rev'] = c
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
                        c = st.selectbox("Manual", get_all_teacher_names(), key=f"m_r_{eid}")
                        if st.button("Confirm", key=f"m_c_r_{eid}"):
                            data['confirmed_rev'] = c
                            st.rerun()

            # --- INVIGILATION ---
            with i_col:
                st.markdown(f"#### 📝 Exam ({exam['exam_p']})")
                if data['confirmed_inv']:
                    st.success(f"✅ Assigned: **{data['confirmed_inv']}**")
                    if st.button("🔄 Unassign", key=f"un_i_{eid}"):
                        data['confirmed_inv'] = None
                        st.rerun()
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
                        c = st.selectbox("Manual", get_all_teacher_names(), key=f"m_i_{eid}")
                        if st.button("Confirm", key=f"c_m_i_{eid}"):
                            data['confirmed_inv'] = c
                            st.rerun()

# --- TAB 5: FINAL TIMETABLE ---
with tabs[4]:
    st.markdown("<div class='glass-container'><h3>🗓️ Final Timetable</h3></div>", unsafe_allow_html=True)
    if st.session_state.timetable:
        
        # Filter By Class
        all_classes_opt = ["All Classes"] + get_all_classes()
        filter_class = st.selectbox("Filter by Class:", all_classes_opt)
        
        rows = []
        for exam in st.session_state.timetable:
            if filter_class != "All Classes" and exam['class'] != filter_class:
                continue
                
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
        
        if rows:
            df = pd.DataFrame(rows)
            # SORTING: Date first, then Class
            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values(by=['Class', 'Date'])
            df['Date'] = df['Date'].dt.date # Convert back for display
            
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button("📥 Download Excel", convert_df_to_excel(df), "timetable.xlsx")
        else:
            st.info("No exams found for this filter.")
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
            
        df_stats = pd.DataFrame(list(stats.items()), columns=["Teacher Name", "Total Duties"])
        df_stats = df_stats.sort_values(by="Total Duties", ascending=False)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("#### Duties Table")
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
            
        with col2:
            st.markdown("#### Duties Graph")
            st.bar_chart(df_stats.set_index("Teacher Name"))
    else:
        st.warning("Add teachers first.")
