import sqlite3
import re

def drop_constraint():
    con = sqlite3.connect('backend/timetable.db')
    cur = con.cursor()
    
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='fixed_slots'")
    schema = cur.fetchone()[0]
    
    if 'uq_fixed_slot_position' not in schema:
        print('Constraint already removed.')
        return
        
    print('Old schema:', schema)
    
    # Remove the constraint line
    # CONSTRAINT uq_fixed_slot_position UNIQUE (semester_id, day, slot),
    new_schema = re.sub(r',\s*CONSTRAINT\s+uq_fixed_slot_position\s+UNIQUE\s*\([^\)]+\)', '', schema, flags=re.IGNORECASE)
    # also remove it if it's the last item without a trailing comma
    new_schema = re.sub(r'CONSTRAINT\s+uq_fixed_slot_position\s+UNIQUE\s*\([^\)]+\)', '', new_schema, flags=re.IGNORECASE)
    
    print('New schema:', new_schema)
    
    # SQLite alter table trick
    cur.execute('PRAGMA foreign_keys=OFF')
    cur.execute('BEGIN TRANSACTION')
    
    # 1. rename old table
    cur.execute('ALTER TABLE fixed_slots RENAME TO fixed_slots_old')
    
    # 2. create new table
    cur.execute(new_schema)
    
    # 3. copy data
    cur.execute('INSERT INTO fixed_slots SELECT * FROM fixed_slots_old')
    
    # 4. drop old table
    cur.execute('DROP TABLE fixed_slots_old')
    
    cur.execute('COMMIT')
    cur.execute('PRAGMA foreign_keys=ON')
    
    print('Constraint successfully removed.')

if __name__ == '__main__':
    drop_constraint()
