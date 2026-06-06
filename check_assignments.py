import sqlite3
import json

con = sqlite3.connect('backend/timetable.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

cur.execute("SELECT * FROM elective_groups LIMIT 1")
print("Group:", dict(cur.fetchone() or {}))

cur.execute("SELECT * FROM subject_component_assignments WHERE subject_id=33")
for r in cur.fetchall():
    print("Assignment:", dict(r))
