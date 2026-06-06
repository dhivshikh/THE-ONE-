"""
Excel Export Service matching the K.Ramakrishnan College timetable format.
ODD SEMESTER FORMAT.
"""
from io import BytesIO
from typing import List, Dict, Tuple
from datetime import datetime
import openpyxl
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

from sqlalchemy.orm import Session, joinedload

from app.db.models import Semester, Allocation, Subject, ComponentType, Teacher

COLLEGE_NAME = "K.RAMAKRISHNAN COLLEGE OF TECHNOLOGY(Autonomous)"
DAY_NAMES = ["MON", "TUE", "WED", "THU", "FRI"]

class TimetableExcelService:
    def __init__(self, db: Session):
        self.db = db

    def _get_subject_mnemonic(self, subject: Subject) -> str:
        if not subject:
            return ""
        acronym = getattr(subject, 'acronym', None)
        if acronym and acronym.strip():
            return acronym.strip()
        words = subject.name.replace('&', ' ').replace('-', ' ').split()
        return "".join(word[0].upper() for word in words if word).strip()

    def _get_component_suffix(self, alloc: Allocation) -> str:
        if alloc.component_type:
            val = alloc.component_type.value
            if val == "theory": return "(L)"
            if val == "tutorial": return "(T)"
            if val == "lab": return " LAB"
        return ""

    def _get_all_semesters(self) -> List[Semester]:
        return self.db.query(Semester).options(
            joinedload(Semester.department)
        ).order_by(Semester.year, Semester.code).all()

    def _get_semester_allocations(self, semester_id: int) -> Tuple[Dict, List[Allocation]]:
        allocations = self.db.query(Allocation).options(
            joinedload(Allocation.subject),
            joinedload(Allocation.teacher),
            joinedload(Allocation.room)
        ).filter(Allocation.semester_id == semester_id).all()
        
        grid = {}
        for alloc in allocations:
            day = alloc.day
            slot = alloc.slot
            if day not in grid: grid[day] = {}
            if slot not in grid[day]: grid[day][slot] = []
            grid[day][slot].append(alloc)
            
        return grid, allocations

    def _build_semester_worksheet(self, ws, semester: Semester, allocations: List[Allocation], grid: Dict):
        # Format Styles
        border_thin = Border(left=Side(style='thin'), right=Side(style='thin'), 
                             top=Side(style='thin'), bottom=Side(style='thin'))
        fill_blue = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        fill_peach = PatternFill(start_color="FCE4D6", end_color="FCE4D6", fill_type="solid")
        fill_grey = PatternFill(start_color="EAEAEA", end_color="EAEAEA", fill_type="solid")

        # Header Details
        dept_name = f"DEPARTMENT OF {semester.department.name.upper()}" if semester.department else "DEPARTMENT OF ARTIFICIAL INTELLIGENCE & MACHINE LEARNING"
        current_year = datetime.now().year
        academic_year_str = f"{current_year} - {str(current_year+1)[-2:]}"
        
        def to_roman(num):
            val = [10, 9, 5, 4, 1]
            syb = ["X", "IX", "V", "IV", "I"]
            roman_num = ''
            i = 0
            while num > 0:
                for _ in range(num // val[i]):
                    roman_num += syb[i]
                    num -= val[i]
                i += 1
            return roman_num
        
        roman_sem = to_roman(semester.semester_number)
        title = f"CLASS TIME TABLE - {roman_sem} SEMESTER - ACADEMIC YEAR {academic_year_str} (ODD SEMESTER)"

        room_counts = {}
        for alloc in allocations:
            if alloc.room and alloc.component_type and alloc.component_type.value == "theory":
                room_counts[alloc.room.name] = room_counts.get(alloc.room.name, 0) + 1
        primary_room = "LHC201"
        if room_counts:
            primary_room = max(room_counts.items(), key=lambda x: x[1])[0]

        section = semester.section or "A"
        strength = str(semester.student_count) if semester.student_count else "59"

        # Apply basic formatting for the first 5 rows (Header)
        for row in range(1, 6):
            ws.row_dimensions[row].height = 20
            for col in range(1, 11):
                cell = ws.cell(row=row, column=col)
                cell.border = border_thin
                cell.font = Font(name='Times New Roman', size=10, bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                if row <= 4:
                    cell.fill = fill_blue

        # Row 1
        ws.cell(row=1, column=1, value="REVISION NO.")
        ws.cell(row=1, column=2, value="***")
        ws.merge_cells('C1:F1')
        ws.cell(row=1, column=3, value=COLLEGE_NAME).fill = fill_peach
        
        ws.merge_cells('G1:J3')
        ws.cell(row=1, column=7, value="Format No:UFP1-01\nIssue No: 01\nDate: 01.07.11").alignment = Alignment(horizontal='left', vertical='top', wrap_text=True)

        # Row 2
        ws.merge_cells('A2:A3')
        ws.cell(row=2, column=1, value="REVISION DATE")
        ws.merge_cells('B2:B3')
        ws.cell(row=2, column=2, value="***")
        
        ws.merge_cells('C2:F2')
        ws.cell(row=2, column=3, value=dept_name)

        # Row 3
        ws.merge_cells('C3:F3')
        ws.cell(row=3, column=3, value=title)

        # Row 4
        ws.cell(row=4, column=1, value="HOD")
        ws.cell(row=4, column=2, value="Dr.T.Avudaiappan")
        ws.cell(row=4, column=3, value="SECTION")
        ws.cell(row=4, column=4, value=section)
        ws.cell(row=4, column=5, value="CHAIR PERSON")
        ws.cell(row=4, column=6, value="Mrs. Joany Franklin")
        ws.cell(row=4, column=7, value="ROOM NO.")
        ws.merge_cells('H4:J4')
        ws.cell(row=4, column=8, value=primary_room)

        # Row 5 (White fill)
        ws.cell(row=5, column=1, value="CLASS ADVISOR")
        ws.cell(row=5, column=2, value="Mrs.M.Bharathi")
        ws.cell(row=5, column=3, value="STRENGTH")
        ws.cell(row=5, column=4, value=strength)
        ws.cell(row=5, column=5, value="ASST.CLASS ADVISOR")
        ws.cell(row=5, column=6, value="***")
        ws.cell(row=5, column=7, value="CLASS REP")
        ws.merge_cells('H5:J5')
        ws.cell(row=5, column=8, value="***")

        # Grid Headers (Row 6)
        headers = ["DAYS", "1", "2", "BREAK", "3", "4", "LUNCH", "5", "6", "7"]
        ws.row_dimensions[6].height = 20
        for i, header in enumerate(headers, 1):
            cell = ws.cell(row=6, column=i, value=header)
            cell.font = Font(name='Times New Roman', size=10, bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border_thin
            cell.fill = fill_grey

        # Timings (Row 7)
        timings = ["TIMINGS", "8:45 a.m. -\n9:45 a.m.", "9:45 a.m. -\n10:45 a.m.", "10:45 a.m.-\n11:00 a.m.", "11:00 a.m.-\n12:00 p.m.", "12:00 p.m.-\n01:00 p.m.", "01:00 p.m.-\n02:00 p.m.", "02:00 p.m.-\n03:00 p.m.", "03:00 p.m.-\n03:50 p.m.", "03:50 p.m.-\n04:40 p.m."]
        ws.row_dimensions[7].height = 30
        for i, t in enumerate(timings, 1):
            cell = ws.cell(row=7, column=i, value=t)
            cell.font = Font(name='Times New Roman', size=8, bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.border = border_thin
            cell.fill = fill_grey

        # Merged Break and Lunch columns
        for row in range(8, 13):
            for col in [4, 7]:
                cell = ws.cell(row=row, column=col)
                cell.fill = fill_grey
                cell.border = border_thin
                
        ws.merge_cells('D8:D12')
        ws.cell(row=8, column=4, value="B\nR\nE\nA\nK").alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.cell(row=8, column=4).font = Font(name='Times New Roman', bold=True)
        
        ws.merge_cells('G8:G12')
        ws.cell(row=8, column=7, value="L\nU\nN\nC\nH").alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.cell(row=8, column=7).font = Font(name='Times New Roman', bold=True)

        slot_to_col = {0: 2, 1: 3, 2: 5, 3: 6, 4: 8, 5: 9, 6: 10}
        
        for day in range(5):
            row_num = 8 + day
            ws.row_dimensions[row_num].height = 25
            cell = ws.cell(row=row_num, column=1, value=DAY_NAMES[day])
            cell.font = Font(name='Times New Roman', bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border_thin
            cell.fill = fill_grey

            skip_cols = set()
            for slot in range(7):
                col_num = slot_to_col[slot]
                if col_num in skip_cols:
                    continue
                    
                allocs = grid.get(day, {}).get(slot, [])
                cell = ws.cell(row=row_num, column=col_num)
                cell.border = border_thin
                cell.font = Font(name='Times New Roman', size=10, bold=True)
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                
                if not allocs:
                    continue
                    
                alloc = allocs[0]
                is_lab = any(a.component_type and a.component_type.value == "lab" for a in allocs)
                
                if getattr(alloc, 'academic_component', None) == 'mentor_period':
                    cell.value = "MENTOR PERIOD"
                else:
                    if is_lab:
                        texts = []
                        for a in allocs:
                            suffix = self._get_component_suffix(a)
                            texts.append(f"{self._get_subject_mnemonic(a.subject)}{suffix}")
                        cell.value = " / ".join(list(set(texts)))
                        
                        if slot < 6:
                            next_allocs = grid.get(day, {}).get(slot+1, [])
                            if next_allocs and any(a.component_type and a.component_type.value == "lab" for a in next_allocs):
                                next_col = slot_to_col[slot+1]
                                ws.merge_cells(start_row=row_num, start_column=col_num, end_row=row_num, end_column=next_col)
                                skip_cols.add(next_col)
                                ws.cell(row=row_num, column=next_col).border = border_thin
                    else:
                        mnemonic = self._get_subject_mnemonic(alloc.subject)
                        suffix = self._get_component_suffix(alloc)
                        cell.value = f"{mnemonic}{suffix}"

        # Subjects Table
        subject_data = {}
        for alloc in allocations:
            if not alloc.subject: continue
            key = (alloc.subject.id, alloc.component_type.value if alloc.component_type else "theory")
            if key not in subject_data:
                subject_data[key] = {
                    "subject": alloc.subject,
                    "teachers": set(),
                    "component": alloc.component_type,
                    "slots": set()
                }
            if alloc.teacher:
                subject_data[key]["teachers"].add(alloc.teacher.name)
            subject_data[key]["slots"].add((alloc.day, alloc.slot))

        # Row 13: Top header span
        ws.merge_cells('A13:J13')
        cell = ws.cell(row=13, column=1, value="L-LECTURE,T-TUTORIAL,P-PRACTICAL,S-SELF STUDY")
        cell.font = Font(name='Times New Roman', size=10, bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.fill = fill_grey
        for c in range(1, 11):
            ws.cell(row=13, column=c).border = border_thin

        # Row 14: Columns header
        col_mappings = [
            (1, 1, "SUB CODE"),
            (2, 3, "SUBJECT NAME"),
            (4, 4, "MNEMONIC"),
            (5, 5, "CREDIT"),
            (6, 7, "STAFF NAME(M)"),
            (8, 8, "DEPT"),
            (9, 10, "TOTAL HOURS")
        ]
        
        for start_col, end_col, title in col_mappings:
            if start_col != end_col:
                ws.merge_cells(start_row=14, start_column=start_col, end_row=14, end_column=end_col)
            cell = ws.cell(row=14, column=start_col, value=title)
            cell.font = Font(name='Times New Roman', size=10, bold=True)
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            cell.fill = fill_grey
            for c in range(start_col, end_col + 1):
                ws.cell(row=14, column=c).border = border_thin

        # Fill subjects
        current_row = 15
        total_hours = 0
        
        for data_row in subject_data.values():
            subj = data_row["subject"]
            tname = "\n".join(sorted(data_row["teachers"])) if data_row["teachers"] else "***"
            hours = len(data_row["slots"])
            total_hours += hours
            
            credit = getattr(subj, 'theory_hours_per_week', 3) or 3
            if getattr(subj, 'lab_hours_per_week', 0):
                credit += getattr(subj, 'lab_hours_per_week', 0) // 2
                
            mnemonic = f"{self._get_subject_mnemonic(subj)}"
            dept_code = semester.department.code if semester.department else "AI"
            
            values = [
                (1, 1, subj.code, 'center'),
                (2, 3, subj.name, 'left'),
                (4, 4, mnemonic, 'center'),
                (5, 5, str(credit), 'center'),
                (6, 7, tname, 'left'),
                (8, 8, dept_code, 'center'),
                (9, 10, str(hours), 'center')
            ]
            
            for start_col, end_col, val, align in values:
                if start_col != end_col:
                    ws.merge_cells(start_row=current_row, start_column=start_col, end_row=current_row, end_column=end_col)
                cell = ws.cell(row=current_row, column=start_col, value=val)
                cell.font = Font(name='Times New Roman', size=9)
                cell.alignment = Alignment(horizontal=align, vertical='center', wrap_text=True)
                for c in range(start_col, end_col + 1):
                    ws.cell(row=current_row, column=c).border = border_thin
                    
            current_row += 1

        # Total hours footer
        ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=8)
        cell = ws.cell(row=current_row, column=1, value="TOTAL HOURS")
        cell.font = Font(name='Times New Roman', size=10, bold=True)
        cell.alignment = Alignment(horizontal='right', vertical='center')
        
        ws.merge_cells(start_row=current_row, start_column=9, end_row=current_row, end_column=10)
        cell = ws.cell(row=current_row, column=9, value=str(total_hours))
        cell.font = Font(name='Times New Roman', size=10, bold=True)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        
        for c in range(1, 11):
            ws.cell(row=current_row, column=c).border = border_thin

        # Column widths
        widths = {
            'A': 12, 'B': 15, 'C': 15, 'D': 8, 'E': 15, 
            'F': 15, 'G': 10, 'H': 15, 'I': 15, 'J': 15
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width

    def generate_semester_excel(self, semester_id: int) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        semester = self.db.query(Semester).filter(Semester.id == semester_id).first()
        safe_code = "".join(c for c in semester.code if c.isalnum() or c in (' ', '-', '_'))
        ws.title = safe_code[:31]
        grid, allocations = self._get_semester_allocations(semester.id)
        self._build_semester_worksheet(ws, semester, allocations, grid)
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()

    def generate_all_timetables_excel_zip(self) -> bytes:
        import zipfile
        buffer = BytesIO()
        semesters = [s for s in self._get_all_semesters() if self._get_semester_allocations(s.id)[1]]
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for sem in semesters:
                wb = openpyxl.Workbook()
                ws = wb.active
                safe_code = "".join(c for c in sem.code if c.isalnum() or c in (' ', '-', '_'))
                ws.title = safe_code[:31]
                grid, allocations = self._get_semester_allocations(sem.id)
                self._build_semester_worksheet(ws, sem, allocations, grid)
                
                wb_buffer = BytesIO()
                wb.save(wb_buffer)
                zipf.writestr(f"timetable_{safe_code}.xlsx", wb_buffer.getvalue())
                
        return buffer.getvalue()

    def generate_all_timetables_excel(self) -> bytes:
        wb = openpyxl.Workbook()
        semesters = [s for s in self._get_all_semesters() if self._get_semester_allocations(s.id)[1]]
        
        if not semesters:
            ws = wb.active
            ws.cell(row=1, column=1, value="No Timetable Generated")
        else:
            for i, semester in enumerate(semesters):
                if i == 0:
                    ws = wb.active
                else:
                    ws = wb.create_sheet()
                    
                safe_code = "".join(c for c in semester.code if c.isalnum() or c in (' ', '-', '_'))
                ws.title = safe_code[:31]
                
                grid, allocations = self._get_semester_allocations(semester.id)
                self._build_semester_worksheet(ws, semester, allocations, grid)
                
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue()
