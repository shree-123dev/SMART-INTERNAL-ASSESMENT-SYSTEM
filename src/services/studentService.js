import { getDB, saveCollection } from './db';

const delay = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));

export const studentService = {
  async getAll() {
    await delay();
    return [...getDB().students];
  },

  async getById(id) {
    await delay();
    return getDB().students.find((s) => s.id === id) || null;
  },

  async create(data) {
    await delay();
    const db = getDB();
    const usnUpper = (data.usn || '').trim().toUpperCase();

    if (!usnUpper || !data.fullName || !data.email) {
      throw new Error('USN, Full Name, and Email are required.');
    }

    const exists = db.students.some((s) => s.usn.toUpperCase() === usnUpper);
    if (exists) {
      throw new Error(`Student with USN "${usnUpper}" already exists.`);
    }

    const newStudent = {
      id: 'std_' + Date.now(),
      usn: usnUpper,
      fullName: data.fullName.trim(),
      email: data.email.trim().toLowerCase(),
      department: data.department || 'CSE',
      semester: Number(data.semester) || 1,
      section: (data.section || 'A').toUpperCase()
    };

    const updated = [newStudent, ...db.students];
    saveCollection('students', updated);
    return newStudent;
  },

  async update(id, data) {
    await delay();
    const db = getDB();
    const usnUpper = (data.usn || '').trim().toUpperCase();

    const existingWithUsn = db.students.find(
      (s) => s.id !== id && s.usn.toUpperCase() === usnUpper
    );
    if (existingWithUsn) {
      throw new Error(`Another student already uses USN "${usnUpper}".`);
    }

    const updated = db.students.map((s) => {
      if (s.id === id) {
        return {
          ...s,
          ...data,
          usn: usnUpper || s.usn,
          fullName: data.fullName?.trim() || s.fullName,
          email: data.email?.trim().toLowerCase() || s.email,
          semester: data.semester ? Number(data.semester) : s.semester,
          section: data.section ? data.section.toUpperCase() : s.section
        };
      }
      return s;
    });

    saveCollection('students', updated);
    return updated.find((s) => s.id === id);
  },

  async remove(id) {
    await delay();
    const db = getDB();
    const updated = db.students.filter((s) => s.id !== id);
    saveCollection('students', updated);
    return true;
  }
};
