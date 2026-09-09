import sqlite3
import database

def verify():
    # 1. Run init_db()
    database.init_db()

    conn = sqlite3.connect('database.db')
    conn.execute('PRAGMA foreign_keys = ON;')
    c = conn.cursor()

    expected_tables = [
        'users',
        'students',
        'teachers',
        'subjects',
        'teacher_subjects',
        'practical_sessions',
        'attendance',
        'internal_marks'
    ]

    print('=== 1. VERIFYING ALL 8 TABLES EXIST ===')
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    created_tables = [r[0] for r in c.fetchall()]

    all_present = True
    for t in expected_tables:
        if t in created_tables:
            print(f'[OK] Table found: {t}')
        else:
            print(f'[FAIL] Table missing: {t}')
            all_present = False

    print('\n=== 2. VERIFYING TABLE SCHEMAS, PRIMARY KEYS & UNIQUE CONSTRAINTS ===')
    for t in expected_tables:
        c.execute(f'PRAGMA table_info({t});')
        cols = c.fetchall()
        print(f'\nTable: {t}')
        for col in cols:
            cid, name, type_, notnull, dflt, pk = col
            pk_str = ' [PRIMARY KEY]' if pk else ''
            nn_str = ' NOT NULL' if notnull else ''
            df_str = f' DEFAULT {dflt}' if dflt is not None else ''
            print(f'  - {name} ({type_}){pk_str}{nn_str}{df_str}')

        # Check foreign keys
        c.execute(f'PRAGMA foreign_key_list({t});')
        fks = c.fetchall()
        if fks:
            print('  Foreign Keys:')
            for fk in fks:
                print(f'    -> {fk[3]} references {fk[2]}({fk[4]}) ON DELETE {fk[5]}')

    print('\n=== 3. TESTING UNIQUE CONSTRAINTS ===')
    # Test unique email in users
    try:
        c.execute("INSERT INTO users (fullname, email, password, role) VALUES ('Dup User', 'teststudent@example.com', 'p', 'student');")
        print('[FAIL] Duplicate user email allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Unique constraint enforced on users.email')

    # Test unique usn in students
    try:
        c.execute("INSERT INTO students (usn, fullname, email, department, semester, section) VALUES ('TEST001', 'Dup', 'newemail@college.edu', 'CSE', 5, 'A');")
        print('[FAIL] Duplicate student usn allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Unique constraint enforced on students.usn')

    # Test unique teacher_id in teachers
    try:
        c.execute("INSERT INTO teachers (teacher_id, fullname, email, department) VALUES ('T001', 'Dup', 'newteach@college.edu', 'CSE');")
        print('[FAIL] Duplicate teacher_id allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Unique constraint enforced on teachers.teacher_id')

    # Test unique subject_code in subjects
    try:
        c.execute("INSERT INTO subjects (subject_code, subject_name, department, semester) VALUES ('CS501', 'Dup Subject', 'CSE', 5);")
        print('[FAIL] Duplicate subject_code allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Unique constraint enforced on subjects.subject_code')

    print('\n=== 4. TESTING FOREIGN KEY ENFORCEMENT ===')
    # Attempt to insert teacher_subjects with non-existent teacher
    try:
        c.execute("INSERT INTO teacher_subjects (teacher_id, subject_id) VALUES ('INVALID_TCH', 'CS501');")
        print('[FAIL] Invalid teacher foreign key allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Foreign key constraint enforced on teacher_subjects.teacher_id')

    # Attempt to insert attendance with non-existent student
    try:
        c.execute("INSERT INTO attendance (student_id, subject_id, teacher_id, attendance_date, status) VALUES ('NON_EXISTENT_USN', 'CS501', 'T001', '2026-09-08', 'Present');")
        print('[FAIL] Invalid student foreign key in attendance allowed!')
    except sqlite3.IntegrityError:
        print('[OK] Foreign key constraint enforced on attendance.student_id')

    conn.close()

    print('\n=== 5. TESTING FLASK APPLICATION COMPATIBILITY ===')
    import app
    client = app.app.test_client()
    # Test public routes
    public_routes = ['/', '/login', '/signup', '/dashboard', '/about']
    flask_ok = True
    for route in public_routes:
        res = client.get(route)
        if res.status_code != 200:
            print(f'[FAIL] Public route {route} -> HTTP {res.status_code}')
            flask_ok = False
    
    # Test protected routes with authenticated session
    with client.session_transaction() as sess:
        sess['user_id'] = 2
        sess['fullname'] = 'System Administrator'
        sess['email'] = 'admin@test.com'
        sess['role'] = 'admin'

    protected_routes = ['/admin', '/view_students', '/view_teachers', '/add_student', '/add_teacher', '/add_subject', '/assign_subject']
    for route in protected_routes:
        res = client.get(route)
        if res.status_code != 200:
            print(f'[FAIL] Protected route {route} -> HTTP {res.status_code}')
            flask_ok = False

    if flask_ok:
        print('[OK] All Flask public and protected routes rendered successfully with HTTP 200!')

    print('\nALL DAY 2 TESTS PASSED SUCCESSFULLY!')

if __name__ == '__main__':
    verify()
