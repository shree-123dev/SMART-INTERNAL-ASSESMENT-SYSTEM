// In-memory data store with localStorage persistence

const STORAGE_KEYS = {
  STUDENTS: 'siams_db_students',
  TEACHERS: 'siams_db_teachers',
  SUBJECTS: 'siams_db_subjects',
  ASSIGNMENTS: 'siams_db_assignments',
  SESSIONS: 'siams_db_sessions',
  MARKS: 'siams_db_marks',
  PRACTICAL_MARKS: 'siams_db_practical_marks'
};

const SEED_STUDENTS = [
  // Semester 4
  { id: 'std_1', usn: '1MS24CS001', fullName: 'Alice Student', email: 'student1@test.com', department: 'CSE', semester: 4, section: 'A' },
  { id: 'std_2', usn: '1MS24CS002', fullName: 'Bob Student', email: 'student2@test.com', department: 'CSE', semester: 4, section: 'B' },
  // Semester 5
  { id: 'std_3', usn: 'CS2026A', fullName: 'Student Alpha', email: 'student_alpha_d6@college.edu', department: 'CSE', semester: 5, section: 'A' },
  { id: 'std_4', usn: 'CS2026B', fullName: 'Student Beta', email: 'student_beta_d6@college.edu', department: 'CSE', semester: 5, section: 'B' },
  { id: 'std_5', usn: 'TEST001', fullName: 'Test Student', email: 'student1@college.edu', department: 'Computer Science', semester: 5, section: 'A' },
  // Semester 6 (Enrolled in CSE 6th Sem: CS601, CS602, CSL607)
  { id: 'std_6', usn: '1MS21CS042', fullName: 'Alex Johnson', email: 'student@test.com', department: 'CSE', semester: 6, section: 'A' },
  { id: 'std_7', usn: '1MS21CS005', fullName: 'Ananya Sharma', email: 'ananya.s@college.edu', department: 'CSE', semester: 6, section: 'A' },
  { id: 'std_8', usn: '1MS21CS018', fullName: 'Chetan Rao', email: 'chetan.r@college.edu', department: 'CSE', semester: 6, section: 'A' },
  { id: 'std_9', usn: '1MS21CS029', fullName: 'Divya Nair', email: 'divya.n@college.edu', department: 'CSE', semester: 6, section: 'A' },
  { id: 'std_10', usn: '1MS21CS034', fullName: 'Eshwar Reddy', email: 'eshwar.r@college.edu', department: 'CSE', semester: 6, section: 'B' },
  { id: 'std_11', usn: '1MS21CS048', fullName: 'Fatima Zahra', email: 'fatima.z@college.edu', department: 'CSE', semester: 6, section: 'B' },
  { id: 'std_12', usn: '1MS21CS052', fullName: 'Gautam Patel', email: 'gautam.p@college.edu', department: 'CSE', semester: 6, section: 'B' },
  { id: 'std_13', usn: '1MS21CS060', fullName: 'Harini Sundar', email: 'harini.s@college.edu', department: 'CSE', semester: 6, section: 'B' }
];

const SEED_TEACHERS = [
  { id: 'tch_1', teacherCode: 'T001', fullName: 'Prof. Alan Turing', email: 'alan.turing@college.edu', department: 'Computer Science' },
  { id: 'tch_2', teacherCode: 'T002', fullName: 'Prof. Ada Lovelace', email: 'ada.lovelace@college.edu', department: 'Information Science' },
  { id: 'tch_3', teacherCode: 'TCH_A', fullName: 'Prof. Teacher Alpha', email: 'teacherA@test.com', department: 'CSE' },
  { id: 'tch_4', teacherCode: 'TCH_B', fullName: 'Prof. Teacher Beta', email: 'teacherB@test.com', department: 'CSE' },
  { id: 'tch_5', teacherCode: 'TCH_D7_A', fullName: 'Prof. Alpha', email: 'teacher_alpha_d7@college.edu', department: 'CSE' },
  { id: 'tch_6', teacherCode: 'TCH_D7_B', fullName: 'Prof. Beta', email: 'teacher_beta_d7@college.edu', department: 'ISE' },
  { id: 'tch_7', teacherCode: 'TCH_CS01', fullName: 'Dr. Rajesh Sharma', email: 'teacher@test.com', department: 'CSE' }
];

