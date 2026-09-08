import sqlite3

def get_db_connection():
    """Returns a SQLite connection with foreign keys enabled and row access."""
    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the SIAMS SQLite database schema with all required tables and constraints."""
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. USERS TABLE (Login Accounts)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student'))
    );
    """)

    # 2. STUDENTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usn TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        section TEXT NOT NULL,
        qr_path TEXT
    );
    """)

    # 3. TEACHERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT UNIQUE NOT NULL,
        fullname TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL
    );
    """)

    # 4. SUBJECTS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject_code TEXT UNIQUE NOT NULL,
        subject_name TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL
    );
    """)

    # 5. TEACHER_SUBJECTS TABLE (Mapping & Relationship)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teacher_subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE
    );
    """)

    # 6. PRACTICAL_SESSIONS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS practical_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        teacher_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        session_date TEXT NOT NULL,
        start_time TEXT,
        end_time TEXT,
        status TEXT DEFAULT 'active' CHECK(status IN ('active', 'completed')),
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE
    );
    """)

    # 7. ATTENDANCE TABLE (Used later by QR attendance)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        teacher_id TEXT NOT NULL,
        attendance_date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present', 'Absent')),
        session_id INTEGER,
        FOREIGN KEY (student_id) REFERENCES students(usn) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
        FOREIGN KEY (session_id) REFERENCES practical_sessions(id) ON DELETE SET NULL
    );
    """)

    # 8. INTERNAL_MARKS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS internal_marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        ia1 REAL DEFAULT 0,
        ia2 REAL DEFAULT 0,
        assignment REAL DEFAULT 0,
        seminar REAL DEFAULT 0,
        viva REAL DEFAULT 0,
        practical REAL DEFAULT 0,
        FOREIGN KEY (student_id) REFERENCES students(usn) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("SIAMS Database initialized successfully with all 8 tables!")