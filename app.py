from datetime import date
from flask import Flask, render_template, request, redirect, session
import sqlite3
import qrcode
import json

from database import init_db
from generate_qr import generate_student_qr

app = Flask(__name__)
app.secret_key = "siams_secret_key_2026"

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN PAGE ----------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT fullname, email, role FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:

            role = user[2]
            session["fullname"] = user[0]
            session["email"] = user[1]
            session["role"] = user[2]

            if role == "student":
                return redirect("/student")

            elif role == "teacher":
                return redirect("/teacher")

            elif role == "admin":
                return redirect("/admin")

        return "Invalid Email or Password"

    return render_template("login.html")


# ---------------- SIGNUP PAGE ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        fullname = request.form["fullname"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users(fullname,email,password,role) VALUES(?,?,?,?)",
                (fullname, email, password, role)
            )

            conn.commit()

        except sqlite3.IntegrityError:
            return "Email already registered!"

        finally:
            conn.close()

        return redirect("/login")

    return render_template("signup.html")


# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ---------------- STUDENT ----------------
@app.route("/student")
def student():

    if "email" not in session:
        return redirect("/login")

    email = session["email"]

    conn = sqlite3.connect("database.db")
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

    student = cursor.fetchone()

    conn.close()

    return render_template(
        "student.html",
        student=student
    )

# ---------------- TEACHER ----------------
@app.route("/teacher")
def teacher():
    return render_template("teacher.html")


# ---------------- ADD STUDENT ----------------
@app.route("/add_student", methods=["GET", "POST"])
def add_student():

    if request.method == "POST":

        usn = request.form["usn"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        department = request.form["department"]
        semester = request.form["semester"]
        section = request.form["section"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
                INSERT INTO students
                (usn, fullname, email, department, semester, section)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usn, fullname, email, department, semester, section))

            conn.commit()
            qr_path=generate_student_qr(
                usn,
                fullname,
                department,
                semester
            )
            cursor.execute("""
            UPDATE students
            SET qr_path = ?
            WHERE usn = ?
            """, (qr_path, usn))

            conn.commit()

        except sqlite3.IntegrityError:
            return "Student already exists!"

        finally:
            conn.close()

        return "Student Added Successfully!"

    return render_template("add_student.html")
# ---------------- VIEW STUDENTS ----------------
@app.route("/view_students")
def view_students():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT usn, fullname, email, department, semester, section
    FROM students
    """)

    students = cursor.fetchall()

    conn.close()

    return render_template(
        "view_students.html",
        students=students
    )
# ---------------- ADD SUBJECT ----------------
@app.route("/add_subject", methods=["GET", "POST"])
def add_subject():

    if request.method == "POST":

        subject_code = request.form["subject_code"]
        subject_name = request.form["subject_name"]
        department = request.form["department"]
        semester = request.form["semester"]
        teacher_id = request.form["teacher_id"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO subjects
            (subject_code, subject_name, department, semester, teacher_id)
            VALUES (?, ?, ?, ?, ?)
            """, (subject_code, subject_name, department, semester, teacher_id))

            conn.commit()

        except sqlite3.IntegrityError:
            return "Subject already exists!"

        finally:
            conn.close()

        return "Subject Added Successfully!"

    return render_template("add_subject.html")
# ---------------- ADD TEACHER ----------------
@app.route("/add_teacher", methods=["GET", "POST"])
def add_teacher():

    if request.method == "POST":

        teacher_id = request.form["teacher_id"]
        fullname = request.form["fullname"]
        email = request.form["email"]
        department = request.form["department"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:

            cursor.execute("""
            INSERT INTO teachers
            (teacher_id, fullname, email, department)
            VALUES (?, ?, ?, ?)
            """, (teacher_id, fullname, email, department))

            conn.commit()

        except sqlite3.IntegrityError:
            return "Teacher already exists!"

        finally:
            conn.close()

        return "Teacher Added Successfully!"

    return render_template("add_teacher.html")
# ---------------- VIEW TEACHERS ----------------
@app.route("/view_teachers")
def view_teachers():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT teacher_id, fullname, email, department
    FROM teachers
    """)

    teachers = cursor.fetchall()

    conn.close()

    return render_template(
        "view_teachers.html",
        teachers=teachers
    )

# ------------------ASSSIGN_SUBJECT--------------------
@app.route("/assign_subject", methods=["GET", "POST"])
def assign_subject():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    if request.method == "POST":

        teacher_id = request.form["teacher_id"]
        subject_code = request.form["subject_code"]

        cursor.execute("""
        INSERT INTO teacher_subjects
        (teacher_id, subject_code)
        VALUES (?, ?)
        """, (teacher_id, subject_code))

        conn.commit()
        conn.close()

        return "Subject Assigned Successfully!"

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
def teacher_subjects(teacher_id):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT subjects.subject_code,
           subjects.subject_name
    FROM teacher_subjects
    JOIN subjects
    ON teacher_subjects.subject_code = subjects.subject_code
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
def practical_session(subject_code):

    conn = sqlite3.connect("database.db")
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
        subject_name=subject[0],
        today=date.today()
    )

# ---------------- ADMIN ----------------
@app.route("/admin")
def admin():
    return render_template("admin.html")


# ---------------- ABOUT ----------------
@app.route("/about")
def about():
    return render_template("about.html")


# ---------------- MAIN ----------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)