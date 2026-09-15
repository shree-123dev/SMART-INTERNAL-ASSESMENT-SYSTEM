import os
import sqlite3
import qrcode
import json
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import init_db, get_db_connection
from generate_qr import generate_student_qr, ensure_student_qr
from ppt_importer import parse_pptx_ia_marks

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

    experiment_evaluations = []
    ia_scores = []

    # Automatically ensure QR code exists for this student & fetch live marks
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

        # Live fetch practical experiment evaluations & marks recorded by teachers (Day 8)
        cursor.execute("""
            SELECT em.experiment_no, em.experiment_name, em.practical_marks, em.assignment_marks,
                   em.max_practical_marks, em.max_assignment_marks, em.recorded_date,
                   s.subject_name, s.subject_code, t.fullname as teacher_name
            FROM experiment_marks em
            JOIN subjects s ON em.subject_id = s.subject_code
            JOIN teachers t ON em.teacher_id = t.teacher_id
            WHERE em.student_id = ?
            ORDER BY em.id DESC
        """, (usn,))
        experiment_evaluations = cursor.fetchall()

        # Live fetch continuous internal assessment (IA) marks for all courses in student's department/semester (Day 9)
        cursor.execute("""
            SELECT s.subject_code, s.subject_name,
                   im.ia1, im.ia2, im.max_ia1, im.max_ia2
            FROM subjects s
            LEFT JOIN internal_marks im ON s.subject_code = im.subject_id AND im.student_id = ?
            WHERE s.department = ? AND s.semester = ?
            ORDER BY s.subject_code ASC
        """, (usn, student_data["department"], student_data["semester"]))
        raw_ia_records = cursor.fetchall()

        for r in raw_ia_records:
            sub_code = r["subject_code"]
            ia1_val = r["ia1"]
            ia2_val = r["ia2"]

            # Calculate IA Average (/20)
            valid_ias = [float(x) for x in [ia1_val, ia2_val] if x is not None and str(x) != ""]
            ia_avg = round(sum(valid_ias) / len(valid_ias), 2) if valid_ias else None

            # Fetch Practical and Assignment averages from experiment_marks (Day 8)
            cursor.execute("""
                SELECT AVG(practical_marks) as avg_p, AVG(assignment_marks) as avg_a
                FROM experiment_marks
                WHERE student_id = ? AND subject_id = ?
            """, (usn, sub_code))
            exp_stats = cursor.fetchone()
            prac_avg = round(exp_stats["avg_p"], 2) if exp_stats and exp_stats["avg_p"] is not None else None
            assign_avg = round(exp_stats["avg_a"], 2) if exp_stats and exp_stats["avg_a"] is not None else None

            # Calculate total continuous evaluation score (/35)
            total_parts = [p for p in [ia_avg, prac_avg, assign_avg] if p is not None]
            total_score = round(sum(total_parts), 2) if total_parts else None

            ia_scores.append({
                "subject_code": sub_code,
                "subject_name": r["subject_name"],
                "ia1": ia1_val,
                "ia2": ia2_val,
                "ia_avg": ia_avg,
                "practical_avg": prac_avg,
                "assignment_avg": assign_avg,
                "total_score": total_score
            })

    conn.close()

    return render_template(
        "student.html",
        student=student_data,
        evaluations=experiment_evaluations,
        ia_scores=ia_scores,
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

        # Query currently active session for this teacher (Day 7/8)
        cursor.execute("""
            SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.start_time, ps.end_time, ps.status,
                   ps.experiment_no, ps.experiment_name,
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
# PRACTICAL SESSION MANAGEMENT MODULE (DAY 7 & DAY 8)
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

    experiment_no = request.form.get("experiment_no", "").strip() or "Experiment 1"
    experiment_name = request.form.get("experiment_name", "").strip() or "Practical Lab Evaluation"

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

    # Create new practical session with experiment details (Day 8)
    session_date = date.today().isoformat()
    start_time = datetime.now().strftime("%I:%M %p")

    try:
        cursor.execute("""
            INSERT INTO practical_sessions (teacher_id, subject_id, session_date, start_time, status, experiment_no, experiment_name)
            VALUES (?, ?, ?, ?, 'active', ?, ?)
        """, (teacher_id, subject_code, session_date, start_time, experiment_no, experiment_name))
        conn.commit()
        conn.close()
        flash(f"Practical session for '{subject_code}' ({experiment_no}) initiated successfully at {start_time}!", "success")
        return redirect(url_for("practical_session", subject_code=subject_code))
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
                       ps.experiment_no, ps.experiment_name,
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
                   ps.experiment_no, ps.experiment_name,
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
    evaluated_students = []

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
                       ps.experiment_no, ps.experiment_name,
                       s.subject_name, s.department, s.semester, t.fullname as teacher_name
                FROM practical_sessions ps
                JOIN subjects s ON ps.subject_id = s.subject_code
                JOIN teachers t ON ps.teacher_id = t.teacher_id
                WHERE ps.teacher_id = ? AND ps.subject_id = ? AND ps.status = 'active'
                ORDER BY ps.id DESC LIMIT 1
            """, (teacher_id, subject_code))
            active_session = cursor.fetchone()

            if active_session:
                cursor.execute("""
                    SELECT em.student_id as usn, st.fullname, st.department, st.semester, st.section,
                           em.practical_marks, em.assignment_marks, em.max_practical_marks, em.max_assignment_marks
                    FROM experiment_marks em
                    JOIN students st ON em.student_id = st.usn
                    WHERE em.session_id = ?
                    ORDER BY em.id DESC
                """, (active_session["id"],))
                evaluated_students = cursor.fetchall()

    conn.close()

    return render_template(
        "practical_session.html",
        subject=subject,
        subject_name=subject["subject_name"],
        subject_code=subject["subject_code"],
        active_session=active_session,
        evaluated_students=evaluated_students,
        teacher_id=teacher_id,
        teacher_name=teacher_name,
        today=date.today().isoformat()
    )


# ---------------- SCAN STUDENT QR CODE (DAY 8) ----------------
@app.route("/scan_student_qr", methods=["POST"])
@role_required("teacher")
def scan_student_qr():
    """Identifies student from scanned USN QR, verifies active session ownership,
    automatically marks attendance, and returns student info with any existing marks."""
    data = request.get_json(silent=True) or request.form
    session_id = data.get("session_id")
    usn = data.get("usn", "").strip().upper()

    if not session_id or not usn:
        return jsonify({"success": False, "error": "Missing session ID or student USN."}), 400

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Identify logged-in teacher
    cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        return jsonify({"success": False, "error": "Faculty record not found."}), 403

    teacher_id = tch["teacher_id"]

    # Retrieve and verify active session ownership
    cursor.execute("""
        SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.status,
               ps.experiment_no, ps.experiment_name, s.subject_name
        FROM practical_sessions ps
        JOIN subjects s ON ps.subject_id = s.subject_code
        WHERE ps.id = ?
    """, (session_id,))
    sess = cursor.fetchone()

    if not sess:
        conn.close()
        return jsonify({"success": False, "error": "Practical session not found."}), 404

    if sess["teacher_id"] != teacher_id:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized: This session belongs to another faculty instructor."}), 403

    if sess["status"] != "active":
        conn.close()
        return jsonify({"success": False, "error": "This practical session is not active (status: completed)."}), 400

    # Identify student by USN
    cursor.execute("""
        SELECT usn, fullname, email, department, semester, section
        FROM students
        WHERE usn = ?
    """, (usn,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return jsonify({"success": False, "error": f"Unknown student USN: '{usn}'. Student record not found in system."}), 404

    # Automatic Attendance Marking
    # Check if attendance already marked for this session
    cursor.execute("""
        SELECT id FROM attendance
        WHERE student_id = ? AND session_id = ?
    """, (usn, session_id))
    att_session = cursor.fetchone()

    attendance_message = "Attendance marked: PRESENT ✓"

    if att_session:
        attendance_message = "Attendance already marked."
    else:
        # Also check date-based duplicate fallback
        cursor.execute("""
            SELECT id FROM attendance
            WHERE student_id = ? AND subject_id = ? AND attendance_date = ? AND teacher_id = ?
        """, (usn, sess["subject_id"], sess["session_date"], teacher_id))
        att_fallback = cursor.fetchone()
        if att_fallback:
            attendance_message = "Attendance already marked."
            cursor.execute("UPDATE attendance SET session_id = ? WHERE id = ?", (session_id, att_fallback["id"]))
            conn.commit()
        else:
            try:
                cursor.execute("""
                    INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status, session_id)
                    VALUES (?, ?, ?, ?, 'Present', ?)
                """, (usn, sess["subject_id"], teacher_id, sess["session_date"], session_id))
                conn.commit()
                attendance_message = "Attendance marked: PRESENT ✓"
            except Exception as e:
                pass

    # Check for existing experiment marks for this student and session
    cursor.execute("""
        SELECT practical_marks, assignment_marks
        FROM experiment_marks
        WHERE session_id = ? AND student_id = ?
    """, (session_id, usn))
    existing_marks = cursor.fetchone()

    p_marks = existing_marks["practical_marks"] if existing_marks else 0
    a_marks = existing_marks["assignment_marks"] if existing_marks else 0

    conn.close()

    return jsonify({
        "success": True,
        "student": {
            "usn": student["usn"],
            "fullname": student["fullname"],
            "department": student["department"],
            "semester": student["semester"],
            "section": student["section"]
        },
        "session": {
            "id": sess["id"],
            "subject_id": sess["subject_id"],
            "subject_name": sess["subject_name"],
            "experiment_no": sess["experiment_no"] or "Experiment",
            "experiment_name": sess["experiment_name"] or "Practical Lab Session",
            "session_date": sess["session_date"]
        },
        "attendance_status": "Present",
        "attendance_message": attendance_message,
        "practical_marks": p_marks,
        "assignment_marks": a_marks
    })


# ---------------- SAVE SESSION PRACTICAL & ASSIGNMENT MARKS (DAY 8) ----------------
@app.route("/save_session_marks", methods=["POST"])
@role_required("teacher")
def save_session_marks():
    """Saves practical and assignment marks for a student in an active practical session.
    Validates mark limits (0-10 for practical, 0-5 for assignment) and records linked data."""
    data = request.get_json(silent=True) or request.form
    session_id = data.get("session_id")
    student_id = data.get("student_id", "").strip().upper()
    practical_marks_raw = data.get("practical_marks")
    assignment_marks_raw = data.get("assignment_marks")

    if not session_id or not student_id:
        return jsonify({"success": False, "error": "Missing session ID or student identifier."}), 400

    # Validate numeric marks
    try:
        practical_marks = float(practical_marks_raw)
        assignment_marks = float(assignment_marks_raw)
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid marks entered. Marks must be valid numeric values."}), 400

    # Range validations
    if practical_marks < 0 or practical_marks > 10:
        return jsonify({"success": False, "error": "Practical experiment marks must be between 0 and 10."}), 400

    if assignment_marks < 0 or assignment_marks > 5:
        return jsonify({"success": False, "error": "Assignment marks must be between 0 and 5."}), 400

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Identify teacher
    cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        return jsonify({"success": False, "error": "Faculty profile record not found."}), 403

    teacher_id = tch["teacher_id"]

    # Validate active session ownership
    cursor.execute("""
        SELECT ps.id, ps.teacher_id, ps.subject_id, ps.session_date, ps.status,
               ps.experiment_no, ps.experiment_name
        FROM practical_sessions ps
        WHERE ps.id = ?
    """, (session_id,))
    sess = cursor.fetchone()

    if not sess:
        conn.close()
        return jsonify({"success": False, "error": "Practical session not found."}), 404

    if sess["teacher_id"] != teacher_id:
        conn.close()
        return jsonify({"success": False, "error": "Unauthorized: You cannot modify evaluations for another instructor's session."}), 403

    if sess["status"] != "active":
        conn.close()
        return jsonify({"success": False, "error": "Cannot save marks: This practical session is already completed."}), 400

    # Validate student
    cursor.execute("SELECT usn, fullname FROM students WHERE usn = ?", (student_id,))
    student = cursor.fetchone()
    if not student:
        conn.close()
        return jsonify({"success": False, "error": f"Student '{student_id}' not found in system."}), 404

    # Ensure attendance is marked Present
    cursor.execute("""
        SELECT id FROM attendance
        WHERE student_id = ? AND session_id = ?
    """, (student_id, session_id))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status, session_id)
            VALUES (?, ?, ?, ?, 'Present', ?)
        """, (student_id, sess["subject_id"], teacher_id, sess["session_date"], session_id))

    # Upsert into experiment_marks
    cursor.execute("""
        SELECT id FROM experiment_marks
        WHERE session_id = ? AND student_id = ?
    """, (session_id, student_id))
    existing_em = cursor.fetchone()

    today_str = date.today().isoformat()

    try:
        if existing_em:
            cursor.execute("""
                UPDATE experiment_marks
                SET practical_marks = ?, assignment_marks = ?, recorded_date = ?
                WHERE id = ?
            """, (practical_marks, assignment_marks, today_str, existing_em["id"]))
        else:
            cursor.execute("""
                INSERT INTO experiment_marks (
                    session_id, student_id, subject_id, teacher_id,
                    experiment_no, experiment_name,
                    practical_marks, assignment_marks,
                    max_practical_marks, max_assignment_marks,
                    recorded_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 10, 5, ?)
            """, (
                session_id, student_id, sess["subject_id"], teacher_id,
                sess["experiment_no"], sess["experiment_name"],
                practical_marks, assignment_marks,
                today_str
            ))
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "message": "Attendance and marks saved successfully.",
            "usn": student["usn"],
            "student_name": student["fullname"],
            "practical_marks": practical_marks,
            "assignment_marks": assignment_marks
        })
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "error": f"Database error while saving marks: {str(e)}"}), 500


# ====================================================
# INTERNAL ASSESSMENT (IA) MARKS & PPT IMPORT MODULE (DAY 9)
# ====================================================

# ---------------- TEACHER IA HUB GATEWAY ----------------
@app.route("/ia_marks")
@app.route("/teacher/ia_marks")
@role_required("teacher")
def teacher_ia_hub():
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
        SELECT subjects.subject_code
        FROM teacher_subjects
        JOIN subjects ON teacher_subjects.subject_id = subjects.subject_code
        WHERE teacher_subjects.teacher_id = ?
        ORDER BY subjects.subject_code ASC
        LIMIT 1
    """, (teacher_id,))
    first_sub = cursor.fetchone()
    conn.close()

    if first_sub:
        return redirect(url_for("ia_marks_subject", subject_code=first_sub["subject_code"]))
    else:
        flash("No courses are currently assigned to your faculty profile. Please contact the administrator.", "info")
        return redirect(url_for("teacher"))


# ---------------- SUBJECT IA GRADEBOOK COCKPIT ----------------
@app.route("/ia_marks/<subject_code>")
@role_required("teacher", "admin")
def ia_marks_subject(subject_code):
    subject_code = subject_code.strip().upper()
    role = session.get("role")
    email = session.get("email")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify subject exists
    cursor.execute("""
        SELECT subject_code, subject_name, department, semester
        FROM subjects
        WHERE subject_code = ?
    """, (subject_code,))
    subject = cursor.fetchone()

    if not subject:
        conn.close()
        flash(f"Subject course '{subject_code}' not found.", "error")
        return redirect(url_for("teacher"))

    teacher_name = session.get("fullname", "Faculty Member")

    # Security check: if teacher role, strictly verify assignment
    if role == "teacher":
        cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
        tch = cursor.fetchone()
        if not tch:
            conn.close()
            flash("Faculty record not found.", "error")
            return redirect(url_for("teacher"))

        teacher_id = tch["teacher_id"]
        teacher_name = tch["fullname"]

        cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
        if not cursor.fetchone():
            conn.close()
            flash(f"Unauthorized: You are not assigned to manage Internal Assessment marks for course '{subject_code}'.", "error")
            return redirect(url_for("teacher"))

    # Query all students enrolled in this course (matching department & semester)
    cursor.execute("""
        SELECT usn, fullname, department, semester, section
        FROM students
        WHERE department = ? AND semester = ?
        ORDER BY usn ASC
    """, (subject["department"], subject["semester"]))
    students_in_cohort = cursor.fetchall()

    # Fallback: if no cohort matches strictly, get all students who have marks or attendance
    if not students_in_cohort:
        cursor.execute("SELECT usn, fullname, department, semester, section FROM students ORDER BY usn ASC")
        students_in_cohort = cursor.fetchall()

    students_marks = []
    ia1_count = 0
    ia2_count = 0
    total_scores_list = []

    for st in students_in_cohort:
        usn = st["usn"]

        # Fetch IA marks
        cursor.execute("""
            SELECT ia1, ia2, max_ia1, max_ia2
            FROM internal_marks
            WHERE student_id = ? AND subject_id = ?
        """, (usn, subject_code))
        im = cursor.fetchone()

        ia1 = im["ia1"] if im and im["ia1"] is not None else None
        ia2 = im["ia2"] if im and im["ia2"] is not None else None

        if ia1 is not None:
            ia1_count += 1
        if ia2 is not None:
            ia2_count += 1

        # Calculate IA Average (/20)
        valid_ias = [float(x) for x in [ia1, ia2] if x is not None and str(x) != ""]
        ia_avg = round(sum(valid_ias) / len(valid_ias), 2) if valid_ias else None

        # Fetch Practical & Assignment Averages from experiment_marks (Day 8)
        cursor.execute("""
            SELECT AVG(practical_marks) as avg_p, AVG(assignment_marks) as avg_a
            FROM experiment_marks
            WHERE student_id = ? AND subject_id = ?
        """, (usn, subject_code))
        exp_stats = cursor.fetchone()
        prac_avg = round(exp_stats["avg_p"], 2) if exp_stats and exp_stats["avg_p"] is not None else None
        assign_avg = round(exp_stats["avg_a"], 2) if exp_stats and exp_stats["avg_a"] is not None else None

        # Calculate Total Score (/35)
        components = [c for c in [ia_avg, prac_avg, assign_avg] if c is not None]
        total_score = round(sum(components), 2) if components else None

        if total_score is not None:
            total_scores_list.append(total_score)

        students_marks.append({
            "usn": usn,
            "fullname": st["fullname"],
            "section": st["section"],
            "ia1": ia1,
            "ia2": ia2,
            "ia_avg": ia_avg,
            "practical_avg": prac_avg,
            "assignment_avg": assign_avg,
            "total_score": total_score
        })

    avg_class_total = round(sum(total_scores_list) / len(total_scores_list), 1) if total_scores_list else 0

    stats = {
        "ia1_count": ia1_count,
        "ia2_count": ia2_count,
        "avg_total": avg_class_total
    }

    conn.close()

    return render_template(
        "ia_marks_subject.html",
        subject=subject,
        students_marks=students_marks,
        stats=stats,
        teacher_name=teacher_name
    )


# ---------------- MANUAL IA MARKS ENTRY ----------------
@app.route("/ia_marks/manual/<subject_code>", methods=["GET"])
@role_required("teacher")
def ia_marks_manual(subject_code):
    subject_code = subject_code.strip().upper()
    ia_type = request.args.get("ia_type", "IA1").strip().upper()
    if ia_type not in ["IA1", "IA2"]:
        ia_type = "IA1"

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Identify teacher & verify assignment
    cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        flash("Faculty profile record not found.", "error")
        return redirect(url_for("teacher"))

    teacher_id = tch["teacher_id"]

    cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
    if not cursor.fetchone():
        conn.close()
        flash(f"Unauthorized: Course '{subject_code}' is not assigned to you.", "error")
        return redirect(url_for("teacher"))

    cursor.execute("SELECT subject_code, subject_name, department, semester FROM subjects WHERE subject_code = ?", (subject_code,))
    subject = cursor.fetchone()

    # Query students in cohort
    cursor.execute("""
        SELECT usn, fullname, department, semester, section
        FROM students
        WHERE department = ? AND semester = ?
        ORDER BY usn ASC
    """, (subject["department"], subject["semester"]))
    students_list = cursor.fetchall()

    if not students_list:
        cursor.execute("SELECT usn, fullname, department, semester, section FROM students ORDER BY usn ASC")
        students_list = cursor.fetchall()

    students_with_marks = []
    for st in students_list:
        cursor.execute("SELECT ia1, ia2 FROM internal_marks WHERE student_id = ? AND subject_id = ?", (st["usn"], subject_code))
        im = cursor.fetchone()
        students_with_marks.append({
            "usn": st["usn"],
            "fullname": st["fullname"],
            "section": st["section"],
            "ia1": im["ia1"] if im else None,
            "ia2": im["ia2"] if im else None
        })

    conn.close()

    return render_template(
        "ia_marks_manual.html",
        subject=subject,
        students=students_with_marks,
        ia_type=ia_type
    )


# ---------------- SAVE MANUAL IA MARKS ----------------
@app.route("/ia_marks/save_manual/<subject_code>", methods=["POST"])
@role_required("teacher")
def save_manual_ia_marks(subject_code):
    subject_code = subject_code.strip().upper()
    ia_type = request.form.get("ia_type", "IA1").strip().upper()
    if ia_type not in ["IA1", "IA2"]:
        ia_type = "IA1"

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT teacher_id, fullname FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        flash("Faculty profile not found.", "error")
        return redirect(url_for("teacher"))

    teacher_id = tch["teacher_id"]

    cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
    if not cursor.fetchone():
        conn.close()
        flash(f"Unauthorized: You cannot modify marks for '{subject_code}'.", "error")
        return redirect(url_for("teacher"))

    # Iterate over form entries: key format "mark_<usn>"
    today_str = date.today().isoformat()
    saved_count = 0
    errors = []

    for key, val in request.form.items():
        if key.startswith("mark_"):
            usn = key.replace("mark_", "").strip().upper()
            val_str = val.strip()
            if not val_str:
                continue

            try:
                numeric_val = float(val_str)
            except (ValueError, TypeError):
                errors.append(f"Invalid non-numeric mark '{val_str}' for student {usn}.")
                continue

            if numeric_val < 0 or numeric_val > 20:
                errors.append(f"Marks ({numeric_val}) for student {usn} must be between 0 and 20.")
                continue

            # Upsert into internal_marks
            cursor.execute("SELECT id, ia1, ia2 FROM internal_marks WHERE student_id = ? AND subject_id = ?", (usn, subject_code))
            existing = cursor.fetchone()

            if existing:
                if ia_type == "IA1":
                    cursor.execute("""
                        UPDATE internal_marks
                        SET ia1 = ?, teacher_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (numeric_val, teacher_id, today_str, existing["id"]))
                else:
                    cursor.execute("""
                        UPDATE internal_marks
                        SET ia2 = ?, teacher_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (numeric_val, teacher_id, today_str, existing["id"]))
            else:
                if ia_type == "IA1":
                    cursor.execute("""
                        INSERT INTO internal_marks (student_id, subject_id, ia1, ia2, max_ia1, max_ia2, teacher_id, updated_at)
                        VALUES (?, ?, ?, NULL, 20, 20, ?, ?)
                    """, (usn, subject_code, numeric_val, teacher_id, today_str))
                else:
                    cursor.execute("""
                        INSERT INTO internal_marks (student_id, subject_id, ia1, ia2, max_ia1, max_ia2, teacher_id, updated_at)
                        VALUES (?, ?, NULL, ?, 20, 20, ?, ?)
                    """, (usn, subject_code, numeric_val, teacher_id, today_str))

            saved_count += 1

    conn.commit()
    conn.close()

    if errors:
        for err in errors[:3]:
            flash(err, "error")

    flash(f"Successfully saved {ia_type} marks for {saved_count} students.", "success")
    return redirect(url_for("ia_marks_subject", subject_code=subject_code))


# ---------------- UPLOAD PPT/PPTX & STAGING PREVIEW (DAY 9) ----------------
@app.route("/ia_marks/upload_ppt/<subject_code>", methods=["POST"])
@role_required("teacher")
def upload_ppt_marks(subject_code):
    subject_code = subject_code.strip().upper()
    ia_type = request.form.get("ia_type", "IA1").strip().upper()
    if ia_type not in ["IA1", "IA2"]:
        ia_type = "IA1"

    email = session.get("email")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Verify teacher assignment
    cursor.execute("SELECT teacher_id FROM teachers WHERE email = ?", (email,))
    tch = cursor.fetchone()
    if not tch:
        conn.close()
        flash("Faculty profile not found.", "error")
        return redirect(url_for("teacher"))

    teacher_id = tch["teacher_id"]

    cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
    if not cursor.fetchone():
        conn.close()
        flash(f"Unauthorized: Course '{subject_code}' is not assigned to you.", "error")
        return redirect(url_for("teacher"))

    cursor.execute("SELECT subject_name FROM subjects WHERE subject_code = ?", (subject_code,))
    sub_row = cursor.fetchone()
    subject_name = sub_row["subject_name"] if sub_row else subject_code
    conn.close()

    # Validate file
    if "ppt_file" not in request.files:
        flash("No presentation file selected for upload.", "error")
        return redirect(url_for("ia_marks_subject", subject_code=subject_code))

    file = request.files["ppt_file"]
    if not file or not file.filename:
        flash("No file was chosen. Please select a valid .pptx PowerPoint file.", "error")
        return redirect(url_for("ia_marks_subject", subject_code=subject_code))

    orig_name = secure_filename(file.filename)
    if not orig_name.lower().endswith(".pptx"):
        flash("Invalid file format! Please upload a valid PowerPoint presentation (.pptx) file.", "error")
        return redirect(url_for("ia_marks_subject", subject_code=subject_code))

    # Save to staging upload directory
    upload_dir = os.path.join(app.root_path, "static", "uploads", "ppt")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved_filename = f"{subject_code}_{ia_type}_{timestamp}_{orig_name}"
    saved_path = os.path.join(upload_dir, saved_filename)
    file.save(saved_path)

    # Parse presentation
    parsed_result = parse_pptx_ia_marks(saved_path, subject_code, ia_type=ia_type, max_marks=20.0)

    if not parsed_result["success"]:
        # Clean up failed upload file
        if os.path.exists(saved_path):
            os.remove(saved_path)
        flash(parsed_result.get("error", "Failed to parse presentation file."), "error")
        return redirect(url_for("ia_marks_subject", subject_code=subject_code))

    # Save parsed data into staging session
    session["staged_ppt_import"] = {
        "saved_path": saved_path,
        "subject_code": subject_code,
        "subject_name": subject_name,
        "ia_type": ia_type,
        "filename": orig_name,
        "max_marks": 20.0,
        "summary": parsed_result["summary"],
        "rows": parsed_result["rows"]
    }

    return render_template(
        "ia_marks_import_preview.html",
        subject_code=subject_code,
        subject_name=subject_name,
        ia_type=ia_type,
        filename=orig_name,
        max_marks=20.0,
        summary=parsed_result["summary"],
        rows=parsed_result["rows"]
    )


# ---------------- CONFIRM & APPLY BULK PPT IMPORT ----------------
@app.route("/ia_marks/confirm_import", methods=["POST"])
@role_required("teacher")
def confirm_ppt_import():
    staged = session.get("staged_ppt_import")
    if not staged:
        flash("No active staging import found or session expired. Please upload the PPTX file again.", "error")
        return redirect(url_for("teacher"))

    subject_code = staged["subject_code"]
    ia_type = staged["ia_type"]
    rows = staged["rows"]
    saved_path = staged.get("saved_path")

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

    cursor.execute("SELECT id FROM teacher_subjects WHERE teacher_id = ? AND subject_id = ?", (teacher_id, subject_code))
    if not cursor.fetchone():
        conn.close()
        flash(f"Unauthorized: You cannot import marks for course '{subject_code}'.", "error")
        return redirect(url_for("teacher"))

    today_str = date.today().isoformat()
    imported_count = 0
    updated_count = 0
    skipped_count = 0

    for r in rows:
        if r.get("is_valid") and r.get("marks") is not None:
            usn = r["usn"]
            mark_val = float(r["marks"])

            cursor.execute("SELECT id, ia1, ia2 FROM internal_marks WHERE student_id = ? AND subject_id = ?", (usn, subject_code))
            existing = cursor.fetchone()

            if existing:
                if ia_type == "IA1":
                    cursor.execute("""
                        UPDATE internal_marks
                        SET ia1 = ?, teacher_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (mark_val, teacher_id, today_str, existing["id"]))
                else:
                    cursor.execute("""
                        UPDATE internal_marks
                        SET ia2 = ?, teacher_id = ?, updated_at = ?
                        WHERE id = ?
                    """, (mark_val, teacher_id, today_str, existing["id"]))
                
                if r["status"] == "valid_update":
                    updated_count += 1
                else:
                    imported_count += 1
            else:
                if ia_type == "IA1":
                    cursor.execute("""
                        INSERT INTO internal_marks (student_id, subject_id, ia1, ia2, max_ia1, max_ia2, teacher_id, updated_at)
                        VALUES (?, ?, ?, NULL, 20, 20, ?, ?)
                    """, (usn, subject_code, mark_val, teacher_id, today_str))
                else:
                    cursor.execute("""
                        INSERT INTO internal_marks (student_id, subject_id, ia1, ia2, max_ia1, max_ia2, teacher_id, updated_at)
                        VALUES (?, ?, NULL, ?, 20, 20, ?, ?)
                    """, (usn, subject_code, mark_val, teacher_id, today_str))
                imported_count += 1
        else:
            skipped_count += 1

    conn.commit()
    conn.close()

    # Clean up uploaded temporary presentation file
    if saved_path and os.path.exists(saved_path):
        try:
            os.remove(saved_path)
        except Exception:
            pass

    session.pop("staged_ppt_import", None)

    flash(f"Bulk Import Complete! Successfully saved {imported_count} new marks, updated {updated_count} marks, and skipped {skipped_count} invalid records.", "success")
    return redirect(url_for("ia_marks_subject", subject_code=subject_code))


# ---------------- CANCEL BULK PPT IMPORT ----------------
@app.route("/ia_marks/cancel_import/<subject_code>")
@role_required("teacher")
def cancel_ppt_import(subject_code):
    staged = session.get("staged_ppt_import")
    if staged and staged.get("saved_path") and os.path.exists(staged["saved_path"]):
        try:
            os.remove(staged["saved_path"])
        except Exception:
            pass

    session.pop("staged_ppt_import", None)
    flash("Bulk presentation import cancelled. No marks were modified.", "info")
    return redirect(url_for("ia_marks_subject", subject_code=subject_code))


# ---------------- ADMIN INSTITUTIONAL MARKS ROSTER ----------------
@app.route("/admin/marks")
@role_required("admin")
def admin_marks():
    selected_subject = request.args.get("subject", "").strip().upper()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all subjects for dropdown filter
    cursor.execute("SELECT subject_code, subject_name, department, semester FROM subjects ORDER BY subject_code ASC")
    all_subjects = cursor.fetchall()

    if selected_subject:
        cursor.execute("""
            SELECT im.student_id, st.fullname, im.subject_id, s.subject_name,
                   im.ia1, im.ia2, im.max_ia1, im.max_ia2
            FROM internal_marks im
            JOIN students st ON im.student_id = st.usn
            JOIN subjects s ON im.subject_id = s.subject_code
            WHERE im.subject_id = ?
            ORDER BY im.student_id ASC
        """, (selected_subject,))
    else:
        cursor.execute("""
            SELECT im.student_id, st.fullname, im.subject_id, s.subject_name,
                   im.ia1, im.ia2, im.max_ia1, im.max_ia2
            FROM internal_marks im
            JOIN students st ON im.student_id = st.usn
            JOIN subjects s ON im.subject_id = s.subject_code
            ORDER BY im.subject_id ASC, im.student_id ASC
        """)
    raw_records = cursor.fetchall()

    marks_records = []
    for r in raw_records:
        usn = r["student_id"]
        sub_code = r["subject_id"]
        ia1_val = r["ia1"]
        ia2_val = r["ia2"]

        valid_ias = [float(x) for x in [ia1_val, ia2_val] if x is not None and str(x) != ""]
        ia_avg = round(sum(valid_ias) / len(valid_ias), 2) if valid_ias else None

        cursor.execute("""
            SELECT AVG(practical_marks) as avg_p, AVG(assignment_marks) as avg_a
            FROM experiment_marks
            WHERE student_id = ? AND subject_id = ?
        """, (usn, sub_code))
        exp_stats = cursor.fetchone()
        prac_avg = round(exp_stats["avg_p"], 2) if exp_stats and exp_stats["avg_p"] is not None else None
        assign_avg = round(exp_stats["avg_a"], 2) if exp_stats and exp_stats["avg_a"] is not None else None

        components = [c for c in [ia_avg, prac_avg, assign_avg] if c is not None]
        total_score = round(sum(components), 2) if components else None

        marks_records.append({
            "student_id": usn,
            "fullname": r["fullname"],
            "subject_id": sub_code,
            "subject_name": r["subject_name"],
            "ia1": ia1_val,
            "ia2": ia2_val,
            "ia_avg": ia_avg,
            "practical_avg": prac_avg,
            "assignment_avg": assign_avg,
            "total_score": total_score
        })

    conn.close()

    return render_template(
        "admin_marks.html",
        all_subjects=all_subjects,
        selected_subject=selected_subject,
        marks_records=marks_records
    )


# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)