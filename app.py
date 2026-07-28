from flask import Flask, render_template

app = Flask(__name__)

# ---------------- HOME PAGE ----------------
@app.route("/")
def home():
    return render_template("index.html")


# ---------------- LOGIN PAGE ----------------
@app.route("/login")
def login():
    return render_template("login.html")


# ---------------- SIGNUP PAGE ----------------
@app.route("/signup")
def signup():
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
    app.run(debug=True)