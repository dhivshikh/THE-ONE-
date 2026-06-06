from app.db.session import SessionLocal
from app.services.generator import TimetableGenerator

db = SessionLocal()
gen = TimetableGenerator(db)

room_map = gen._read_room_assignment_map()
print("Room Map:")
for k, v in room_map.items():
    if k[0] == 6 and k[1] == 39:
        print(k, v)

db.close()
