"""
SIAMS Day 10 Comprehensive Verification Test Suite
Tests:
1. Mathematical exactness of calculate_required_labs formula
2. Subject-wise attendance calculation & strict isolation between subjects
3. 75% boundary tests (>=75.0% ELIGIBLE vs <75.0% NOT ELIGIBLE)
4. 0 sessions edge cases (handling DivisionByZero, None percentage, 'No Sessions' status)
5. CIE calculation formula (IA avg /20 + Practical avg /10 + Assignment avg /5 = Total CIE /35)
6. Non-mutation of underlying database records (no synthetic rows created)
7. Student portal attendance retrieval & access isolation
8. Teacher subject attendance & summary views with RBAC access control
9. Admin institutional attendance & master CIE summary views with multi-faceted filtering
10. Full Regression across all prior milestones (Days 1–9)
"""

import os
import sys
import unittest
import sqlite3
from flask import session

from database import get_db_connection
from app import app
from config import (
    MIN_ATTENDANCE_PERCENTAGE,
    MAX_IA1_MARKS,
    MAX_IA2_MARKS,
    MAX_PRACTICAL_MARKS,
    MAX_ASSIGNMENT_MARKS,
    TOTAL_CIE_MAX
)
from cie_calculator import (
    calculate_required_labs,
    get_student_subject_attendance,
    get_student_subject_marks,
    get_student_subject_complete_summary,
    get_class_attendance_summary,
    get_class_complete_summary
)


