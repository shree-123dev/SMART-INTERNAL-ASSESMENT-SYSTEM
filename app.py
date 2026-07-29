from flask import Flask, render_template,request,redirect
import sqlite3
from database import init_db


app = Flask(__name__)

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
            "SELECT role FROM users WHERE email=? AND password=?",
            (email, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            role = user[0]

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

        cursor.execute(
            "INSERT INTO users(fullname,email,password,role) VALUES(?,?,?,?)",
            (fullname, email, password, role)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("signup.html")


# ---------------- FORGOT PASSWORD ----------------
@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


#------------------DASHBOARD------------------------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


#-----------------STUDENT------------------
@app.route("/student")
def student():
    return render_template("student.html")

#----------------TEACHER----------------
@app.route("/teacher")
def teacher():
    return render_template("teacher.html")

#--------------ADMIN------------------
@app.route("/admin")
def admin():
    return render_template("admin.html")

#---------------ABOUT------------------
@app.route("/about")
def about():
    return render_template("about.html")



if __name__ == "__main__":
    init_db()
    app.run(debug=True)