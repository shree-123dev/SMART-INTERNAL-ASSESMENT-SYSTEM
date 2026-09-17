import math
import sqlite3
from config import (
    MIN_ATTENDANCE_PERCENTAGE,
    MAX_IA1_MARKS,
    MIN_PASS_IA1,
    MAX_IA2_MARKS,
    MIN_PASS_IA2,
    MIN_PASS_COMBINED_IA,
    MAX_PRACTICAL_MARKS,
    MIN_PASS_PRACTICAL,
    MAX_ASSIGNMENT_MARKS,
    MIN_PASS_ASSIGNMENT,
    MAX_ORAL_MARKS,
    MIN_PASS_ORAL,
    TOTAL_CIE_MAX
)
from database import get_db_connection

def calculate_student_cie(
    ia1=None,
    ia2=None,
    practical_avg=None,
    assignment_avg=None,
    oral_marks=None,
    attendance_pct=None
):
    """
    Pure calculation function that evaluates passing status across all institutional CIE components:
    - IA1: min 8 / 20
    - IA2: min 8 / 20
    - Combined IA: min 16 / 40
    - Practical Experiments: min 10 / 15
    - Assignments: min 15 / 30
    - Oral / Viva: min 15 / 25
    - Attendance: min 75.0%
    - Total CIE: scale out of 90.0 (IA avg + practical + assignment + oral)
    - Overall Status: 'PASS' / 'FAIL' / 'PENDING'
    """
    has_ia1 = ia1 is not None and str(ia1) != ""
    has_ia2 = ia2 is not None and str(ia2) != ""
    valid_ias = [float(x) for x in [ia1, ia2] if x is not None and str(x) != ""]
    ia_avg = round(sum(valid_ias) / len(valid_ias), 2) if valid_ias else None
    combined_ia_score = round(sum(valid_ias), 2) if (has_ia1 and has_ia2) else None

    is_ia1_pass = (float(ia1) >= MIN_PASS_IA1) if has_ia1 else None
    is_ia2_pass = (float(ia2) >= MIN_PASS_IA2) if has_ia2 else None
    is_combined_ia_pass = (combined_ia_score >= MIN_PASS_COMBINED_IA) if (has_ia1 and has_ia2) else None

    is_practical_pass = (float(practical_avg) >= MIN_PASS_PRACTICAL) if practical_avg is not None and str(practical_avg) != "" else None
    is_assignment_pass = (float(assignment_avg) >= MIN_PASS_ASSIGNMENT) if assignment_avg is not None and str(assignment_avg) != "" else None
    is_oral_pass = (float(oral_marks) >= MIN_PASS_ORAL) if oral_marks is not None and str(oral_marks) != "" else None
    is_attendance_pass = (float(attendance_pct) >= MIN_ATTENDANCE_PERCENTAGE) if attendance_pct is not None and str(attendance_pct) != "" else None

    oral_val = float(oral_marks) if oral_marks is not None and str(oral_marks) != "" else None
    prac_val = float(practical_avg) if practical_avg is not None and str(practical_avg) != "" else None
    assign_val = float(assignment_avg) if assignment_avg is not None and str(assignment_avg) != "" else None

    cie_parts = [p for p in [ia_avg, prac_val, assign_val, oral_val] if p is not None]
    total_cie = round(sum(cie_parts), 2) if cie_parts else None

    component_passes = [is_ia1_pass, is_ia2_pass, is_combined_ia_pass, is_practical_pass, is_assignment_pass, is_oral_pass]
    if attendance_pct is not None:
        component_passes.append(is_attendance_pass)

    if any(p is False for p in component_passes):
        overall_status = "FAIL"
    elif all(p is True for p in component_passes):
        overall_status = "PASS"
    else:
        overall_status = "PENDING"

    return {
        "ia1": float(ia1) if ia1 is not None and str(ia1) != "" else None,
        "ia2": float(ia2) if ia2 is not None and str(ia2) != "" else None,
        "ia_avg": ia_avg,
        "combined_ia_score": combined_ia_score,
        "is_ia1_pass": is_ia1_pass,
        "is_ia2_pass": is_ia2_pass,
        "is_combined_ia_pass": is_combined_ia_pass,
        "practical_avg": prac_val,
        "is_practical_pass": is_practical_pass,
        "assignment_avg": assign_val,
        "is_assignment_pass": is_assignment_pass,
        "oral_marks": oral_val,
        "is_oral_pass": is_oral_pass,
        "attendance_pct": float(attendance_pct) if attendance_pct is not None and str(attendance_pct) != "" else None,
        "is_attendance_pass": is_attendance_pass,
        "total_cie": total_cie,
        "max_cie": TOTAL_CIE_MAX,
        "overall_status": overall_status
    }


