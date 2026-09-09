from datetime import date
from functools import wraps
from flask import Flask, render_template, request, redirect, session, url_for, flash
import sqlite3
import qrcode
import json
from werkzeug.security import generate_password_hash, check_password_hash

from database import init_db, get_db_connection
from generate_qr import generate_student_qr

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
    conn.close()

    return render_template(
        "student.html",
        student=student_data,
        fullname=session.get("fullname", "Student")
    )


# ---------------- TEACHER DASHBOARD (ROLE PROTECTED) ----------------
@app.route("/teacher")
@role_required("teacher")
def teacher():
    return render_template(
        "teacher.html",
        fullname=session.get("fullname", "Faculty Member")
    )


# ---------------- ADMIN DASHBOARD (ROLE PROTECTED) ----------------
@app.route("/admin")
@role_required("admin")
def admin():
    return render_template(
        "admin.html",
        fullname=session.get("fullname", "Administrator")
    )


# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET", "POST"])
@role_required("admin", "teacher")
def add_student():
    if request.method == "POST":
        usn = request.form["usn"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        department = request.form["department"]
        semester = request.form["semester"]
        section = request.form["section"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO students
                (usn, fullname, email, department, semester, section)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usn, fullname, email, department, semester, section))
            conn.commit()

            qr_path = generate_student_qr(usn, fullname, department, semester)
            cursor.execute("""
                UPDATE students
                SET qr_path = ?
                WHERE usn = ?
            """, (qr_path, usn))
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Student already exists!"

        conn.close()
        return redirect(url_for("view_students"))

    return render_template("add_student.html")


# ---------------- VIEW STUDENTS ----------------
@app.route("/view_students")
@role_required("admin", "teacher")
def view_students():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT usn, fullname, email, department, semester, section
    FROM students
    """)
    students = cursor.fetchall()
    conn.close()

    return render_template("view_students.html", students=students)


# ---------------- ADD SUBJECT ----------------
@app.route("/add_subject", methods=["GET", "POST"])
@role_required("admin", "teacher")
def add_subject():
    if request.method == "POST":
        subject_code = request.form["subject_code"]
        subject_name = request.form["subject_name"]
        department = request.form["department"]
        semester = request.form["semester"]
        teacher_id = request.form.get("teacher_id", "").strip()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO subjects
            (subject_code, subject_name, department, semester)
            VALUES (?, ?, ?, ?)
            """, (subject_code, subject_name, department, semester))
            conn.commit()

            if teacher_id:
                cursor.execute("""
                INSERT INTO teacher_subjects (teacher_id, subject_id)
                VALUES (?, ?)
                """, (teacher_id, subject_code))
                conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Subject already exists!"

        conn.close()
        return redirect(url_for("admin"))

    return render_template("add_subject.html")


# ---------------- ADD TEACHER ----------------
@app.route("/add_teacher", methods=["GET", "POST"])
@role_required("admin")
def add_teacher():
    if request.method == "POST":
        teacher_id = request.form["teacher_id"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        department = request.form["department"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
            INSERT INTO teachers
            (teacher_id, fullname, email, department)
            VALUES (?, ?, ?, ?)
            """, (teacher_id, fullname, email, department))
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            return "Teacher already exists!"

        conn.close()
        return redirect(url_for("view_teachers"))

    return render_template("add_teacher.html")


# ---------------- VIEW TEACHERS ----------------
@app.route("/view_teachers")
@role_required("admin", "teacher")
def view_teachers():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT teacher_id, fullname, email, department
    FROM teachers
    """)
    teachers = cursor.fetchall()
    conn.close()

    return render_template("view_teachers.html", teachers=teachers)


# ---------------- ASSIGN SUBJECT ----------------
@app.route("/assign_subject", methods=["GET", "POST"])
@role_required("admin", "teacher")
def assign_subject():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == "POST":
        teacher_id = request.form["teacher_id"]
        subject_code = request.form["subject_code"]

        cursor.execute("""
        INSERT INTO teacher_subjects
        (teacher_id, subject_id)
        VALUES (?, ?)
        """, (teacher_id, subject_code))
        conn.commit()
        conn.close()

        return redirect(url_for("view_teachers"))

    # Load teachers
    cursor.execute("SELECT teacher_id, fullname FROM teachers")
    teachers = cursor.fetchall()

    # Load subjects
    cursor.execute("SELECT subject_code, subject_name FROM subjects")
    subjects = cursor.fetchall()
    conn.close()

    return render_template(
        "assign_subject.html",
        teachers=teachers,
        subjects=subjects
    )


# ---------------- TEACHER SUBJECTS ----------------
@app.route("/teacher_subjects/<teacher_id>")
@role_required("teacher", "admin")
def teacher_subjects(teacher_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subjects.subject_code,
           subjects.subject_name
    FROM teacher_subjects
    JOIN subjects
    ON teacher_subjects.subject_id = subjects.subject_code
    WHERE teacher_subjects.teacher_id = ?
    """, (teacher_id,))

    subjects = cursor.fetchall()
    conn.close()

    return render_template(
        "teacher_subjects.html",
        subjects=subjects
    )


# ---------------- PRACTICAL SESSION ----------------
@app.route("/practical_session/<subject_code>")
@role_required("teacher", "admin")
def practical_session(subject_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subject_name
    FROM subjects
    WHERE subject_code = ?
    """, (subject_code,))

    subject = cursor.fetchone()
    conn.close()

    if not subject:
        return "Subject not found", 404

    return render_template(
        "practical_session.html",
        subject_name=subject["subject_name"],
        today=date.today()
    )


# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)