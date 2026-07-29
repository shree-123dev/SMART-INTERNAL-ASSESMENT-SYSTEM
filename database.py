import sqlite3

def init_db():
    conn = sqlite3.connect("database.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usn TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        section TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_code TEXT UNIQUE NOT NULL,
        subject_name TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        teacher_id TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_usn TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        class_type TEXT NOT NULL,
        attendance_date TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS internal_marks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_usn TEXT NOT NULL,
        subject_code TEXT NOT NULL,
        ia1 REAL DEFAULT 0,
        ia2 REAL DEFAULT 0,
        assignment REAL DEFAULT 0,
        seminar REAL DEFAULT 0,
        viva REAL DEFAULT 0,
        practical REAL DEFAULT 0
    )
    """)


    conn.commit()
    conn.close()