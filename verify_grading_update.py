"""
Verification Script for Updated Grading & Institutional Examination Criteria
Tests:
1. Configuration constants
2. Database schema migration (oral_marks, max_oral_marks, oral_recorded_date)
3. Calculation engine passing rules (IA1 >= 8, IA2 >= 8, Combined IA >= 16, Practical >= 10/15, Assignment >= 15/30, Oral >= 15/25, Total /90)
4. Overall Status calculation (PASS / FAIL / PENDING)
5. Practical session marks validation (0-15 practical, 0-30 assignment)
6. Oral / Viva evaluation routes & RBAC security
7. Student, Teacher, and Admin summary renderings
"""

import sys
import os
import sqlite3
import unittest
from werkzeug.security import generate_password_hash

# Import application components
from config import (
    MIN_ATTENDANCE_PERCENTAGE,
    MIN_PASS_IA1,
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
from app import app
from database import get_db_connection, init_db
from cie_calculator import (
    calculate_student_cie,
    get_student_subject_complete_summary,
    get_class_complete_summary
)

class TestGradingUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Clean old test records
        cursor.execute("DELETE FROM internal_marks WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM attendance WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM experiment_marks WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM students WHERE usn IN ('1MS24CS999', '1MS24CS_GRADE')")

        # Seed test entities if not present
        cursor.execute("SELECT id FROM users WHERE email = 'teacher_g@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'teacher')",
                           ("Prof. Grading Tester", "teacher_g@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = 'TCH_G'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teachers (teacher_id, fullname, email, department) VALUES ('TCH_G', 'Prof. Grading Tester', 'teacher_g@test.com', 'CSE')")

        cursor.execute("SELECT id FROM users WHERE email = 'student_g@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'student')",
                           ("George Student", "student_g@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM students WHERE usn = '1MS24CS_GRADE'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO students (usn, fullname, email, department, semester, section) VALUES ('1MS24CS_GRADE', 'George Student', 'student_g@test.com', 'CSE', 4, 'A')")

        cursor.execute("SELECT id FROM subjects WHERE subject_code = 'CS999'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES ('CS999', 'Advanced Systems Lab', 'CSE', 4)")

        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_G' AND subject_id = 'CS999'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('TCH_G', 'CS999')")

        conn.commit()
        conn.close()

    @classmethod
    def tearDownClass(cls):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM internal_marks WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM attendance WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM experiment_marks WHERE student_id IN ('1MS24CS999', '1MS24CS_GRADE')")
        cursor.execute("DELETE FROM students WHERE usn IN ('1MS24CS999', '1MS24CS_GRADE')")
        conn.commit()
        conn.close()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def login(self, email, password="pass123"):
        return self.app.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    def test_01_config_constants(self):
        """Verify institutional grading constants in config.py"""
        self.assertEqual(MIN_ATTENDANCE_PERCENTAGE, 75.0)
        self.assertEqual(MIN_PASS_IA1, 8.0)
        self.assertEqual(MIN_PASS_IA2, 8.0)
        self.assertEqual(MIN_PASS_COMBINED_IA, 16.0)
        self.assertEqual(MAX_PRACTICAL_MARKS, 15.0)
        self.assertEqual(MIN_PASS_PRACTICAL, 10.0)
        self.assertEqual(MAX_ASSIGNMENT_MARKS, 30.0)
        self.assertEqual(MIN_PASS_ASSIGNMENT, 15.0)
        self.assertEqual(MAX_ORAL_MARKS, 25.0)
        self.assertEqual(MIN_PASS_ORAL, 15.0)
        self.assertEqual(TOTAL_CIE_MAX, 90.0)
        print("[OK] Test 01 Passed: Configuration constants match institutional examination criteria.")

    def test_02_database_schema(self):
        """Verify oral_marks columns exist in internal_marks table"""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(internal_marks)")
        columns = [row['name'] for row in cursor.fetchall()]
        conn.close()

        self.assertIn('oral_marks', columns)
        self.assertIn('max_oral_marks', columns)
        self.assertIn('oral_recorded_date', columns)
        print("[OK] Test 02 Passed: Database schema contains oral_marks columns.")

    def test_03_cie_calculator_passing_rules(self):
        """Verify passing logic and 90-mark scale calculation in cie_calculator"""
        # Case A: Complete All Pass
        res_pass = calculate_student_cie(
            ia1=16.0,
            ia2=18.0,
            practical_avg=12.5,
            assignment_avg=24.0,
            oral_marks=20.0,
            attendance_pct=85.0
        )
        self.assertTrue(res_pass['is_ia1_pass'])
        self.assertTrue(res_pass['is_ia2_pass'])
        self.assertTrue(res_pass['is_combined_ia_pass'])
        self.assertTrue(res_pass['is_practical_pass'])
        self.assertTrue(res_pass['is_assignment_pass'])
        self.assertTrue(res_pass['is_oral_pass'])
        # Total = ((16+18)/2) + 12.5 + 24.0 + 20.0 = 17.0 + 12.5 + 24.0 + 20.0 = 73.5
        self.assertEqual(res_pass['total_cie'], 73.5)
        self.assertEqual(res_pass['overall_status'], 'PASS')

        # Case B: IA1 fail (<8)
        res_fail_ia1 = calculate_student_cie(
            ia1=7.5,
            ia2=18.0,
            practical_avg=12.5,
            assignment_avg=24.0,
            oral_marks=20.0,
            attendance_pct=85.0
        )
        self.assertFalse(res_fail_ia1['is_ia1_pass'])
        self.assertEqual(res_fail_ia1['overall_status'], 'FAIL')

        # Case C: Combined IA fail (<16) despite IA1=8, IA2=7.5 (sum=15.5)
        res_fail_comb = calculate_student_cie(
            ia1=8.0,
            ia2=7.5,
            practical_avg=12.5,
            assignment_avg=24.0,
            oral_marks=20.0,
            attendance_pct=85.0
        )
        self.assertFalse(res_fail_comb['is_ia2_pass'])
        self.assertFalse(res_fail_comb['is_combined_ia_pass'])
        self.assertEqual(res_fail_comb['overall_status'], 'FAIL')

        # Case D: Practical fail (<10)
        res_fail_prac = calculate_student_cie(
            ia1=10.0,
            ia2=10.0,
            practical_avg=9.5,
            assignment_avg=20.0,
            oral_marks=18.0,
            attendance_pct=80.0
        )
        self.assertFalse(res_fail_prac['is_practical_pass'])
        self.assertEqual(res_fail_prac['overall_status'], 'FAIL')

        # Case E: Assignment fail (<15)
        res_fail_assign = calculate_student_cie(
            ia1=10.0,
            ia2=10.0,
            practical_avg=11.0,
            assignment_avg=14.5,
            oral_marks=18.0,
            attendance_pct=80.0
        )
        self.assertFalse(res_fail_assign['is_assignment_pass'])
        self.assertEqual(res_fail_assign['overall_status'], 'FAIL')

        # Case F: Oral Viva fail (<15)
        res_fail_oral = calculate_student_cie(
            ia1=10.0,
            ia2=10.0,
            practical_avg=11.0,
            assignment_avg=20.0,
            oral_marks=14.0,
            attendance_pct=80.0
        )
        self.assertFalse(res_fail_oral['is_oral_pass'])
        self.assertEqual(res_fail_oral['overall_status'], 'FAIL')

        # Case G: Attendance fail (<75%)
        res_fail_att = calculate_student_cie(
            ia1=15.0,
            ia2=15.0,
            practical_avg=12.0,
            assignment_avg=20.0,
            oral_marks=20.0,
            attendance_pct=70.0
        )
        self.assertEqual(res_fail_att['overall_status'], 'FAIL')

        # Case H: Pending evaluated marks (IA2 not yet held, Oral not held)
        res_pending = calculate_student_cie(
            ia1=10.0,
            ia2=None,
            practical_avg=12.0,
            assignment_avg=20.0,
            oral_marks=None,
            attendance_pct=80.0
        )
        self.assertEqual(res_pending['overall_status'], 'PENDING')
        print("[OK] Test 03 Passed: CIE calculation engine handles all passing thresholds and statuses.")

    def test_04_save_session_marks_validation(self):
        """Verify practical marks (0-15) and assignment marks (0-30) boundary validation"""
        self.login("teacher_g@test.com")

        # Create a test practical session
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO practical_sessions (subject_id, teacher_id, session_date, start_time, status, experiment_no, experiment_name)
            VALUES ('CS999', 'TCH_G', '2026-09-17', '10:00:00', 'active', 'Exp T1', 'Validation Test')
        """)
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Test invalid practical marks (>15)
        res_invalid_prac = self.app.post('/save_session_marks', json={
            'session_id': session_id,
            'student_id': '1MS24CS_GRADE',
            'practical_marks': 16.0,
            'assignment_marks': 10.0
        })
        self.assertIn(b'Practical experiment marks must be between 0 and 15', res_invalid_prac.data)

        # Test invalid assignment marks (>30)
        res_invalid_assign = self.app.post('/save_session_marks', json={
            'session_id': session_id,
            'student_id': '1MS24CS_GRADE',
            'practical_marks': 12.0,
            'assignment_marks': 35.0
        })
        self.assertIn(b'Assignment marks must be between 0 and 30', res_invalid_assign.data)

        # Test valid save
        res_valid = self.app.post('/save_session_marks', json={
            'session_id': session_id,
            'student_id': '1MS24CS_GRADE',
            'practical_marks': 13.5,
            'assignment_marks': 25.0
        })
        self.assertEqual(res_valid.status_code, 200)
        data = res_valid.get_json()
        self.assertTrue(data['success'])

        # Clean up test session
        conn = get_db_connection()
        conn.execute("DELETE FROM attendance WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM experiment_marks WHERE session_id = ?", (session_id,))
        conn.execute("DELETE FROM practical_sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()

        print("[OK] Test 04 Passed: Practical session marks validated against /15 and /30.")

    def test_05_oral_marks_workflow_and_rbac(self):
        """Verify Oral/Viva marks entry, saving, and RBAC authorization"""
        # 1. Access assigned subject oral marks page -> 200
        self.login("teacher_g@test.com")
        res = self.app.get("/oral_marks/CS999")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'ORAL / PRACTICAL VIVA EXAMINATION EVALUATION', res.data)
        self.assertIn(b'Max Scale:', res.data)

        # 2. Access unassigned subject oral marks page -> denied / redirect with error
        res_forbidden = self.app.get("/oral_marks/CS401", follow_redirects=True)
        self.assertIn(b'Access Denied: You are not assigned', res_forbidden.data)

        # 3. Save oral marks for student
        res_save = self.app.post("/oral_marks/save/CS999", data={
            "oral_1MS24CS_GRADE": "21.5"
        }, follow_redirects=True)
        self.assertEqual(res_save.status_code, 200)
        self.assertIn(b'Oral examination marks', res_save.data)

        # 4. Verify marks in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT oral_marks FROM internal_marks WHERE student_id = '1MS24CS_GRADE' AND subject_id = 'CS999'")
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row['oral_marks'], 21.5)

        # 5. Test invalid marks (>25)
        res_invalid = self.app.post("/oral_marks/save/CS999", data={
            "oral_1MS24CS_GRADE": "30.0"
        }, follow_redirects=True)
        self.assertIn(b'out of range', res_invalid.data)

        # 6. Student role cannot access oral marks route
        self.login("student_g@test.com")
        res_stu = self.app.get("/oral_marks/CS999", follow_redirects=True)
        self.assertNotIn(b'Enrolled Student Oral Examination Roster', res_stu.data)

        print("[OK] Test 05 Passed: Oral/Viva examination evaluation and RBAC isolation fully validated.")

    def test_06_summary_views_rendering(self):
        """Verify Student, Teacher, and Admin summary pages render updated grading criteria"""
        # 1. Student Dashboard
        self.login("student_g@test.com")
        res_student = self.app.get('/student')
        self.assertEqual(res_student.status_code, 200)
        self.assertIn(b'Oral / Viva (/25)', res_student.data)
        self.assertIn(b'Combined IA', res_student.data)
        self.assertIn(b'Total (/90)', res_student.data)
        self.assertIn(b'Min Pass: 16', res_student.data)

        # 2. Teacher Summary
        self.login("teacher_g@test.com")
        res_teacher = self.app.get("/teacher/summary/CS999")
        self.assertEqual(res_teacher.status_code, 200)
        self.assertIn(b'Oral / Viva (/25)', res_teacher.data)
        self.assertIn(b'Total (/90)', res_teacher.data)

        # 3. Admin Summary
        self.login("admin@test.com", "admin123")
        res_admin = self.app.get('/admin/summary')
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Oral / Viva (/25, Min 15)', res_admin.data)
        self.assertIn(b'Total CIE (/90)', res_admin.data)

        print("[OK] Test 06 Passed: All summary interfaces render updated grading columns and thresholds.")

if __name__ == '__main__':
    unittest.main()
