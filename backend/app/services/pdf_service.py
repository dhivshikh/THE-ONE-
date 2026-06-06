"""
PDF Generation Service for Official College Timetable Export.
READ-ONLY service - does not modify any timetable data.

Generates PDF that EXACTLY matches the K.Ramakrishnan College timetable format.
Uses Times-Roman font for formal, classic appearance as requested.
ODD SEMESTER FORMAT.
"""
from io import BytesIO
from typing import List, Dict, Tuple
from datetime import datetime
import json

from sqlalchemy.orm import Session, joinedload
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from app.db.models import Semester, Allocation, Subject, ComponentType, Teacher

# Fixed Configuration matching ODD SEM Template
FONT_REGULAR = "Times-Roman"
FONT_BOLD = "Times-Bold"
COLLEGE_NAME = "K.RAMAKRISHNAN COLLEGE OF TECHNOLOGY(Autonomous)"
DAY_NAMES = ["MON", "TUE", "WED", "THU", "FRI"]

COLORS = {
    "black": colors.HexColor("#000000"),
    "white": colors.HexColor("#FFFFFF"),
    "header_blue": colors.HexColor("#D9E1F2"),
    "header_peach": colors.HexColor("#FCE4D6"),
    "grey": colors.HexColor("#EAEAEA"),
}

