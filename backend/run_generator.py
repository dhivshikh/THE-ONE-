from app.db.session import SessionLocal
from app.services.generator import TimetableGenerator

db = SessionLocal()
generator = TimetableGenerator(db)
result = generator.generate(semester_type="ODD")

print("Result:")
print(result[0], result[1])

print("\nAllocation Failures:")
if hasattr(generator, 'allocation_failures'):
    for failure in generator.allocation_failures:
        print(failure)
else:
    print("No allocation_failures attribute found.")

db.close()
