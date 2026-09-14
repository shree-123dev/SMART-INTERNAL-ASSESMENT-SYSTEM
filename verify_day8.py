import sqlite3
import unittest
from datetime import date
from werkzeug.security import generate_password_hash
from app import app
from database import get_db_connection, init_db

class TestDay8QRAttendanceAndMarks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Seed 2 Teachers
        # Teacher A
        cursor.execute("SELECT id FROM users WHERE email = 'teacherA@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'teacher')",
                           ("Prof. Teacher Alpha", "teacherA@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = 'TCH_A'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teachers (teacher_id, fullname, email, department) VALUES ('TCH_A', 'Prof. Teacher Alpha', 'teacherA@test.com', 'CSE')")

        # Teacher B
        cursor.execute("SELECT id FROM users WHERE email = 'teacherB@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'teacher')",
                           ("Prof. Teacher Beta", "teacherB@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = 'TCH_B'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teachers (teacher_id, fullname, email, department) VALUES ('TCH_B', 'Prof. Teacher Beta', 'teacherB@test.com', 'CSE')")

        # Seed 2 Students
        # Student 1
        cursor.execute("SELECT id FROM users WHERE email = 'student1@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'student')",
                           ("Alice Student", "student1@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM students WHERE usn = '1MS24CS001'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO students (usn, fullname, email, department, semester, section) VALUES ('1MS24CS001', 'Alice Student', 'student1@test.com', 'CSE', 4, 'A')")

        # Student 2
        cursor.execute("SELECT id FROM users WHERE email = 'student2@test.com'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, 'student')",
                           ("Bob Student", "student2@test.com", generate_password_hash("pass123")))
        cursor.execute("SELECT id FROM students WHERE usn = '1MS24CS002'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO students (usn, fullname, email, department, semester, section) VALUES ('1MS24CS002', 'Bob Student', 'student2@test.com', 'CSE', 4, 'B')")

        # Seed Subjects
        cursor.execute("SELECT id FROM subjects WHERE subject_code = 'CS401'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES ('CS401', 'Data Structures Lab', 'CSE', 4)")

        cursor.execute("SELECT id FROM subjects WHERE subject_code = 'CS402'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES ('CS402', 'Algorithms Lab', 'CSE', 4)")

        # Assign Subjects
        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_A' AND subject_id = 'CS401'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('TCH_A', 'CS401')")

        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_A' AND subject_id = 'CS402'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('TCH_A', 'CS402')")

        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_B' AND subject_id = 'CS402'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('TCH_B', 'CS402')")

        # Clean any old test sessions, attendance, and experiment marks for these test entities
        cursor.execute("DELETE FROM experiment_marks WHERE student_id IN ('1MS24CS001', '1MS24CS002')")
        cursor.execute("DELETE FROM attendance WHERE student_id IN ('1MS24CS001', '1MS24CS002')")
        cursor.execute("DELETE FROM practical_sessions WHERE teacher_id IN ('TCH_A', 'TCH_B')")

        conn.commit()
        conn.close()

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def login(self, email, password="pass123"):
        return self.app.post("/login", data={"email": email, "password": password}, follow_redirects=True)

    def test_01_start_session_with_experiment(self):
        """Teacher A starts a practical session specifying subject, experiment no, and experiment name."""
        self.login("teacherA@test.com")
        res = self.app.post("/start_session", data={
            "subject_code": "CS401",
            "experiment_no": "Experiment 3",
            "experiment_name": "Implement Stack using Array"
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, teacher_id, subject_id, status, experiment_no, experiment_name
            FROM practical_sessions
            WHERE teacher_id = 'TCH_A' AND subject_id = 'CS401' AND status = 'active'
        """)
        sess = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(sess, "Active session should exist for Teacher A in CS401")
        self.assertEqual(sess["experiment_no"], "Experiment 3")
        self.assertEqual(sess["experiment_name"], "Implement Stack using Array")

    def test_02_scan_student_qr_and_auto_attendance(self):
        """Teacher A scans Student 1 QR: Student identified and attendance marked Present."""
        self.login("teacherA@test.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        sess = cursor.fetchone()
        self.assertIsNotNone(sess)
        session_id = sess["id"]
        conn.close()

        # Call /scan_student_qr
        res = self.app.post("/scan_student_qr", json={
            "session_id": session_id,
            "usn": "1MS24CS001"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["student"]["usn"], "1MS24CS001")
        self.assertEqual(data["student"]["fullname"], "Alice Student")
        self.assertIn("PRESENT", data["attendance_message"].upper())

        # Verify in attendance table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT student_id, subject_id, teacher_id, status, session_id
            FROM attendance
            WHERE student_id = '1MS24CS001' AND session_id = ?
        """, (session_id,))
        att = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(att, "Attendance record must be stored in database")
        self.assertEqual(att["status"], "Present")
        self.assertEqual(att["teacher_id"], "TCH_A")
        self.assertEqual(att["subject_id"], "CS401")

    def test_03_save_practical_and_assignment_marks(self):
        """Teacher A enters practical (8.5/10) and assignment (4.0/5) marks for Student 1."""
        self.login("teacherA@test.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        res = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "8.5",
            "assignment_marks": "4.0"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("saved successfully", data["message"].lower())

        # Verify in experiment_marks table
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, student_id, subject_id, teacher_id, experiment_no, experiment_name,
                   practical_marks, assignment_marks, max_practical_marks, max_assignment_marks
            FROM experiment_marks
            WHERE session_id = ? AND student_id = '1MS24CS001'
        """, (session_id,))
        em = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(em, "Experiment marks record must exist")
        self.assertEqual(em["practical_marks"], 8.5)
        self.assertEqual(em["assignment_marks"], 4.0)
        self.assertEqual(em["max_practical_marks"], 10.0)
        self.assertEqual(em["max_assignment_marks"], 5.0)
        self.assertEqual(em["experiment_no"], "Experiment 3")
        self.assertEqual(em["experiment_name"], "Implement Stack using Array")

    def test_04_duplicate_qr_scan_handling(self):
        """Scanning the same student again reports already marked attendance and fetches saved marks."""
        self.login("teacherA@test.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        res = self.app.post("/scan_student_qr", json={
            "session_id": session_id,
            "usn": "1MS24CS001"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("already marked", data["attendance_message"].lower())
        self.assertEqual(data["practical_marks"], 8.5)
        self.assertEqual(data["assignment_marks"], 4.0)

    def test_05_marks_validation_limits(self):
        """Validate negative marks and marks exceeding maximum limits are rejected."""
        self.login("teacherA@test.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        # Practical > 10
        res = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "12.0",
            "assignment_marks": "4.0"
        })
        self.assertFalse(res.get_json()["success"])

        # Practical < 0
        res = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "-2.0",
            "assignment_marks": "4.0"
        })
        self.assertFalse(res.get_json()["success"])

        # Assignment > 5
        res = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "8.0",
            "assignment_marks": "7.5"
        })
        self.assertFalse(res.get_json()["success"])

        # Non-numeric
        res = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "abc",
            "assignment_marks": "4.0"
        })
        self.assertFalse(res.get_json()["success"])

    def test_06_scan_student_2_and_save_marks(self):
        """Teacher A scans Student 2 and saves practical & assignment marks."""
        self.login("teacherA@test.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        # Scan Student 2
        res_scan = self.app.post("/scan_student_qr", json={
            "session_id": session_id,
            "usn": "1MS24CS002"
        })
        self.assertTrue(res_scan.get_json()["success"])
        self.assertEqual(res_scan.get_json()["student"]["fullname"], "Bob Student")

        # Save Marks
        res_save = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS002",
            "practical_marks": "9.5",
            "assignment_marks": "5.0"
        })
        self.assertTrue(res_save.get_json()["success"])

        # Verify Roster in practical_session cockpit
        res_cockpit = self.app.get("/practical_session/CS401")
        self.assertEqual(res_cockpit.status_code, 200)
        html = res_cockpit.get_data(as_text=True)
        self.assertIn("1MS24CS001", html)
        self.assertIn("Alice Student", html)
        self.assertIn("1MS24CS002", html)
        self.assertIn("Bob Student", html)

    def test_07_cross_teacher_security(self):
        """Teacher B cannot access or modify Teacher A's session or marks."""
        # Find Teacher A's active session ID
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        # Login as Teacher B
        self.login("teacherB@test.com")

        # Attempt to scan in Teacher A's session
        res_scan = self.app.post("/scan_student_qr", json={
            "session_id": session_id,
            "usn": "1MS24CS001"
        })
        self.assertEqual(res_scan.status_code, 403)
        self.assertFalse(res_scan.get_json()["success"])

        # Attempt to save marks in Teacher A's session
        res_save = self.app.post("/save_session_marks", json={
            "session_id": session_id,
            "student_id": "1MS24CS001",
            "practical_marks": "10",
            "assignment_marks": "5"
        })
        self.assertEqual(res_save.status_code, 403)
        self.assertFalse(res_save.get_json()["success"])

        # Attempt to end Teacher A's session
        res_end = self.app.post(f"/end_session/{session_id}", follow_redirects=True)
        self.assertIn("Unauthorized", res_end.get_data(as_text=True))

    def test_08_student_role_security(self):
        """Students cannot scan QR, enter marks, or start/end sessions."""
        self.login("student1@test.com")

        # Attempt to scan QR
        res_scan = self.app.post("/scan_student_qr", json={"session_id": 1, "usn": "1MS24CS001"})
        self.assertEqual(res_scan.status_code, 302)  # Redirected by role_required

        # Attempt to save marks
        res_save = self.app.post("/save_session_marks", json={"session_id": 1, "student_id": "1MS24CS001", "practical_marks": 10, "assignment_marks": 5})
        self.assertEqual(res_save.status_code, 302)

        # Attempt to start session
        res_start = self.app.post("/start_session", data={"subject_code": "CS401"})
        self.assertEqual(res_start.status_code, 302)

        # Student can view own QR
        res_qr = self.app.get("/my_qr")
        self.assertEqual(res_qr.status_code, 200)
        self.assertIn("1MS24CS001", res_qr.get_data(as_text=True))

    def test_09_experiment_isolation_across_sessions(self):
        """Verify Experiment 1 and Experiment 2 marks are stored independently and not overwritten."""
        self.login("teacherA@test.com")

        # Conclude Session 1 (Experiment 3)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        sess1_id = cursor.fetchone()["id"]
        conn.close()

        res_end = self.app.post(f"/end_session/{sess1_id}", follow_redirects=True)
        self.assertEqual(res_end.status_code, 200)

        # Start Session 2 (Experiment 4)
        res_start2 = self.app.post("/start_session", data={
            "subject_code": "CS401",
            "experiment_no": "Experiment 4",
            "experiment_name": "Implement Queue using Array"
        }, follow_redirects=True)
        self.assertEqual(res_start2.status_code, 200)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        sess2_id = cursor.fetchone()["id"]
        conn.close()

        self.assertNotEqual(sess1_id, sess2_id)

        # Scan Student 1 and save different marks for Experiment 4
        res_scan = self.app.post("/scan_student_qr", json={"session_id": sess2_id, "usn": "1MS24CS001"})
        self.assertTrue(res_scan.get_json()["success"])

        res_save = self.app.post("/save_session_marks", json={
            "session_id": sess2_id,
            "student_id": "1MS24CS001",
            "practical_marks": "7.5",
            "assignment_marks": "3.5"
        })
        self.assertTrue(res_save.get_json()["success"])

        # Check database: both experiment records must exist with their respective scores
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT session_id, experiment_no, practical_marks, assignment_marks
            FROM experiment_marks
            WHERE student_id = '1MS24CS001' AND subject_id = 'CS401'
            ORDER BY id ASC
        """)
        records = cursor.fetchall()
        conn.close()

        self.assertEqual(len(records), 2, "Must have exactly 2 separate experiment mark entries for Student 1")
        self.assertEqual(records[0]["experiment_no"], "Experiment 3")
        self.assertEqual(records[0]["practical_marks"], 8.5)
        self.assertEqual(records[0]["assignment_marks"], 4.0)

        self.assertEqual(records[1]["experiment_no"], "Experiment 4")
        self.assertEqual(records[1]["practical_marks"], 7.5)
        self.assertEqual(records[1]["assignment_marks"], 3.5)

    def test_10_error_handling_unknown_student_and_invalid_qr(self):
        """Unknown USN or missing student returns clear error."""
        self.login("teacherA@test.com")
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_A' AND status = 'active'")
        sess_id = cursor.fetchone()["id"]
        conn.close()

        res = self.app.post("/scan_student_qr", json={"session_id": sess_id, "usn": "NON_EXISTENT_USN_999"})
        self.assertEqual(res.status_code, 404)
        self.assertFalse(res.get_json()["success"])
        self.assertIn("not found", res.get_json()["error"].lower())

if __name__ == "__main__":
    unittest.main()
