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
DATA_FILE = "school_data_v4.json"

# --- PERSISTENCE FUNCTIONS ---
def save_to_disk():
    data = {
        "teachers": st.session_state.teachers,
        "timetable": st.session_state.timetable,
        "allocations": st.session_state.allocations,
        "class_subjects": st.session_state.class_subjects
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, default=str)

def load_from_disk():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                st.session_state.teachers = data.get("teachers", [])
                st.session_state.timetable = data.get("timetable", [])
                st.session_state.allocations = data.get("allocations", {})
                
                saved_subs = data.get("class_subjects", {})
                st.session_state.class_subjects = get_default_subjects()
                st.session_state.class_subjects.update(saved_subs)
        except:
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
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); font-family: 'Segoe UI', sans-serif; }
    .glass-container { background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; margin-bottom: 20px; }
    h1, h2, h3, h4 { color: #ffffff !important; }
    p, label, span, div { color: #ffffff !important; }
    
    .stTextInput input, .stDateInput input, .stSelectbox div, .stMultiSelect div {
        background-color: #ffffff !important; color: #000000 !important;
    }
    .stSelectbox div[data-baseweb="select"] div { color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    li[data-baseweb="option"] { color: #000000 !important; background-color: #fff !important; }
    
    button[data-baseweb="tab"][aria-selected="true"] { background-color: #ffffff !important; }
    button[data-baseweb="tab"][aria-selected="true"] p { color: #000000 !important; }
    
    div[data-testid="stDataFrame"] { background-color: rgba(255,255,255, 0.95); padding: 10px; border-radius: 10px; color: black !important; }
    .stButton button { background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); color: black; font-weight: bold; border: none; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. LOGIC FUNCTIONS
# ==========================================
def get_ordered_classes():
    keys = list(st.session_state.class_subjects.keys())
    def sort_key(x):
        if "Class" in x:
            parts = x.replace("Class ", "").split(" ")
            try:
                num = int(parts[0])
                suffix = parts[1] if len(parts) > 1 else ""
                return num, suffix
            except: return 99, x
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
    primary_pool = [] # Same class, diff subject
    backup_pool = []  # Neighbor class
    
    for t in st.session_state.teachers:
        mappings = t.get('mappings', [])
        teaches_class = any(m['class'] == exam_class for m in mappings)
        teaches_subject = any(m['subject'] == exam_subject for m in mappings)
        
        if teaches_subject: continue # Conflict
        
        if teaches_class:
            primary_pool.append(t['name'])
        else:
            neighbors = get_neighbor_classes(exam_class)
            if any(m['class'] in neighbors for m in mappings):
                backup_pool.append(t['name'])
                
    random.shuffle(primary_pool)
    random.shuffle(backup_pool)
    return primary_pool + backup_pool # Primary first, then backup

def get_subject_teacher(exam_class, exam_subject):
    cands = []
    for t in st.session_state.teachers:
        for m in t.get('mappings', []):
            if m['class'] == exam_class and m['subject'] == exam_subject:
                cands.append(t['name'])
    return cands[0] if cands else "Not Found"

def auto_assign_allocation(eid, cls, sub):
    # Only assign if not already assigned
    if eid not in st.session_state.allocations:
        rev = get_subject_teacher(cls, sub)
        inv_list = find_smart_invigilators(cls, sub)
        inv = inv_list[0] if inv_list else "No Invigilator"
        
        st.session_state.allocations[eid] = {
            "rev_teacher": rev,
            "inv_teacher": inv,
            "inv_backups": inv_list # Store list for editing later
        }

def get_all_subjects_unique():
    s = set()
    for v in st.session_state.class_subjects.values(): s.update(v)
    return sorted(list(s))

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='Sheet1') # Index=True for Date column
    return output.getvalue()

# ==========================================
# 4. APP UI
# ==========================================

st.markdown("<h1>🏫 Exam & Invigilation Manager</h1>", unsafe_allow_html=True)
tabs = st.tabs(["👨‍🏫 Teachers", "📅 Schedule", "✅ Allocation", "🗓️ Matrix View", "📊 Stats", "📚 Subjects"])

# --- TAB 1: TEACHERS ---
with tabs[0]:
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<div class='glass-container'><h3>Add Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Teacher Name")
        
        st.markdown("##### Assign Subjects to Classes")
        # Multi-select Classes for one subject
        m_sub = st.selectbox("Subject", get_all_subjects_unique())
        m_classes = st.multiselect("Select Classes", ORDERED_CLASSES)
        
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
            # Flatten for DataFrame
            rows = []
            for i, t in enumerate(st.session_state.teachers):
                # Create a concise string of mappings
                map_txt = ", ".join([f"{m['subject']} ({m['class']})" for m in t.get('mappings', [])])
                rows.append({"Name": t['name'], "Subjects & Classes": map_txt})
            
            df_t = pd.DataFrame(rows)
            st.dataframe(df_t, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            col_del_1, col_del_2 = st.columns([3, 1])
            with col_del_1:
                del_name = st.selectbox("Select Teacher to Delete", [t['name'] for t in st.session_state.teachers])
            with col_del_2:
                if st.button("Delete"):
                    # Find and remove
                    for i, t in enumerate(st.session_state.teachers):
                        if t['name'] == del_name:
                            st.session_state.teachers.pop(i)
                            save_to_disk()
                            st.rerun()
                            break
        else:
            st.info("No teachers added.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SCHEDULE (Auto-Scheduler) ---
with tabs[1]:
    st.markdown("<div class='glass-container'><h3>Auto-Scheduler</h3>", unsafe_allow_html=True)
    
    with st.form("auto_sched"):
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Start Date")
        with c2:
            exam_type = st.radio("Exam Type", ["Unit Test (2/day)", "Terminal Exam (1/day)"])
            
        if st.form_submit_button("🚀 Generate Schedule"):
            st.session_state.timetable = [] # Reset
            st.session_state.allocations = {} # Reset allocations
            
            curr_date = start_date
            # Determine max subjects to schedule
            max_subs = max([len(v) for v in st.session_state.class_subjects.values()])
            
            slots_per_day = 2 if "Unit" in exam_type else 1
            
            # Logic to iterate days
            subjects_scheduled_count = 0
            while subjects_scheduled_count < max_subs:
                # Skip Sundays
                while curr_date.weekday() == 6: # 6 = Sunday
                    curr_date += timedelta(days=1)
                
                # Schedule for this day
                for cls in ORDERED_CLASSES:
                    subs = st.session_state.class_subjects[cls]
                    
                    # Morning Slot
                    if subjects_scheduled_count < len(subs):
                        s1 = subs[subjects_scheduled_count]
                        eid = f"{curr_date}_{cls}_Morning"
                        st.session_state.timetable.append({
                            "id": eid, "date": str(curr_date), "class": cls,
                            "subject": s1, "slot": "Morning",
                            "rev_p": "1st-2nd", "exam_p": "3rd-4th"
                        })
                        # Auto-Assign Immediately
                        auto_assign_allocation(eid, cls, s1)
                    
                    # Afternoon Slot (Only for Unit Tests)
                    if slots_per_day == 2:
                        idx_2 = subjects_scheduled_count + 1
                        if idx_2 < len(subs):
                            s2 = subs[idx_2]
                            eid = f"{curr_date}_{cls}_Afternoon"
                            st.session_state.timetable.append({
                                "id": eid, "date": str(curr_date), "class": cls,
                                "subject": s2, "slot": "Afternoon",
                                "rev_p": "5th-6th", "exam_p": "7th-8th"
                            })
                            auto_assign_allocation(eid, cls, s2)
                
                # Increment subject counter
                subjects_scheduled_count += slots_per_day
                curr_date += timedelta(days=1)
                
            save_to_disk()
            st.success("Schedule & Allocations Generated Successfully!")
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 3: ALLOCATION (Auto-Assigned View) ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Teacher Allocations (Auto-Assigned)</h3>", unsafe_allow_html=True)
    
    if not st.session_state.timetable:
        st.info("No schedule found. Go to Schedule tab.")
    else:
        # Group by Date
        df = pd.DataFrame(st.session_state.timetable)
        dates = sorted(df['date'].unique())
        
        for d in dates:
            with st.expander(f"📅 {d}", expanded=False):
                day_exams = df[df['date'] == d]
                for _, ex in day_exams.iterrows():
                    eid = ex['id']
                    alloc = st.session_state.allocations.get(eid, {})
                    
                    c1, c2, c3, c4 = st.columns([1, 2, 2, 2])
                    with c1: st.write(f"**{ex['class']}**")
                    with c2: st.caption(f"{ex['subject']} ({ex['slot']})")
                    
                    # Edit Logic
                    with c3:
                        curr_rev = alloc.get('rev_teacher', 'None')
                        curr_inv = alloc.get('inv_teacher', 'None')
                        st.write(f"**Rev:** {curr_rev} | **Inv:** {curr_inv}")
                        
                    with c4:
                        # Edit Button triggers a selectbox
                        if st.checkbox(f"Edit {ex['class']} ({ex['slot']})", key=f"ed_{eid}"):
                            # Revision Edit
                            rev_opts = [curr_rev] + get_all_teacher_names()
                            new_rev = st.selectbox("Rev", rev_opts, key=f"nr_{eid}")
                            
                            # Inv Edit
                            backups = alloc.get('inv_backups', [])
                            all_t = get_all_teacher_names()
                            # Combine priorities
                            inv_opts = [curr_inv] + backups + [t for t in all_t if t not in backups]
                            new_inv = st.selectbox("Inv", inv_opts, key=f"ni_{eid}")
                            
                            if st.button("Save Change", key=f"sv_{eid}"):
                                st.session_state.allocations[eid]['rev_teacher'] = new_rev
                                st.session_state.allocations[eid]['inv_teacher'] = new_inv
                                save_to_disk()
                                st.rerun()
                st.write("")

# --- TAB 4: MATRIX VIEW (Dates x Classes) ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>🗓️ Timetable Matrix</h3></div>", unsafe_allow_html=True)
    
    if st.session_state.timetable:
        # Prepare Data for Matrix
        data = {} # Key: Date, Value: {Class: "Math (M) / Sci (A)"}
        
        for ex in st.session_state.timetable:
            d = ex['date']
            c = ex['class']
            s = ex['subject']
            slot_code = "(M)" if "Morning" in ex['slot'] else "(A)"
            
            if d not in data: data[d] = {}
            
            # Combine if multiple exams per day
            if c in data[d]:
                data[d][c] += f" | {s} {slot_code}"
            else:
                data[d][c] = f"{s} {slot_code}"
                
        # Convert to DataFrame
        matrix_df = pd.DataFrame.from_dict(data, orient='index')
        matrix_df = matrix_df.reindex(columns=ORDERED_CLASSES) # Sort columns
        matrix_df.index.name = "Date"
        matrix_df.sort_index(inplace=True)
        
        # Display
        st.dataframe(matrix_df, use_container_width=True)
        st.download_button("📥 Download Excel", convert_df_to_excel(matrix_df), "matrix_timetable.xlsx")
    else:
        st.info("No schedule available.")

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

# --- TAB 6: SUBJECTS (Last) ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>Manage Subjects</h3>", unsafe_allow_html=True)
    with st.form("sub_form"):
        classes = st.multiselect("Select Classes", ORDERED_CLASSES)
        new_sub = st.text_input("Subject Name")
        if st.form_submit_button("Add Subject"):
            count = 0
            for c in classes:
                if new_sub not in st.session_state.class_subjects[c]:
                    st.session_state.class_subjects[c].append(new_sub)
                    count += 1
            if count > 0:
                save_to_disk()
                st.success(f"Added to {count} classes.")
    st.markdown("</div>", unsafe_allow_html=True)

# --- SIDEBAR: DATA BACKUP ---
with st.sidebar:
    st.header("💾 Backup & Restore")
    json_str = json.dumps({
        "teachers": st.session_state.teachers,
        "timetable": st.session_state.timetable,
        "allocations": st.session_state.allocations,
        "class_subjects": st.session_state.class_subjects
    }, indent=4, default=str)
    st.download_button("⬇️ Download JSON", json_str, "backup.json", "application/json")
    
    uploaded_file = st.file_uploader("⬆️ Restore JSON", type=["json"])
    if uploaded_file and st.button("Confirm Restore"):
        try:
            data = json.load(uploaded_file)
            st.session_state.teachers = data.get("teachers", [])
            st.session_state.timetable = data.get("timetable", [])
            st.session_state.allocations = data.get("allocations", {})
            st.session_state.class_subjects = data.get("class_subjects", get_default_subjects())
            save_to_disk()
            st.rerun()
        except: st.error("Invalid file.")
