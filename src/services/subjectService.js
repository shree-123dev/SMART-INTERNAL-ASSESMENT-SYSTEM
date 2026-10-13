import { getDB, saveCollection } from './db';

const delay = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));

export const subjectService = {
  async getAll() {
    await delay();
    return [...getDB().subjects];
  },

  async getById(id) {
    await delay();
    return getDB().subjects.find((s) => s.id === id) || null;
  },

  async create(data) {
    await delay();
    const db = getDB();
    const code = (data.code || '').trim().toUpperCase();
    const sem = Number(data.semester);

    if (!code || !data.name) {
      throw new Error('Subject Code and Subject Name are required.');
    }

    if (!sem || sem < 1 || sem > 8) {
      throw new Error('Semester must be an integer between 1 and 8.');
    }

    const exists = db.subjects.some((s) => s.code.toUpperCase() === code);
    if (exists) {
      throw new Error(`Subject with Code "${code}" already exists.`);
    }

    const newSubject = {
      id: 'sub_' + Date.now(),
      code: code,
      name: data.name.trim(),
      department: data.department || 'CSE',
      semester: sem
    };

    const updated = [newSubject, ...db.subjects];
    saveCollection('subjects', updated);
    return newSubject;
  },

  async update(id, data) {
    await delay();
    const db = getDB();
    const code = (data.code || '').trim().toUpperCase();
    const sem = data.semester ? Number(data.semester) : null;

    if (sem && (sem < 1 || sem > 8)) {
      throw new Error('Semester must be an integer between 1 and 8.');
    }

    const existingWithCode = db.subjects.find(
      (s) => s.id !== id && s.code.toUpperCase() === code
    );
    if (existingWithCode) {
      throw new Error(`Another subject already uses Code "${code}".`);
    }

    const updated = db.subjects.map((s) => {
      if (s.id === id) {
        return {
          ...s,
          ...data,
          code: code || s.code,
          name: data.name?.trim() || s.name,
          department: data.department || s.department,
          semester: sem !== null ? sem : s.semester
        };
      }
      return s;
    });

    saveCollection('subjects', updated);
    return updated.find((s) => s.id === id);
  },

  async remove(id) {
    await delay();
    const db = getDB();
    const updatedSubjects = db.subjects.filter((s) => s.id !== id);
    saveCollection('subjects', updatedSubjects);

    // Cascade delete any assignments linked to this subject
    const updatedAssignments = db.assignments.filter((a) => a.subjectId !== id);
    saveCollection('assignments', updatedAssignments);

    return true;
  }
};