const SEED_SUBJECTS = [
  { id: 'sub_1', code: 'CS401', name: 'Data Structures Lab', department: 'CSE', semester: 4 },
  { id: 'sub_2', code: 'CS402', name: 'Algorithms Lab', department: 'CSE', semester: 4 },
  { id: 'sub_3', code: 'CS403', name: 'Database Systems', department: 'CSE', semester: 4 },
  { id: 'sub_4', code: 'CS501', name: 'Database Management Systems', department: 'Computer Science', semester: 5 },
  { id: 'sub_5', code: 'CS502', name: 'Operating Systems', department: 'Computer Science', semester: 5 },
  { id: 'sub_6', code: 'CS601', name: 'Machine Learning Principles', department: 'CSE', semester: 6 },
  { id: 'sub_7', code: 'CS602', name: 'Cloud Computing & DevOps', department: 'CSE', semester: 6 },
  { id: 'sub_8', code: 'IS501', name: 'Software Engineering', department: 'Information Science', semester: 5 },
  { id: 'sub_9', code: 'CSL607', name: 'Cloud Computing Laboratory', department: 'CSE', semester: 6 }
];

const SEED_ASSIGNMENTS = [
  { id: 'asg_1', teacherId: 'tch_3', subjectId: 'sub_1' },
  { id: 'asg_2', teacherId: 'tch_3', subjectId: 'sub_2' },
  { id: 'asg_3', teacherId: 'tch_4', subjectId: 'sub_2' },
  { id: 'asg_4', teacherId: 'tch_4', subjectId: 'sub_3' },
  { id: 'asg_5', teacherId: 'tch_1', subjectId: 'sub_4' },
  { id: 'asg_6', teacherId: 'tch_2', subjectId: 'sub_8' },
  { id: 'asg_7', teacherId: 'tch_7', subjectId: 'sub_6' },
  { id: 'asg_8', teacherId: 'tch_7', subjectId: 'sub_7' },
  { id: 'asg_9', teacherId: 'tch_7', subjectId: 'sub_9' }
];

const SEED_SESSIONS = [
  {
    id: 'sess_1',
    teacherId: 'tch_7',
    subjectId: 'sub_9',
    experimentNumber: 1,
    experimentName: 'Docker Containerization & Virtualization',
    token: 'ATT_SES_91823',
    status: 'completed',
    createdAt: new Date(Date.now() - 86400000 * 4).toISOString(),
    endedAt: new Date(Date.now() - 86400000 * 4 + 3600000).toISOString(),
    attended: [
      { usn: '1MS21CS042', studentId: 'std_6', studentName: 'Alex Johnson', timestamp: '10:02 AM' },
      { usn: '1MS21CS005', studentId: 'std_7', studentName: 'Ananya Sharma', timestamp: '10:04 AM' },
      { usn: '1MS21CS018', studentId: 'std_8', studentName: 'Chetan Rao', timestamp: '10:06 AM' },
      { usn: '1MS21CS029', studentId: 'std_9', studentName: 'Divya Nair', timestamp: '10:07 AM' },
      { usn: '1MS21CS034', studentId: 'std_10', studentName: 'Eshwar Reddy', timestamp: '10:08 AM' },
      { usn: '1MS21CS048', studentId: 'std_11', studentName: 'Fatima Zahra', timestamp: '10:10 AM' }
    ]
  },
  {
    id: 'sess_2',
    teacherId: 'tch_7',
    subjectId: 'sub_9',
    experimentNumber: 2,
    experimentName: 'Kubernetes Cluster Setup & Pod Scheduling',
    token: 'ATT_SES_72411',
    status: 'completed',
    createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
    endedAt: new Date(Date.now() - 86400000 * 2 + 3600000).toISOString(),
    attended: [
      { usn: '1MS21CS042', studentId: 'std_6', studentName: 'Alex Johnson', timestamp: '11:15 AM' },
      { usn: '1MS21CS005', studentId: 'std_7', studentName: 'Ananya Sharma', timestamp: '11:16 AM' },
      { usn: '1MS21CS018', studentId: 'std_8', studentName: 'Chetan Rao', timestamp: '11:17 AM' },
      { usn: '1MS21CS029', studentId: 'std_9', studentName: 'Divya Nair', timestamp: '11:19 AM' },
      { usn: '1MS21CS052', studentId: 'std_12', studentName: 'Gautam Patel', timestamp: '11:21 AM' },
      { usn: '1MS21CS060', studentId: 'std_13', studentName: 'Harini Sundar', timestamp: '11:22 AM' }
    ]
  },
  {
    id: 'sess_3',
    teacherId: 'tch_7',
    subjectId: 'sub_7',
    experimentNumber: 1,
    experimentName: 'Cloud Infrastructure & IAM Security',
    token: 'ATT_SES_39018',
    status: 'completed',
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    endedAt: new Date(Date.now() - 86400000 + 3600000).toISOString(),
    attended: [
      { usn: '1MS21CS042', studentId: 'std_6', studentName: 'Alex Johnson', timestamp: '09:05 AM' },
      { usn: '1MS21CS005', studentId: 'std_7', studentName: 'Ananya Sharma', timestamp: '09:06 AM' },
      { usn: '1MS21CS018', studentId: 'std_8', studentName: 'Chetan Rao', timestamp: '09:08 AM' },
      { usn: '1MS21CS029', studentId: 'std_9', studentName: 'Divya Nair', timestamp: '09:09 AM' },
      { usn: '1MS21CS034', studentId: 'std_10', studentName: 'Eshwar Reddy', timestamp: '09:12 AM' },
      { usn: '1MS21CS048', studentId: 'std_11', studentName: 'Fatima Zahra', timestamp: '09:15 AM' },
      { usn: '1MS21CS052', studentId: 'std_12', studentName: 'Gautam Patel', timestamp: '09:16 AM' }
    ]
  }
];

