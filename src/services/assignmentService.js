import { getDB, saveCollection } from './db';

const delay = (ms = 80) => new Promise((resolve) => setTimeout(resolve, ms));

export const assignmentService = {
  async getAll() {
    await delay();
    return [...getDB().assignments];
  },

  async create({ teacherId, subjectId }) {
    await delay();
    const db = getDB();

    if (!teacherId || !subjectId) {
      throw new Error('Please select both a faculty instructor and a curriculum subject.');
    }

    const teacher = db.teachers.find((t) => t.id === teacherId);
    if (!teacher) {
      throw new Error('Selected teacher does not exist.');
    }

    const subject = db.subjects.find((s) => s.id === subjectId);
    if (!subject) {
      throw new Error('Selected subject does not exist.');
    }

    const duplicate = db.assignments.some(
      (a) => a.teacherId === teacherId && a.subjectId === subjectId
    );
    if (duplicate) {
      throw new Error('This subject is already assigned to this faculty member.');
    }

    const newAssignment = {
      id: 'asg_' + Date.now(),
      teacherId,
      subjectId
    };

    const updated = [newAssignment, ...db.assignments];
    saveCollection('assignments', updated);
    return newAssignment;
  },

  async remove(id) {
    await delay();
    const db = getDB();
    const updated = db.assignments.filter((a) => a.id !== id);
    saveCollection('assignments', updated);
    return true;
  }
};
