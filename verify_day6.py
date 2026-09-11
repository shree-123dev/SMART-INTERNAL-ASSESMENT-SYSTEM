import os
import sqlite3
import unittest
from werkzeug.security import generate_password_hash
from app import app
from database import get_db_connection
from generate_qr import generate_student_qr, ensure_student_qr


class TestDay6StudentQRCodeSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test_siams_day6_key"
        cls.client = app.test_client()

        # Seed test student accounts and admin account
        conn = get_db_connection()
        cursor = conn.cursor()

        # Ensure Admin user
        cursor.execute("SELECT id FROM users WHERE email = 'admin@test.com'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("System Admin", "admin@test.com", generate_password_hash("admin123"), "admin")
            )

        # Ensure Student 1
        cursor.execute("SELECT id FROM users WHERE email = 'student_alpha_d6@college.edu'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Student Alpha", "student_alpha_d6@college.edu", generate_password_hash("student123"), "student")
            )

        cursor.execute("SELECT id FROM students WHERE usn = 'CS2026A'")
        if not cursor.fetchone():
            qr_path_1 = generate_student_qr("CS2026A", "Student Alpha", "CSE", 5)
            cursor.execute(
                "INSERT INTO students (usn, fullname, email, department, semester, section, qr_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("CS2026A", "Student Alpha", "student_alpha_d6@college.edu", "CSE", 5, "A", qr_path_1)
            )

        # Ensure Student 2
        cursor.execute("SELECT id FROM users WHERE email = 'student_beta_d6@college.edu'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Student Beta", "student_beta_d6@college.edu", generate_password_hash("student123"), "student")
            )

        cursor.execute("SELECT id FROM students WHERE usn = 'CS2026B'")
        if not cursor.fetchone():
            qr_path_2 = generate_student_qr("CS2026B", "Student Beta", "CSE", 5)
            cursor.execute(
                "INSERT INTO students (usn, fullname, email, department, semester, section, qr_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("CS2026B", "Student Beta", "student_beta_d6@college.edu", "CSE", 5, "B", qr_path_2)
            )

        # Ensure Teacher
        cursor.execute("SELECT id FROM users WHERE email = 'teacher@test.com'")
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                ("Prof. Raman", "teacher@test.com", generate_password_hash("teacher123"), "teacher")
            )

        conn.commit()
        conn.close()

    def test_01_qr_generation_utility_creates_file(self):
        """Test 1: QR generation creates image file in static/qr/."""
        test_usn = "TEST_QR_GEN_01"
        file_path = generate_student_qr(test_usn, "Test Name", "ISE", 4)
        self.assertTrue(os.path.exists(file_path), f"QR file should exist at {file_path}")
        self.assertGreater(os.path.getsize(file_path), 0, "QR file should not be empty")
        self.assertTrue(file_path.startswith("static/qr"), "QR file must be in static/qr/")

        # Cleanup test file
        if os.path.exists(file_path):
            os.remove(file_path)

    def test_02_distinct_qr_codes_for_different_students(self):
        """Test 2: Two different students receive different QR code images."""
        qr1 = generate_student_qr("CS2026A")
        qr2 = generate_student_qr("CS2026B")

        self.assertTrue(os.path.exists(qr1))
        self.assertTrue(os.path.exists(qr2))
        self.assertNotEqual(qr1, qr2, "QR paths must be different")

        with open(qr1, "rb") as f1, open(qr2, "rb") as f2:
            content1 = f1.read()
            content2 = f2.read()
            self.assertNotEqual(content1, content2, "QR image binary payloads must be different for different USNs")

    def test_03_admin_auto_generates_qr_on_add_student(self):
        """Test 3: Admin adding a student automatically generates their QR code."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["email"] = "admin@test.com"
            sess["fullname"] = "System Admin"
            sess["role"] = "admin"

        new_usn = "AUTO_QR_001"
        response = self.client.post("/add_student", data={
            "usn": new_usn,
            "fullname": "Auto Generated Student",
            "email": "auto_qr_d6@test.com",
            "department": "AIML",
            "semester": "3",
            "section": "A"
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)

        # Check DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT qr_path FROM students WHERE usn = ?", (new_usn,))
        row = cursor.fetchone()
        conn.close()

        self.assertIsNotNone(row, "Student record must exist in DB")
        qr_path = row["qr_path"]
        self.assertTrue(os.path.exists(qr_path), f"QR code file must exist on disk at {qr_path}")

        # Clean up auto student
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE usn = ?", (new_usn,))
        conn.commit()
        conn.close()
        if os.path.exists(qr_path):
            os.remove(qr_path)

    def test_04_admin_can_regenerate_qr(self):
        """Test 4: Admin can regenerate a student QR code."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["email"] = "admin@test.com"
            sess["fullname"] = "System Admin"
            sess["role"] = "admin"

        response = self.client.post("/admin/generate_qr/CS2026A", follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"QR Code regenerated successfully", response.data)

        # Verify QR file exists
        self.assertTrue(os.path.exists("static/qr/CS2026A.png"))

    def test_05_admin_can_view_student_qr_card(self):
        """Test 5: Admin can view student's print-friendly digital QR pass."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["email"] = "admin@test.com"
            sess["fullname"] = "System Admin"
            sess["role"] = "admin"

        response = self.client.get("/admin/student_qr/CS2026A")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CS2026A", response.data)
        self.assertIn(b"Student Alpha", response.data)
        self.assertIn(b"Print ID Card", response.data)

    def test_06_student_sees_only_own_qr(self):
        """Test 6: Logged-in student sees ONLY their own QR code."""
        # Login as Student 1
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["email"] = "student_alpha_d6@college.edu"
            sess["fullname"] = "Student Alpha"
            sess["role"] = "student"

        response = self.client.get("/student")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CS2026A", response.data)
        self.assertIn(b"Student Alpha", response.data)
        self.assertNotIn(b"CS2026B", response.data)
        self.assertNotIn(b"Student Beta", response.data)

    def test_07_student_isolated_my_qr_portal(self):
        """Test 7: Student portal /my_qr renders logged-in student's QR pass."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["email"] = "student_alpha_d6@college.edu"
            sess["fullname"] = "Student Alpha"
            sess["role"] = "student"

        response = self.client.get("/my_qr")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"CS2026A", response.data)
        self.assertIn(b"Student Alpha", response.data)
        self.assertNotIn(b"CS2026B", response.data)

    def test_08_student_cannot_access_admin_qr_management(self):
        """Test 8: Student is blocked from Admin QR routes."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 2
            sess["email"] = "student_alpha_d6@college.edu"
            sess["fullname"] = "Student Alpha"
            sess["role"] = "student"

        # Attempt to regenerate QR as student -> redirected to /student
        res1 = self.client.post("/admin/generate_qr/CS2026A")
        self.assertEqual(res1.status_code, 302)
        self.assertIn("/student", res1.location)

        # Attempt to view admin student QR page as student -> redirected to /student
        res2 = self.client.get("/admin/student_qr/CS2026B")
        self.assertEqual(res2.status_code, 302)
        self.assertIn("/student", res2.location)

    def test_09_teacher_cannot_access_qr_management(self):
        """Test 9: Teacher is blocked from Admin QR generation/management routes."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 3
            sess["email"] = "teacher@test.com"
            sess["fullname"] = "Prof. Raman"
            sess["role"] = "teacher"

        res = self.client.post("/admin/generate_qr/CS2026A")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/teacher", res.location)

    def test_10_missing_student_handled_gracefully(self):
        """Test 10: Non-existing USN returns error gracefully without crash."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["email"] = "admin@test.com"
            sess["fullname"] = "System Admin"
            sess["role"] = "admin"

        res1 = self.client.post("/admin/generate_qr/NON_EXISTENT_USN", follow_redirects=True)
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b"not found", res1.data.lower())

        res2 = self.client.get("/admin/student_qr/NON_EXISTENT_USN", follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b"not found", res2.data.lower())


if __name__ == "__main__":
    unittest.main()
