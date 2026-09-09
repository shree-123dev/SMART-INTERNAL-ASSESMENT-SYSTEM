import sqlite3
from werkzeug.security import check_password_hash
import app

def test_day3():
    print("==================================================")
    print("RUNNING DAY 3 AUTHENTICATION & ACCESS CONTROL TESTS")
    print("==================================================")

    client = app.app.test_client()
    passed = True

    # 1. DATABASE HASH VERIFICATION
    print("\n--- TEST 1: DATABASE PASSWORD HASHING ---")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT id, fullname, email, password, role FROM users")
    users = c.fetchall()
    conn.close()

    for u in users:
        pwd = u[3]
        is_hashed = pwd.startswith("scrypt:") or pwd.startswith("pbkdf2:")
        if not is_hashed:
            print(f"[FAIL] User {u[2]} has plaintext password: {pwd}")
            passed = False
        else:
            print(f"[OK] User {u[2]} ({u[4]}) password is secure hash: {pwd[:22]}...")

    # 2. TEST AUTHENTICATION & REDIRECTION PER ROLE
    print("\n--- TEST 2: ROLE-BASED LOGIN & REDIRECTION ---")

    # 2a. Student Login
    res_student = client.post("/login", data={"email": "student@test.com", "password": "student123"}, follow_redirects=False)
    if res_student.status_code == 302 and res_student.headers["Location"] in ["/student", "http://localhost/student"]:
        print("[OK] Student login redirects to /student (302)")
    else:
        print(f"[FAIL] Student login unexpected response: {res_student.status_code} -> {res_student.headers.get('Location')}")
        passed = False

    # 2b. Teacher Login
    res_teacher = client.post("/login", data={"email": "teacher@test.com", "password": "teacher123"}, follow_redirects=False)
    if res_teacher.status_code == 302 and res_teacher.headers["Location"] in ["/teacher", "http://localhost/teacher"]:
        print("[OK] Teacher login redirects to /teacher (302)")
    else:
        print(f"[FAIL] Teacher login unexpected response: {res_teacher.status_code} -> {res_teacher.headers.get('Location')}")
        passed = False

    # 2c. Admin Login
    res_admin = client.post("/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=False)
    if res_admin.status_code == 302 and res_admin.headers["Location"] in ["/admin", "http://localhost/admin"]:
        print("[OK] Admin login redirects to /admin (302)")
    else:
        print(f"[FAIL] Admin login unexpected response: {res_admin.status_code} -> {res_admin.headers.get('Location')}")
        passed = False

    # 3. TEST INVALID CREDENTIALS
    print("\n--- TEST 3: INVALID CREDENTIALS HANDLING ---")

    # Wrong password
    res_bad_pw = client.post("/login", data={"email": "admin@test.com", "password": "wrongpassword"}, follow_redirects=True)
    if res_bad_pw.status_code == 200 and b"Invalid" in res_bad_pw.data:
        print("[OK] Wrong password correctly rejected with error feedback")
    else:
        print(f"[FAIL] Wrong password check failed: {res_bad_pw.status_code}")
        passed = False

    # Unknown email
    res_unknown = client.post("/login", data={"email": "ghost@test.com", "password": "anypassword"}, follow_redirects=True)
    if res_unknown.status_code == 200 and b"Invalid" in res_unknown.data:
        print("[OK] Unknown email correctly rejected with error feedback")
    else:
        print(f"[FAIL] Unknown email check failed: {res_unknown.status_code}")
        passed = False

    # 4. TEST DIRECT ACCESS WITHOUT LOGIN
    print("\n--- TEST 4: UNATHENTICATED DASHBOARD PROTECTION ---")
    anon_client = app.app.test_client()
    for route in ["/student", "/teacher", "/admin"]:
        res_anon = anon_client.get(route, follow_redirects=False)
        if res_anon.status_code == 302 and res_anon.headers["Location"] in ["/login", "http://localhost/login"]:
            print(f"[OK] Unauthenticated access to {route} redirected to /login")
        else:
            print(f"[FAIL] Unauthenticated access to {route} allowed or wrong redirect: {res_anon.status_code} -> {res_anon.headers.get('Location')}")
            passed = False

    # 5. TEST ROLE PROTECTION ACROSS DASHBOARDS
    print("\n--- TEST 5: ROLE-BASED ACCESS CONTROL (RBAC) ---")

    # Student session
    student_client = app.app.test_client()
    student_client.post("/login", data={"email": "student@test.com", "password": "student123"})
    
    # Student accessing /teacher -> redirected to /student
    res_s_to_t = student_client.get("/teacher", follow_redirects=False)
    if res_s_to_t.status_code == 302 and res_s_to_t.headers["Location"] in ["/student", "http://localhost/student"]:
        print("[OK] Student accessing /teacher blocked and redirected to /student")
    else:
        print(f"[FAIL] Student access to /teacher failed: {res_s_to_t.status_code} -> {res_s_to_t.headers.get('Location')}")
        passed = False

    # Student accessing /admin -> redirected to /student
    res_s_to_a = student_client.get("/admin", follow_redirects=False)
    if res_s_to_a.status_code == 302 and res_s_to_a.headers["Location"] in ["/student", "http://localhost/student"]:
        print("[OK] Student accessing /admin blocked and redirected to /student")
    else:
        print(f"[FAIL] Student access to /admin failed: {res_s_to_a.status_code} -> {res_s_to_a.headers.get('Location')}")
        passed = False

    # Teacher session
    teacher_client = app.app.test_client()
    teacher_client.post("/login", data={"email": "teacher@test.com", "password": "teacher123"})

    # Teacher accessing /student -> redirected to /teacher
    res_t_to_s = teacher_client.get("/student", follow_redirects=False)
    if res_t_to_s.status_code == 302 and res_t_to_s.headers["Location"] in ["/teacher", "http://localhost/teacher"]:
        print("[OK] Teacher accessing /student blocked and redirected to /teacher")
    else:
        print(f"[FAIL] Teacher access to /student failed: {res_t_to_s.status_code} -> {res_t_to_s.headers.get('Location')}")
        passed = False

    # Teacher accessing /admin -> redirected to /teacher
    res_t_to_a = teacher_client.get("/admin", follow_redirects=False)
    if res_t_to_a.status_code == 302 and res_t_to_a.headers["Location"] in ["/teacher", "http://localhost/teacher"]:
        print("[OK] Teacher accessing /admin blocked and redirected to /teacher")
    else:
        print(f"[FAIL] Teacher access to /admin failed: {res_t_to_a.status_code} -> {res_t_to_a.headers.get('Location')}")
        passed = False

    # Admin session
    admin_client = app.app.test_client()
    admin_client.post("/login", data={"email": "admin@test.com", "password": "admin123"})

    # Admin accessing /student -> redirected to /admin
    res_a_to_s = admin_client.get("/student", follow_redirects=False)
    if res_a_to_s.status_code == 302 and res_a_to_s.headers["Location"] in ["/admin", "http://localhost/admin"]:
        print("[OK] Admin accessing /student redirected to /admin")
    else:
        print(f"[FAIL] Admin access to /student failed: {res_a_to_s.status_code} -> {res_a_to_s.headers.get('Location')}")
        passed = False

    # 6. TEST LOGOUT
    print("\n--- TEST 6: LOGOUT FUNCTIONALITY ---")
    res_logout = student_client.get("/logout", follow_redirects=False)
    if res_logout.status_code == 302 and res_logout.headers["Location"] in ["/login", "http://localhost/login"]:
        print("[OK] /logout redirects to /login (302)")
    else:
        print(f"[FAIL] Logout redirect failed: {res_logout.status_code}")
        passed = False

    # Verify session cleared after logout
    res_post_logout = student_client.get("/student", follow_redirects=False)
    if res_post_logout.status_code == 302 and res_post_logout.headers["Location"] in ["/login", "http://localhost/login"]:
        print("[OK] Session cleared: subsequent protected access redirected to /login")
    else:
        print(f"[FAIL] Session was not cleared after logout: {res_post_logout.status_code}")
        passed = False

    # 7. TEST SIGNUP SECURITY (NO PUBLIC ADMIN SIGNUP)
    print("\n--- TEST 7: SIGNUP RESTRICTIONS & PASSWORD HASHING ---")
    signup_client = app.app.test_client()

    # Attempt to signup with admin role
    res_admin_signup = signup_client.post("/signup", data={
        "fullname": "Attacker Admin",
        "email": "hacker@test.com",
        "password": "hackpass123",
        "role": "admin"
    }, follow_redirects=True)
    if b"Invalid role" in res_admin_signup.data:
        print("[OK] Public admin signup strictly blocked!")
    else:
        print("[FAIL] Public admin signup was not rejected!")
        passed = False

    # Valid student signup
    test_new_email = "new_student_auto@test.com"
    # Clean up if existed from previous run
    conn = sqlite3.connect("database.db")
    conn.execute("DELETE FROM users WHERE email = ?", (test_new_email,))
    conn.commit()
    conn.close()

    res_valid_signup = signup_client.post("/signup", data={
        "fullname": "New Auto Student",
        "email": test_new_email,
        "password": "newpassword123",
        "role": "student"
    }, follow_redirects=True)
    if b"Account created successfully" in res_valid_signup.data:
        print("[OK] Valid student signup succeeded")
    else:
        print(f"[FAIL] Valid student signup failed")
        passed = False

    # Verify new user password in database is hashed
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT password FROM users WHERE email = ?", (test_new_email,))
    row = c.fetchone()
    conn.close()
    if row and (row[0].startswith("scrypt:") or row[0].startswith("pbkdf2:")):
        print(f"[OK] Newly registered user password is cryptographically hashed: {row[0][:22]}...")
    else:
        print(f"[FAIL] Newly registered user password is not hashed: {row}")
        passed = False

    # 8. TEST DYNAMIC USERNAME DISPLAY
    print("\n--- TEST 8: DYNAMIC USERNAME DISPLAY IN DASHBOARDS ---")
    student_test_client = app.app.test_client()
    student_test_client.post("/login", data={"email": "student@test.com", "password": "student123"})
    res_s_page = student_test_client.get("/student")
    if b"Shreeram Student" in res_s_page.data:
        print("[OK] Student dashboard dynamically displays logged-in student name")
    else:
        print("[FAIL] Student name not found on student dashboard")
        passed = False

    teacher_test_client = app.app.test_client()
    teacher_test_client.post("/login", data={"email": "teacher@test.com", "password": "teacher123"})
    res_t_page = teacher_test_client.get("/teacher")
    if b"Prof. Alan Teacher" in res_t_page.data:
        print("[OK] Faculty dashboard dynamically displays logged-in teacher name")
    else:
        print("[FAIL] Teacher name not found on teacher dashboard")
        passed = False

    admin_test_client = app.app.test_client()
    admin_test_client.post("/login", data={"email": "admin@test.com", "password": "admin123"})
    res_a_page = admin_test_client.get("/admin")
    if b"System Administrator" in res_a_page.data:
        print("[OK] Admin dashboard dynamically displays logged-in admin name")
    else:
        print("[FAIL] Admin name not found on admin dashboard")
        passed = False

    print("\n==================================================")
    if passed:
        print("ALL DAY 3 TESTS PASSED PERFECTLY (100% SUCCESS)!")
    else:
        print("SOME TESTS FAILED!")
    print("==================================================")

if __name__ == "__main__":
    test_day3()
