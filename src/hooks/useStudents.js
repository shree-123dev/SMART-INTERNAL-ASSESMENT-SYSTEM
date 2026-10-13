import { useState, useEffect, useCallback } from 'react';
import { studentService } from '../services/studentService';

export const useStudents = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchStudents = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await studentService.getAll();
      setStudents(data);
    } catch (err) {
      setError(err.message || 'Failed to load students');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStudents();
  }, [fetchStudents]);

  const addStudent = async (data) => {
    const created = await studentService.create(data);
    await fetchStudents();
    return created;
  };

  const updateStudent = async (id, data) => {
    const updated = await studentService.update(id, data);
    await fetchStudents();
    return updated;
  };

  const deleteStudent = async (id) => {
    await studentService.remove(id);
    await fetchStudents();
  };

  return {
    students,
    loading,
    error,
    refresh: fetchStudents,
    addStudent,
    updateStudent,
    deleteStudent
  };
};
