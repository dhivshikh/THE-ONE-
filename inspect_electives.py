import sqlite3
import json

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== DEPARTMENTS & SEMESTERS ===")
cur.execute("SELECT * FROM semesters WHERE name LIKE '%AIDS%' OR name LIKE '%AIML%'")
sems = cur.fetchall()
sem_map = {s['id']: dict(s) for s in sems}
for s in sems:
    print(dict(s))

print("\n=== ELECTIVE BASKETS ===")
cur.execute("SELECT * FROM elective_baskets")
baskets = cur.fetchall()
basket_map = {b['id']: dict(b) for b in baskets}
for b in baskets:
    print(dict(b))

print("\n=== BASKET CLASSES ===")
cur.execute("SELECT basket_id, semester_id FROM elective_basket_classes")
for r in cur.fetchall():
    print(dict(r))

print("\n=== ELECTIVE SUBJECTS ===")
cur.execute("""
    SELECT s.id, s.name, s.subject_code, s.elective_basket_id, s.hours_per_week 
    FROM subjects s 
    WHERE s.elective_basket_id IS NOT NULL
""")
subs = cur.fetchall()
for s in subs:
    print(dict(s))

print("\n=== SUBJECT COMPONENTS (THEORY/LAB) ===")
cur.execute("""
    SELECT sc.subject_id, sc.component_type, sc.hours_per_week, sc.block_size
    FROM subject_components sc
    JOIN subjects s ON s.id = sc.subject_id
    WHERE s.elective_basket_id IS NOT NULL
""")
for sc in cur.fetchall():
    print(dict(sc))

print("\n=== CLASS SUBJECT TEACHERS (ASSIGNMENTS) ===")
cur.execute("""
    SELECT cst.semester_id, cst.subject_id, cst.teacher_id, cst.component_type
    FROM class_subject_teachers cst
    JOIN subjects s ON s.id = cst.subject_id
    WHERE s.elective_basket_id IS NOT NULL
""")
for cst in cur.fetchall():
    sem_name = sem_map.get(cst['semester_id'], {}).get('name', str(cst['semester_id']))
    print(f"Class: {sem_name}, SubjectID: {cst['subject_id']}, TeacherID: {cst['teacher_id']}, Type: {cst['component_type']}")

print("\n=== ELECTIVE LAB ROOMS ===")
cur.execute("""
    SELECT er.elective_basket_id, er.subject_id, er.room_id
    FROM elective_rooms er
""")
for er in cur.fetchall():
    print(dict(er))

conn.close()