const SEED_MARKS = [
  // CIE Marks for sub_7 (Cloud Computing & DevOps)
  { studentId: 'std_6', subjectId: 'sub_7', ia1: 18, ia2: 19, assignment: 26, oral: 22 },
  { studentId: 'std_7', subjectId: 'sub_7', ia1: 17, ia2: 16, assignment: 27, oral: 21 },
  { studentId: 'std_8', subjectId: 'sub_7', ia1: 15, ia2: 14, assignment: 24, oral: 19 },
  { studentId: 'std_9', subjectId: 'sub_7', ia1: 19, ia2: 18, assignment: 29, oral: 24 },
  { studentId: 'std_10', subjectId: 'sub_7', ia1: 12, ia2: 13, assignment: 20, oral: 16 },
  // CIE Marks for sub_6 (Machine Learning Principles)
  { studentId: 'std_6', subjectId: 'sub_6', ia1: 19, ia2: 18, assignment: 28, oral: 23 },
  { studentId: 'std_7', subjectId: 'sub_6', ia1: 16, ia2: 17, assignment: 25, oral: 20 }
];

const SEED_PRACTICAL_MARKS = [
  // Session 1 (CSL607 Exp 1)
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_6', marks: 14 },
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_7', marks: 13 },
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_8', marks: 12 },
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_9', marks: 15 },
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_10', marks: 11 },
  { sessionId: 'sess_1', subjectId: 'sub_9', studentId: 'std_11', marks: 13 },
  // Session 2 (CSL607 Exp 2)
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_6', marks: 15 },
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_7', marks: 14 },
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_8', marks: 13 },
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_9', marks: 14 },
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_12', marks: 12 },
  { sessionId: 'sess_2', subjectId: 'sub_9', studentId: 'std_13', marks: 13 }
];

const loadFromStorage = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) {
      localStorage.setItem(key, JSON.stringify(fallback));
      return fallback;
    }
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
};

const saveToStorage = (key, data) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (err) {
    console.error('Storage error:', err);
  }
};

// Initial data load
let initialStudents = loadFromStorage(STORAGE_KEYS.STUDENTS, SEED_STUDENTS);
let initialTeachers = loadFromStorage(STORAGE_KEYS.TEACHERS, SEED_TEACHERS);
let initialSubjects = loadFromStorage(STORAGE_KEYS.SUBJECTS, SEED_SUBJECTS);
let initialAssignments = loadFromStorage(STORAGE_KEYS.ASSIGNMENTS, SEED_ASSIGNMENTS);
let initialSessions = loadFromStorage(STORAGE_KEYS.SESSIONS, SEED_SESSIONS);
let initialMarks = loadFromStorage(STORAGE_KEYS.MARKS, SEED_MARKS);
let initialPracticalMarks = loadFromStorage(STORAGE_KEYS.PRACTICAL_MARKS, SEED_PRACTICAL_MARKS);

