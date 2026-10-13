import { getDB, saveCollection } from './db';

const delay = (ms = 50) => new Promise((resolve) => setTimeout(resolve, ms));

const normalize = (str) => (str || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');

const isClassMatch = (student, subject) => {
  if (!student || !subject) return false;
  if (Number(student.semester) !== Number(subject.semester)) return false;

  const sDept = normalize(student.department);
  const subDept = normalize(subject.department);

  if (sDept === subDept) return true;
  const isCs = (d) => d === 'cse' || d === 'computerscience' || d === 'computerscienceengineering';
  if (isCs(sDept) && isCs(subDept)) return true;

  return false;
};

export const marksService = {
  /**
   * Retrieves CIE marks (IA1, IA2, assignment, oral) for all students in a subject.
   */
  async getCieMarks(subjectId) {
    await delay();
    const db = getDB();
    const marks = db.marks || [];
    return marks.filter((m) => m.subjectId === subjectId);
  },

  /**
   * Saves or updates CIE marks for students in a subject.
   * marksList: Array of { studentId, ia1, ia2, assignment, oral }
   */
  async saveCieMarks(subjectId, marksList) {
    await delay();
    const db = getDB();
    let marks = [...(db.marks || [])];

    marksList.forEach((entry) => {
      const existingIdx = marks.findIndex(
        (m) => m.subjectId === subjectId && m.studentId === entry.studentId
      );

      const parsedRecord = {
        studentId: entry.studentId,
        subjectId,
        ia1: entry.ia1 !== '' && entry.ia1 !== null && entry.ia1 !== undefined ? Number(entry.ia1) : null,
        ia2: entry.ia2 !== '' && entry.ia2 !== null && entry.ia2 !== undefined ? Number(entry.ia2) : null,
        assignment: entry.assignment !== '' && entry.assignment !== null && entry.assignment !== undefined ? Number(entry.assignment) : null,
        oral: entry.oral !== '' && entry.oral !== null && entry.oral !== undefined ? Number(entry.oral) : null,
        updatedAt: new Date().toISOString()
      };

      if (existingIdx >= 0) {
        marks[existingIdx] = {
          ...marks[existingIdx],
          ...parsedRecord
        };
      } else {
        marks.push(parsedRecord);
      }
    });

    saveCollection('marks', marks);
    return true;
  },

  /**
   * Retrieves practical evaluation marks for a specific experiment session.
   */
  async getPracticalMarks(sessionId) {
    await delay();
    const db = getDB();
    const practicalMarks = db.practicalMarks || [];
    return practicalMarks.filter((p) => p.sessionId === sessionId);
  },

  /**
   * Saves practical marks for a session.
   * marksList: Array of { studentId, marks }
   */
  async savePracticalMarks(sessionId, subjectId, marksList) {
    await delay();
    const db = getDB();
    let practicalMarks = [...(db.practicalMarks || [])];

    marksList.forEach((entry) => {
      const existingIdx = practicalMarks.findIndex(
        (p) => p.sessionId === sessionId && p.studentId === entry.studentId
      );

      const parsedVal =
        entry.marks !== '' && entry.marks !== null && entry.marks !== undefined
          ? Number(entry.marks)
          : null;

      const record = {
        sessionId,
        subjectId,
        studentId: entry.studentId,
        marks: parsedVal,
        updatedAt: new Date().toISOString()
      };

      if (existingIdx >= 0) {
        practicalMarks[existingIdx] = record;
      } else {
        practicalMarks.push(record);
      }
    });

    saveCollection('practicalMarks', practicalMarks);
    return true;
  },

  /**
   * Computes student's average practical score across all evaluated sessions in this subject.
   * Feeds into Practical /15 rubric in CIE evaluation.
   */
  async getStudentPracticalAverage(studentId, subjectId) {
    await delay(20);
    const db = getDB();
    const practicalMarks = db.practicalMarks || [];

    const studentSessionMarks = practicalMarks.filter(
      (p) =>
        p.studentId === studentId &&
        p.subjectId === subjectId &&
        p.marks !== null &&
        !isNaN(p.marks)
    );

    if (studentSessionMarks.length === 0) return null;

    const sum = studentSessionMarks.reduce((acc, curr) => acc + curr.marks, 0);
    return Number((sum / studentSessionMarks.length).toFixed(1));
  },

  /**
   * Computes practical averages for all students in a subject.
   */
  async getAllStudentsPracticalAverages(subjectId) {
    await delay(30);
    const db = getDB();
    const practicalMarks = db.practicalMarks || [];
    const subjectMarks = practicalMarks.filter(
      (p) => p.subjectId === subjectId && p.marks !== null && !isNaN(p.marks)
    );

    const map = {};
    subjectMarks.forEach((item) => {
      if (!map[item.studentId]) {
        map[item.studentId] = { sum: 0, count: 0 };
      }
      map[item.studentId].sum += item.marks;
      map[item.studentId].count += 1;
    });

    const averages = {};
    Object.keys(map).forEach((stdId) => {
      averages[stdId] = Number((map[stdId].sum / map[stdId].count).toFixed(1));
    });

    return averages;
  },

  /**
   * Counts how many students are missing any CIE mark across all subjects assigned to this teacher.
   */
  async getPendingCieCount(teacherId) {
    await delay(40);
    const db = getDB();
    const assignments = (db.assignments || []).filter((a) => a.teacherId === teacherId);
    const assignedSubjectIds = assignments.map((a) => a.subjectId);

    let pendingCount = 0;

    assignedSubjectIds.forEach((subId) => {
      const subject = (db.subjects || []).find((s) => s.id === subId);
      if (!subject) return;

      const classStudents = (db.students || []).filter((s) => isClassMatch(s, subject));
      const cieMarks = (db.marks || []).filter((m) => m.subjectId === subId);

      classStudents.forEach((student) => {
        const studentMark = cieMarks.find((m) => m.studentId === student.id);
        if (!studentMark) {
          pendingCount += 1;
        } else {
          const isMissing =
            studentMark.ia1 === null ||
            studentMark.ia1 === undefined ||
            studentMark.ia2 === null ||
            studentMark.ia2 === undefined ||
            studentMark.assignment === null ||
            studentMark.assignment === undefined ||
            studentMark.oral === null ||
            studentMark.oral === undefined;
          if (isMissing) {
            pendingCount += 1;
          }
        }
      });
    });

    return pendingCount;
  }
};
