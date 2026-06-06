import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM subjects WHERE code = 'CGI1363'")
for r in cur.fetchall():
    print(dict(r))

print("Class Subject Teachers for CGI1363:")
cur.execute("SELECT * FROM class_subject_teachers WHERE subject_id = (SELECT id FROM subjects WHERE code = 'CGI1363')")
for r in cur.fetchall():
    print(dict(r))

conn.close()
