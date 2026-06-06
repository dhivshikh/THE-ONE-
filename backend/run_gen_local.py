import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.services.generator import TimetableGenerator
from app.api.subjects import integrity_repair

def run_gen():
    db = SessionLocal()
    try:
        integrity_repair(db)
        generator = TimetableGenerator(db)
        success, message, allocs, time = generator.generate(semester_type="ODD", clear_existing=True)
        print("Success:", success)
        print("Message:", message)
        print("Allocations:", len(allocs))
        print("Time:", time)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    run_gen()