class TimetablePDFService:
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()

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

    def _build_header_section(self, semester: Semester, allocations: List[Allocation]) -> Table:
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

        header_data = [
            ["REVISION NO.", "***", COLLEGE_NAME, "", "", "", "Format No:UFP1-01\nIssue No: 01\nDate: 01.07.11", ""],
            ["REVISION DATE", "***", dept_name, "", "", "", "", ""],
            ["", "", title, "", "", "", "", ""],
            ["HOD", "Dr.T.Avudaiappan", "SECTION", section, "CHAIR PERSON", "Mrs. Joany Franklin", "ROOM NO.", primary_room],
            ["CLASS ADVISOR", "Mrs.M.Bharathi", "STRENGTH", strength, "ASST.CLASS ADVISOR", "***", "CLASS REP", "***"],
        ]
        
        col_widths = [3.2*cm, 2.0*cm, 4.0*cm, 2.0*cm, 4.0*cm, 6.0*cm, 3.0*cm, 3.5*cm]
        table = Table(header_data, colWidths=col_widths)
        
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            
            # Format No merged across row 1, 2, 3
            ('SPAN', (6, 0), (7, 2)), 
            # Revision date merged rows 2 and 3
            ('SPAN', (0, 1), (0, 2)),
            ('SPAN', (1, 1), (1, 2)),
            
            ('SPAN', (2, 0), (5, 0)), 
            ('SPAN', (2, 1), (5, 1)), 
            ('SPAN', (2, 2), (5, 2)), 
            
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            ('BACKGROUND', (0, 0), (1, 3), COLORS["header_blue"]),
            ('BACKGROUND', (2, 0), (5, 0), COLORS["header_peach"]),
            ('BACKGROUND', (2, 1), (5, 2), COLORS["header_blue"]),
            ('BACKGROUND', (6, 0), (7, 3), COLORS["header_blue"]),
            ('BACKGROUND', (2, 3), (5, 3), COLORS["header_blue"]),
            
            ('BACKGROUND', (0, 4), (-1, 4), COLORS["white"]),
            ('GRID', (0, 0), (-1, -1), 1, COLORS["black"]),
            
            ('ALIGN', (6, 0), (7, 2), 'LEFT'),
            ('FONTSIZE', (6, 0), (7, 2), 7),
        ])
        
        table.setStyle(style)
        return table

    def _build_timetable_grid(self, semester: Semester, grid: Dict) -> Table:
        timings = [
            "8:45 a.m. -\n9:45 a.m.",
            "9:45 a.m. -\n10:45 a.m.",
            "10:45 a.m.-\n11:00 a.m.",
            "11:00 a.m. -\n12:00 p.m.",
            "12:00 p.m. -\n01:00 p.m.",
            "01:00 p.m-\n02:00 p.m.",
            "02:00 p.m. -\n03:00 p.m.",
            "03:00 p.m-\n03:50 p.m.",
            "03:50 p.m. -\n04:40 p.m."
        ]
        
        header_row1 = ["DAYS", "1", "2", "BREAK", "3", "4", "LUNCH", "5", "6", "7"]
        header_row2 = ["TIMINGS", timings[0], timings[1], timings[2], timings[3], timings[4], timings[5], timings[6], timings[7], timings[8]]
        
        data = [header_row1, header_row2]
        slot_to_col = {0: 1, 1: 2, 2: 4, 3: 5, 4: 7, 5: 8, 6: 9}
        
        for day_idx, day_name in enumerate(DAY_NAMES):
            row = [day_name, "", "", "", "", "", "", "", "", ""]
            data.append(row)
            
        col_widths = [3.2*cm, 3.0*cm, 3.0*cm, 2.0*cm, 3.0*cm, 3.0*cm, 2.0*cm, 2.8*cm, 2.8*cm, 2.9*cm]
        row_heights = [0.6*cm, 1.0*cm] + [1.0*cm] * 5
        
        style_commands = [
            ('FONTNAME', (0, 0), (-1, -1), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTSIZE', (0, 1), (-1, 1), 8), 
            
            ('BACKGROUND', (0, 0), (-1, 1), COLORS["grey"]), 
            ('BACKGROUND', (0, 2), (0, -1), COLORS["grey"]), 
            
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, COLORS["black"]),
            
            ('SPAN', (3, 2), (3, 6)),
            ('SPAN', (6, 2), (6, 6)),
            ('BACKGROUND', (3, 2), (3, 6), COLORS["grey"]),
            ('BACKGROUND', (6, 2), (6, 6), COLORS["grey"]),
        ]
        
        data[2][3] = "B\nR\nE\nA\nK"
        data[2][6] = "L\nU\nN\nC\nH"

        for day_idx in range(5):
            row_idx = day_idx + 2
            skip_cols = set()
            for slot_idx in range(7):
                col_idx = slot_to_col[slot_idx]
                if col_idx in skip_cols:
                    continue
                    
                slot_allocs = grid.get(day_idx, {}).get(slot_idx, [])
                if not slot_allocs:
                    continue
                    
                alloc = slot_allocs[0]
                is_lab = any(a.component_type and a.component_type.value == "lab" for a in slot_allocs)
                
                if getattr(alloc, 'academic_component', None) == 'mentor_period':
                    data[row_idx][col_idx] = "MENTOR PERIOD"
                else:
                    if is_lab:
                        texts = []
                        for a in slot_allocs:
                            suffix = self._get_component_suffix(a)
                            # Template explicitly has "DAA LAB", "MLT LAB", etc without "(L)"
                            texts.append(f"{self._get_subject_mnemonic(a.subject)}{suffix}")
                        cell_text = " / ".join(list(set(texts)))
                        data[row_idx][col_idx] = cell_text
                        
                        if slot_idx < 6:
                            next_allocs = grid.get(day_idx, {}).get(slot_idx+1, [])
                            if next_allocs and any(a.component_type and a.component_type.value == "lab" for a in next_allocs):
                                next_col = slot_to_col[slot_idx+1]
                                style_commands.append(('SPAN', (col_idx, row_idx), (next_col, row_idx)))
                                skip_cols.add(next_col)
                    else:
                        mnemonic = self._get_subject_mnemonic(alloc.subject)
                        suffix = self._get_component_suffix(alloc)
                        data[row_idx][col_idx] = f"{mnemonic}{suffix}"
                        
        table = Table(data, colWidths=col_widths, rowHeights=row_heights)
        table.setStyle(TableStyle(style_commands))
        return table

    def _build_subject_table(self, semester: Semester, allocations: List[Allocation]) -> Table:
        header = ["SUB CODE", "SUBJECT NAME", "MNEMONIC", "CREDIT", "STAFF NAME(M)", "DEPT", "TOTAL HOURS"]
        data = [
            ["L-LECTURE,T-TUTORIAL,P-PRACTICAL,S-SELF STUDY", "", "", "", "", "", ""],
            header
        ]
        
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
            dept = semester.department.code if semester.department else "AI"
            
            row = [
                subj.code,
                Paragraph(subj.name, ParagraphStyle('Normal', fontName=FONT_REGULAR, fontSize=9)),
                mnemonic,
                str(credit),
                Paragraph(tname, ParagraphStyle('Normal', fontName=FONT_REGULAR, fontSize=9)),
                dept,
                str(hours)
            ]
            data.append(row)
            
        data.append(["", "", "", "", "", "TOTAL HOURS", str(total_hours)])
        
        col_widths = [2.5*cm, 7.7*cm, 2.5*cm, 2.0*cm, 6.0*cm, 2.0*cm, 5.0*cm]
        table = Table(data, colWidths=col_widths)
        
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
            ('FONTNAME', (0, 0), (-1, 1), FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            
            ('SPAN', (0, 0), (-1, 0)),
            
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 2), (1, -2), 'LEFT'), 
            ('ALIGN', (4, 2), (4, -2), 'LEFT'), 
            
            ('BACKGROUND', (0, 0), (-1, 1), COLORS["grey"]),
            
            ('GRID', (0, 0), (-1, -1), 1, COLORS["black"]),
            
            ('SPAN', (0, -1), (4, -1)),
            ('ALIGN', (5, -1), (5, -1), 'RIGHT'),
            ('FONTNAME', (5, -1), (-1, -1), FONT_BOLD),
        ])
        table.setStyle(style)
        return table

    def _build_semester_page(self, semester: Semester) -> List:
        elements = []
        grid, allocations = self._get_semester_allocations(semester.id)
        
        elements.append(self._build_header_section(semester, allocations))
        elements.append(self._build_timetable_grid(semester, grid))
        elements.append(self._build_subject_table(semester, allocations))
        
        return elements

    def generate_semester_pdf(self, semester: Semester) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.6*cm,
            leftMargin=0.6*cm,
            topMargin=0.6*cm,
            bottomMargin=0.6*cm
        )
        elements = self._build_semester_page(semester)
        doc.build(elements)
        return buffer.getvalue()

    def generate_all_timetables_pdf_zip(self) -> bytes:
        import zipfile
        buffer = BytesIO()
        semesters = self._get_all_semesters()
        
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for sem in semesters:
                pdf_bytes = self.generate_semester_pdf(sem)
                safe_code = "".join(c for c in sem.code if c.isalnum() or c in (' ', '-', '_'))
                zipf.writestr(f"timetable_{safe_code}.pdf", pdf_bytes)
                
        return buffer.getvalue()

    def generate_all_timetables_pdf(self) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=0.6*cm,
            leftMargin=0.6*cm,
            topMargin=0.6*cm,
            bottomMargin=0.6*cm
        )
        elements = []
        semesters = [s for s in self._get_all_semesters() if self._get_semester_allocations(s.id)[1]]
        
        if not semesters:
            elements.append(Paragraph("No Timetable Generated", ParagraphStyle('Empty', fontName=FONT_BOLD, fontSize=18, alignment=TA_CENTER)))
        else:
            for i, semester in enumerate(semesters):
                elements.extend(self._build_semester_page(semester))
                if i < len(semesters) - 1:
                    elements.append(PageBreak())
                    
        doc.build(elements)
        return buffer.getvalue()