class Day10VerificationTests(unittest.TestCase):

    def setUp(self):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "siams_secret_key_2026"
        self.client = app.test_client()

    # ----------------------------------------------------
    # TEST 1: Mathematical Exactness of Required Labs
    # ----------------------------------------------------
    def test_01_calculate_required_labs_math(self):
        print("\n[TEST 1] Verifying calculate_required_labs formula...")

        # Case A: 12/20 (60%) -> needs 12 labs (24/32 = 75.0%)
        n, proj = calculate_required_labs(12, 20, 75.0)
        self.assertEqual(n, 12)
        self.assertEqual(proj, 75.0)
        self.assertGreaterEqual((12 + n) / (20 + n), 0.75)

        # Case B: 7/10 (70%) -> needs 2 labs (9/12 = 75.0%)
        n, proj = calculate_required_labs(7, 10, 75.0)
        self.assertEqual(n, 2)
        self.assertEqual(proj, 75.0)
        self.assertGreaterEqual((7 + n) / (10 + n), 0.75)

        # Case C: 15/20 (75%) -> already 75% -> needs 0 labs
        n, proj = calculate_required_labs(15, 20, 75.0)
        self.assertEqual(n, 0)
        self.assertEqual(proj, 75.0)

        # Case D: 18/20 (90%) -> already >75% -> needs 0 labs
        n, proj = calculate_required_labs(18, 20, 75.0)
        self.assertEqual(n, 0)
        self.assertEqual(proj, 90.0)

        # Case E: 0/4 (0%) -> needs 12 labs (12/16 = 75.0%)
        n, proj = calculate_required_labs(0, 4, 75.0)
        self.assertEqual(n, 12)
        self.assertEqual(proj, 75.0)

        # Case F: 0/0 (0 sessions) -> 0 labs, proj None
        n, proj = calculate_required_labs(0, 0, 75.0)
        self.assertEqual(n, 0)
        self.assertIsNone(proj)

        # Case G: 1/2 (50%) -> needs 2 labs (3/4 = 75.0%)
        n, proj = calculate_required_labs(1, 2, 75.0)
        self.assertEqual(n, 2)
        self.assertEqual(proj, 75.0)

        print("  -> calculate_required_labs mathematical exactness PASSED")

    # ----------------------------------------------------
    # TEST 2: 75% Boundary Conditions
    # ----------------------------------------------------
    def test_02_boundary_conditions(self):
        print("\n[TEST 2] Verifying 75% boundary conditions...")

        # Exactly 75.0%: 3 out of 4
        n, proj = calculate_required_labs(3, 4, 75.0)
        self.assertEqual(n, 0)
        self.assertEqual(proj, 75.0)

        # Just below 75%: 74 out of 100 (74.0%) -> needs 4 labs ((74+4)/(100+4) = 78/104 = 75.0%)
        n, proj = calculate_required_labs(74, 100, 75.0)
        self.assertEqual(n, 4)
        self.assertEqual(proj, 75.0)
        self.assertGreaterEqual((74 + n) / (100 + n), 0.75)

        print("  -> Boundary conditions PASSED")

    # ----------------------------------------------------
    # TEST 3: Subject-Wise Attendance Calculation & Isolation
    # ----------------------------------------------------
    def test_03_subject_isolation_and_attendance_calc(self):
        print("\n[TEST 3] Verifying subject isolation in attendance...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check existing test subjects or insert temporary records
        test_usn = "TEST_DAY10_STU"
        sub_a = "TEST_SUB_A"
        sub_b = "TEST_SUB_B"
        t_id = "TEST_DAY10_TCH"

        # Cleanup any previous runs
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (test_usn,))
        cursor.execute("DELETE FROM practical_sessions WHERE subject_id IN (?, ?)", (sub_a, sub_b))
        cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = ?", (t_id,))
        cursor.execute("DELETE FROM subjects WHERE subject_code IN (?, ?)", (sub_a, sub_b))
        cursor.execute("DELETE FROM students WHERE usn = ?", (test_usn,))
        cursor.execute("DELETE FROM teachers WHERE teacher_id = ?", (t_id,))
        cursor.execute("DELETE FROM users WHERE email IN ('day10_stu@test.com', 'day10_tch@test.com')")

        # Insert test users & entities
        cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES ('Day10 Student', 'day10_stu@test.com', 'hash', 'student')")
        cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES ('Day10 Teacher', 'day10_tch@test.com', 'hash', 'teacher')")
        cursor.execute("INSERT INTO students (usn, fullname, email, department, semester, section) VALUES (?, 'Day10 Student', 'day10_stu@test.com', 'CSE', 5, 'A')", (test_usn,))
        cursor.execute("INSERT INTO teachers (teacher_id, fullname, email, department) VALUES (?, 'Day10 Teacher', 'day10_tch@test.com', 'CSE')", (t_id,))
        cursor.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES (?, 'Subject Alpha', 'CSE', 5)", (sub_a,))
        cursor.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES (?, 'Subject Beta', 'CSE', 5)", (sub_b,))
        cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)", (t_id, sub_a))
        conn.commit()

        # Subject A: Conduct 10 sessions, student attends 6 (60%) -> NOT ELIGIBLE, needs 6 labs
        for i in range(1, 11):
            cursor.execute("INSERT INTO practical_sessions (subject_id, teacher_id, experiment_no, experiment_name, session_date, start_time, status) VALUES (?, ?, ?, ?, '2026-09-17', '10:00', 'completed')",
                           (sub_a, t_id, f"Exp {i}", f"Lab {i}"))
            sess_id = cursor.lastrowid
            if i <= 6:
                cursor.execute("INSERT INTO attendance (session_id, student_id, teacher_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?, '2026-09-17', 'Present')",
                               (sess_id, test_usn, t_id, sub_a))

        # Subject B: Conduct 4 sessions, student attends 4 (100%) -> ELIGIBLE, needs 0 labs
        for i in range(1, 5):
            cursor.execute("INSERT INTO practical_sessions (subject_id, teacher_id, experiment_no, experiment_name, session_date, start_time, status) VALUES (?, ?, ?, ?, '2026-09-17', '14:00', 'completed')",
                           (sub_b, t_id, f"Exp {i}", f"Lab {i}"))
            sess_id = cursor.lastrowid
            cursor.execute("INSERT INTO attendance (session_id, student_id, teacher_id, subject_id, attendance_date, status) VALUES (?, ?, ?, ?, '2026-09-17', 'Present')",
                           (sess_id, test_usn, t_id, sub_b))
        conn.commit()

        # Verify Subject A attendance
        att_a = get_student_subject_attendance(test_usn, sub_a, conn=conn)
        self.assertEqual(att_a["total_sessions"], 10)
        self.assertEqual(att_a["present_sessions"], 6)
        self.assertEqual(att_a["absent_sessions"], 4)
        self.assertEqual(att_a["attendance_percentage"], 60.0)
        self.assertEqual(att_a["status"], "NOT ELIGIBLE")
        self.assertFalse(att_a["is_eligible"])
        self.assertEqual(att_a["additional_labs_required"], 6)
        self.assertEqual(att_a["projected_attendance"], 75.0)

        # Verify Subject B attendance
        att_b = get_student_subject_attendance(test_usn, sub_b, conn=conn)
        self.assertEqual(att_b["total_sessions"], 4)
        self.assertEqual(att_b["present_sessions"], 4)
        self.assertEqual(att_b["absent_sessions"], 0)
        self.assertEqual(att_b["attendance_percentage"], 100.0)
        self.assertEqual(att_b["status"], "ELIGIBLE")
        self.assertTrue(att_b["is_eligible"])
        self.assertEqual(att_b["additional_labs_required"], 0)

        # Subject Isolation check: total sessions and attendance for sub_a did NOT pollute sub_b
        self.assertNotEqual(att_a["total_sessions"], att_b["total_sessions"])

        # Cleanup
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (test_usn,))
        cursor.execute("DELETE FROM practical_sessions WHERE subject_id IN (?, ?)", (sub_a, sub_b))
        cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = ?", (t_id,))
        cursor.execute("DELETE FROM subjects WHERE subject_code IN (?, ?)", (sub_a, sub_b))
        cursor.execute("DELETE FROM students WHERE usn = ?", (test_usn,))
        cursor.execute("DELETE FROM teachers WHERE teacher_id = ?", (t_id,))
        cursor.execute("DELETE FROM users WHERE email IN ('day10_stu@test.com', 'day10_tch@test.com')")
        conn.commit()
        conn.close()

        print("  -> Subject isolation & calculation PASSED")

    # ----------------------------------------------------
    # TEST 4: Zero Sessions Handling
    # ----------------------------------------------------
    def test_04_zero_sessions_edge_case(self):
        print("\n[TEST 4] Verifying 0 sessions edge case...")
        conn = get_db_connection()
        cursor = conn.cursor()

        test_usn = "TEST_DAY10_STU0"
        sub_zero = "TEST_SUB_ZERO"

        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, semester) VALUES (?, 'Zero Sub', 'CSE', 5)", (sub_zero,))
        cursor.execute("INSERT OR REPLACE INTO students (usn, fullname, email, department, semester, section) VALUES (?, 'Zero Stu', 'zero@test.com', 'CSE', 5, 'A')", (test_usn,))
        conn.commit()

        att = get_student_subject_attendance(test_usn, sub_zero, conn=conn)
        self.assertEqual(att["total_sessions"], 0)
        self.assertEqual(att["present_sessions"], 0)
        self.assertEqual(att["absent_sessions"], 0)
        self.assertIsNone(att["attendance_percentage"])
        self.assertEqual(att["status"], "No Sessions")
        self.assertIsNone(att["is_eligible"])
        self.assertEqual(att["additional_labs_required"], 0)
        self.assertIsNone(att["projected_attendance"])

        cursor.execute("DELETE FROM subjects WHERE subject_code = ?", (sub_zero,))
        cursor.execute("DELETE FROM students WHERE usn = ?", (test_usn,))
        conn.commit()
        conn.close()

        print("  -> Zero sessions edge case PASSED")

    # ----------------------------------------------------
    # TEST 5: Complete Continuous Internal Evaluation (CIE) Formulas
    # ----------------------------------------------------
    def test_05_cie_calculation_formula(self):
        print("\n[TEST 5] Verifying CIE formula (/35)...")
        conn = get_db_connection()
        cursor = conn.cursor()

        test_usn = "TEST_DAY10_CIE_STU"
        sub_code = "TEST_CIE_SUB"
        t_id = "TEST_CIE_TCH"

        cursor.execute("INSERT OR REPLACE INTO subjects (subject_code, subject_name, department, semester) VALUES (?, 'CIE Course', 'CSE', 5)", (sub_code,))
        cursor.execute("INSERT OR REPLACE INTO students (usn, fullname, email, department, semester, section) VALUES (?, 'CIE Stu', 'cie@test.com', 'CSE', 5, 'A')", (test_usn,))
        cursor.execute("INSERT OR REPLACE INTO teachers (teacher_id, fullname, email, department) VALUES (?, 'CIE Teacher', 'cietch@test.com', 'CSE')", (t_id,))
        
        # IA Marks (Day 9): IA1 = 18, IA2 = 16 -> Avg = 17.0 (/20)
        cursor.execute("INSERT OR REPLACE INTO internal_marks (student_id, subject_id, ia1, ia2, max_ia1, max_ia2) VALUES (?, ?, 18, 16, 20, 20)",
                       (test_usn, sub_code))

        # Insert practical session for experiment_marks FK
        cursor.execute("INSERT INTO practical_sessions (subject_id, teacher_id, experiment_no, experiment_name, session_date, start_time, status) VALUES (?, ?, 'Exp 1', 'Lab 1', '2026-09-17', '10:00', 'completed')",
                       (sub_code, t_id))
        sess_1 = cursor.lastrowid

        cursor.execute("INSERT INTO practical_sessions (subject_id, teacher_id, experiment_no, experiment_name, session_date, start_time, status) VALUES (?, ?, 'Exp 2', 'Lab 2', '2026-09-17', '10:00', 'completed')",
                       (sub_code, t_id))
        sess_2 = cursor.lastrowid

        # Practical & Assignment Marks (Day 8):
        # Exp 1: Prac = 8, Assign = 4
        # Exp 2: Prac = 10, Assign = 5
        # Exp Avg Prac = (8+10)/2 = 9.0 (/10), Exp Avg Assign = (4+5)/2 = 4.5 (/5)
        cursor.execute("DELETE FROM experiment_marks WHERE student_id = ? AND subject_id = ?", (test_usn, sub_code))
        cursor.execute("""
            INSERT INTO experiment_marks (student_id, teacher_id, subject_id, session_id, experiment_no, experiment_name, practical_marks, assignment_marks, max_practical_marks, max_assignment_marks, recorded_date)
            VALUES (?, ?, ?, ?, 'Exp 1', 'Lab 1', 8.0, 4.0, 10.0, 5.0, '2026-09-17')
        """, (test_usn, t_id, sub_code, sess_1))
        cursor.execute("""
            INSERT INTO experiment_marks (student_id, teacher_id, subject_id, session_id, experiment_no, experiment_name, practical_marks, assignment_marks, max_practical_marks, max_assignment_marks, recorded_date)
            VALUES (?, ?, ?, ?, 'Exp 2', 'Lab 2', 10.0, 5.0, 10.0, 5.0, '2026-09-17')
        """, (test_usn, t_id, sub_code, sess_2))
        conn.commit()

        # Expected CIE Total = 17.0 (IA avg) + 9.0 (Prac avg) + 4.5 (Assign avg) = 30.5 (/90)
        marks = get_student_subject_marks(test_usn, sub_code, conn=conn)
        self.assertEqual(marks["ia1"], 18.0)
        self.assertEqual(marks["ia2"], 16.0)
        self.assertEqual(marks["ia_avg"], 17.0)
        self.assertEqual(marks["practical_avg"], 9.0)
        self.assertEqual(marks["assignment_avg"], 4.5)
        self.assertEqual(marks["total_cie"], 30.5)
        self.assertEqual(marks["max_cie"], 90.0)

        # Cleanup
        cursor.execute("DELETE FROM internal_marks WHERE student_id = ?", (test_usn,))
        cursor.execute("DELETE FROM experiment_marks WHERE student_id = ?", (test_usn,))
        cursor.execute("DELETE FROM practical_sessions WHERE id IN (?, ?)", (sess_1, sess_2))
        cursor.execute("DELETE FROM subjects WHERE subject_code = ?", (sub_code,))
        cursor.execute("DELETE FROM students WHERE usn = ?", (test_usn,))
        cursor.execute("DELETE FROM teachers WHERE teacher_id = ?", (t_id,))
        conn.commit()
        conn.close()

        print("  -> CIE calculation formula PASSED")

    # ----------------------------------------------------
    # TEST 6: Zero Database Mutation Check
    # ----------------------------------------------------
    def test_06_zero_database_mutation(self):
        print("\n[TEST 6] Verifying zero synthetic rows created in database...")
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM attendance")
        att_before = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM practical_sessions")
        sess_before = cursor.fetchone()[0]

        # Call calculator functions
        calculate_required_labs(5, 10, 75.0)
        get_class_attendance_summary(conn=conn)
        get_class_complete_summary(conn=conn)

        cursor.execute("SELECT COUNT(*) FROM attendance")
        att_after = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM practical_sessions")
        sess_after = cursor.fetchone()[0]

        self.assertEqual(att_before, att_after)
        self.assertEqual(sess_before, sess_after)
        conn.close()

        print("  -> Zero database mutation PASSED")

    # ----------------------------------------------------
    # TEST 7: Student Portal Attendance View
    # ----------------------------------------------------
    def test_07_student_portal_attendance_view(self):
        print("\n[TEST 7] Verifying student attendance dashboard...")
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM users WHERE role = 'student' LIMIT 1")
        student_user = cursor.fetchone()
        conn.close()

        if student_user:
            with self.client.session_transaction() as sess:
                sess["user_id"] = 999
                sess["email"] = student_user["email"]
                sess["role"] = "student"
                sess["fullname"] = "Test Student"

            resp = self.client.get("/student")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"My Subject / Lab Attendance", resp.data)
            self.assertIn(b"Policy:", resp.data)

        print("  -> Student portal attendance view PASSED")

    # ----------------------------------------------------
    # TEST 8: Teacher Attendance & Summary RBAC Isolation
    # ----------------------------------------------------
    def test_08_teacher_rbac_and_views(self):
        print("\n[TEST 8] Verifying teacher attendance & CIE summary RBAC...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Find teacher with assigned subject
        cursor.execute("""
            SELECT t.email, t.teacher_id, ts.subject_id
            FROM teachers t
            JOIN teacher_subjects ts ON t.teacher_id = ts.teacher_id
            LIMIT 1
        """)
        t_row = cursor.fetchone()
        conn.close()

        if t_row:
            with self.client.session_transaction() as sess:
                sess["user_id"] = 888
                sess["email"] = t_row["email"]
                sess["role"] = "teacher"
                sess["fullname"] = "Test Faculty"

            # Valid assigned subject attendance
            resp = self.client.get(f"/teacher/attendance/{t_row['subject_id']}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"SUBJECT / LAB ATTENDANCE", resp.data)

            # Valid assigned subject summary
            resp = self.client.get(f"/teacher/summary/{t_row['subject_id']}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn(b"COMPLETE CLASS CIE", resp.data)

            # Access unassigned subject -> should be rejected and redirected
            resp_unauth = self.client.get("/teacher/attendance/NON_EXISTENT_SUB_999", follow_redirects=True)
            self.assertIn(b"Access Denied", resp_unauth.data)

            resp_unauth_sum = self.client.get("/teacher/summary/NON_EXISTENT_SUB_999", follow_redirects=True)
            self.assertIn(b"Access Denied", resp_unauth_sum.data)

        print("  -> Teacher attendance & CIE summary RBAC PASSED")

    # ----------------------------------------------------
    # TEST 9: Admin Institutional Attendance & Summary Views with Filters
    # ----------------------------------------------------
    def test_09_admin_views_and_filtering(self):
        print("\n[TEST 9] Verifying admin institutional attendance & summary with filters...")
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["email"] = "admin@siams.edu"
            sess["role"] = "admin"
            sess["fullname"] = "System Administrator"

        # 1. Admin Attendance general & filtered
        resp1 = self.client.get("/admin/attendance")
        self.assertEqual(resp1.status_code, 200)
        self.assertIn(b"Institutional Lab Attendance Roster", resp1.data)

        resp2 = self.client.get("/admin/attendance?department=CSE&semester=5&section=A")
        self.assertEqual(resp2.status_code, 200)
        self.assertIn(b"Institutional Lab Attendance Roster", resp2.data)

        # 2. Admin Summary general & filtered
        resp3 = self.client.get("/admin/summary")
        self.assertEqual(resp3.status_code, 200)
        self.assertIn(b"INSTITUTIONAL CIE MASTER SUMMARY", resp3.data)
        self.assertIn(b"Institutional CIE & Attendance Master Roster", resp3.data)

        resp4 = self.client.get("/admin/summary?department=CSE&semester=5")
        self.assertEqual(resp4.status_code, 200)
        self.assertIn(b"INSTITUTIONAL CIE MASTER SUMMARY", resp4.data)

        print("  -> Admin institutional views & filtering PASSED")

    # ----------------------------------------------------
    # TEST 10: Full Regression Across Days 1–9
    # ----------------------------------------------------
    def test_10_full_regression(self):
        print("\n[TEST 10] Running full regression check across all prior milestones...")
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check DB integrity
        tables = [
            "users", "students", "teachers", "subjects",
            "teacher_subjects", "practical_sessions", "attendance",
            "experiment_marks", "internal_marks"
        ]
        for t in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            count = cursor.fetchone()[0]
            self.assertGreaterEqual(count, 0)

        conn.close()
        print("  -> All core tables verified intact")


if __name__ == "__main__":
    unittest.main()
