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
DATA_FILE = "school_data_v3.json"

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

# FIXED: Initialize this outside the check so it always exists
if 'temp_teacher_mappings' not in st.session_state:
    st.session_state.temp_teacher_mappings = []

# ==========================================
# 2. RESTORED SLEEK UI CSS
# ==========================================
st.markdown("""
<style>
    /* 1. Main Background - Deep Dark Blue Gradient */
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

    /* 3. Text Colors (Global White) */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800 !important; }
    p, label, span, div[data-testid="stMarkdownContainer"] p { 
        color: #ffffff !important; 
    }

    /* 4. TABS - Fixed Visibility */
    /* Unselected Tabs: White Text */
    button[data-baseweb="tab"] {
        color: #ffffff !important; 
        background-color: transparent !important;
        font-weight: 600 !important;
    }
    /* Selected Tab: White BG + BLACK Text */
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        border-radius: 8px;
    }
    button[data-baseweb="tab"][aria-selected="true"] > div,
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #000000 !important;
        font-weight: 900 !important;
    }

    /* 5. INPUTS & DROPDOWNS (High Contrast: White Box, Black Text) */
    .stTextInput input, .stDateInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    
    /* SelectBox Fixes */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    .stSelectbox div[data-baseweb="select"] div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; 
    }
    
    /* Dropdown Menus */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[data-baseweb="menu"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    li[data-baseweb="option"] {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* MultiSelect */
    .stMultiSelect div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
    }
    .stMultiSelect span[data-baseweb="tag"] {
        background-color: #e0e0e0 !important;
        color: black !important;
    }

    /* 6. BUTTONS */
    .stButton button {
        background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 8px;
    }
    .stButton button:hover {
        transform: scale(1.02);
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

def find_smart_invigilators(exam_class, exam_subject, eid):
    primary_pool = []
    backup_pool = []
    
    for t in st.session_state.teachers:
        name = t['name']
        mappings = t['mappings']
        
        teaches_this_class = any(m['class'] == exam_class for m in mappings)
        teaches_exam_subject = any(m['subject'] == exam_subject for m in mappings)
        
        if teaches_exam_subject:
            continue
            
        if teaches_this_class:
            primary_pool.append(name)
        else:
            neighbors = get_neighbor_classes(exam_class)
            teaches_neighbor = any(m['class'] in neighbors for m in mappings)
            if teaches_neighbor:
                backup_pool.append(name)
                
    return primary_pool, backup_pool

def convert_df_to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# ==========================================
# 4. APP UI
# ==========================================

st.markdown("<h1>🏫 Exam & Invigilation Manager</h1>", unsafe_allow_html=True)
tabs = st.tabs(["👨‍🏫 Teachers", "📚 Subjects", "📅 Schedule", "✅ Allocation", "🗓️ Timetable", "📊 Stats"])

# --- TAB 1: TEACHERS ---
with tabs[0]:
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown("<div class='glass-container'><h3>Add Teacher</h3>", unsafe_allow_html=True)
        t_name = st.text_input("Teacher Name")
        
        st.markdown("##### Assign Classes & Subjects")
        col_a, col_b = st.columns(2)
        with col_a:
            m_cls = st.selectbox("Class", ORDERED_CLASSES)
        with col_b:
            avail_subs = st.session_state.class_subjects.get(m_cls, [])
            m_sub = st.selectbox("Subject", avail_subs)
        
        if st.button("Add Mapping"):
            st.session_state.temp_teacher_mappings.append({"class": m_cls, "subject": m_sub})
            
        if st.session_state.temp_teacher_mappings:
            st.write("Current Assignments:")
            for i, m in enumerate(st.session_state.temp_teacher_mappings):
                st.caption(f"{i+1}. {m['class']} - {m['subject']}")
                
        if st.button("💾 Save Teacher Profile", type="primary"):
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
                st.error("Name and at least one mapping required.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div class='glass-container'><h3>Teacher Directory</h3>", unsafe_allow_html=True)
        if st.session_state.teachers:
            for i, t in enumerate(st.session_state.teachers):
                with st.expander(f"👤 {t['name']}"):
                    map_str = [f"{m['class']}: {m['subject']}" for m in t['mappings']]
                    st.write(" | ".join(map_str))
                    if st.button("Delete", key=f"del_t_{i}"):
                        st.session_state.teachers.pop(i)
                        save_to_disk()
                        st.rerun()
        else:
            st.info("No teachers added.")
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 2: SUBJECTS ---
with tabs[1]:
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

# --- TAB 3: SCHEDULE ---
with tabs[2]:
    st.markdown("<div class='glass-container'><h3>Auto-Scheduler</h3>", unsafe_allow_html=True)
    
    with st.form("auto_sched"):
        start_date = st.date_input("Start Date")
        if st.form_submit_button("🚀 Generate Full Schedule"):
            st.session_state.timetable = []
            curr_date = start_date
            max_subs = max([len(v) for v in st.session_state.class_subjects.values()])
            
            for day_idx in range(max_subs):
                exam_day = curr_date + timedelta(days=day_idx)
                for cls in ORDERED_CLASSES:
                    subs = st.session_state.class_subjects[cls]
                    if day_idx < len(subs):
                        subject = subs[day_idx]
                        eid = f"{exam_day}_{cls}_Morning"
                        st.session_state.timetable.append({
                            "id": eid, "date": str(exam_day), "class": cls,
                            "subject": subject, "slot": "Morning (Exam: 3rd-4th)",
                            "rev_p": "1st-2nd", "exam_p": "3rd-4th"
                        })
            save_to_disk()
            st.success("Schedule Generated!")
            st.rerun()
            
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.session_state.timetable:
        st.markdown("<div class='glass-container'><h3>Manage Exams</h3>", unsafe_allow_html=True)
        f_cls = st.selectbox("Filter Class", ["All"] + ORDERED_CLASSES)
        exams = sorted(st.session_state.timetable, key=lambda x: x['date'])
        
        for ex in exams:
            if f_cls != "All" and ex['class'] != f_cls: continue
            
            with st.expander(f"{ex['date']} | {ex['class']} | {ex['subject']}"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    new_date = st.date_input("Date", pd.to_datetime(ex['date']), key=f"d_{ex['id']}")
                with c2:
                    curr_subs = st.session_state.class_subjects[ex['class']]
                    # Handle subject not found safe-guard
                    try:
                        idx = curr_subs.index(ex['subject'])
                    except ValueError:
                        idx = 0
                    new_sub = st.selectbox("Subject", curr_subs, index=idx, key=f"s_{ex['id']}")
                with c3:
                    st.write("") 
                    st.write("")
                    if st.button("Update", key=f"up_{ex['id']}"):
                        ex['date'] = str(new_date)
                        ex['subject'] = new_sub
                        ex['id'] = f"{new_date}_{ex['class']}_Morning"
                        if ex['id'] in st.session_state.allocations:
                            del st.session_state.allocations[ex['id']]
                        save_to_disk()
                        st.rerun()
                    if st.button("Delete", key=f"del_{ex['id']}"):
                        st.session_state.timetable.remove(ex)
                        save_to_disk()
                        st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# --- TAB 4: ALLOCATION ---
with tabs[3]:
    st.markdown("<div class='glass-container'><h3>Invigilation Allocation</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.timetable:
        st.info("No schedule found.")
        
    for exam in st.session_state.timetable:
        eid = exam['id']
        
        if eid not in st.session_state.allocations:
            prim, back = find_smart_invigilators(exam['class'], exam['subject'], eid)
            random.shuffle(prim)
            random.shuffle(back)
            
            rev_cands = []
            for t in st.session_state.teachers:
                for m in t['mappings']:
                    if m['class'] == exam['class'] and m['subject'] == exam['subject']:
                        rev_cands.append(t['name'])
            
            st.session_state.allocations[eid] = {
                "rev_pool": rev_cands, "rev_idx": 0, "confirmed_rev": None,
                "inv_pool": prim + back, "inv_idx": 0, "confirmed_inv": None
            }
            
        alloc = st.session_state.allocations[eid]
        
        with st.expander(f"{exam['date']} | {exam['class']} | {exam['subject']}", expanded=True):
            rc, ic = st.columns(2)
            
            with rc:
                st.markdown(f"#### 📖 Revision ({exam['rev_p']})")
                if alloc['confirmed_rev']:
                    st.success(f"**{alloc['confirmed_rev']}**")
                    if st.button("🔄 Unassign", key=f"un_r_{eid}"):
                        alloc['confirmed_rev'] = None
                        save_to_disk()
                        st.rerun()
                else:
                    pool = alloc['rev_pool']
                    if pool:
                        cand = pool[0]
                        st.info(f"Draft: **{cand}**")
                        if st.button("Confirm", key=f"cf_r_{eid}"):
                            alloc['confirmed_rev'] = cand
                            save_to_disk()
                            st.rerun()
                    else:
                        st.warning("No subject teacher found.")
                        man = st.selectbox("Manual", [t['name'] for t in st.session_state.teachers], key=f"mn_r_{eid}")
                        if st.button("Assign", key=f"mn_btn_r_{eid}"):
                            alloc['confirmed_rev'] = man
                            save_to_disk()
                            st.rerun()

            with ic:
                st.markdown(f"#### 📝 Invigilation ({exam['exam_p']})")
                if alloc['confirmed_inv']:
                    st.success(f"**{alloc['confirmed_inv']}**")
                    if st.button("🔄 Unassign", key=f"un_i_{eid}"):
                        alloc['confirmed_inv'] = None
                        save_to_disk()
                        st.rerun()
                else:
                    pool = alloc['inv_pool']
                    idx = alloc['inv_idx']
                    if idx < len(pool):
                        cand = pool[idx]
                        st.info(f"Candidate: **{cand}**")
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Available", key=f"ok_i_{eid}_{idx}"):
                            alloc['confirmed_inv'] = cand
                            save_to_disk()
                            st.rerun()
                        if c2.button("❌ Skip", key=f"no_i_{eid}_{idx}"):
                            alloc['inv_idx'] += 1
                            save_to_disk()
                            st.rerun()
                    else:
                        st.error("No smart suggestions left.")
                        man = st.selectbox("Manual Backup", [t['name'] for t in st.session_state.teachers], key=f"mn_i_{eid}")
                        if st.button("Assign", key=f"mn_btn_i_{eid}"):
                            alloc['confirmed_inv'] = man
                            save_to_disk()
                            st.rerun()

# --- TAB 5: TIMETABLE ---
with tabs[4]:
    st.markdown("<div class='glass-container'><h3>🗓️ Date-wise Timetable</h3></div>", unsafe_allow_html=True)
    
    if st.session_state.timetable:
        df = pd.DataFrame(st.session_state.timetable)
        dates = sorted(df['date'].unique())
        
        for d in dates:
            st.markdown(f"### {d}")
            day_exams = df[df['date'] == d]
            
            table_rows = []
            for _, ex in day_exams.iterrows():
                alloc = st.session_state.allocations.get(ex['id'], {})
                rev = alloc.get('confirmed_rev', 'Pending')
                inv = alloc.get('confirmed_inv', 'Pending')
                
                table_rows.append({
                    "Class": ex['class'],
                    "Subject": ex['subject'],
                    "Revision Teacher": rev,
                    "Invigilator": inv
                })
            
            day_df = pd.DataFrame(table_rows)
            # Use Categorical sorting for classes
            day_df['Class'] = pd.Categorical(day_df['Class'], categories=ORDERED_CLASSES, ordered=True)
            day_df = day_df.sort_values('Class')
            
            st.dataframe(day_df, use_container_width=True, hide_index=True)
            st.markdown("---")
            
    else:
        st.info("Schedule is empty.")

# --- TAB 6: STATS ---
with tabs[5]:
    st.markdown("<div class='glass-container'><h3>Stats</h3></div>", unsafe_allow_html=True)
    if st.session_state.allocations:
        counts = {t['name']: 0 for t in st.session_state.teachers}
        for a in st.session_state.allocations.values():
            if a.get('confirmed_inv'):
                counts[a['confirmed_inv']] = counts.get(a['confirmed_inv'], 0) + 1
                
        df_s = pd.DataFrame(list(counts.items()), columns=["Teacher", "Invigilations"])
        df_s = df_s.sort_values("Invigilations", ascending=False)
        st.dataframe(df_s, use_container_width=True)
        st.bar_chart(df_s.set_index("Teacher"))
