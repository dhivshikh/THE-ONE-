import sqlite3
import json

con = sqlite3.connect('backend/timetable.db')
con.row_factory = sqlite3.Row
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(tables)

if 'elective_subjects' in tables:
    cur.execute("SELECT * FROM elective_subjects LIMIT 1")
    print(dict(cur.fetchone() or {}))
