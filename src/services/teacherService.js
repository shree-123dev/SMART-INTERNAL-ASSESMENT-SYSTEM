import { getDB, saveCollection } from './db';

const delay = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));

export const teacherService = {
  async getAll() {
    await delay();
    return [...getDB().teachers];
  },

  async getById(id) {
    await delay();
    return getDB().teachers.find((t) => t.id === id) || null;
  },

  async create(data) {
    await delay();
    const db = getDB();
    const code = (data.teacherCode || '').trim();

    if (!code || !data.fullName || !data.email) {
      throw new Error('Teacher ID/Code, Full Name, and Email are required.');
    }

    const exists = db.teachers.some(
      (t) => t.teacherCode.toLowerCase() === code.toLowerCase()
    );
    if (exists) {
      throw new Error(`Teacher with ID/Code "${code}" already exists.`);
    }

    const newTeacher = {
      id: 'tch_' + Date.now(),
      teacherCode: code,
      fullName: data.fullName.trim(),
      email: data.email.trim().toLowerCase(),
      department: data.department || 'Computer Science'
    };

    const updated = [newTeacher, ...db.teachers];
    saveCollection('teachers', updated);
    return newTeacher;
  },

  async update(id, data) {
    await delay();
    const db = getDB();
    const code = (data.teacherCode || '').trim();

    const existingWithCode = db.teachers.find(
      (t) => t.id !== id && t.teacherCode.toLowerCase() === code.toLowerCase()
    );
    if (existingWithCode) {
      throw new Error(`Another faculty member already uses ID/Code "${code}".`);
    }

    const updated = db.teachers.map((t) => {
      if (t.id === id) {
        return {
          ...t,
          ...data,
          teacherCode: code || t.teacherCode,
          fullName: data.fullName?.trim() || t.fullName,
          email: data.email?.trim().toLowerCase() || t.email,
          department: data.department || t.department
        };
      }
      return t;
    });

    saveCollection('teachers', updated);
    return updated.find((t) => t.id === id);
  },

  async remove(id) {
    await delay();
    const db = getDB();
    const updatedTeachers = db.teachers.filter((t) => t.id !== id);
    saveCollection('teachers', updatedTeachers);

    // Cascade delete any assignments linked to this teacher
    const updatedAssignments = db.assignments.filter((a) => a.teacherId !== id);
    saveCollection('assignments', updatedAssignments);

    return true;
  }
};