def calculate_required_labs(present: int, total: int, min_pct: float = MIN_ATTENDANCE_PERCENTAGE):
    """
    Calculates the exact minimum integer number of consecutive future practical/lab sessions
    a student must attend to reach the minimum required attendance percentage (default 75%).
    
    Formula:
        (P + N) / (T + N) >= R
        where P = Present sessions, T = Total conducted sessions, R = min_pct / 100.0, N = required labs.
        N = ceil((R * T - P) / (1 - R))
    
    Returns:
        tuple: (additional_labs_required: int, projected_attendance_percentage: float or None)
    """
    if total == 0:
        return 0, None

    current_pct = (present / total) * 100.0
    if current_pct >= min_pct:
        return 0, round(current_pct, 2)

    req_ratio = min_pct / 100.0
    if req_ratio >= 1.0:
        if present == total:
            return 0, 100.0
        return 0, round(current_pct, 2)

    needed = math.ceil((req_ratio * total - present) / (1.0 - req_ratio))
    needed = max(0, int(needed))

    # Safety verification loop ensuring mathematically exact integer N
    while (present + needed) / (total + needed) < (req_ratio - 1e-9):
        needed += 1

    projected_pct = round(((present + needed) / (total + needed)) * 100.0, 2)
    return needed, projected_pct


def get_student_subject_attendance(student_usn: str, subject_code: str, conn=None):
    """
    Retrieves and calculates subject/lab-wise attendance metrics for an individual student.
    Guarantees subject isolation (attendance from one subject never affects another).
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    # 1. Total conducted practical sessions for this subject
    cursor.execute("""
        SELECT COUNT(*) FROM practical_sessions
        WHERE subject_id = ?
    """, (subject_code,))
    total_sessions_row = cursor.fetchone()
    total_sessions = total_sessions_row[0] if total_sessions_row else 0

    # 2. Present sessions for this student in this subject
    cursor.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE student_id = ? AND subject_id = ? AND status = 'Present'
    """, (student_usn, subject_code))
    present_sessions_row = cursor.fetchone()
    present_sessions = present_sessions_row[0] if present_sessions_row else 0

    # Safeguard: if present records exceed conducted sessions in database
    if present_sessions > total_sessions:
        total_sessions = present_sessions

    absent_sessions = max(0, total_sessions - present_sessions)

    # 3. Attendance percentage & Eligibility
    if total_sessions == 0:
        attendance_percentage = None
        status = "No Sessions"
        is_eligible = None
        additional_labs_required = 0
        projected_attendance = None
    else:
        attendance_percentage = round((present_sessions / total_sessions) * 100.0, 2)
        is_eligible = attendance_percentage >= MIN_ATTENDANCE_PERCENTAGE
        status = "ELIGIBLE" if is_eligible else "NOT ELIGIBLE"
        additional_labs_required, projected_attendance = calculate_required_labs(
            present_sessions, total_sessions, MIN_ATTENDANCE_PERCENTAGE
        )

    if should_close:
        conn.close()

    return {
        "usn": student_usn,
        "subject_code": subject_code,
        "total_sessions": total_sessions,
        "present_sessions": present_sessions,
        "absent_sessions": absent_sessions,
        "attendance_percentage": attendance_percentage,
        "required_percentage": MIN_ATTENDANCE_PERCENTAGE,
        "status": status,
        "is_eligible": is_eligible,
        "additional_labs_required": additional_labs_required,
        "projected_attendance": projected_attendance
    }


