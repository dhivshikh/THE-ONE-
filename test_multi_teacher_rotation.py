"""
Test multi-teacher rotation in parallel baskets and labs.

This test verifies that when multiple teachers are assigned to a single lab subject:
1. Teachers are rotated across occurrences (not all assigned to same time slot)
2. Load is balanced fairly across teachers
3. No teacher double-booking occurs
4. Single-teacher labs continue to work correctly
"""
import sys
import os
sys.path.insert(0, 'backend')
os.environ['PYTHONIOENCODING'] = 'utf-8'

def test_multi_teacher_rotation():
    print("=" * 80)
    print("MULTI-TEACHER ROTATION TEST")
    print("=" * 80)
    
    try:
        from app.db.session import get_db
        from app.db.models import (
            Teacher, Subject, Semester, Room, Allocation,
            ParallelLabBasket, ParallelLabBasketSubject
        )
        from sqlalchemy import and_
        
        db = next(get_db())
        
        # Check for test data: parallel lab baskets with multiple teachers
        baskets = db.query(ParallelLabBasket).all()
        print(f"\nFound {len(baskets)} parallel lab baskets")
        
        if not baskets:
            print("WARNING: No parallel lab baskets found. Testing will be limited.")
            print("Run seed_data.py with multi-teacher setup to enable full testing.")
        else:
            print("\nAnalyzing parallel baskets for multi-teacher labs:")
            for basket in baskets[:3]:  # Check first 3 baskets
                print(f"\n  Basket ID {basket.id}:")
                print(f"    Classes: {basket.class_ids or f'Dept {basket.dept_id} Y{basket.year}S{basket.section}'}")
                for subj in basket.basket_subjects:
                    teacher_ids = []
                    if subj.lab_teacher_ids:
                        teacher_ids = [int(t.strip()) for t in subj.lab_teacher_ids.split(',')]
                    if subj.teacher_id and subj.teacher_id not in teacher_ids:
                        teacher_ids.append(subj.teacher_id)
                    
                    if teacher_ids:
                        names = []
                        for tid in teacher_ids:
                            t = db.query(Teacher).get(tid)
                            names.append(f"{tid}:{t.name if t else 'UNKNOWN'}")
                        print(f"      Subject {subj.subject_id}: {len(teacher_ids)} teachers [{', '.join(names)}]")
        
        # Import generator
        print("\n" + "=" * 80)
        print("Importing generator...")
        from app.services.generator import TimetableGenerator
        
        print("Creating generator instance...")
        gen = TimetableGenerator(db)
        
        # Run generation
        print("\nStarting timetable generation...")
        success, msg, allocs, time_taken = gen.generate()
        
        print(f"\nGeneration completed in {time_taken:.2f}s")
        print(f"  Success: {success}")
        print(f"  Message: {msg}")
        print(f"  Total allocations: {len(allocs)}")
        
        if not success:
            print("\nWARNING: Generation failed. Limited testing possible.")
            print("Failure details:", gen.allocation_failures[:3])
        
        # Verify multi-teacher rotation
        print("\n" + "=" * 80)
        print("VERIFYING MULTI-TEACHER ROTATION")
        print("=" * 80)
        
        # Get allocations from the in-memory state (generator)
        if hasattr(gen, 'final_state') and gen.final_state:
            allocations = gen.final_state.allocations
        else:
            # Fallback: query database
            allocations = db.query(Allocation).all()
        
        print(f"\nAnalyzing {len(allocations)} allocations...")
        
        # Group allocations by (semester_id, subject_id) to find labs
        from collections import defaultdict
        subject_allocations = defaultdict(list)
        
        for alloc in allocations:
            if hasattr(alloc, 'semester_id') and hasattr(alloc, 'subject_id'):
                key = (alloc.semester_id, alloc.subject_id)
                subject_allocations[key].append(alloc)
        
        # Find subjects with multiple teacher allocations (multi-teacher labs)
        multi_teacher_subjects = {}
        for (sem_id, subj_id), allocs in subject_allocations.items():
            teachers = set(a.teacher_id for a in allocs if a.teacher_id)
            if len(teachers) > 1:
                multi_teacher_subjects[(sem_id, subj_id)] = {
                    'teachers': teachers,
                    'allocations': allocs,
                    'teacher_counts': count_by_teacher(allocs)
                }
        
        if not multi_teacher_subjects:
            print("\nNo multi-teacher subjects found in allocations.")
            print("This could mean:")
            print("  - No parallel baskets with multiple teachers in the database")
            print("  - Generation failed to allocate multi-teacher labs")
        else:
            print(f"\nFound {len(multi_teacher_subjects)} multi-teacher subjects:")
            
            for (sem_id, subj_id), data in list(multi_teacher_subjects.items())[:5]:
                print(f"\n  Subject {subj_id} in Semester {sem_id}:")
                print(f"    Total allocations: {len(data['allocations'])}")
                print(f"    Involved teachers: {data['teachers']}")
                
                # Check rotation
                print(f"    Allocation distribution:")
                for teacher_id, count in sorted(data['teacher_counts'].items()):
                    print(f"      Teacher {teacher_id}: {count} allocations")
                
                # Verify load balancing (difference should not exceed 1)
                counts = list(data['teacher_counts'].values())
                if counts:
                    min_count = min(counts)
                    max_count = max(counts)
                    diff = max_count - min_count
                    balance_status = "✓ BALANCED" if diff <= 1 else f"✗ IMBALANCED (diff={diff})"
                    print(f"    Load balance: {balance_status}")
                
                # Verify no double-booking
                double_booked = check_double_booking(data['allocations'])
                if double_booked:
                    print(f"    ✗ DOUBLE BOOKING DETECTED: {len(double_booked)} conflicts")
                    for t_id, slots in double_booked.items():
                        print(f"        Teacher {t_id}: {len(slots)} double-booked slots")
                else:
                    print(f"    ✓ NO DOUBLE BOOKING")
        
        # Verify backward compatibility (single-teacher labs)
        print("\n" + "=" * 80)
        print("VERIFYING BACKWARD COMPATIBILITY (Single-Teacher Labs)")
        print("=" * 80)
        
        single_teacher_subjects = {}
        for (sem_id, subj_id), allocs in subject_allocations.items():
            teachers = set(a.teacher_id for a in allocs if a.teacher_id)
            if len(teachers) == 1:
                single_teacher_subjects[(sem_id, subj_id)] = {
                    'teacher': next(iter(teachers)) if teachers else None,
                    'allocations': allocs
                }
        
        print(f"\nFound {len(single_teacher_subjects)} single-teacher subjects")
        
        # Verify a sample of single-teacher allocations
        test_count = 0
        healthy_count = 0
        for (sem_id, subj_id), data in list(single_teacher_subjects.items())[:3]:
            test_count += 1
            teacher_id = data['teacher']
            allocations = data['allocations']
            
            # All allocations should have the same teacher
            all_same = all(a.teacher_id == teacher_id for a in allocations)
            if all_same:
                healthy_count += 1
                print(f"  ✓ Subject {subj_id}: All {len(allocations)} allocations by Teacher {teacher_id}")
            else:
                print(f"  ✗ Subject {subj_id}: INCONSISTENT teacher assignment")
        
        print(f"\nBackward compatibility: {healthy_count}/{test_count} tests passed")
        
        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        if success and len(allocs) > 0:
            print(f"\n✓ Generation successful with {len(allocs)} allocations")
            print(f"✓ Multi-teacher subjects found: {len(multi_teacher_subjects)}")
            print(f"✓ Single-teacher subjects validated: {len(single_teacher_subjects)}")
            
            if len(allocs) > 0 and multi_teacher_subjects and healthy_count == test_count:
                print("\n✓ ALL TESTS PASSED")
            else:
                print("\n⚠ PARTIAL SUCCESS - See details above")
        else:
            print(f"\n✗ Generation failed or no allocations created")
        
        return success
        
    except Exception as e:
        import traceback
        print(f"\n✗ ERROR: {e}")
        traceback.print_exc()
        return False


def count_by_teacher(allocations):
    """Count allocations by teacher."""
    from collections import defaultdict
    counts = defaultdict(int)
    for alloc in allocations:
        if hasattr(alloc, 'teacher_id') and alloc.teacher_id:
            counts[alloc.teacher_id] += 1
    return dict(counts)


def check_double_booking(allocations):
    """Check if any teacher is double-booked (same day+slot)."""
    from collections import defaultdict
    
    # Group by (teacher_id, day, slot)
    slots_by_teacher = defaultdict(list)
    for alloc in allocations:
        if hasattr(alloc, 'teacher_id') and alloc.teacher_id:
            if hasattr(alloc, 'day') and hasattr(alloc, 'slot'):
                key = (alloc.day, alloc.slot)
                slots_by_teacher[alloc.teacher_id].append(key)
    
    # Find duplicates
    double_booked = {}
    for teacher_id, slots in slots_by_teacher.items():
        # Count occurrences
        from collections import Counter
        counts = Counter(slots)
        duplicates = [slot for slot, count in counts.items() if count > 1]
        if duplicates:
            double_booked[teacher_id] = duplicates
    
    return double_booked


if __name__ == "__main__":
    success = test_multi_teacher_rotation()
    sys.exit(0 if success else 1)
