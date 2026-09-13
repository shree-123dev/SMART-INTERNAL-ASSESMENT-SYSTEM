import os
import sqlite3
import unittest
from werkzeug.security import generate_password_hash
from app import app
from database import get_db_connection


class TestDay7PracticalSessionManagement(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test_siams_day7_key"
        cls.client = app.test_client()

        # Seed test faculty, subjects, and assignments in database
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Teacher Alpha (TCH_D7_A)
        cursor.execute("SELECT id FROM users WHERE email = 'teacher_alpha_d7@college.edu'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Prof. Alpha", "teacher_alpha_d7@college.edu", generate_password_hash("teacher123"), "teacher")
            )
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = 'TCH_D7_A'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO teachers (teacher_id, fullname, email, department) VALUES (?, ?, ?, ?)",
                ("TCH_D7_A", "Prof. Alpha", "teacher_alpha_d7@college.edu", "CSE")
            )

        # 2. Teacher Beta (TCH_D7_B)
        cursor.execute("SELECT id FROM users WHERE email = 'teacher_beta_d7@college.edu'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Prof. Beta", "teacher_beta_d7@college.edu", generate_password_hash("teacher123"), "teacher")
            )
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = 'TCH_D7_B'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO teachers (teacher_id, fullname, email, department) VALUES (?, ?, ?, ?)",
                ("TCH_D7_B", "Prof. Beta", "teacher_beta_d7@college.edu", "ISE")
            )

        # 3. Student
        cursor.execute("SELECT id FROM users WHERE email = 'student_d7@college.edu'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Student D7", "student_d7@college.edu", generate_password_hash("student123"), "student")
            )

        # 4. Subjects: SUB_D7_1 (assigned to Alpha) and SUB_D7_2 (assigned to Beta)
        cursor.execute("SELECT id FROM subjects WHERE subject_code = 'SUB_D7_1'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES (?, ?, ?, ?)",
                ("SUB_D7_1", "Compiler Design Lab", "CSE", 6)
            )

        cursor.execute("SELECT id FROM subjects WHERE subject_code = 'SUB_D7_2'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES (?, ?, ?, ?)",
                ("SUB_D7_2", "Computer Networks Lab", "ISE", 6)
            )

        # 5. Assign SUB_D7_1 -> TCH_D7_A, SUB_D7_2 -> TCH_D7_B
        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_D7_A' AND subject_id = 'SUB_D7_1'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)",
                ("TCH_D7_A", "SUB_D7_1")
            )

        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'TCH_D7_B' AND subject_id = 'SUB_D7_2'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES (?, ?)",
                ("TCH_D7_B", "SUB_D7_2")
            )

        # Clean up any leftover test sessions from previous runs
        cursor.execute("DELETE FROM practical_sessions WHERE teacher_id IN ('TCH_D7_A', 'TCH_D7_B')")

        conn.commit()
        conn.close()

    def test_01_teacher_sees_only_assigned_subjects(self):
        """Test 1: Teacher Alpha sees only their assigned subjects on dashboard."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.get("/teacher")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SUB_D7_1", response.data)
        self.assertIn(b"Compiler Design Lab", response.data)
        self.assertNotIn(b"SUB_D7_2", response.data)
        self.assertNotIn(b"Computer Networks Lab", response.data)

    def test_02_teacher_can_start_practical_session(self):
        """Test 2: Teacher can start a practical session for an assigned subject."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.post("/start_session", data={
            "subject_code": "SUB_D7_1"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"initiated successfully", response.data)

        # Verify record in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, teacher_id, subject_id, session_date, start_time, end_time, status
            FROM practical_sessions
            WHERE teacher_id = 'TCH_D7_A' AND subject_id = 'SUB_D7_1' AND status = 'active'
        """)
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row, "Active practical session must be stored in database")
        self.assertEqual(row["teacher_id"], "TCH_D7_A")
        self.assertEqual(row["subject_id"], "SUB_D7_1")
        self.assertEqual(row["status"], "active")
        self.assertIsNotNone(row["session_date"])
        self.assertIsNotNone(row["start_time"])
        self.assertIsNone(row["end_time"])

    def test_03_active_session_displayed_on_dashboard(self):
        """Test 3: Active practical session is prominently displayed on teacher dashboard."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.get("/teacher")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ACTIVE PRACTICAL SESSION IN PROGRESS", response.data)
        self.assertIn(b"Compiler Design Lab", response.data)
        self.assertIn(b"End Session Now", response.data)

    def test_04_prevent_unassigned_subject_start(self):
        """Test 4: Teacher cannot start session for a subject not assigned to them."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.post("/start_session", data={
            "subject_code": "SUB_D7_2"  # Assigned to Beta, not Alpha
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unauthorized", response.data)

    def test_05_prevent_multiple_concurrent_active_sessions(self):
        """Test 5: Teacher cannot start a 2nd active session while one is in progress."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.post("/start_session", data={
            "subject_code": "SUB_D7_1"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already have an active practical session", response.data)

    def test_06_teacher_can_end_own_session(self):
        """Test 6: Teacher can end their active session, setting end_time and status='completed'."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_D7_A' AND status = 'active'")
        session_id = cursor.fetchone()["id"]
        conn.close()

        response = self.client.post(f"/end_session/{session_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"completed and ended successfully", response.data)

        # Verify in DB: status='completed', end_time is not null, session is NOT deleted
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status, end_time FROM practical_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()

        self.assertEqual(row["status"], "completed")
        self.assertIsNotNone(row["end_time"])

    def test_07_prevent_ending_another_teachers_session(self):
        """Test 7: Teacher Alpha cannot end a session belonging to Teacher Beta."""
        # Start a session as Teacher Beta
        with self.client.session_transaction() as sess:
            sess["user_id"] = 102
            sess["email"] = "teacher_beta_d7@college.edu"
            sess["fullname"] = "Prof. Beta"
            sess["role"] = "teacher"

        self.client.post("/start_session", data={"subject_code": "SUB_D7_2"}, follow_redirects=True)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM practical_sessions WHERE teacher_id = 'TCH_D7_B' AND status = 'active'")
        beta_session_id = cursor.fetchone()["id"]
        conn.close()

        # Now attempt to end Beta's session while logged in as Alpha
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.post(f"/end_session/{beta_session_id}", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Unauthorized", response.data)

        # Verify Beta's session is still active
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT status FROM practical_sessions WHERE id = ?", (beta_session_id,))
        self.assertEqual(cursor.fetchone()["status"], "active")
        conn.close()

        # Clean up Beta's session
        with self.client.session_transaction() as sess:
            sess["user_id"] = 102
            sess["email"] = "teacher_beta_d7@college.edu"
            sess["fullname"] = "Prof. Beta"
            sess["role"] = "teacher"
        self.client.post(f"/end_session/{beta_session_id}", follow_redirects=True)

    def test_08_session_history_isolation(self):
        """Test 8: Practical sessions log displays only the logged-in teacher's sessions."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 101
            sess["email"] = "teacher_alpha_d7@college.edu"
            sess["fullname"] = "Prof. Alpha"
            sess["role"] = "teacher"

        response = self.client.get("/practical_sessions")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Compiler Design Lab", response.data)
        self.assertIn(b"SUB_D7_1", response.data)
        self.assertNotIn(b"Computer Networks Lab", response.data)
        self.assertNotIn(b"SUB_D7_2", response.data)

    def test_09_students_cannot_manage_sessions(self):
        """Test 9: Students are blocked from session start/end/history management routes."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 103
            sess["email"] = "student_d7@college.edu"
            sess["fullname"] = "Student D7"
            sess["role"] = "student"

        res1 = self.client.post("/start_session", data={"subject_code": "SUB_D7_1"})
        self.assertEqual(res1.status_code, 302)
        self.assertIn("/student", res1.location)

        res2 = self.client.post("/end_session/1")
        self.assertEqual(res2.status_code, 302)
        self.assertIn("/student", res2.location)

        res3 = self.client.get("/practical_sessions")
        self.assertEqual(res3.status_code, 302)
        self.assertIn("/student", res3.location)


if __name__ == "__main__":
    unittest.main()
