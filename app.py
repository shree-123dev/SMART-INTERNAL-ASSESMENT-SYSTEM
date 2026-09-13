import os
import sqlite3
import qrcode
import json
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db_connection
from generate_qr import generate_student_qr, ensure_student_qr

app = Flask(__name__)
app.secret_key = "siams_secret_key_2026"

# ----------------------------------------------------
# AUTHENTICATION & ACCESS CONTROL HELPERS (DAY 3)
# ----------------------------------------------------

def login_required(f):
    """Ensures a user is authenticated before accessing a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or "role" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Ensures the authenticated user has one of the allowed roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session or "role" not in session:
                return redirect(url_for("login"))
            user_role = session.get("role")
            if user_role not in allowed_roles:
                # Redirect unauthorized users to their designated role dashboard
                if user_role == "student":
                    return redirect(url_for("student"))
                elif user_role == "teacher":
                    return redirect(url_for("teacher"))
                elif user_role == "admin":
                    return redirect(url_for("admin"))
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN PAGE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    success = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            error = "Please provide both institutional email and password."
            return render_template("login.html", error=error)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, fullname, email, password, role FROM users WHERE email = ?",
            (email,)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            # Clear old session and establish fresh session
            session.clear()
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            role = user["role"]
            if role == "student":
                return redirect(url_for("student"))
            elif role == "teacher":
                return redirect(url_for("teacher"))
            elif role == "admin":
                return redirect(url_for("admin"))
        else:
            error = "Invalid institutional email or password."

    elif request.method == "GET":
        # If user is already logged in and visits /login via GET, redirect directly to their dashboard
        if "user_id" in session and "role" in session:
            role = session.get("role")
            if role == "student":
                return redirect(url_for("student"))
            elif role == "teacher":
                return redirect(url_for("teacher"))
            elif role == "admin":
                return redirect(url_for("admin"))

    return render_template("login.html", error=error, success=success)


# ---------------- SIGNUP PAGE ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None

    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "").strip()

        # Validation: check empty fields
        if not fullname or not email or not password or not role:
            error = "All fields are required. Please fill out the entire registration form."
            return render_template("signup.html", error=error)

        # Validation: check allowed roles (DO NOT allow public admin registration)
        if role not in ["student", "teacher"]:
            error = "Invalid role selected! Public registration is only available for students and teachers."
            return render_template("signup.html", error=error)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash password securely using Werkzeug
        hashed_password = generate_password_hash(password)

        try:
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                (fullname, email, hashed_password, role)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            error = "An account with this email address already exists. Please sign in instead."
            return render_template("signup.html", error=error)

        conn.close()
        return render_template("login.html", success="Account created successfully! Please sign in with your credentials.")

    return render_template("signup.html", error=error)


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


# ---------------- DASHBOARD GATEWAY ----------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ---------------- STUDENT DASHBOARD (ROLE PROTECTED) ----------------
@app.route("/student")
@role_required("student")
def student():
    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT usn,
           fullname,
           email,
           department,
           semester,
           section,
           qr_path
    FROM students
    WHERE email = ?
    """, (email,))

    student_data = cursor.fetchone()

    # Automatically ensure QR code exists for this student
    if student_data:
        usn = student_data["usn"]
        qr_file = ensure_student_qr(usn, student_data["fullname"], student_data["department"], student_data["semester"])
        if student_data["qr_path"] != qr_file:
            cursor.execute("UPDATE students SET qr_path = ? WHERE usn = ?", (qr_file, usn))
            conn.commit()
            cursor.execute("""
                SELECT usn, fullname, email, department, semester, section, qr_path
                FROM students
                WHERE email = ?
            """, (email,))
            student_data = cursor.fetchone()

    conn.close()

    return render_template(
        "student.html",
        student=student_data,
        fullname=session.get("fullname", (student_data["fullname"] if student_data else "Student"))
    )


