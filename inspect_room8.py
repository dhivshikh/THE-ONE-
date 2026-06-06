import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT * FROM rooms WHERE id = 8")
for r in cur.fetchall():
    print(dict(r))

conn.close()