// Auto-heal / synchronize essential seeds if missing in existing localStorage
// 1. Ensure teacher@test.com exists
const teacherIndex = initialTeachers.findIndex((t) => t.email.toLowerCase() === 'teacher@test.com');
if (teacherIndex === -1) {
  initialTeachers.push(SEED_TEACHERS.find((t) => t.email === 'teacher@test.com'));
  saveToStorage(STORAGE_KEYS.TEACHERS, initialTeachers);
} else {
  // Update name and department if needed
  if (initialTeachers[teacherIndex].fullName !== 'Dr. Rajesh Sharma' || initialTeachers[teacherIndex].department !== 'CSE') {
    initialTeachers[teacherIndex] = {
      ...initialTeachers[teacherIndex],
      fullName: 'Dr. Rajesh Sharma',
      department: 'CSE'
    };
    saveToStorage(STORAGE_KEYS.TEACHERS, initialTeachers);
  }
}

// 2. Ensure teacher has assignments for sub_6, sub_7, sub_9
const teacherRecord = initialTeachers.find((t) => t.email.toLowerCase() === 'teacher@test.com');
if (teacherRecord) {
  const teacherId = teacherRecord.id;
  ['sub_6', 'sub_7', 'sub_9'].forEach((subId) => {
    const hasAsg = initialAssignments.some((a) => a.teacherId === teacherId && a.subjectId === subId);
    if (!hasAsg) {
      initialAssignments.push({ id: 'asg_' + Date.now() + Math.random().toString(36).slice(2, 6), teacherId, subjectId: subId });
      saveToStorage(STORAGE_KEYS.ASSIGNMENTS, initialAssignments);
    }
  });
}

// 3. Ensure semester 6 students exist
const hasSem6 = initialStudents.some((s) => Number(s.semester) === 6 && (s.department === 'CSE' || s.department === 'Computer Science'));
if (!hasSem6) {
  SEED_STUDENTS.filter((s) => Number(s.semester) === 6).forEach((s) => {
    if (!initialStudents.some((existing) => existing.usn === s.usn)) {
      initialStudents.push(s);
    }
  });
  saveToStorage(STORAGE_KEYS.STUDENTS, initialStudents);
}

// 4. Ensure sessions exist
if (!initialSessions || initialSessions.length === 0) {
  initialSessions = SEED_SESSIONS;
  saveToStorage(STORAGE_KEYS.SESSIONS, initialSessions);
}

// 5. Ensure marks exist
if (!initialMarks || initialMarks.length === 0) {
  initialMarks = SEED_MARKS;
  saveToStorage(STORAGE_KEYS.MARKS, initialMarks);
}

if (!initialPracticalMarks || initialPracticalMarks.length === 0) {
  initialPracticalMarks = SEED_PRACTICAL_MARKS;
  saveToStorage(STORAGE_KEYS.PRACTICAL_MARKS, initialPracticalMarks);
}

let db = {
  students: initialStudents,
  teachers: initialTeachers,
  subjects: initialSubjects,
  assignments: initialAssignments,
  sessions: initialSessions,
  marks: initialMarks,
  practicalMarks: initialPracticalMarks
};

export const getDB = () => db;

export const saveCollection = (name, items) => {
  db[name] = items;
  if (name === 'students') saveToStorage(STORAGE_KEYS.STUDENTS, items);
  if (name === 'teachers') saveToStorage(STORAGE_KEYS.TEACHERS, items);
  if (name === 'subjects') saveToStorage(STORAGE_KEYS.SUBJECTS, items);
  if (name === 'assignments') saveToStorage(STORAGE_KEYS.ASSIGNMENTS, items);
  if (name === 'sessions') saveToStorage(STORAGE_KEYS.SESSIONS, items);
  if (name === 'marks') saveToStorage(STORAGE_KEYS.MARKS, items);
  if (name === 'practicalMarks') saveToStorage(STORAGE_KEYS.PRACTICAL_MARKS, items);
};
