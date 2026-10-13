import { useState, useEffect, useCallback } from 'react';
import { subjectService } from '../services/subjectService';

export const useSubjects = () => {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchSubjects = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await subjectService.getAll();
      setSubjects(data);
    } catch (err) {
      setError(err.message || 'Failed to load subjects');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubjects();
  }, [fetchSubjects]);

  const addSubject = async (data) => {
    const created = await subjectService.create(data);
    await fetchSubjects();
    return created;
  };

  const updateSubject = async (id, data) => {
    const updated = await subjectService.update(id, data);
    await fetchSubjects();
    return updated;
  };

  const deleteSubject = async (id) => {
    await subjectService.remove(id);
    await fetchSubjects();
  };

  return {
    subjects,
    loading,
    error,
    refresh: fetchSubjects,
    addSubject,
    updateSubject,
    deleteSubject
  };
};
