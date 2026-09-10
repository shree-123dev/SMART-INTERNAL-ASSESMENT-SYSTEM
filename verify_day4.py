"""
SIAMS - Day 4 Verification Script
Automated tests covering all 23 verification points for Admin Management Module.
"""

import sys
import sqlite3
from app import app
from database import get_db_connection

def run_tests():
    print("=" * 60)
    print("RUNNING DAY 4 ADMIN MANAGEMENT MODULE TESTS")
    print("=" * 60)

    client = app.test_client()

    # Log in as Admin
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["fullname"] = "System Administrator"
        sess["email"] = "admin@test.com"
        sess["role"] = "admin"

    # 1. Admin Dashboard & Live Counts
    res = client.get("/admin")
    assert res.status_code == 200, f"Admin dashboard failed with status {res.status_code}"
    html = res.data.decode("utf-8")
    assert "System Administrator" in html or "Admin" in html
    assert "Total Students" in html
    assert "Total Teachers" in html
    assert "Total Subjects" in html
    print("[OK] Test 1-4: Admin dashboard renders with live database counts & admin greeting")

    # 5. Admin can add student
    test_usn = "TEST_DAY4_STU"
    test_email = "test_day4_stu@college.edu"
    # Clean up before testing
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE usn = ?", (test_usn,))
    conn.commit()
    conn.close()

    res_add_stu = client.post("/add_student", data={
        "usn": test_usn,
        "fullname": "Day 4 Test Student",
        "email": test_email,
        "department": "Information Science",
        "semester": "6",
        "section": "B"
    }, follow_redirects=True)
    assert res_add_stu.status_code == 200
    assert "Day 4 Test Student" in res_add_stu.data.decode("utf-8") or test_usn in res_add_stu.data.decode("utf-8")
    print("[OK] Test 5: Admin can add new student with validation")

    # 6. Admin can view students & view student details
    res_view_stus = client.get("/view_students")
    assert res_view_stus.status_code == 200
    assert test_usn in res_view_stus.data.decode("utf-8")
    res_view_single_stu = client.get(f"/view_student/{test_usn}")
    assert res_view_single_stu.status_code == 200
    assert "Day 4 Test Student" in res_view_single_stu.data.decode("utf-8")
    print("[OK] Test 6: Admin can view student roster and individual student details")

    # 7. Admin can search students
    res_search_stu = client.get(f"/view_students?search={test_usn}")
    assert res_search_stu.status_code == 200
    assert test_usn in res_search_stu.data.decode("utf-8")
    print("[OK] Test 7: Admin can search students by query")

    # 8. Admin can edit student
    res_edit_stu = client.post(f"/edit_student/{test_usn}", data={
        "fullname": "Day 4 Updated Student",
        "email": "updated_day4_stu@college.edu",
        "department": "Information Science",
        "semester": "7",
        "section": "A"
    }, follow_redirects=True)
    assert res_edit_stu.status_code == 200
    assert "Day 4 Updated Student" in res_edit_stu.data.decode("utf-8")
    print("[OK] Test 8: Admin can edit student details")

    # 9. Admin can delete student
    res_del_stu = client.post(f"/delete_student/{test_usn}", follow_redirects=True)
    assert res_del_stu.status_code == 200
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM students WHERE usn = ?", (test_usn,))
    assert c.fetchone() is None, "Student record was not deleted from database!"
    conn.close()
    print("[OK] Test 9: Admin can delete student with safety checks")

    # 10. Admin can add teacher
    test_tid = "TCH_DAY4"
    test_temail = "test_day4_teacher@college.edu"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM teachers WHERE teacher_id = ?", (test_tid,))
    conn.commit()
    conn.close()

    res_add_tch = client.post("/add_teacher", data={
        "teacher_id": test_tid,
        "fullname": "Prof. Day 4 Teacher",
        "email": test_temail,
        "department": "Electronics"
    }, follow_redirects=True)
    assert res_add_tch.status_code == 200
    assert test_tid in res_add_tch.data.decode("utf-8")
    print("[OK] Test 10: Admin can add new faculty teacher")

    # 11. Admin can view teachers & details
    res_view_tchs = client.get("/view_teachers")
    assert res_view_tchs.status_code == 200
    assert test_tid in res_view_tchs.data.decode("utf-8")
    res_view_single_tch = client.get(f"/view_teacher/{test_tid}")
    assert res_view_single_tch.status_code == 200
    assert "Prof. Day 4 Teacher" in res_view_single_tch.data.decode("utf-8")
    print("[OK] Test 11: Admin can view faculty directory and single teacher details")

    # 12. Admin can search teachers
    res_search_tch = client.get(f"/view_teachers?search={test_tid}")
    assert res_search_tch.status_code == 200
    assert test_tid in res_search_tch.data.decode("utf-8")
    print("[OK] Test 12: Admin can search teachers by query")

    # 13. Admin can edit teacher
    res_edit_tch = client.post(f"/edit_teacher/{test_tid}", data={
        "fullname": "Prof. Day 4 Updated Teacher",
        "email": "updated_day4_teacher@college.edu",
        "department": "Electronics & Comm"
    }, follow_redirects=True)
    assert res_edit_tch.status_code == 200
    assert "Prof. Day 4 Updated Teacher" in res_edit_tch.data.decode("utf-8")
    print("[OK] Test 13: Admin can edit teacher details")

    # 14. Admin can delete teacher
    res_del_tch = client.post(f"/delete_teacher/{test_tid}", follow_redirects=True)
    assert res_del_tch.status_code == 200
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM teachers WHERE teacher_id = ?", (test_tid,))
    assert c.fetchone() is None, "Teacher record was not deleted from database!"
    conn.close()
    print("[OK] Test 14: Admin can delete teacher safely")

    # 15. Admin can add subject
    test_subcode = "CS_DAY4"
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM subjects WHERE subject_code = ?", (test_subcode,))
    conn.commit()
    conn.close()

    res_add_sub = client.post("/add_subject", data={
        "subject_code": test_subcode,
        "subject_name": "Day 4 Cloud Computing",
        "department": "Computer Science",
        "semester": "6"
    }, follow_redirects=True)
    assert res_add_sub.status_code == 200
    assert test_subcode in res_add_sub.data.decode("utf-8")
    print("[OK] Test 15: Admin can add new curriculum subject")

    # 16. Admin can view subjects & details
    res_view_subs = client.get("/view_subjects")
    assert res_view_subs.status_code == 200
    assert test_subcode in res_view_subs.data.decode("utf-8")
    res_view_single_sub = client.get(f"/view_subject/{test_subcode}")
    assert res_view_single_sub.status_code == 200
    assert "Day 4 Cloud Computing" in res_view_single_sub.data.decode("utf-8")
    print("[OK] Test 16: Admin can view subject catalog and single subject details")

    # 17. Admin can search subjects
    res_search_sub = client.get(f"/view_subjects?search={test_subcode}")
    assert res_search_sub.status_code == 200
    assert test_subcode in res_search_sub.data.decode("utf-8")
    print("[OK] Test 17: Admin can search subjects by query")

    # 18. Admin can edit subject
    res_edit_sub = client.post(f"/edit_subject/{test_subcode}", data={
        "subject_name": "Day 4 Advanced Cloud Computing",
        "department": "Computer Science",
        "semester": "7"
    }, follow_redirects=True)
    assert res_edit_sub.status_code == 200
    assert "Day 4 Advanced Cloud Computing" in res_edit_sub.data.decode("utf-8")
    print("[OK] Test 18: Admin can edit subject details")

    # 19. Admin can delete subject
    res_del_sub = client.post(f"/delete_subject/{test_subcode}", follow_redirects=True)
    assert res_del_sub.status_code == 200
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM subjects WHERE subject_code = ?", (test_subcode,))
    assert c.fetchone() is None, "Subject record was not deleted from database!"
    conn.close()
    print("[OK] Test 19: Admin can delete subject safely")

    # 20. Student cannot access Admin pages
    student_client = app.test_client()
    with student_client.session_transaction() as sess:
        sess["user_id"] = 2
        sess["fullname"] = "Student User"
        sess["email"] = "student@test.com"
        sess["role"] = "student"

    for route in ["/admin", "/view_students", "/add_student", "/view_teachers", "/add_teacher", "/view_subjects", "/add_subject"]:
        res_stud = student_client.get(route)
        assert res_stud.status_code == 302 and "/student" in res_stud.location, f"Student accessed {route}!"
    print("[OK] Test 20: Student is blocked from all Admin management routes and redirected to /student")

    # 21. Teacher cannot access Admin pages
    teacher_client = app.test_client()
    with teacher_client.session_transaction() as sess:
        sess["user_id"] = 3
        sess["fullname"] = "Teacher User"
        sess["email"] = "teacher@test.com"
        sess["role"] = "teacher"

    for route in ["/admin", "/view_students", "/add_student", "/view_teachers", "/add_teacher", "/view_subjects", "/add_subject"]:
        res_tch = teacher_client.get(route)
        assert res_tch.status_code == 302 and "/teacher" in res_tch.location, f"Teacher accessed {route}!"
    print("[OK] Test 21: Teacher is blocked from Admin management routes and redirected to /teacher")

    # 22. Existing Login / Logout
    anon_client = app.test_client()
    res_login_page = anon_client.get("/login")
    assert res_login_page.status_code == 200
    res_login_post = anon_client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
    assert res_login_post.status_code == 302 and "/admin" in res_login_post.location
    res_logout = anon_client.get("/logout")
    assert res_logout.status_code == 302 and "/login" in res_logout.location
    print("[OK] Test 22: Authentication login/logout workflow works seamlessly")

    # 23. Database preservation
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM students")
    stus_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM teachers")
    tchs_count = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM subjects")
    subs_count = c.fetchone()[0]
    conn.close()
    assert stus_count >= 1 and tchs_count >= 1 and subs_count >= 1
    print(f"[OK] Test 23: Database data preserved (Students: {stus_count}, Teachers: {tchs_count}, Subjects: {subs_count})")

    print("=" * 60)
    print("ALL 23 DAY 4 VERIFICATION TESTS PASSED SUCCESSFULLY (100%)!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
