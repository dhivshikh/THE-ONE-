from app.db.session import SessionLocal
from app.services.generator import TimetableGenerator

db = SessionLocal()
gen = TimetableGenerator(db)
semesters = gen._read_semesters(None, None, "ODD")
reqs = gen._build_requirements(semesters)

print("Requirements for DS3B CGI1363 Lab:")
for req in reqs:
    if req.semester_id == 6 and req.subject_id == 39 and req.component_type.value == 'lab':
        print(f"Room ID: {req.assigned_room_id}")

db.close()
