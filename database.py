import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    """Returns a SQLite connection with foreign keys enabled and row access."""
    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def seed_default_users(conn):
    """Seeds default accounts with hashed passwords if not already present, and upgrades any plaintext passwords."""
    cursor = conn.cursor()

    default_accounts = [
        ("System Administrator", "admin@test.com", "admin123", "admin"),
        ("Prof. Alan Teacher", "teacher@test.com", "teacher123", "teacher"),
        ("Shreeram Student", "student@test.com", "student123", "student")
    ]

    for fullname, email, plain_pass, role in default_accounts:
        cursor.execute("SELECT id, password FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            hashed = generate_password_hash(plain_pass)
            cursor.execute(
                "INSERT INTO users (fullname, email, password, role) VALUES (?, ?, ?, ?)",
                (fullname, email, hashed, role)
            )
        else:
            # Upgrade plaintext password if found
            current_pass = row[1]
            if not current_pass.startswith("scrypt:") and not current_pass.startswith("pbkdf2:"):
                hashed = generate_password_hash(plain_pass)
                cursor.execute("UPDATE users SET password = ? WHERE id = ?", (hashed, row[0]))

    # Also upgrade any other legacy plaintext passwords
    cursor.execute("SELECT id, password FROM users")
    all_users = cursor.fetchall()
    for uid, pwd in all_users:
        if pwd and not (pwd.startswith("scrypt:") or pwd.startswith("pbkdf2:")):
            cursor.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(pwd), uid))

    conn.commit()

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
        experiment_no TEXT,
        experiment_name TEXT,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE
    );
    """)

    # Seamless migration for existing practical_sessions table if columns missing
    cursor.execute("PRAGMA table_info(practical_sessions);")
    ps_columns = [row[1] for row in cursor.fetchall()]
    if "experiment_no" not in ps_columns:
        cursor.execute("ALTER TABLE practical_sessions ADD COLUMN experiment_no TEXT;")
    if "experiment_name" not in ps_columns:
        cursor.execute("ALTER TABLE practical_sessions ADD COLUMN experiment_name TEXT;")

    # 7. ATTENDANCE TABLE (Used by QR attendance)
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

    # 8. EXPERIMENT_MARKS TABLE (Day 8: Granular Practical & Assignment Marks per Session/Experiment)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS experiment_marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id TEXT NOT NULL,
        subject_id TEXT NOT NULL,
        teacher_id TEXT NOT NULL,
        experiment_no TEXT,
        experiment_name TEXT,
        practical_marks REAL DEFAULT 0,
        assignment_marks REAL DEFAULT 0,
        max_practical_marks REAL DEFAULT 10,
        max_assignment_marks REAL DEFAULT 5,
        recorded_date TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES practical_sessions(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES students(usn) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE
    );
    """)

    # 9. INTERNAL_MARKS TABLE (Day 9: Cumulative Course Internal Assessment & Continuous Evaluation)
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
        max_ia1 REAL DEFAULT 20,
        max_ia2 REAL DEFAULT 20,
        oral_marks REAL,
        max_oral_marks REAL DEFAULT 25,
        oral_recorded_date TEXT,
        teacher_id TEXT,
        updated_at TEXT,
        FOREIGN KEY (student_id) REFERENCES students(usn) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(subject_code) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL
    );
    """)

    # Seamless migration for existing internal_marks table if columns missing
    cursor.execute("PRAGMA table_info(internal_marks);")
    im_columns = [row[1] for row in cursor.fetchall()]
    if "max_ia1" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN max_ia1 REAL DEFAULT 20;")
    if "max_ia2" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN max_ia2 REAL DEFAULT 20;")
    if "oral_marks" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN oral_marks REAL;")
    if "max_oral_marks" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN max_oral_marks REAL DEFAULT 25;")
    if "oral_recorded_date" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN oral_recorded_date TEXT;")
    if "teacher_id" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN teacher_id TEXT;")
    if "updated_at" not in im_columns:
        cursor.execute("ALTER TABLE internal_marks ADD COLUMN updated_at TEXT;")

    # Unique index on (student_id, subject_id) for internal_marks
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_internal_marks_student_subject ON internal_marks(student_id, subject_id);")

    conn.commit()

    # Seed initial test/admin accounts securely
    seed_default_users(conn)

    conn.close()

if __name__ == "__main__":
    init_db()
    print("SIAMS Database initialized successfully with all tables, experiment tracking, and hashed accounts!")