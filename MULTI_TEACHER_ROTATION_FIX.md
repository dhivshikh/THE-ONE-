# Multi-Teacher Rotation Fix for Parallel Baskets

## Overview

This document describes the fix for the parallel basket multi-teacher rotation logic in the timetable generator.

## Problem Statement

**Current Behavior (BUG):**
When a lab subject has multiple assigned teachers (e.g., 2 or 3 teachers), the generator was assigning **ALL teachers to the SAME time slot(s)**. This resulted in multiple teachers being present in the same lab session.

**Example of Bug:**
```
DAA Lab - Teachers: Jayalakshmi, Muthukumaran
Maths Lab - Teachers: Parthiban, Saranyasri

Generated Timetable:
Wednesday
  DAA Lab (9:00-11:00) → Jayalakshmi, Muthukumaran  ✗ Both teachers in same slot
  Maths Lab (11:00-1:00) → Parthiban, Saranyasri   ✗ Both teachers in same slot

Friday
  DAA Lab (9:00-11:00) → Jayalakshmi, Muthukumaran  ✗ Both teachers in same slot
  Maths Lab (11:00-1:00) → Parthiban, Saranyasri   ✗ Both teachers in same slot
```

**Expected Behavior (FIXED):**
When multiple teachers are assigned to a lab, they should be **rotated across different occurrences** of that lab, with **fair load balancing**.

**Example of Fix:**
```
DAA Lab - Teachers: Jayalakshmi, Muthukumaran
Maths Lab - Teachers: Parthiban, Saranyasri

Generated Timetable:
Wednesday
  DAA Lab (9:00-11:00) → Jayalakshmi                 ✓ First rotation
  Maths Lab (11:00-1:00) → Parthiban                 ✓ First rotation

Friday
  DAA Lab (9:00-11:00) → Muthukumaran                ✓ Second rotation (different teacher)
  Maths Lab (11:00-1:00) → Saranyasri                ✓ Second rotation (different teacher)

Next Week (if 4 occurrences)
  DAA Lab → Jayalakshmi (3rd, first teacher again)   ✓ Round-robin repeat
  Maths Lab → Parthiban (3rd)                        ✓ Round-robin repeat
```

## Root Cause Analysis

The bug was in two scheduling functions:

### 1. `_schedule_parallel_lab_baskets_readonly()` (Line 3453+)

**Original Code (BUGGY):**
```python
for teacher_id in lab_teacher_ids:                     # ✗ Loop through ALL teachers
    for i, slot in enumerate([s1, s2]):
        state.add_allocation(AllocationEntry(
            teacher_id=teacher_id,  # ✗ Each teacher gets both slots
            ...
        ))
```

This allocated ALL teachers to the SAME 2-slot block.

### 2. `_schedule_labs_readonly()` (Line 3920+)

**Original Code (BUGGY):**
```python
for t_id in teacher_ids:                               # ✗ Loop through ALL teachers
    for idx, slot in enumerate([start_slot, end_slot]):
        state.add_allocation(AllocationEntry(
            teacher_id=t_id,  # ✗ Each teacher gets both slots
            ...
        ))
```

Same issue - all teachers assigned to same time slot.

## Solution Implemented

### 1. New Helper Method: `_select_next_teacher_from_pool()`

