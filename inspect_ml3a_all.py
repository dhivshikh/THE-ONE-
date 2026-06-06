import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Subjects for ML3A:")
cur.execute("""
    SELECT s.id, s.name, s.code, s.elective_basket_id, cst.component_type, cst.room_id
    FROM class_subject_teachers cst
    JOIN subjects s ON s.id = cst.subject_id
    WHERE cst.semester_id = 4 AND s.elective_basket_id IS NOT NULL
""")
for r in cur.fetchall():
    print(dict(r))

conn.close()
