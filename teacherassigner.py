import streamlit as st
import pandas as pd
import random
import io
import json
import os
from datetime import timedelta, datetime

# ==========================================
# 1. CONFIGURATION & STATE
# ==========================================
st.set_page_config(page_title="Exam Manager", layout="wide")
DATA_FILE = "school_data_v6.json"

# --- PERSISTENCE FUNCTIONS ---
def save_to_disk():
    """Saves current session state to a local JSON file."""
    data = {
        "teachers": st.session_state.teachers,
        "timetable": st.session_state.timetable,
        "allocations": st.session_state.allocations,
        "class_subjects": st.session_state.class_subjects
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

def load_from_disk():
    """Loads data from local JSON file if it exists."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                st.session_state.teachers = data.get("teachers", [])
                st.session_state.timetable = data.get("timetable", [])
                st.session_state.allocations = data.get("allocations", {})
                
                # Merge saved subjects
                saved_subs = data.get("class_subjects", {})
                st.session_state.class_subjects = get_default_subjects()
                st.session_state.class_subjects.update(saved_subs)
        except Exception as e:
            pass

def get_default_subjects():
    base = {
        "Class 1": ["EVS", "English", "Telugu", "EHV", "Maths"],
        "Class 2": ["EVS", "English", "Telugu", "EHV", "Maths"],
    }
    for i in range(3, 11):
        cls_name = f"Class {i}"
        subs = ["EVS", "English", "Telugu", "EHV", "Maths", "Hindi", "Science", "Social"]
        if i >= 5: subs.append("Computer")
        if i >= 9: subs.insert(0, "AI")
        base[cls_name] = subs
        
    groups = ["MPC", "BPC", "CAE"]
    common = ["English", "Telugu", "EHV"]
    spec = {
        "MPC": ["Maths", "Physics", "Chemistry"],
        "BPC": ["Biology", "Physics", "Chemistry"],
        "CAE": ["Business Studies", "Accounts", "Economics"]
    }
    for i in [11, 12]:
        for g in groups:
            base[f"Class {i} ({g})"] = common + spec[g]
    return base

# --- INITIALIZATION ---
if 'teachers' not in st.session_state:
    st.session_state.teachers = []
    st.session_state.timetable = []
    st.session_state.allocations = {}
    st.session_state.class_subjects = get_default_subjects()
    load_from_disk()

if 'temp_teacher_mappings' not in st.session_state:
    st.session_state.temp_teacher_mappings = []

# ==========================================
# 2. UI CSS
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

    /* 5. INPUTS & DROPDOWNS */
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
# 3. HELPER FUNCTIONS & LOGIC
# ==========================================
def get_all_teacher_names():
    return [t['name'] for t in st.session_state.teachers]

def get_ordered_classes():
    keys = list(st.session_state.class_subjects.keys())
    def sort_key(x):
        if "Class" in x:
            parts = x.replace("Class ", "").split(" ")
            try:
                num = int(parts[0])
                suffix = parts[1] if len(parts) > 1 else ""
                return num, suffix
            except:
                return 99, x
        return 99, x
    return sorted(keys, key=sort_key)

ORDERED_CLASSES = get_ordered_classes()

def get_neighbor_classes(target_class):
    if target_class not in ORDERED_CLASSES: return []
    idx = ORDERED_CLASSES.index(target_class)
    neighbors = []
    if idx > 0: neighbors.append(ORDERED_CLASSES[idx - 1])
    if idx < len(ORDERED_CLASSES) - 1: neighbors.append(ORDERED_CLASSES[idx + 1])
    return neighbors

def find_smart_invigilators(exam_class, exam_subject):
    primary_pool = []
    backup_pool = []
    
    for t in st.session_state.teachers:
        name = t['name']
        mappings = t.get('mappings', [])
        
        teaches_class = any(m['class'] == exam_class for m in mappings)
        teaches_subject = any(m['subject'] == exam_subject for m in mappings)
        
        if teaches_subject: continue 
            
        if teaches_class:
            primary_pool.append(name)
        else:
            neighbors = get_neighbor_classes(exam_class)
            if any(m['class'] in neighbors for m in mappings):
                backup_pool.append(name)
    
    random.shuffle(primary_pool)
    random.shuffle(backup_pool)
    return primary_pool + backup_pool

def get_subject_teacher(exam_class, exam_subject):
    cands = []
    for t in st.session_state.teachers:
        for m in t.get('mappings', []):
            if m['class'] == exam_class and m['subject'] == exam_subject:
                cands.append(t['name'])
    return cands[0] if cands else "Unassigned"

def auto_assign_exam(eid, cls, sub):
    rev_teacher = get_subject_teacher(cls, sub)
    inv_options = find_smart_invigilators(cls, sub)
    inv_teacher = inv_options[0] if inv_options else "Unassigned"
    
    st.session_state.allocations[eid] = {
        "rev_teacher": rev_teacher,
        "inv_teacher": inv_teacher,
        "backup_invs": inv_options
    }

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1')
    return output.getvalue()

def get_all_subjects_unique():
    s = set()
    for v in st.session_state.class_subjects.values(): s.update(v)
    return sorted(list(s))

# ==========================================
# 4. SIDEBAR: DATA BACKUP
# ==========================================
with st.sidebar:
    st.header("💾 Data Manager")
    
    current_data = {
        "teachers": st.session_state.teachers,
        "timetable": st.session_state.timetable,
        "allocations": st.session_state.allocations,
        "class_subjects": st.session_state.class_subjects
    }
    json_str = json.dumps(current_data, indent=4, default=str)
    st.download_button(
        label="⬇️ Download Backup",
        data=json_str,
        file_name="school_data_backup.json",
        mime="application/json",
    )
    
    st.markdown("---")
    uploaded_file = st.file_uploader("⬆️ Restore Data", type=["json"])
    if uploaded_file is not None:
        if st.button("Confirm Restore"):
            try:
                data = json.load(uploaded_file)
                st.session_state.teachers = data.get("teachers", [])
                st.session_state.timetable = data.get("timetable", [])
                st.session_state.allocations = data.get("allocations", {})
                st.session_state.class_subjects = data.get("class_subjects", get_default_subjects())
                save_to_disk() 
                st.success("Data Restored! Reloading...")
                st.rerun()
            except Exception as e:
                st.error(f"Error restoring: {e}")

# ==========================================
# 5. MAIN APP
# ==========================================

st.markdown("<h1>🏫 Exam & Invigilation Manager</h1>", unsafe_allow_html=True)

tabs = st.tabs(["👨‍🏫 Teachers", "📅 Schedule", "✅ Allocation", "🗓️ Matrix Timetable", "📊 Stats", "📚 Subjects"])

# --- TAB 1: TEACHERS ---
with tabs[0]:
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<div class='glass-container'><h3>Add Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Teacher Name")
        
        st.markdown("##### Assign Subjects")
        m_sub = st.selectbox("Subject", get_all_subjects_unique())
        m_classes = st.multiselect("Select Classes Taught", ORDERED_CLASSES)
        
        if st.button("Add Mapping"):
            if m_sub and m_classes:
                for c in m_classes:
                    st.session_state.temp_teacher_mappings.append({"class": c, "subject": m_sub})
            else:
                st.error("Select subject and at least one class.")
            
        if st.session_state.temp_teacher_mappings:
            st.write("**Pending Assignments:**")
            st.dataframe(pd.DataFrame(st.session_state.temp_teacher_mappings), height=150)
                
        if st.button("💾 Save Teacher", type="primary"):
            if t_name and st.session_state.temp_teacher_mappings:
                st.session_state.teachers.append({
                    "name": t_name,
                    "mappings": st.session_state.temp_teacher_mappings
                })
                st.session_state.temp_teacher_mappings = []
                save_to_disk()
                st.success(f"Saved {t_name}")
                st.rerun()
            else:
                st.error("Name and mappings required.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='glass-container'><h3>Teacher Directory</h3>", unsafe_allow_html=True)
        if st.session_state.teachers:
            rows = []
            for i, t in enumerate(st.session_state.teachers):
                map_txt = ", ".join([f"{m['subject']} ({m['class']})" for m in t.get('mappings', [])])
                rows.append({"Name": t['name'], "Subjects & Classes": map_txt})
            
            df_t = pd.DataFrame(rows)
            st.dataframe(df_t, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col_del_1, col_del_2 = st.columns([3, 1])
            with col_del_1:
                del_name = st.selectbox("Select Teacher to Delete", [t['name'] for t in st.session_state.teachers])
            with col_del_2:
                if st.button("Delete Teacher"):
                    for i, t in enumerate(st.session_state.teachers):
                        if t['name'] == del_name:
                            st.session_state.teachers.pop(i)
                            save_to_disk()
                            st.rerun()
                            break
        else:
            st.info("No teachers added.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SCHEDULE ---
with tabs[1]:
    st.markdown("<div class='glass-container'><h3>Auto-Scheduler</h3>", unsafe_allow_html=True)
    
    with st.form("auto_sched"):
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Start Date")
        with c2:
            exam_type = st.radio("Exam Type", ["Unit Test (2/day)", "Terminal Exam (1/day)"])
            
        if st.form_submit_button("🚀 Generate Schedule & Assign Teachers"):
            st.session_state.timetable = [] 
            st.session_state.allocations = {} 
            
            curr_date = start_date
            max_subs = max([len(v) for v in st.session_state.class_subjects.values()])
            
            slots_per_day = 2 if "Unit" in exam_type else 1
            sub_idx = 0
            
            while sub_idx < max_subs:
                while curr_date.weekday() == 6:
                    curr_date += timedelta(days=1)
                
                # SLOT 1
                if sub_idx < max_subs:
                    for cls in ORDERED_CLASSES:
                        subs = st.session_state.class_subjects[cls]
                        if sub_idx < len(subs):
                            s1 = subs[sub_idx]
                            eid = f"{curr_date}_{cls}_Morning"
                            st.session_state.timetable.append({
                                "id": eid, "date": str(curr_date), "class": cls,
                                "subject": s1, "slot": "Morning", 
                                "rev_p": "1st-2nd", "exam_p": "3rd-4th"
                            })
                            auto_assign_exam(eid, cls, s1)
                
                # SLOT 2
                if slots_per_day == 2 and (sub_idx + 1) < max_subs:
                    for cls in ORDERED_CLASSES:
                        subs = st.session_state.class_subjects[cls]
                        if (sub_idx + 1) < len(subs):
                            s2 = subs[sub_idx + 1]
                            eid = f"{curr_date}_{cls}_Afternoon"
                            st.session_state.timetable.append({
                                "id": eid, "date": str(curr_date), "class": cls,
                                "subject": s2, "slot": "Afternoon",
                                "rev_p": "5th-6th", "exam_p": "7th-8th"
                            })
                            auto_assign_exam(eid, cls, s2)
                            
                sub_idx += slots_per_day
                curr_date += timedelta(days=1)
                
            save_to_disk()
            st.success("Schedule Generated & Teachers Assigned!")
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: ALLOCATION (Date Filter + Table + Edit) ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Allocations</h3>", unsafe_allow_html=True)
    
    if not st.session_state.timetable:
        st.info("No schedule found.")
    else:
        # 1. DATE FILTER
        all_dates = sorted(list(set(ex['date'] for ex in st.session_state.timetable)))
        selected_date = st.selectbox("📅 Select Date", all_dates)
        
        # Filter exams for this date
        day_exams = [ex for ex in st.session_state.timetable if ex['date'] == selected_date]
        
        # 2. TABLE VIEW
        st.markdown("#### Overview")
        table_data = []
        for ex in day_exams:
            eid = ex['id']
            alloc = st.session_state.allocations.get(eid, {})
            table_data.append({
                "Class": ex['class'],
                "Exam": f"{ex['subject']} ({ex['slot']})",
                "Revision Teacher": alloc.get('rev_teacher', 'Unassigned'),
                "Invigilator": alloc.get('inv_teacher', 'Unassigned')
            })
        
        df_alloc = pd.DataFrame(table_data)
        # Sort by Class
        if not df_alloc.empty:
            df_alloc['Class'] = pd.Categorical(df_alloc['Class'], categories=ORDERED_CLASSES, ordered=True)
            df_alloc = df_alloc.sort_values('Class')
            st.dataframe(df_alloc, use_container_width=True, hide_index=True)
        
        # 3. EDIT SECTION
        st.markdown("---")
        st.markdown("#### ✏️ Edit Allocation")
        
        # Create friendly labels for dropdown
        exam_opts = {f"{ex['class']} - {ex['subject']} ({ex['slot']})": ex for ex in day_exams}
        
        if exam_opts:
            selected_label = st.selectbox("Select Exam to Edit", list(exam_opts.keys()))
            target_ex = exam_opts[selected_label]
            eid = target_ex['id']
            alloc = st.session_state.allocations.get(eid, {})
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.info(f"**Current Revision:** {alloc.get('rev_teacher')}")
                all_t = get_all_teacher_names()
                new_rev = st.selectbox("Change Revision To", [alloc.get('rev_teacher')] + all_t, key="nr")
                
            with c2:
                st.success(f"**Current Invigilator:** {alloc.get('inv_teacher')}")
                backups = alloc.get('backup_invs', [])
                # Prioritize backups in dropdown
                inv_opts = [alloc.get('inv_teacher')] + backups + [t for t in all_t if t not in backups]
                # Remove duplicates/None
                inv_opts = [x for x in list(dict.fromkeys(inv_opts)) if x]
                
                new_inv = st.selectbox("Change Invigilator To", inv_opts, key="ni")
                
            with c3:
                st.write("") 
                st.write("") 
                if st.button("💾 Update Allocation", type="primary"):
                    st.session_state.allocations[eid]['rev_teacher'] = new_rev
                    st.session_state.allocations[eid]['inv_teacher'] = new_inv
                    save_to_disk()
                    st.rerun()
        else:
            st.info("No exams for this date.")
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: MATRIX VIEW ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>🗓️ Timetable Matrix</h3>", unsafe_allow_html=True)
    st.caption("Rows = Dates | Columns = Classes")
    
    if st.session_state.timetable:
        data = {} 
        for ex in st.session_state.timetable:
            d = ex['date']
            c = ex['class']
            s = ex['subject']
            slot_code = "(M)" if "Morning" in ex['slot'] else "(A)"
            
            if d not in data: data[d] = {}
            if c in data[d]:
                data[d][c] += f"\n{s} {slot_code}"
            else:
                data[d][c] = f"{s} {slot_code}"
                
        matrix_df = pd.DataFrame.from_dict(data, orient='index')
        cols = [c for c in ORDERED_CLASSES if c in matrix_df.columns]
        matrix_df = matrix_df[cols]
        matrix_df.index.name = "Date"
        matrix_df.sort_index(inplace=True)
        
        st.dataframe(matrix_df, use_container_width=True)
        st.download_button("📥 Download Excel", convert_df_to_excel(matrix_df), "matrix_timetable.xlsx")
    else:
        st.info("No schedule available.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 5: STATS ---
with tabs[4]:
    st.markdown("<div class='glass-container'><h3>Stats</h3></div>", unsafe_allow_html=True)
    if st.session_state.allocations:
        counts = {t['name']: 0 for t in st.session_state.teachers}
        for a in st.session_state.allocations.values():
            inv = a.get('inv_teacher')
            if inv and inv in counts:
                counts[inv] += 1
                
        df_s = pd.DataFrame(list(counts.items()), columns=["Teacher", "Invigilations"])
        df_s = df_s.sort_values("Invigilations", ascending=False)
        
        c1, c2 = st.columns([1, 2])
        with c1: st.dataframe(df_s, hide_index=True)
        with c2: st.bar_chart(df_s.set_index("Teacher"))

# --- TAB 6: SUBJECTS ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>Manage Subjects</h3>", unsafe_allow_html=True)
    with st.form("sub_form"):
        target_classes = st.multiselect("Select Classes", ORDERED_CLASSES)
        new_sub = st.text_input("New Subject Name")
        if st.form_submit_button("Add Subject"):
            if new_sub and target_classes:
                count = 0
                for c in target_classes:
                    if new_sub not in st.session_state.class_subjects[c]:
                        st.session_state.class_subjects[c].append(new_sub)
                        count += 1
                if count > 0:
                    save_to_disk()
                    st.success(f"Added to {count} classes.")
    st.markdown("</div>", unsafe_allow_html=True)