def get_student_subject_marks(student_usn: str, subject_code: str, conn=None):
    """
    Retrieves and calculates all assessment marks components for an individual student in a subject:
    - IA1 (Max: 20, Pass: 8)
    - IA2 (Max: 20, Pass: 8)
    - Combined IA (Pass: 16)
    - Practical Experiments (Max: 15, Pass: 10)
    - Assignments (Max: 30, Pass: 15)
    - Oral / Viva Examination (Max: 25, Pass: 15)
    - Continuous Internal Evaluation (CIE) Total out of 90.0
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    # IA1, IA2 & Oral Marks (internal_marks table)
    cursor.execute("""
        SELECT ia1, ia2, max_ia1, max_ia2, oral_marks, max_oral_marks, oral_recorded_date
        FROM internal_marks
        WHERE student_id = ? AND subject_id = ?
    """, (student_usn, subject_code))
    ia_row = cursor.fetchone()

    ia1 = ia_row["ia1"] if ia_row and ia_row["ia1"] is not None else None
    ia2 = ia_row["ia2"] if ia_row and ia_row["ia2"] is not None else None
    max_ia1 = ia_row["max_ia1"] if ia_row and ia_row["max_ia1"] is not None else MAX_IA1_MARKS
    max_ia2 = ia_row["max_ia2"] if ia_row and ia_row["max_ia2"] is not None else MAX_IA2_MARKS
    oral_marks = ia_row["oral_marks"] if ia_row and ia_row["oral_marks"] is not None else None
    max_oral_marks = ia_row["max_oral_marks"] if ia_row and ia_row["max_oral_marks"] is not None else MAX_ORAL_MARKS
    oral_recorded_date = ia_row["oral_recorded_date"] if ia_row and ia_row["oral_recorded_date"] else None

    # Calculate IA Average (/20) and Combined IA Score (/40)
    has_ia1 = ia1 is not None and str(ia1) != ""
    has_ia2 = ia2 is not None and str(ia2) != ""
    valid_ias = [float(x) for x in [ia1, ia2] if x is not None and str(x) != ""]
    ia_avg = round(sum(valid_ias) / len(valid_ias), 2) if valid_ias else None
    combined_ia_score = round(sum(valid_ias), 2) if (has_ia1 and has_ia2) else None

    # IA Passing Validations
    is_ia1_pass = (float(ia1) >= MIN_PASS_IA1) if has_ia1 else None
    is_ia2_pass = (float(ia2) >= MIN_PASS_IA2) if has_ia2 else None
    is_combined_ia_pass = (combined_ia_score >= MIN_PASS_COMBINED_IA) if (has_ia1 and has_ia2) else None

    # Practical & Assignment Marks per Experiment (experiment_marks table)
    cursor.execute("""
        SELECT id, experiment_no, experiment_name, practical_marks, assignment_marks,
               max_practical_marks, max_assignment_marks, recorded_date
        FROM experiment_marks
        WHERE student_id = ? AND subject_id = ?
        ORDER BY id ASC
    """, (student_usn, subject_code))
    experiments = cursor.fetchall()

    experiments_list = []
    practical_scores = []
    assignment_scores = []

    for exp in experiments:
        p_mark = float(exp["practical_marks"]) if exp["practical_marks"] is not None else 0.0
        a_mark = float(exp["assignment_marks"]) if exp["assignment_marks"] is not None else 0.0
        practical_scores.append(p_mark)
        assignment_scores.append(a_mark)

        experiments_list.append({
            "id": exp["id"],
            "experiment_no": exp["experiment_no"],
            "experiment_name": exp["experiment_name"],
            "practical_marks": p_mark,
            "max_practical_marks": exp["max_practical_marks"] or MAX_PRACTICAL_MARKS,
            "assignment_marks": a_mark,
            "max_assignment_marks": exp["max_assignment_marks"] or MAX_ASSIGNMENT_MARKS,
            "recorded_date": exp["recorded_date"]
        })

    practical_avg = round(sum(practical_scores) / len(practical_scores), 2) if practical_scores else None
    assignment_avg = round(sum(assignment_scores) / len(assignment_scores), 2) if assignment_scores else None

    # Practical, Assignment, and Oral Passing Validations
    is_practical_pass = (practical_avg >= MIN_PASS_PRACTICAL) if practical_avg is not None else None
    is_assignment_pass = (assignment_avg >= MIN_PASS_ASSIGNMENT) if assignment_avg is not None else None
    is_oral_pass = (float(oral_marks) >= MIN_PASS_ORAL) if oral_marks is not None and str(oral_marks) != "" else None

    # Cumulative Continuous Internal Evaluation (CIE) Total (/90)
    oral_val = float(oral_marks) if oral_marks is not None and str(oral_marks) != "" else None
    cie_parts = [p for p in [ia_avg, practical_avg, assignment_avg, oral_val] if p is not None]
    total_cie = round(sum(cie_parts), 2) if cie_parts else None

    # Overall Subject Assessment Status
    component_passes = [is_ia1_pass, is_ia2_pass, is_combined_ia_pass, is_practical_pass, is_assignment_pass, is_oral_pass]
    if any(p is False for p in component_passes):
        overall_status = "FAIL"
    elif all(p is True for p in component_passes):
        overall_status = "PASS"
    else:
        overall_status = "PENDING"

    if should_close:
        conn.close()

    return {
        # IA Component
        "ia1": ia1,
        "ia2": ia2,
        "max_ia1": max_ia1,
        "max_ia2": max_ia2,
        "ia_avg": ia_avg,
        "combined_ia_score": combined_ia_score,
        "min_pass_ia1": MIN_PASS_IA1,
        "min_pass_ia2": MIN_PASS_IA2,
        "min_pass_combined_ia": MIN_PASS_COMBINED_IA,
        "is_ia1_pass": is_ia1_pass,
        "is_ia2_pass": is_ia2_pass,
        "is_combined_ia_pass": is_combined_ia_pass,
        # Practical Component
        "practical_avg": practical_avg,
        "max_practical": MAX_PRACTICAL_MARKS,
        "min_pass_practical": MIN_PASS_PRACTICAL,
        "is_practical_pass": is_practical_pass,
        # Assignment Component
        "assignment_avg": assignment_avg,
        "max_assignment": MAX_ASSIGNMENT_MARKS,
        "min_pass_assignment": MIN_PASS_ASSIGNMENT,
        "is_assignment_pass": is_assignment_pass,
        # Oral Component
        "oral_marks": oral_val,
        "max_oral_marks": max_oral_marks,
        "min_pass_oral": MIN_PASS_ORAL,
        "is_oral_pass": is_oral_pass,
        "oral_recorded_date": oral_recorded_date,
        # Total CIE & Result
        "total_cie": total_cie,
        "max_cie": TOTAL_CIE_MAX,
        "overall_status": overall_status,
        "experiments": experiments_list,
        "experiment_count": len(experiments_list)
    }


def get_student_subject_complete_summary(student_usn: str, subject_code: str, conn=None):
    """
    Generates a unified, complete summary containing both Attendance & CIE Assessment
    metrics for a single student and subject.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    # Student metadata
    cursor.execute("""
        SELECT usn, fullname, email, department, semester, section
        FROM students WHERE usn = ?
    """, (student_usn,))
    student = cursor.fetchone()

    # Subject metadata
    cursor.execute("""
        SELECT subject_code, subject_name, department, semester
        FROM subjects WHERE subject_code = ?
    """, (subject_code,))
    subject = cursor.fetchone()

    att = get_student_subject_attendance(student_usn, subject_code, conn=conn)
    marks = get_student_subject_marks(student_usn, subject_code, conn=conn)

    if should_close:
        conn.close()

    return {
        "student": dict(student) if student else {"usn": student_usn, "fullname": student_usn},
        "subject": dict(subject) if subject else {"subject_code": subject_code, "subject_name": subject_code},
        "attendance": att,
        "marks": marks
    }


