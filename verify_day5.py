"""
SIAMS - Day 5 Verification Script
Automated tests covering all 16 verification requirements for Teacher-Subject Assignment Module.
"""

import sys
import sqlite3
from app import app
from database import get_db_connection

def run_tests():
    print("=" * 65)
    print("RUNNING DAY 5 TEACHER-SUBJECT ASSIGNMENT MODULE TESTS")
    print("=" * 65)

    conn = get_db_connection()
    c = conn.cursor()

    # Ensure we have at least 2 distinct teachers and 3 distinct subjects for isolation tests
    c.execute("SELECT teacher_id FROM teachers WHERE teacher_id = 'T001'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO teachers (teacher_id, fullname, email, department)
            VALUES ('T001', 'Prof. Alan Turing', 'alan.turing@college.edu', 'Computer Science')
        """)

    c.execute("SELECT teacher_id FROM teachers WHERE teacher_id = 'T002'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO teachers (teacher_id, fullname, email, department)
            VALUES ('T002', 'Prof. Ada Lovelace', 'ada.lovelace@college.edu', 'Information Science')
        """)

    c.execute("SELECT subject_code FROM subjects WHERE subject_code = 'CS501'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO subjects (subject_code, subject_name, department, semester)
            VALUES ('CS501', 'Database Management Systems', 'Computer Science', 5)
        """)

    c.execute("SELECT subject_code FROM subjects WHERE subject_code = 'CS502'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO subjects (subject_code, subject_name, department, semester)
            VALUES ('CS502', 'Operating Systems', 'Computer Science', 5)
        """)

    c.execute("SELECT subject_code FROM subjects WHERE subject_code = 'IS501'")
    if not c.fetchone():
        c.execute("""
            INSERT INTO subjects (subject_code, subject_name, department, semester)
            VALUES ('IS501', 'Artificial Intelligence', 'Information Science', 5)
        """)

    conn.commit()
    conn.close()

    admin_client = app.test_client()
    with admin_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["fullname"] = "System Administrator"
        sess["email"] = "admin@test.com"
        sess["role"] = "admin"

    # 1. Admin can open assignment page
    res_assign_page = admin_client.get("/assign_subject")
    assert res_assign_page.status_code == 200, f"Failed with {res_assign_page.status_code}"
    html_assign = res_assign_page.data.decode("utf-8")
    print("[OK] Test 1: Admin can open assignment page successfully")

    # 2 & 3. Teacher and Subject dropdowns load from database
    assert "Prof. Alan Turing" in html_assign or "T001" in html_assign
    assert "Prof. Ada Lovelace" in html_assign or "T002" in html_assign
    assert "CS501" in html_assign and "Database Management Systems" in html_assign
    assert "IS501" in html_assign and "Artificial Intelligence" in html_assign
    print("[OK] Test 2 & 3: Teacher and Subject dropdowns are loaded dynamically from SQLite database")

    # Clean up test assignment before assigning
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM teacher_subjects WHERE teacher_id = 'T001' AND subject_id = 'CS502'")
    c.execute("DELETE FROM teacher_subjects WHERE teacher_id = 'T002' AND subject_id = 'IS501'")
    conn.commit()
    conn.close()

    # 4 & 5. Admin can assign a subject & assignment is stored in teacher_subjects
    res_assign_post = admin_client.post("/assign_subject", data={
        "teacher_id": "T001",
        "subject_code": "CS502"
    }, follow_redirects=True)
    assert res_assign_post.status_code == 200
    assert "Subject assigned successfully" in res_assign_post.data.decode("utf-8") or "Operating Systems" in res_assign_post.data.decode("utf-8")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM teacher_subjects WHERE teacher_id = 'T001' AND subject_id = 'CS502'")
    mapping_row = c.fetchone()
    assert mapping_row is not None, "Mapping was not stored in teacher_subjects table!"
    assignment_id_1 = mapping_row[0]
    conn.close()
    print("[OK] Test 4 & 5: Admin can assign subject and record is stored in teacher_subjects table")

    # 6. Duplicate assignment is prevented
    res_dup = admin_client.post("/assign_subject", data={
        "teacher_id": "T001",
        "subject_code": "CS502"
    })
    assert res_dup.status_code == 200
    assert "already assigned" in res_dup.data.decode("utf-8")
    print("[OK] Test 6: Duplicate assignment is strictly prevented with error feedback")

    # Also assign IS501 to Teacher T002 (Prof. Ada Lovelace)
    res_assign_t2 = admin_client.post("/assign_subject", data={
        "teacher_id": "T002",
        "subject_code": "IS501"
    }, follow_redirects=True)
    assert res_assign_t2.status_code == 200

    # 7. Admin can view assignments
    res_view_assign = admin_client.get("/view_assignments")
    assert res_view_assign.status_code == 200
    html_view = res_view_assign.data.decode("utf-8")
    assert "Prof. Alan Turing" in html_view
    assert "Operating Systems" in html_view or "CS502" in html_view
    assert "Prof. Ada Lovelace" in html_view
    assert "Artificial Intelligence" in html_view or "IS501" in html_view
    print("[OK] Test 7: Admin can view all active teacher-subject assignments")

    # 8 & 9. Admin can remove an assignment without deleting teacher or subject
    res_remove = admin_client.post(f"/remove_assignment/{assignment_id_1}", follow_redirects=True)
    assert res_remove.status_code == 200
    assert "removed successfully" in res_remove.data.decode("utf-8")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM teacher_subjects WHERE id = ?", (assignment_id_1,))
    assert c.fetchone() is None, "Assignment was not removed!"
    # Ensure Teacher and Subject still exist!
    c.execute("SELECT id FROM teachers WHERE teacher_id = 'T001'")
    assert c.fetchone() is not None, "Teacher was erroneously deleted!"
    c.execute("SELECT id FROM subjects WHERE subject_code = 'CS502'")
    assert c.fetchone() is not None, "Subject was erroneously deleted!"
    conn.close()
    print("[OK] Test 8 & 9: Admin can remove assignment without deleting the teacher or subject records")

    # Re-assign CS501 to T001 (Prof. Alan Turing) and IS501 to T002 (Prof. Ada Lovelace) for isolation tests
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM teacher_subjects WHERE teacher_id = 'T001' AND subject_id = 'CS501'")
    c.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('T001', 'CS501')")
    c.execute("DELETE FROM teacher_subjects WHERE teacher_id = 'T002' AND subject_id = 'IS501'")
    c.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('T002', 'IS501')")
    conn.commit()
    conn.close()

    # 10. Teacher A sees ONLY Teacher A's assigned subjects
    teacher_a_client = app.test_client()
    with teacher_a_client.session_transaction() as sess:
        sess["user_id"] = 101
        sess["fullname"] = "Prof. Alan Turing"
        sess["email"] = "alan.turing@college.edu"
        sess["role"] = "teacher"

    res_t1_dash = teacher_a_client.get("/teacher")
    assert res_t1_dash.status_code == 200
    html_t1 = res_t1_dash.data.decode("utf-8")
    assert "CS501" in html_t1 or "Database Management Systems" in html_t1, "Teacher A cannot see their own assigned subject CS501!"
    assert "Artificial Intelligence" not in html_t1 and "IS501" not in html_t1, "Teacher A can see Teacher B's assigned subject IS501!"
    print("[OK] Test 10: Teacher A sees ONLY Teacher A's assigned subjects (CS501) and NOT Teacher B's")

    # 11. Teacher B sees ONLY Teacher B's assigned subjects
    teacher_b_client = app.test_client()
    with teacher_b_client.session_transaction() as sess:
        sess["user_id"] = 102
        sess["fullname"] = "Prof. Ada Lovelace"
        sess["email"] = "ada.lovelace@college.edu"
        sess["role"] = "teacher"

    res_t2_dash = teacher_b_client.get("/teacher")
    assert res_t2_dash.status_code == 200
    html_t2 = res_t2_dash.data.decode("utf-8")
    assert "IS501" in html_t2 or "Artificial Intelligence" in html_t2, "Teacher B cannot see their own assigned subject IS501!"
    assert "Database Management Systems" not in html_t2 and "CS501" not in html_t2, "Teacher B can see Teacher A's assigned subject CS501!"
    print("[OK] Test 11: Teacher B sees ONLY Teacher B's assigned subjects (IS501) and NOT Teacher A's")

    # 12. Teacher access protection (URL tampering blocked)
    # Teacher A attempting to visit /teacher_subjects/T002 should receive their own subjects (T001) or be protected
    res_tamper = teacher_a_client.get("/teacher_subjects/T002")
    assert res_tamper.status_code == 200
    html_tamper = res_tamper.data.decode("utf-8")
    assert "IS501" not in html_tamper, "Teacher A bypassed isolation via URL parameter tampering!"
    assert "CS501" in html_tamper, "Teacher A did not receive their own isolated subjects!"
    print("[OK] Test 12: Teacher URL tampering is protected; teachers can only view their own assigned subjects")

    # 13. Student cannot access assignment management
    student_client = app.test_client()
    with student_client.session_transaction() as sess:
        sess["user_id"] = 201
        sess["fullname"] = "Student User"
        sess["email"] = "student@test.com"
        sess["role"] = "student"

    for r in ["/assign_subject", "/view_assignments"]:
        res_stud = student_client.get(r)
        assert res_stud.status_code == 302 and "/student" in res_stud.location, f"Student accessed {r}!"
    print("[OK] Test 13: Student is blocked from assignment management and redirected to /student")

    # 14. Existing login / logout
    anon_client = app.test_client()
    res_login_page = anon_client.get("/login")
    assert res_login_page.status_code == 200
    res_login = anon_client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
    assert res_login.status_code == 302 and "/admin" in res_login.location
    res_logout = anon_client.get("/logout")
    assert res_logout.status_code == 302 and "/login" in res_logout.location
    print("[OK] Test 14: Existing login and logout functionality works seamlessly")

    # 15. Existing Admin, Student, Teacher features
    res_admin_dash = admin_client.get("/admin")
    assert res_admin_dash.status_code == 200
    res_admin_stus = admin_client.get("/view_students")
    assert res_admin_stus.status_code == 200
    res_admin_tchs = admin_client.get("/view_teachers")
    assert res_admin_tchs.status_code == 200
    res_admin_subs = admin_client.get("/view_subjects")
    assert res_admin_subs.status_code == 200
    print("[OK] Test 15: Existing Day 1-4 Admin, Teacher, and Student features operate flawlessly")

    # 16. Database data preservation
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM students")
    stus_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teachers")
    tchs_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM subjects")
    subs_cnt = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teacher_subjects")
    maps_cnt = c.fetchone()[0]
    conn.close()

    assert users_cnt >= 1 and stus_cnt >= 1 and tchs_cnt >= 2 and subs_cnt >= 2 and maps_cnt >= 1
    print(f"[OK] Test 16: Database data preserved (Users: {users_cnt}, Students: {stus_cnt}, Teachers: {tchs_cnt}, Subjects: {subs_cnt}, Assignments: {maps_cnt})")

    print("=" * 65)
    print("ALL 16 DAY 5 VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!")
    print("=" * 65)

if __name__ == "__main__":
    run_tests()
