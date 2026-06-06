import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("\n=== ELECTIVE LAB ROOMS ===")
cur.execute("""
    SELECT er.elective_basket_id, er.subject_id, er.room_id, r.name as room_name, s.name as subj_name
    FROM elective_rooms er
    JOIN rooms r ON r.id = er.room_id
    JOIN subjects s ON s.id = er.subject_id
    WHERE er.elective_basket_id = 1
""")
for er in cur.fetchall():
    print(dict(er))

conn.close()
