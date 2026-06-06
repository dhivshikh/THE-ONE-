import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== DEPARTMENTS & SEMESTERS ===")
cur.execute("SELECT * FROM semesters")
sems = cur.fetchall()
sem_map = {s['id']: dict(s) for s in sems}
for s in sems:
    print(dict(s))

print("\n=== CLASS SUBJECT TEACHERS (ASSIGNMENTS) ===")
cur.execute("""
    SELECT cst.semester_id, cst.subject_id, cst.teacher_id, cst.component_type, s.elective_basket_id
    FROM class_subject_teachers cst
    JOIN subjects s ON s.id = cst.subject_id
    WHERE s.elective_basket_id IS NOT NULL
""")
for cst in cur.fetchall():
    sem_name = sem_map.get(cst['semester_id'], {}).get('name', str(cst['semester_id']))
    print(f"Class: {sem_name}, SubjectID: {cst['subject_id']}, TeacherID: {cst['teacher_id']}, Type: {cst['component_type']}, BasketID: {cst['elective_basket_id']}")

print("\n=== ELECTIVE SUBJECTS ===")
cur.execute("""
    SELECT s.id, s.name, s.subject_code, s.elective_basket_id, s.hours_per_week 
    FROM subjects s 
    WHERE s.elective_basket_id IS NOT NULL
""")
subs = cur.fetchall()
for s in subs:
    print(dict(s))

conn.close()