def get_class_attendance_summary(subject_code: str = None, department: str = None, semester: int = None, section: str = None, conn=None):
    """
    Computes attendance metrics for students enrolled in a subject cohort.
    If subject_code is None, computes across all active curriculum subjects.
    Supports filtering by department, semester, and section.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    if subject_code:
        cursor.execute("SELECT subject_code, subject_name, department, semester FROM subjects WHERE subject_code = ?", (subject_code,))
        subjects = cursor.fetchall()
    else:
        sub_query = "SELECT subject_code, subject_name, department, semester FROM subjects WHERE 1=1"
        sub_params = []
        if department:
            sub_query += " AND department = ?"
            sub_params.append(department)
        if semester:
            sub_query += " AND semester = ?"
            sub_params.append(int(semester))
        sub_query += " ORDER BY subject_code ASC"
        cursor.execute(sub_query, sub_params)
        subjects = cursor.fetchall()

    if not subjects:
        if should_close:
            conn.close()
        return []

    results = []
    for sub in subjects:
        code = sub["subject_code"]
        name = sub["subject_name"]
        target_dept = department or sub["department"]
        target_sem = semester or sub["semester"]

        query = "SELECT usn, fullname, department, semester, section FROM students WHERE 1=1"
        params = []
        if target_dept:
            query += " AND department = ?"
            params.append(target_dept)
        if target_sem:
            query += " AND semester = ?"
            params.append(int(target_sem))
        if section:
            query += " AND section = ?"
            params.append(section.upper())

        query += " ORDER BY usn ASC"
        cursor.execute(query, params)
        students = cursor.fetchall()

        for st in students:
            usn = st["usn"]
            att = get_student_subject_attendance(usn, code, conn=conn)
            results.append({
                "usn": usn,
                "fullname": st["fullname"],
                "department": st["department"],
                "semester": st["semester"],
                "section": st["section"],
                "subject_code": code,
                "subject_name": name,
                "total_sessions": att["total_sessions"],
                "present_sessions": att["present_sessions"],
                "absent_sessions": att["absent_sessions"],
                "attendance_percentage": att["attendance_percentage"],
                "required_percentage": att["required_percentage"],
                "status": att["status"],
                "is_eligible": att["is_eligible"],
                "additional_labs_required": att["additional_labs_required"],
                "projected_attendance": att["projected_attendance"]
            })

    if should_close:
        conn.close()

    return results


def get_class_complete_summary(subject_code: str = None, department: str = None, semester: int = None, section: str = None, conn=None):
    """
    Computes complete integrated summary (Attendance + IA Marks + Practical + Assignment + Oral + Total CIE)
    for students enrolled in a subject cohort.
    If subject_code is None, computes across all active curriculum subjects.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    if subject_code:
        cursor.execute("SELECT subject_code, subject_name, department, semester FROM subjects WHERE subject_code = ?", (subject_code,))
        subjects = cursor.fetchall()
    else:
        sub_query = "SELECT subject_code, subject_name, department, semester FROM subjects WHERE 1=1"
        sub_params = []
        if department:
            sub_query += " AND department = ?"
            sub_params.append(department)
        if semester:
            sub_query += " AND semester = ?"
            sub_params.append(int(semester))
        sub_query += " ORDER BY subject_code ASC"
        cursor.execute(sub_query, sub_params)
        subjects = cursor.fetchall()

    if not subjects:
        if should_close:
            conn.close()
        return []

    results = []
    for sub in subjects:
        code = sub["subject_code"]
        name = sub["subject_name"]
        target_dept = department or sub["department"]
        target_sem = semester or sub["semester"]

        query = "SELECT usn, fullname, department, semester, section FROM students WHERE 1=1"
        params = []
        if target_dept:
            query += " AND department = ?"
            params.append(target_dept)
        if target_sem:
            query += " AND semester = ?"
            params.append(int(target_sem))
        if section:
            query += " AND section = ?"
            params.append(section.upper())

        query += " ORDER BY usn ASC"
        cursor.execute(query, params)
        students = cursor.fetchall()

        for st in students:
            usn = st["usn"]
            summary = get_student_subject_complete_summary(usn, code, conn=conn)
            att = summary["attendance"]
            marks = summary["marks"]

            results.append({
                "usn": usn,
                "fullname": st["fullname"],
                "department": st["department"],
                "semester": st["semester"],
                "section": st["section"],
                "subject_code": code,
                "subject_name": name,
                # Attendance metrics
                "total_sessions": att["total_sessions"],
                "present_sessions": att["present_sessions"],
                "absent_sessions": att["absent_sessions"],
                "attendance_percentage": att["attendance_percentage"],
                "required_percentage": att["required_percentage"],
                "status": att["status"],
                "is_eligible": att["is_eligible"],
                "additional_labs_required": att["additional_labs_required"],
                "projected_attendance": att["projected_attendance"],
                # Marks metrics
                "ia1": marks["ia1"],
                "ia2": marks["ia2"],
                "ia_avg": marks["ia_avg"],
                "combined_ia_score": marks["combined_ia_score"],
                "is_ia1_pass": marks["is_ia1_pass"],
                "is_ia2_pass": marks["is_ia2_pass"],
                "is_combined_ia_pass": marks["is_combined_ia_pass"],
                "practical_avg": marks["practical_avg"],
                "is_practical_pass": marks["is_practical_pass"],
                "assignment_avg": marks["assignment_avg"],
                "is_assignment_pass": marks["is_assignment_pass"],
                "oral_marks": marks["oral_marks"],
                "is_oral_pass": marks["is_oral_pass"],
                "total_cie": marks["total_cie"],
                "overall_status": marks["overall_status"]
            })

    if should_close:
        conn.close()

    return results
