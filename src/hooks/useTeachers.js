import { useState, useEffect, useCallback } from 'react';
import { teacherService } from '../services/teacherService';

export const useTeachers = () => {
  const [teachers, setTeachers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTeachers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await teacherService.getAll();
      setTeachers(data);
    } catch (err) {
      setError(err.message || 'Failed to load teachers');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTeachers();
  }, [fetchTeachers]);

  const addTeacher = async (data) => {
    const created = await teacherService.create(data);
    await fetchTeachers();
    return created;
  };

  const updateTeacher = async (id, data) => {
    const updated = await teacherService.update(id, data);
    await fetchTeachers();
    return updated;
  };

  const deleteTeacher = async (id) => {
    await teacherService.remove(id);
    await fetchTeachers();
  };

  return {
    teachers,
    loading,
    error,
    refresh: fetchTeachers,
    addTeacher,
    updateTeacher,
    deleteTeacher
  };
};
