import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== CLASS SUBJECT TEACHERS ROOMS ===")
cur.execute("""
    SELECT cst.semester_id, cst.subject_id, cst.teacher_id, cst.component_type, cst.room_id
    FROM class_subject_teachers cst
    JOIN subjects s ON s.id = cst.subject_id
    WHERE s.elective_basket_id = 1
""")
for r in cur.fetchall():
    print(dict(r))

conn.close()
