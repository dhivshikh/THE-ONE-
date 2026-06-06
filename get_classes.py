import sqlite3

conn = sqlite3.connect('backend/timetable.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, name FROM semesters")
for r in cur.fetchall():
    print(f"{r['id']}: {r['name']}")

conn.close()
