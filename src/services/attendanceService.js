import { getDB } from './db';
import { attendancePercent, requiredFutureSessions } from '../utils/cie';

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

export const attendanceService = {
  /**
   * Returns all students whose department and semester match the given subject.
   */
  async getClassStudents(subjectId) {
    await delay();
    const db = getDB();
    const subject = (db.subjects || []).find((s) => s.id === subjectId);
    if (!subject) return [];

    return (db.students || []).filter((s) => isClassMatch(s, subject));
  },

  /**
   * Computes per-student attendance for all students enrolled in a subject.
   */
  async getSubjectAttendanceStats(subjectId) {
    await delay();
    const db = getDB();
    const subject = (db.subjects || []).find((s) => s.id === subjectId);
    if (!subject) return { students: [], totalSessions: 0 };

    const classStudents = (db.students || []).filter((s) => isClassMatch(s, subject));
    const subjectSessions = (db.sessions || []).filter((s) => s.subjectId === subjectId);
    const totalSessions = subjectSessions.length;

    const studentStats = classStudents.map((student) => {
      let attendedCount = 0;
      subjectSessions.forEach((session) => {
        const wasPresent = (session.attended || []).some(
          (a) =>
            a.studentId === student.id ||
            a.usn?.toUpperCase() === student.usn?.toUpperCase()
        );
        if (wasPresent) attendedCount += 1;
      });

      const percentage = attendancePercent(attendedCount, totalSessions);
      const eligible = percentage === null || percentage >= 75;
      const requiredMore = requiredFutureSessions(attendedCount, totalSessions);

      return {
        student,
        attendedCount,
        totalSessions,
        percentage,
        eligible,
        requiredMore
      };
    });

    return {
      subject,
      totalSessions,
      students: studentStats
    };
  },

  /**
   * Total present marks logged across all sessions taken by this teacher.
   */
  async getTotalAttendanceLogged(teacherId) {
    await delay(30);
    const db = getDB();
    const teacherSessions = (db.sessions || []).filter((s) => s.teacherId === teacherId);

    let total = 0;
    teacherSessions.forEach((session) => {
      total += (session.attended || []).length;
    });

    return total;
  },

  /**
   * Get attendance for a single student in a specific subject.
   */
  async getStudentSubjectAttendance(studentId, subjectId) {
    await delay(30);
    const db = getDB();
    const student = (db.students || []).find((s) => s.id === studentId);
    const sessions = (db.sessions || []).filter((s) => s.subjectId === subjectId);
    const totalSessions = sessions.length;

    if (!student) {
      return { attendedCount: 0, totalSessions, percentage: null, eligible: true, requiredMore: 0 };
    }

    let attendedCount = 0;
    sessions.forEach((session) => {
      const wasPresent = (session.attended || []).some(
        (a) =>
          a.studentId === student.id ||
          a.usn?.toUpperCase() === student.usn?.toUpperCase()
      );
      if (wasPresent) attendedCount += 1;
    });

    const percentage = attendancePercent(attendedCount, totalSessions);
    const eligible = percentage === null || percentage >= 75;
    const requiredMore = requiredFutureSessions(attendedCount, totalSessions);

    return {
      attendedCount,
      totalSessions,
      percentage,
      eligible,
      requiredMore
    };
  },

  /**
   * For the student portal: computes overall attendance across all subjects the student is in.
   */
  async getStudentOverallAttendance(studentId) {
    await delay();
    const db = getDB();
    const student = (db.students || []).find((s) => s.id === studentId);
    if (!student) return { overallPercentage: 0, eligible: true, subjects: [] };

    const enrolledSubjects = (db.subjects || []).filter((sub) => isClassMatch(student, sub));

    let totalClasses = 0;
    let totalAttended = 0;
    const breakdown = [];

    enrolledSubjects.forEach((sub) => {
      const sessions = (db.sessions || []).filter((s) => s.subjectId === sub.id);
      const totalSessions = sessions.length;
      let attendedCount = 0;

      sessions.forEach((s) => {
        if (
          (s.attended || []).some(
            (a) =>
              a.studentId === student.id ||
              a.usn?.toUpperCase() === student.usn?.toUpperCase()
          )
        ) {
          attendedCount += 1;
        }
      });

      totalClasses += totalSessions;
      totalAttended += attendedCount;

      const percentage = attendancePercent(attendedCount, totalSessions);
      breakdown.push({
        subject: sub,
        attendedCount,
        totalSessions,
        percentage,
        eligible: percentage === null || percentage >= 75,
        requiredMore: requiredFutureSessions(attendedCount, totalSessions)
      });
    });

    const overallPercentage = attendancePercent(totalAttended, totalClasses) ?? 100;
    const eligible = overallPercentage >= 75;

    return {
      totalAttended,
      totalClasses,
      overallPercentage,
      eligible,
      breakdown
    };
  }
};
