import { useState, useEffect, useCallback } from 'react';
import { assignmentService } from '../services/assignmentService';

export const useAssignments = () => {
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAssignments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await assignmentService.getAll();
      setAssignments(data);
    } catch (err) {
      setError(err.message || 'Failed to load assignments');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAssignments();
  }, [fetchAssignments]);

  const addAssignment = async (data) => {
    const created = await assignmentService.create(data);
    await fetchAssignments();
    return created;
  };

  const deleteAssignment = async (id) => {
    await assignmentService.remove(id);
    await fetchAssignments();
  };

  return {
    assignments,
    loading,
    error,
    refresh: fetchAssignments,
    addAssignment,
    deleteAssignment
  };
};