# ---------------- MY QR CODE (STUDENT ROLE PROTECTED) ----------------
@app.route("/my_qr")
@role_required("student")
def my_qr():
    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT usn, fullname, email, department, semester, section, qr_path
        FROM students
        WHERE email = ?
    """, (email,))
    student_data = cursor.fetchone()

    if not student_data:
        conn.close()
        return redirect(url_for("student"))

    qr_file = ensure_student_qr(student_data["usn"], student_data["fullname"], student_data["department"], student_data["semester"])
    if student_data["qr_path"] != qr_file:
        cursor.execute("UPDATE students SET qr_path = ? WHERE usn = ?", (qr_file, student_data["usn"]))
        conn.commit()
        cursor.execute("""
            SELECT usn, fullname, email, department, semester, section, qr_path
            FROM students
            WHERE email = ?
        """, (email,))
        student_data = cursor.fetchone()

    conn.close()
    return render_template("student_qr_card.html", student=student_data, is_admin=False)


# ---------------- TEACHER DASHBOARD (ROLE PROTECTED) ----------------
@app.route("/teacher")
@role_required("teacher")
def teacher():
    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine logged-in teacher identity from session
    cursor.execute("""
        SELECT teacher_id, fullname, email, department
        FROM teachers
        WHERE email = ?
    """, (email,))
    tch = cursor.fetchone()

    assigned_subjects = []
    teacher_id = None
    active_session = None
    total_sessions = 0

    if tch:
        teacher_id = tch["teacher_id"]
        # JOIN query to retrieve ONLY subjects assigned to this logged-in teacher
        cursor.execute("""
            SELECT subjects.subject_code,
                   subjects.subject_name,
                   subjects.department,
                   subjects.semester
            FROM teacher_subjects
            JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
            WHERE teacher_subjects.teacher_id = ?
            ORDER BY subjects.subject_code ASC
        """, (teacher_id,))
        assigned_subjects = cursor.fetchall()

        # Query currently active session for this teacher (Day 7)
        cursor.execute("""
            SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.start_time, ps.end_time, ps.status,
                   s.subject_name, s.department, s.semester, t.fullname as teacher_name
            FROM practical_sessions ps
            JOIN subjects s ON ps.subject_id = s.subject_code
            JOIN teachers t ON ps.teacher_id = t.teacher_id
            WHERE ps.teacher_id = ? AND ps.status = 'active'
            ORDER BY ps.id DESC LIMIT 1
        """, (teacher_id,))
        active_session = cursor.fetchone()

        # Count total practical sessions conducted by this faculty member
        cursor.execute("SELECT COUNT(*) FROM practical_sessions WHERE teacher_id = ?", (teacher_id,))
        total_sessions = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "teacher.html",
        fullname=session.get("fullname", "Faculty Member"),
        teacher=tch,
        teacher_id=teacher_id,
        assigned_subjects=assigned_subjects,
        active_session=active_session,
        total_sessions=total_sessions
    )


# ---------------- ADMIN DASHBOARD (ROLE PROTECTED) ----------------
@app.route("/admin")
@role_required("admin")
def admin():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query live database counts (not hardcoded)
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM teachers")
    total_teachers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM subjects")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM teacher_subjects")
    total_assignments = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "admin.html",
        fullname=session.get("fullname", "Administrator"),
        total_students=total_students,
        total_teachers=total_teachers,
        total_subjects=total_subjects,
        total_assignments=total_assignments
    )


# ====================================================
# STUDENT MANAGEMENT MODULE (DAY 4)
# ====================================================

# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET", "POST"])
@role_required("admin")
def add_student():
    error = None
    if request.method == "POST":
        usn = request.form.get("usn", "").strip().upper()
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()
        section = request.form.get("section", "").strip().upper()

        if not usn or not fullname or not email or not department or not semester or not section:
            error = "All fields are required. Please fill out the complete student registration form."
            return render_template("add_student.html", error=error)

        try:
            sem_num = int(semester)
            if sem_num < 1 or sem_num > 8:
                error = "Semester must be a valid academic semester between 1 and 8."
                return render_template("add_student.html", error=error)
        except ValueError:
            error = "Semester must be a valid number between 1 and 8."
            return render_template("add_student.html", error=error)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for duplicate USN
        cursor.execute("SELECT id FROM students WHERE usn = ?", (usn,))
        if cursor.fetchone():
            conn.close()
            error = f"A student with USN '{usn}' is already registered in the system."
            return render_template("add_student.html", error=error)

        # Check for duplicate Email
        cursor.execute("SELECT id FROM students WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            error = f"A student with institutional email '{email}' already exists."
            return render_template("add_student.html", error=error)

        try:
            # Generate QR code for student
            qr_path = generate_student_qr(usn, fullname, department, sem_num)

            cursor.execute("""
                INSERT INTO students (usn, fullname, email, department, semester, section, qr_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (usn, fullname, email, department, sem_num, section, qr_path))
            conn.commit()
            conn.close()
            return redirect(url_for("view_students", success=f"Student {fullname} ({usn}) enrolled successfully!"))
        except Exception as e:
            conn.close()
            error = f"Database error while creating student: {str(e)}"
            return render_template("add_student.html", error=error)

    return render_template("add_student.html", error=error)


# ---------------- VIEW STUDENTS (WITH SEARCH) ----------------
@app.route("/view_students")
@role_required("admin")
def view_students():
    search_query = request.args.get("search", "").strip()
    success = request.args.get("success")
    error = request.args.get("error")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        term = f"%{search_query}%"
        cursor.execute("""
            SELECT usn, fullname, email, department, semester, section, qr_path
            FROM students
            WHERE usn LIKE ? OR fullname LIKE ? OR email LIKE ? OR department LIKE ?
            ORDER BY usn ASC
        """, (term, term, term, term))
    else:
        cursor.execute("""
            SELECT usn, fullname, email, department, semester, section, qr_path
            FROM students
            ORDER BY usn ASC
        """)

    students = cursor.fetchall()
    conn.close()

    return render_template(
        "view_students.html",
        students=students,
        search_query=search_query,
        success=success,
        error=error
    )