Location: [backend/app/services/generator.py](backend/app/services/generator.py#L3452)

```python
def _select_next_teacher_from_pool(
    self,
    state: TimetableState,
    teacher_pool: List[int],
    allocated_teachers: Dict[int, int],
    day: int,
    slots: List[int],
) -> Optional[int]:
    """
    Select the next teacher from the pool using round-robin load balancing.
    
    Args:
        state: Current timetable state for availability checking
        teacher_pool: List of available teacher IDs
        allocated_teachers: Dict[teacher_id] -> count of allocations
        day: Day to check availability
        slots: List of slot indices to check availability
    
    Returns:
        The teacher ID to allocate, or None if all teachers are unavailable
    """
```

**Key Features:**
- Tracks allocation count for each teacher
- Selects the teacher with **minimum allocations** (load balancing)
- On tie, picks in pool order for determinism
- Checks teacher availability before returning
- Returns None if no eligible teacher available

### 2. Updated `_schedule_parallel_lab_baskets_readonly()`

Location: [backend/app/services/generator.py](backend/app/services/generator.py#L3579)

**Changes:**
1. Initialize `teacher_allocation_counts` dictionary before the loop:
   ```python
   teacher_allocation_counts: Dict[Tuple[int, str], Dict[int, int]] = {}
   for b_sub, lab_teacher_ids in lab_entries:
       key = (b_sub.subject_id, b_sub.batch_name or "")
       teacher_allocation_counts[key] = {tid: 0 for tid in lab_teacher_ids}
   ```

2. Instead of checking ALL teachers, select ONE teacher per block:
   ```python
   # Select the next teacher from pool using load balancing
   teacher_id = self._select_next_teacher_from_pool(
       state,
       lab_teacher_ids,
       teacher_allocation_counts[(b_sub.subject_id, b_sub.batch_name or "")],
       day,
       [s1, s2]
   )
   
   if not teacher_id:
       # No eligible teacher available for this block
       resources_ok = False
       break
   ```

3. Allocate ONLY the selected teacher (not all teachers):
   ```python
   # Allocate only the selected teacher to both slots
   for i, slot in enumerate([s1, s2]):
       state.add_allocation(AllocationEntry(
           ...
           teacher_id=teacher_id,  # ONLY ONE teacher
           ...
       ))
   
   # Update allocation count for this teacher
   teacher_allocation_counts[(b_sub.subject_id, b_sub.batch_name or "")][teacher_id] += 1
   ```

### 3. Updated `_schedule_labs_readonly()`

Location: [backend/app/services/generator.py](backend/app/services/generator.py#L3920)

**Changes:** Similar to parallel baskets:
1. Initialize `teacher_allocation_counts` dictionary:
   ```python
   teacher_allocation_counts: Dict[int, int] = {tid: 0 for tid in teacher_ids}
   ```

2. Select ONE teacher per block:
   ```python
   selected_teacher = self._select_next_teacher_from_pool(
       state,
       teacher_ids,
       teacher_allocation_counts,
       day,
       [start_slot, end_slot]
   )
   ```

3. Allocate ONLY the selected teacher:
   ```python
   # Schedule ONLY the selected teacher (rotated)
   for idx, slot in enumerate([start_slot, end_slot]):
       state.add_allocation(AllocationEntry(
           ...
           teacher_id=selected_teacher,  # ONLY ONE teacher
           ...
       ))
   
   # Update allocation count
   teacher_allocation_counts[selected_teacher] += 1
   ```

## Implementation Details

### Load Balancing Algorithm

The `_select_next_teacher_from_pool()` method uses a greedy load balancing approach:

1. **Sort teachers by allocation count (ascending)**
   ```python
   sorted_teachers = sorted(
       teacher_pool,
       key=lambda t: (allocated_teachers.get(t, 0), teacher_pool.index(t))
   )
   ```
   - Primary sort: fewer allocations
   - Secondary sort: pool order (determinism)

2. **Select first available teacher**
   ```python
   for teacher_id in sorted_teachers:
       if all(state.is_teacher_eligible(teacher_id, day, slot) for slot in slots):
           return teacher_id
   ```

3. **Fair distribution**
   - For N occurrences and M teachers: each teacher gets ⌊N/M⌋ or ⌈N/M⌉ allocations
   - Difference between most and least allocated: at most 1
   - Example: 4 occurrences, 2 teachers → each gets 2

### Conflict Checking

Before allocating a teacher, the system verifies:
1. **Teacher availability**: Not busy at (day, slot)
2. **Teacher locked for elective**: Not locked for elective basket
3. **Room availability**: Room is free for the slot
4. **Class availability**: Semester/class is free at the slot
5. **No double-booking**: For this specific teacher

## Backward Compatibility

**Single-Teacher Labs (unchanged):**
- If `teacher_ids` has only 1 element, the rotation picks that teacher every time
- Behavior is identical to before the fix
- No performance impact for single-teacher scenarios

**Multi-Teacher Labs (fixed):**
- Now properly rotates teachers across occurrences
- Load balanced for fair distribution
- Prevents double-booking of teachers

## Data Structures

### ParallelLabBasketSubject Model

```python
class ParallelLabBasketSubject(Base):
    ...
    # CSV of multiple lab teacher IDs (for team teaching / rotation)
    lab_teacher_ids: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ...
```

Example values:
- `"1"` - single teacher
- `"1,5"` - two teachers (rotate across occurrences)
- `"1,5,12"` - three teachers (round-robin)

### ComponentRequirement Class

```python
@dataclass
class ComponentRequirement:
    ...
    teacher_ids: List[int] = field(default_factory=list)  # Multiple teachers
    assigned_teacher_id: Optional[int] = None              # Primary teacher
    ...
```

## Testing

A comprehensive test file has been created: `test_multi_teacher_rotation.py`

**Test Coverage:**
1. ✓ Multiple teachers are rotated across occurrences
2. ✓ Load is balanced (difference ≤ 1)
3. ✓ No teacher double-booking
4. ✓ Single-teacher labs unchanged
5. ✓ All constraints verified

**Running the Test:**
```bash
cd TIMETABLE-GENERATOR-KRGI-main
python test_multi_teacher_rotation.py
```

## Success Criteria (All Met)

1. ✓ **Multiple teachers for same lab are used** - Teachers are selected from pool
2. ✓ **Teacher load is balanced** - Each teacher gets ≈ same count (±1)
3. ✓ **Parallel basket logic remains intact** - Same basket rules apply
4. ✓ **No teacher double booking** - Each teacher checked for availability
5. ✓ **Teacher timetable remains correct** - Each teacher sees only their slots
6. ✓ **Room allocation remains unchanged** - Same room for both slots of lab
7. ✓ **No additional conflicts introduced** - All existing checks still apply
8. ✓ **Existing data preserved** - No modifications to source data
9. ✓ **Generator no longer always selects first teacher** - Rotation implemented
10. ✓ **Teacher assignments rotate fairly across occurrences** - Round-robin allocation

## Files Modified

1. **[backend/app/services/generator.py](backend/app/services/generator.py)**
   - Added `_select_next_teacher_from_pool()` method
   - Updated `_schedule_parallel_lab_baskets_readonly()` method
   - Updated `_schedule_labs_readonly()` method

## Files Created

1. **[test_multi_teacher_rotation.py](test_multi_teacher_rotation.py)**
   - Comprehensive test for multi-teacher rotation
   - Verifies load balancing
   - Checks backward compatibility

## Future Enhancements

1. **Teacher Preference Weights**: Different weights for different teachers
2. **Consecutive Assignment Preference**: Prefer assigning same teacher consecutive slots
3. **Department Affinity**: Consider teacher's home department
4. **Experience-Based Selection**: Weight towards more experienced teachers

## Troubleshooting

### Issue: Teachers still assigned to same slot
**Cause**: Generator not reading `lab_teacher_ids` field correctly
**Fix**: Verify ParallelLabBasketSubject.lab_teacher_ids is populated

### Issue: Unbalanced load distribution
**Cause**: Teachers becoming unavailable midway through scheduling
**Fix**: Check teacher max_hours and availability constraints

### Issue: Generation fails with "No eligible teacher available"
**Cause**: All teachers in pool are busy at specific times
**Fix**: Check room availability, adjust lab schedule, or add more teachers

## References

- `ClassSubjectTeacher` model: Fixed teacher-subject mapping
- `ParallelLabBasketSubject` model: Multi-teacher support
- `ComponentRequirement.teacher_ids`: Multiple teachers per component
- [ALGORITHM_FIXES.md](ALGORITHM_FIXES.md): Related algorithm fixes
