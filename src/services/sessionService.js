import { getDB, saveCollection } from './db';

const delay = (ms = 60) => new Promise((resolve) => setTimeout(resolve, ms));

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

export const sessionService = {
  async getAll() {
    await delay();
    return [...(getDB().sessions || [])];
  },

  async getById(id) {
    await delay();
    return (getDB().sessions || []).find((s) => s.id === id) || null;
  },

  async getByTeacher(teacherId) {
    await delay();
    const sessions = getDB().sessions || [];
    return sessions
      .filter((s) => s.teacherId === teacherId)
      .sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
  },

  async getActive(teacherId) {
    await delay();
    const sessions = getDB().sessions || [];
    return sessions.find((s) => s.teacherId === teacherId && s.status === 'active') || null;
  },

  async start({ teacherId, subjectId, experimentNumber, experimentName }) {
    await delay();
    const db = getDB();

    if (!teacherId) throw new Error('Teacher ID is required to start a session.');
    if (!subjectId) throw new Error('Please select an assigned subject.');
    if (!experimentNumber && experimentNumber !== 0) throw new Error('Experiment number is required.');
    if (!experimentName || !experimentName.trim()) throw new Error('Experiment topic/name is required.');

    // Enforce: Only one active session per teacher
    const existingActive = (db.sessions || []).find(
      (s) => s.teacherId === teacherId && s.status === 'active'
    );
    if (existingActive) {
      throw new Error(
        'An active session is already broadcasting. Please end your current session before launching a new one.'
      );
    }

    const token = 'ATT_SESSION_' + Math.floor(100000 + Math.random() * 900000);
    const newSession = {
      id: 'sess_' + Date.now(),
      teacherId,
      subjectId,
      experimentNumber: Number(experimentNumber),
      experimentName: experimentName.trim(),
      token,
      status: 'active',
      createdAt: new Date().toISOString(),
      attended: []
    };

    const updated = [newSession, ...(db.sessions || [])];
    saveCollection('sessions', updated);
    return newSession;
  },

  async end(sessionId) {
    await delay();
    const db = getDB();
    const sessions = db.sessions || [];
    const target = sessions.find((s) => s.id === sessionId);

    if (!target) throw new Error('Session not found.');

    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        return {
          ...s,
          status: 'completed',
          endedAt: new Date().toISOString()
        };
      }
      return s;
    });

    saveCollection('sessions', updated);
    return updated.find((s) => s.id === sessionId);
  },

  async refreshToken(sessionId) {
    await delay(30);
    const db = getDB();
    const sessions = db.sessions || [];
    const newToken = 'ATT_SESSION_' + Math.floor(100000 + Math.random() * 900000);

    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        return {
          ...s,
          token: newToken
        };
      }
      return s;
    });

    saveCollection('sessions', updated);
    return newToken;
  },

  async markAttendance(sessionId, usn) {
    await delay();
    const db = getDB();
    const sessions = db.sessions || [];
    const session = sessions.find((s) => s.id === sessionId);

    if (!session) {
      throw new Error('Session not found.');
    }
    if (session.status !== 'active') {
      throw new Error('This attendance session is no longer active.');
    }

    const cleanUsn = (usn || '').trim().toUpperCase();
    if (!cleanUsn) {
      throw new Error('Please enter a student USN.');
    }

    // 1. Check if student exists in database
    const student = (db.students || []).find(
      (s) => s.usn?.toUpperCase() === cleanUsn
    );
    if (!student) {
      throw new Error(`Unknown USN: No student registered with USN "${cleanUsn}".`);
    }

    // 2. Check if student belongs to this class
    const subject = (db.subjects || []).find((s) => s.id === session.subjectId);
    if (!subject) {
      throw new Error('Subject for this session not found.');
    }

    if (!isClassMatch(student, subject)) {
      throw new Error(
        `Student Not In Class: ${student.fullName} (${cleanUsn}) is in ${student.department} Sem ${student.semester}, but this session is for ${subject.code} (${subject.department} Sem ${subject.semester}).`
      );
    }

    // 3. Duplicate check
    const isDuplicate = (session.attended || []).some(
      (a) => a.usn?.toUpperCase() === cleanUsn || a.studentId === student.id
    );
    if (isDuplicate) {
      throw new Error(
        `Duplicate Scan: Student ${student.fullName} (${cleanUsn}) has already been marked present for this session.`
      );
    }

    const attendanceRecord = {
      usn: student.usn,
      studentId: student.id,
      studentName: student.fullName,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    };

    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        return {
          ...s,
          attended: [...(s.attended || []), attendanceRecord]
        };
      }
      return s;
    });

    saveCollection('sessions', updated);
    return {
      success: true,
      student,
      record: attendanceRecord,
      session: updated.find((s) => s.id === sessionId)
    };
  },

  async removeAttendance(sessionId, usn) {
    await delay();
    const db = getDB();
    const sessions = db.sessions || [];
    const cleanUsn = (usn || '').trim().toUpperCase();

    const updated = sessions.map((s) => {
      if (s.id === sessionId) {
        return {
          ...s,
          attended: (s.attended || []).filter(
            (a) => a.usn?.toUpperCase() !== cleanUsn
          )
        };
      }
      return s;
    });

    saveCollection('sessions', updated);
    return updated.find((s) => s.id === sessionId);
  }
};