# ---------------- VIEW SINGLE STUDENT DETAILS ----------------
@app.route("/view_student/<usn>")
@role_required("admin")
def view_student(usn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT usn, fullname, email, department, semester, section, qr_path
        FROM students
        WHERE usn = ?
    """, (usn,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return redirect(url_for("view_students", error=f"Student record '{usn}' not found."))

    return render_template("view_student.html", student=student)


# ---------------- EDIT STUDENT ----------------
@app.route("/edit_student/<usn>", methods=["GET", "POST"])
@role_required("admin")
def edit_student(usn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students WHERE usn = ?", (usn,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return redirect(url_for("view_students", error=f"Student '{usn}' not found."))

    error = None
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()
        section = request.form.get("section", "").strip().upper()

        if not fullname or not email or not department or not semester or not section:
            error = "All fields are required. Please fill out all student details."
            conn.close()
            return render_template("edit_student.html", student=student, error=error)

        try:
            sem_num = int(semester)
            if sem_num < 1 or sem_num > 8:
                error = "Semester must be a valid academic semester between 1 and 8."
                conn.close()
                return render_template("edit_student.html", student=student, error=error)
        except ValueError:
            error = "Semester must be a valid number between 1 and 8."
            conn.close()
            return render_template("edit_student.html", student=student, error=error)

        # Check if updated email is already taken by another student
        cursor.execute("SELECT id FROM students WHERE email = ? AND usn != ?", (email, usn))
        if cursor.fetchone():
            conn.close()
            error = f"The email '{email}' is already registered to another student."
            return render_template("edit_student.html", student=student, error=error)

        try:
            cursor.execute("""
                UPDATE students
                SET fullname = ?, email = ?, department = ?, semester = ?, section = ?
                WHERE usn = ?
            """, (fullname, email, department, sem_num, section, usn))
            conn.commit()
            conn.close()
            return redirect(url_for("view_students", success=f"Student {usn} details updated successfully!"))
        except Exception as e:
            conn.close()
            error = f"Error updating student: {str(e)}"
            return render_template("edit_student.html", student=student, error=error)

    conn.close()
    return render_template("edit_student.html", student=student, error=error)


# ---------------- DELETE STUDENT ----------------
@app.route("/delete_student/<usn>", methods=["POST"])
@role_required("admin")
def delete_student(usn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT fullname FROM students WHERE usn = ?", (usn,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return redirect(url_for("view_students", error=f"Student '{usn}' not found."))

    try:
        # Safely handle associated attendance and marks data
        cursor.execute("DELETE FROM attendance WHERE student_id = ?", (usn,))
        cursor.execute("DELETE FROM internal_marks WHERE student_id = ?", (usn,))
        cursor.execute("DELETE FROM students WHERE usn = ?", (usn,))
        conn.commit()
        conn.close()

        # Clean up QR file if exists
        qr_file = os.path.join("static", "qr", f"{usn}.png")
        if os.path.exists(qr_file):
            try:
                os.remove(qr_file)
            except Exception:
                pass

        return redirect(url_for("view_students", success=f"Student {student['fullname']} ({usn}) was safely deleted."))
    except Exception as e:
        conn.close()
        return redirect(url_for("view_students", error=f"Could not delete student: {str(e)}"))


# ---------------- ADMIN REGENERATE STUDENT QR ----------------
@app.route("/admin/generate_qr/<usn>", methods=["POST"])
@role_required("admin")
def admin_generate_qr(usn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT usn, fullname, department, semester FROM students WHERE usn = ?", (usn,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return redirect(url_for("view_students", error=f"Student record '{usn}' not found."))

    try:
        qr_path = generate_student_qr(student["usn"], student["fullname"], student["department"], student["semester"])
        cursor.execute("UPDATE students SET qr_path = ? WHERE usn = ?", (qr_path, usn))
        conn.commit()
        conn.close()
        return redirect(url_for("view_students", success=f"QR Code regenerated successfully for student {student['fullname']} ({usn})!"))
    except Exception as e:
        conn.close()
        return redirect(url_for("view_students", error=f"Could not generate QR code: {str(e)}"))


# ---------------- ADMIN VIEW STUDENT QR CARD ----------------
@app.route("/admin/student_qr/<usn>")
@role_required("admin")
def admin_student_qr(usn):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT usn, fullname, email, department, semester, section, qr_path
        FROM students
        WHERE usn = ?
    """, (usn,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return redirect(url_for("view_students", error=f"Student record '{usn}' not found."))

    qr_file = ensure_student_qr(student["usn"], student["fullname"], student["department"], student["semester"])
    if student["qr_path"] != qr_file:
        cursor.execute("UPDATE students SET qr_path = ? WHERE usn = ?", (qr_file, student["usn"]))
        conn.commit()
        cursor.execute("""
            SELECT usn, fullname, email, department, semester, section, qr_path
            FROM students
            WHERE usn = ?
        """, (usn,))
        student = cursor.fetchone()

    conn.close()
    return render_template("student_qr_card.html", student=student, is_admin=True)


# ====================================================
# TEACHER MANAGEMENT MODULE (DAY 4)
# ====================================================

# ---------------- ADD TEACHER ----------------
@app.route("/add_teacher", methods=["GET", "POST"])
@role_required("admin")
def add_teacher():
    error = None
    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", "").strip().upper()
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()

        if not teacher_id or not fullname or not email or not department:
            error = "All fields are required. Please fill out all faculty details."
            return render_template("add_teacher.html", error=error)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate Teacher ID
        cursor.execute("SELECT id FROM teachers WHERE teacher_id = ?", (teacher_id,))
        if cursor.fetchone():
            conn.close()
            error = f"Teacher ID '{teacher_id}' is already assigned to a faculty member."
            return render_template("add_teacher.html", error=error)

        # Check duplicate Email
        cursor.execute("SELECT id FROM teachers WHERE email = ?", (email,))
        if cursor.fetchone():
            conn.close()
            error = f"A faculty member with institutional email '{email}' already exists."
            return render_template("add_teacher.html", error=error)

        try:
            cursor.execute("""
                INSERT INTO teachers (teacher_id, fullname, email, department)
                VALUES (?, ?, ?, ?)
            """, (teacher_id, fullname, email, department))
            conn.commit()
            conn.close()
            return redirect(url_for("view_teachers", success=f"Faculty member {fullname} ({teacher_id}) added successfully!"))
        except Exception as e:
            conn.close()
            error = f"Database error while creating faculty member: {str(e)}"
            return render_template("add_teacher.html", error=error)

    return render_template("add_teacher.html", error=error)


# ---------------- VIEW TEACHERS (WITH SEARCH) ----------------
@app.route("/view_teachers")
@role_required("admin")
def view_teachers():
    search_query = request.args.get("search", "").strip()
    success = request.args.get("success")
    error = request.args.get("error")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        term = f"%{search_query}%"
        cursor.execute("""
            SELECT teacher_id, fullname, email, department
            FROM teachers
            WHERE teacher_id LIKE ? OR fullname LIKE ? OR email LIKE ? OR department LIKE ?
            ORDER BY teacher_id ASC
        """, (term, term, term, term))
    else:
        cursor.execute("""
            SELECT teacher_id, fullname, email, department
            FROM teachers
            ORDER BY teacher_id ASC
        """)

    teachers_raw = cursor.fetchall()

    teachers_list = []
    for t in teachers_raw:
        cursor.execute("""
            SELECT subjects.subject_code, subjects.subject_name
            FROM teacher_subjects
            JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
            WHERE teacher_subjects.teacher_id = ?
        """, (t["teacher_id"],))
        assigned_subjects = cursor.fetchall()
        teachers_list.append({
            "teacher_id": t["teacher_id"],
            "fullname": t["fullname"],
            "email": t["email"],
            "department": t["department"],
            "subjects": assigned_subjects
        })

    conn.close()

    return render_template(
        "view_teachers.html",
        teachers=teachers_list,
        search_query=search_query,
        success=success,
        error=error
    )


# ---------------- VIEW SINGLE TEACHER DETAILS ----------------
@app.route("/view_teacher/<teacher_id>")
@role_required("admin")
def view_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT teacher_id, fullname, email, department
        FROM teachers
        WHERE teacher_id = ?
    """, (teacher_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        return redirect(url_for("view_teachers", error=f"Faculty record '{teacher_id}' not found."))

    cursor.execute("""
        SELECT subjects.subject_code, subjects.subject_name, subjects.department, subjects.semester
        FROM teacher_subjects
        JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
        WHERE teacher_subjects.teacher_id = ?
    """, (teacher_id,))
    assigned_subjects = cursor.fetchall()
    conn.close()

    return render_template("view_teacher.html", teacher=teacher, subjects=assigned_subjects)


# ---------------- EDIT TEACHER ----------------
@app.route("/edit_teacher/<teacher_id>", methods=["GET", "POST"])
@role_required("admin")
def edit_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM teachers WHERE teacher_id = ?", (teacher_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        return redirect(url_for("view_teachers", error=f"Faculty member '{teacher_id}' not found."))

    error = None
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip()
        department = request.form.get("department", "").strip()

        if not fullname or not email or not department:
            error = "All fields are required. Please complete all faculty fields."
            conn.close()
            return render_template("edit_teacher.html", teacher=teacher, error=error)

        # Check if updated email is already taken by another teacher
        cursor.execute("SELECT id FROM teachers WHERE email = ? AND teacher_id != ?", (email, teacher_id))
        if cursor.fetchone():
            conn.close()
            error = f"The email '{email}' is already in use by another faculty member."
            return render_template("edit_teacher.html", teacher=teacher, error=error)

        try:
            cursor.execute("""
                UPDATE teachers
                SET fullname = ?, email = ?, department = ?
                WHERE teacher_id = ?
            """, (fullname, email, department, teacher_id))
            conn.commit()
            conn.close()
            return redirect(url_for("view_teachers", success=f"Faculty member {teacher_id} details updated successfully!"))
        except Exception as e:
            conn.close()
            error = f"Error updating faculty member: {str(e)}"
            return render_template("edit_teacher.html", teacher=teacher, error=error)

    conn.close()
    return render_template("edit_teacher.html", teacher=teacher, error=error)


# ---------------- DELETE TEACHER ----------------
@app.route("/delete_teacher/<teacher_id>", methods=["POST"])
@role_required("admin")
def delete_teacher(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT fullname FROM teachers WHERE teacher_id = ?", (teacher_id,))
    teacher = cursor.fetchone()

    if not teacher:
        conn.close()
        return redirect(url_for("view_teachers", error=f"Faculty member '{teacher_id}' not found."))

    try:
        # Safely clean up teacher-subject mappings and session logs for this teacher
        cursor.execute("DELETE FROM teacher_subjects WHERE teacher_id = ?", (teacher_id,))
        cursor.execute("DELETE FROM practical_sessions WHERE teacher_id = ?", (teacher_id,))
        cursor.execute("DELETE FROM attendance WHERE teacher_id = ?", (teacher_id,))
        cursor.execute("DELETE FROM teachers WHERE teacher_id = ?", (teacher_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("view_teachers", success=f"Faculty member {teacher['fullname']} ({teacher_id}) was safely removed."))
    except Exception as e:
        conn.close()
        return redirect(url_for("view_teachers", error=f"Could not delete faculty member: {str(e)}"))


# ====================================================
# SUBJECT MANAGEMENT MODULE (DAY 4)
# ====================================================

# ---------------- ADD SUBJECT ----------------
@app.route("/add_subject", methods=["GET", "POST"])
@role_required("admin")
def add_subject():
    error = None
    if request.method == "POST":
        subject_code = request.form.get("subject_code", "").strip().upper()
        subject_name = request.form.get("subject_name", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()

        if not subject_code or not subject_name or not department or not semester:
            error = "All fields are required. Please fill out the complete subject form."
            return render_template("add_subject.html", error=error)

        try:
            sem_num = int(semester)
            if sem_num < 1 or sem_num > 8:
                error = "Semester must be a valid academic semester between 1 and 8."
                return render_template("add_subject.html", error=error)
        except ValueError:
            error = "Semester must be a valid number between 1 and 8."
            return render_template("add_subject.html", error=error)

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check duplicate subject_code
        cursor.execute("SELECT id FROM subjects WHERE subject_code = ?", (subject_code,))
        if cursor.fetchone():
            conn.close()
            error = f"A subject with code '{subject_code}' already exists in curriculum catalog."
            return render_template("add_subject.html", error=error)

        try:
            cursor.execute("""
                INSERT INTO subjects (subject_code, subject_name, department, semester)
                VALUES (?, ?, ?, ?)
            """, (subject_code, subject_name, department, sem_num))
            conn.commit()
            conn.close()
            return redirect(url_for("view_subjects", success=f"Subject {subject_name} ({subject_code}) added to catalog!"))
        except Exception as e:
            conn.close()
            error = f"Database error while creating subject: {str(e)}"
            return render_template("add_subject.html", error=error)

    return render_template("add_subject.html", error=error)


# ---------------- VIEW SUBJECTS (WITH SEARCH) ----------------
@app.route("/view_subjects")
@role_required("admin")
def view_subjects():
    search_query = request.args.get("search", "").strip()
    success = request.args.get("success")
    error = request.args.get("error")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        term = f"%{search_query}%"
        cursor.execute("""
            SELECT subject_code, subject_name, department, semester
            FROM subjects
            WHERE subject_code LIKE ? OR subject_name LIKE ? OR department LIKE ?
            ORDER BY subject_code ASC
        """, (term, term, term))
    else:
        cursor.execute("""
            SELECT subject_code, subject_name, department, semester
            FROM subjects
            ORDER BY subject_code ASC
        """)

    subjects_raw = cursor.fetchall()

    subjects_list = []
    for s in subjects_raw:
        cursor.execute("""
            SELECT teachers.teacher_id, teachers.fullname
            FROM teacher_subjects
            JOIN teachers ON teacher_subjects.teacher_id = teachers.teacher_id
            WHERE teacher_subjects.subject_id = ?
        """, (s["subject_code"],))
        mapped_teachers = cursor.fetchall()
        subjects_list.append({
            "subject_code": s["subject_code"],
            "subject_name": s["subject_name"],
            "department": s["department"],
            "semester": s["semester"],
            "teachers": mapped_teachers
        })

    conn.close()

    return render_template(
        "view_subjects.html",
        subjects=subjects_list,
        search_query=search_query,
        success=success,
        error=error
    )


# ---------------- VIEW SINGLE SUBJECT DETAILS ----------------
@app.route("/view_subject/<subject_code>")
@role_required("admin")
def view_subject(subject_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject_code, subject_name, department, semester
        FROM subjects
        WHERE subject_code = ?
    """, (subject_code,))
    subject = cursor.fetchone()

    if not subject:
        conn.close()
        return redirect(url_for("view_subjects", error=f"Subject record '{subject_code}' not found."))

    cursor.execute("""
        SELECT teachers.teacher_id, teachers.fullname, teachers.email, teachers.department
        FROM teacher_subjects
        JOIN teachers ON teacher_subjects.teacher_id = teachers.teacher_id
        WHERE teacher_subjects.subject_id = ?
    """, (subject_code,))
    faculty = cursor.fetchall()
    conn.close()

    return render_template("view_subject.html", subject=subject, teachers=faculty)


# ---------------- EDIT SUBJECT ----------------
@app.route("/edit_subject/<subject_code>", methods=["GET", "POST"])
@role_required("admin")
def edit_subject(subject_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM subjects WHERE subject_code = ?", (subject_code,))
    subject = cursor.fetchone()

    if not subject:
        conn.close()
        return redirect(url_for("view_subjects", error=f"Subject '{subject_code}' not found."))

    error = None
    if request.method == "POST":
        subject_name = request.form.get("subject_name", "").strip()
        department = request.form.get("department", "").strip()
        semester = request.form.get("semester", "").strip()

        if not subject_name or not department or not semester:
            error = "All fields are required. Please complete all subject fields."
            conn.close()
            return render_template("edit_subject.html", subject=subject, error=error)

        try:
            sem_num = int(semester)
            if sem_num < 1 or sem_num > 8:
                error = "Semester must be a valid academic semester between 1 and 8."
                conn.close()
                return render_template("edit_subject.html", subject=subject, error=error)
        except ValueError:
            error = "Semester must be a valid number between 1 and 8."
            conn.close()
            return render_template("edit_subject.html", subject=subject, error=error)

        try:
            cursor.execute("""
                UPDATE subjects
                SET subject_name = ?, department = ?, semester = ?
                WHERE subject_code = ?
            """, (subject_name, department, sem_num, subject_code))
            conn.commit()
            conn.close()
            return redirect(url_for("view_subjects", success=f"Subject {subject_code} updated successfully!"))
        except Exception as e:
            conn.close()
            error = f"Error updating subject: {str(e)}"
            return render_template("edit_subject.html", subject=subject, error=error)

    conn.close()
    return render_template("edit_subject.html", subject=subject, error=error)


# ---------------- DELETE SUBJECT ----------------
@app.route("/delete_subject/<subject_code>", methods=["POST"])
@role_required("admin")
def delete_subject(subject_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT subject_name FROM subjects WHERE subject_code = ?", (subject_code,))
    subject = cursor.fetchone()

    if not subject:
        conn.close()
        return redirect(url_for("view_subjects", error=f"Subject '{subject_code}' not found."))

    try:
        # Safely clean up associated teacher mappings, sessions, attendance, and marks
        cursor.execute("DELETE FROM teacher_subjects WHERE subject_id = ?", (subject_code,))
        cursor.execute("DELETE FROM practical_sessions WHERE subject_id = ?", (subject_code,))
        cursor.execute("DELETE FROM attendance WHERE subject_id = ?", (subject_code,))
        cursor.execute("DELETE FROM internal_marks WHERE subject_id = ?", (subject_code,))
        cursor.execute("DELETE FROM subjects WHERE subject_code = ?", (subject_code,))
        conn.commit()
        conn.close()
        return redirect(url_for("view_subjects", success=f"Subject {subject['subject_name']} ({subject_code}) was safely deleted."))
    except Exception as e:
        conn.close()
        return redirect(url_for("view_subjects", error=f"Could not delete subject: {str(e)}"))


# ====================================================
# TEACHER-SUBJECT ASSIGNMENT MODULE (DAY 5)
# ====================================================

# ---------------- ASSIGN SUBJECT TO TEACHER (ADMIN ONLY) ----------------
@app.route("/assign_subject", methods=["GET", "POST"])
@role_required("admin")
def assign_subject():
    conn = get_db_connection()
    cursor = conn.cursor()
    error = None

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id", "").strip()
        subject_code = request.form.get("subject_code", "").strip()

        # Validation: check empty fields
        if not teacher_id or not subject_code:
            error = "Please select both a faculty instructor and a curriculum subject."
        else:
            # Validate teacher exists
            cursor.execute("SELECT fullname FROM teachers WHERE teacher_id = ?", (teacher_id,))
            teacher_row = cursor.fetchone()

            # Validate subject exists
            cursor.execute("SELECT subject_name FROM subjects WHERE subject_code = ?", (subject_code,))
            subject_row = cursor.fetchone()

            if not teacher_row:
                error = f"Selected faculty member (ID: {teacher_id}) was not found."
            elif not subject_row:
                error = f"Selected subject (Code: {subject_code}) was not found."
            else:
                # Check for duplicate assignment
                cursor.execute("""
                    SELECT id FROM teacher_subjects
                    WHERE teacher_id = ? AND subject_id = ?
                """, (teacher_id, subject_code))
                existing_assignment = cursor.fetchone()

                if existing_assignment:
                    error = f"Subject is already assigned to this teacher."
                else:
                    # Parameterized INSERT into teacher_subjects
                    try:
                        cursor.execute("""
                            INSERT INTO teacher_subjects (teacher_id, subject_id)
                            VALUES (?, ?)
                        """, (teacher_id, subject_code))
                        conn.commit()
                        conn.close()
                        return redirect(url_for("view_assignments", success=f"Subject assigned successfully."))
                    except Exception as e:
                        error = f"Failed to assign subject: {str(e)}"

    # Load all teachers and subjects for dropdown selectors
    cursor.execute("SELECT teacher_id, fullname, department FROM teachers ORDER BY fullname ASC")
    teachers = cursor.fetchall()

    cursor.execute("SELECT subject_code, subject_name, department, semester FROM subjects ORDER BY subject_code ASC")
    subjects = cursor.fetchall()
    conn.close()

    return render_template(
        "assign_subject.html",
        teachers=teachers,
        subjects=subjects,
        error=error
    )


# ---------------- VIEW ALL ASSIGNMENTS (ADMIN ONLY) ----------------
@app.route("/view_assignments")
@role_required("admin")
def view_assignments():
    search_query = request.args.get("search", "").strip()
    success = request.args.get("success")
    error = request.args.get("error")

    conn = get_db_connection()
    cursor = conn.cursor()

    if search_query:
        term = f"%{search_query}%"
        # JOIN query with search filtering
        cursor.execute("""
            SELECT teacher_subjects.id AS assignment_id,
                   teachers.teacher_id,
                   teachers.fullname AS teacher_name,
                   teachers.department AS teacher_department,
                   subjects.subject_code,
                   subjects.subject_name,
                   subjects.department AS subject_department,
                   subjects.semester
            FROM teacher_subjects
            JOIN teachers ON teacher_subjects.teacher_id = teachers.teacher_id
            JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
            WHERE teachers.fullname LIKE ? OR teachers.teacher_id LIKE ? OR subjects.subject_name LIKE ? OR subjects.subject_code LIKE ?
            ORDER BY teachers.fullname ASC, subjects.subject_code ASC
        """, (term, term, term, term))
    else:
        # Standard JOIN query to retrieve all active assignments
        cursor.execute("""
            SELECT teacher_subjects.id AS assignment_id,
                   teachers.teacher_id,
                   teachers.fullname AS teacher_name,
                   teachers.department AS teacher_department,
                   subjects.subject_code,
                   subjects.subject_name,
                   subjects.department AS subject_department,
                   subjects.semester
            FROM teacher_subjects
            JOIN teachers ON teacher_subjects.teacher_id = teachers.teacher_id
            JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
            ORDER BY teachers.fullname ASC, subjects.subject_code ASC
        """)

    assignments = cursor.fetchall()
    conn.close()

    return render_template(
        "view_assignments.html",
        assignments=assignments,
        search_query=search_query,
        success=success,
        error=error
    )


# ---------------- REMOVE ASSIGNMENT (ADMIN ONLY) ----------------
@app.route("/remove_assignment/<int:assignment_id>", methods=["POST"])
@role_required("admin")
def remove_assignment(assignment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT teacher_subjects.id,
               teachers.fullname AS teacher_name,
               subjects.subject_name
        FROM teacher_subjects
        JOIN teachers ON teacher_subjects.teacher_id = teachers.teacher_id
        JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
        WHERE teacher_subjects.id = ?
    """, (assignment_id,))
    assignment = cursor.fetchone()

    if not assignment:
        conn.close()
        return redirect(url_for("view_assignments", error="Assignment record not found."))

    try:
        # ONLY delete from teacher_subjects (preserves teacher, subject, students, attendance, marks)
        cursor.execute("DELETE FROM teacher_subjects WHERE id = ?", (assignment_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("view_assignments", success=f"Assignment for {assignment['teacher_name']} ({assignment['subject_name']}) removed successfully."))
    except Exception as e:
        conn.close()
        return redirect(url_for("view_assignments", error=f"Could not remove assignment: {str(e)}"))


# ---------------- TEACHER ASSIGNED SUBJECTS (ISOLATED) ----------------
@app.route("/teacher_subjects")
@app.route("/teacher_subjects/<teacher_id>")
@role_required("teacher", "admin")
def teacher_subjects(teacher_id=None):
    user_role = session.get("role")
    user_email = session.get("email")

    conn = get_db_connection()
    cursor = conn.cursor()

    # If teacher role, strictly enforce viewing ONLY their own assigned subjects
    if user_role == "teacher":
        cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (user_email,))
        logged_in_teacher = cursor.fetchone()
        if not logged_in_teacher:
            conn.close()
            return redirect(url_for("teacher"))

        actual_teacher_id = logged_in_teacher["teacher_id"]
        # If teacher attempts to access another teacher's ID in URL, override to own ID
        target_teacher_id = actual_teacher_id
        teacher_name = logged_in_teacher["fullname"]
    else:
        # Admin can view any teacher's subjects
        if not teacher_id:
            conn.close()
            return redirect(url_for("view_assignments"))
        target_teacher_id = teacher_id
        cursor.execute("SELECT fullname FROM teachers WHERE teacher_id = ?", (teacher_id,))
        t = cursor.fetchone()
        teacher_name = t["fullname"] if t else teacher_id

    # JOIN query to retrieve assigned subjects
    cursor.execute("""
        SELECT subjects.subject_code,
               subjects.subject_name,
               subjects.department,
               subjects.semester
        FROM teacher_subjects
        JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
        WHERE teacher_subjects.teacher_id = ?
        ORDER BY subjects.subject_code ASC
    """, (target_teacher_id,))

    subjects = cursor.fetchall()
    conn.close()

    return render_template(
        "teacher_subjects.html",
        subjects=subjects,
        teacher_id=target_teacher_id,
        teacher_name=teacher_name
    )


# ====================================================
# PRACTICAL SESSION MANAGEMENT MODULE (DAY 7)
# ====================================================

# ---------------- START PRACTICAL SESSION ----------------
@app.route("/start_session", methods=["POST"])
@app.route("/start_session/<subject_code>", methods=["POST"])
@role_required("teacher")
def start_session(subject_code=None):
    if not subject_code:
        subject_code = request.form.get("subject_code", "").strip().upper()
    else:
        subject_code = subject_code.strip().upper()

    if not subject_code:
        flash("Please select an assigned subject to start a practical session.", "error")
        return redirect(url_for("teacher"))

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine logged-in teacher identity
    cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        flash("Faculty profile record not found. Please contact administration.", "error")
        return redirect(url_for("teacher"))

    teacher_id = tch["teacher_id"]

    # Verify subject is assigned to this teacher
    cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
    if not cursor.fetchone():
        conn.close()
        flash(f"Unauthorized: Subject '{subject_code}' is not assigned to your faculty profile.", "error")
        return redirect(url_for("teacher"))

    # Rule: Prevent multiple concurrent active sessions for the same teacher
    cursor.execute("""
        SELECT ps.id, ps.subject_id, s.subject_name
        FROM practical_sessions ps
        JOIN subjects s ON ps.subject_id = s.subject_code
        WHERE ps.teacher_id = ? AND ps.status = 'active'
    """, (teacher_id,))
    active = cursor.fetchone()
    if active:
        conn.close()
        flash(f"You already have an active practical session in progress for '{active['subject_name']}' ({active['subject_id']}). Please conclude it before beginning a new session.", "error")
        return redirect(url_for("teacher"))

    # Create new practical session
    session_date = date.today().isoformat()
    start_time = datetime.now().strftime("%I:%M %p")

    try:
        cursor.execute("""
            INSERT INTO practical_sessions (teacher_id, subject_id, session_date, start_time, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (teacher_id, subject_code, session_date, start_time))
        conn.commit()
        conn.close()
        flash(f"Practical session for '{subject_code}' initiated successfully at {start_time}!", "success")
        return redirect(url_for("teacher"))
    except Exception as e:
        conn.close()
        flash(f"Database error while starting practical session: {str(e)}", "error")
        return redirect(url_for("teacher"))


# ---------------- END PRACTICAL SESSION ----------------
@app.route("/end_session/<int:session_id>", methods=["POST"])
@role_required("teacher")
def end_session(session_id):
    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT teacher_id FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        flash("Faculty profile not found.", "error")
        return redirect(url_for("teacher"))

    teacher_id = tch["teacher_id"]

    cursor.execute("""
        SELECT ps.id, ps.teacher_id, ps.subject_id, ps.status, s.subject_name
        FROM practical_sessions ps
        JOIN subjects s ON ps.subject_id = s.subject_code
        WHERE ps.id = ?
    """, (session_id,))
    sess_row = cursor.fetchone()

    if not sess_row:
        conn.close()
        flash("Practical session record not found.", "error")
        return redirect(url_for("teacher"))

    # Security: Ensure teacher can only end their own session
    if sess_row["teacher_id"] != teacher_id:
        conn.close()
        flash("Unauthorized: You cannot conclude a session initiated by another faculty instructor.", "error")
        return redirect(url_for("teacher"))

    if sess_row["status"] == "completed":
        conn.close()
        flash("This practical session has already been completed.", "info")
        return redirect(url_for("teacher"))

    end_time = datetime.now().strftime("%I:%M %p")

    try:
        cursor.execute("""
            UPDATE practical_sessions
            SET end_time = ?, status = 'completed'
            WHERE id = ? AND teacher_id = ?
        """, (end_time, session_id, teacher_id))
        conn.commit()
        conn.close()
        flash(f"Practical session for '{sess_row['subject_name']}' completed and ended successfully at {end_time}!", "success")
        return redirect(url_for("teacher"))
    except Exception as e:
        conn.close()
        flash(f"Error concluding practical session: {str(e)}", "error")
        return redirect(url_for("teacher"))


# ---------------- PRACTICAL SESSIONS HISTORY LOG ----------------
@app.route("/practical_sessions")
@app.route("/session_history")
@role_required("teacher", "admin")
def practical_sessions_history():
    email = session.get("email")
    role = session.get("role")
    conn = get_db_connection()
    cursor = conn.cursor()

    teacher_id = None
    teacher_name = session.get("fullname", "Faculty Member")
    assigned_subjects = []

    if role == "teacher":
        cursor.execute("SELECT teacher_id, fullname, department FROM teachers WHERE email = ?", (email,))
        tch = cursor.fetchone()
        if tch:
            teacher_id = tch["teacher_id"]
            teacher_name = tch["fullname"]

            # Assigned subjects for dropdown
            cursor.execute("""
                SELECT subjects.subject_code, subjects.subject_name
                FROM teacher_subjects
                JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
                WHERE teacher_subjects.teacher_id = ?
                ORDER BY subjects.subject_code ASC
            """, (teacher_id,))
            assigned_subjects = cursor.fetchall()

            # Sessions strictly for this teacher
            cursor.execute("""
                SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.start_time, ps.end_time, ps.status,
                       s.subject_name, s.department, s.semester
                FROM practical_sessions ps
                JOIN subjects s ON ps.subject_id = s.subject_code
                WHERE ps.teacher_id = ?
                ORDER BY ps.id DESC
            """, (teacher_id,))
            sessions_list = cursor.fetchall()
        else:
            sessions_list = []
    else:
        # Admin can view all sessions
        cursor.execute("""
            SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.start_time, ps.end_time, ps.status,
                   s.subject_name, s.department, s.semester, t.fullname as teacher_name
            FROM practical_sessions ps
            JOIN subjects s ON ps.subject_id = s.subject_code
            JOIN teachers t ON ps.teacher_id = t.teacher_id
            ORDER BY ps.id DESC
        """)
        sessions_list = cursor.fetchall()

    conn.close()

    return render_template(
        "practical_sessions.html",
        sessions=sessions_list,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        assigned_subjects=assigned_subjects
    )


# ---------------- PRACTICAL SESSION COCKPIT ----------------
@app.route("/practical_session/<subject_code>")
@role_required("teacher", "admin")
def practical_session(subject_code):
    email = session.get("email")
    role = session.get("role")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT subject_code, subject_name, department, semester
        FROM subjects
        WHERE subject_code = ?
    """, (subject_code,))
    subject = cursor.fetchone()

    if not subject:
        conn.close()
        flash(f"Subject '{subject_code}' not found.", "error")
        return redirect(url_for("teacher"))

    teacher_id = None
    teacher_name = session.get("fullname", "Faculty Member")
    active_session = None

    if role == "teacher":
        cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
        tch = cursor.fetchone()
        if tch:
            teacher_id = tch["teacher_id"]
            teacher_name = tch["fullname"]
            # Security check: verify subject assignment
            cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
            if not cursor.fetchone():
                conn.close()
                flash(f"Unauthorized: You are not assigned to conduct practical sessions for subject '{subject_code}'.", "error")
                return redirect(url_for("teacher"))

            # Check if there is an active session for this subject
            cursor.execute("""
                SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.start_time, ps.end_time, ps.status,
                       s.subject_name, s.department, s.semester, t.fullname as teacher_name
                FROM practical_sessions ps
                JOIN subjects s ON ps.subject_id = s.subject_code
                JOIN teachers t ON ps.teacher_id = t.teacher_id
                WHERE ps.teacher_id = ? AND ps.subject_id = ? AND ps.status = 'active'
                ORDER BY ps.id DESC LIMIT 1
            """, (teacher_id, subject_code))
            active_session = cursor.fetchone()

    conn.close()

    return render_template(
        "practical_session.html",
        subject=subject,
        subject_name=subject["subject_name"],
        subject_code=subject["subject_code"],
        active_session=active_session,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        today=date.today().isoformat()
    )


# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)