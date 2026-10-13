import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { TEACHER_NAV_ITEMS } from './teacherNav';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import { assignmentService } from '../../services/assignmentService';
import { subjectService } from '../../services/subjectService';
import { attendanceService } from '../../services/attendanceService';
import { marksService } from '../../services/marksService';
import { calculateCie } from '../../utils/cie';

// Icons
import {
  FiSave,
  FiCheckCircle
} from 'react-icons/fi';

const CieMarksEntry = () => {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const preselectedSubject = searchParams.get('subjectId');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(preselectedSubject || '');
  const [students, setStudents] = useState([]);
  const [marksState, setMarksState] = useState({}); // { [studentId]: { ia1, ia2, assignment, oral, practical } }
  const [errorsState, setErrorsState] = useState({}); // { [studentId]: { ia1, ia2, assignment, oral } }
  const [toastMessage, setToastMessage] = useState('');

  // 1. Load assigned subjects
  useEffect(() => {
    const loadSubjects = async () => {
      if (!user?.id) return;
      try {
        setLoading(true);
        const [allAssignments, allSubjects] = await Promise.all([
          assignmentService.getAll(),
          subjectService.getAll()
        ]);

        const myAssignments = allAssignments.filter((a) => a.teacherId === user.id);
        const mySubjects = allSubjects.filter((s) =>
          myAssignments.some((a) => a.subjectId === s.id)
        );
        setAssignedSubjects(mySubjects);

        if (!selectedSubjectId && mySubjects.length > 0) {
          const initialId = preselectedSubject || mySubjects[0].id;
          setSelectedSubjectId(initialId);
        }
      } catch (err) {
        console.error('Failed to load subjects:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, [user?.id]);

  // 2. Load class students, existing CIE marks, and practical averages for selected subject
  useEffect(() => {
    if (!selectedSubjectId) {
      setStudents([]);
      setMarksState({});
      return;
    }

    const loadClassAndMarks = async () => {
      try {
        setLoading(true);
        const [classStudents, existingMarks, practicalAverages] = await Promise.all([
          attendanceService.getClassStudents(selectedSubjectId),
          marksService.getCieMarks(selectedSubjectId),
          marksService.getAllStudentsPracticalAverages(selectedSubjectId)
        ]);

        setStudents(classStudents);

        const newMarksState = {};
        classStudents.forEach((student) => {
          const m = existingMarks.find((item) => item.studentId === student.id) || {};
          const practicalAvg = practicalAverages[student.id] !== undefined ? practicalAverages[student.id] : null;

          newMarksState[student.id] = {
            ia1: m.ia1 !== null && m.ia1 !== undefined ? m.ia1 : '',
            ia2: m.ia2 !== null && m.ia2 !== undefined ? m.ia2 : '',
            assignment: m.assignment !== null && m.assignment !== undefined ? m.assignment : '',
            oral: m.oral !== null && m.oral !== undefined ? m.oral : '',
            practical: practicalAvg
          };
        });

        setMarksState(newMarksState);
        setErrorsState({});
      } catch (err) {
        console.error('Failed to load marks data:', err);
      } finally {
        setLoading(false);
      }
    };

    loadClassAndMarks();
  }, [selectedSubjectId]);

  // Handle Mark Field Input and Range Validation
  const handleMarkChange = (studentId, field, val) => {
    const rawVal = val.trim();
    let error = '';

    if (rawVal !== '') {
      const num = Number(rawVal);
      if (isNaN(num)) {
        error = 'Must be a valid number';
      } else if (field === 'ia1' && (num < 0 || num > 20)) {
        error = '0 - 20 only';
      } else if (field === 'ia2' && (num < 0 || num > 20)) {
        error = '0 - 20 only';
      } else if (field === 'assignment' && (num < 0 || num > 30)) {
        error = '0 - 30 only';
      } else if (field === 'oral' && (num < 0 || num > 25)) {
        error = '0 - 25 only';
      }
    }

    setMarksState((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [field]: rawVal
      }
    }));

    setErrorsState((prev) => ({
      ...prev,
      [studentId]: {
        ...prev[studentId],
        [field]: error
      }
    }));

    if (toastMessage) setToastMessage('');
  };

  // Has validation errors check
  const hasErrors = Object.values(errorsState).some((studentErrors) =>
    studentErrors && Object.values(studentErrors).some((err) => !!err)
  );

  // Save All Marks
  const handleSaveAll = async () => {
    if (hasErrors || !selectedSubjectId) return;

    try {
      setSaving(true);
      const marksList = students.map((std) => ({
        studentId: std.id,
        ia1: marksState[std.id]?.ia1,
        ia2: marksState[std.id]?.ia2,
        assignment: marksState[std.id]?.assignment,
        oral: marksState[std.id]?.oral
      }));

      await marksService.saveCieMarks(selectedSubjectId, marksList);
      setToastMessage('All Continuous Internal Evaluation (CIE) marks saved successfully!');

      setTimeout(() => {
        setToastMessage('');
      }, 4000);
    } catch (err) {
      console.error('Failed to save CIE marks:', err);
      alert('Error saving marks: ' + (err.message || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  const selectedSubject = assignedSubjects.find((s) => s.id === selectedSubjectId);

  // Compute summary stats for the current ledger
  const summaryStats = students.reduce(
    (acc, std) => {
      const rowMarks = marksState[std.id] || {};
      const evalRes = calculateCie(rowMarks);
      if (evalRes.status === 'PASS') acc.pass += 1;
      else if (evalRes.status === 'FAIL') acc.fail += 1;
      else acc.pending += 1;
      return acc;
    },
    { pass: 0, fail: 0, pending: 0 }
  );

  return (
    <DashboardLayout
      title="CIE Marks Entry"
      emoji="📝"
      welcomeLine={`Welcome, ${user?.name || 'Faculty Member'} 👋 • Continuous Internal Evaluation (IA1, IA2, Assignment, Oral & Practical)`}
      navItems={TEACHER_NAV_ITEMS}
    >
      {/* Subject Picker and Save Action Bar */}
      <Card padding="md">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ minWidth: '320px' }}>
              <label className="siams-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
                Select Assigned Curriculum Subject:
              </label>
              <select
                className="siams-input"
                value={selectedSubjectId}
                onChange={(e) => {
                  setSelectedSubjectId(e.target.value);
                  setSearchParams({ subjectId: e.target.value });
                }}
                disabled={loading || assignedSubjects.length === 0}
              >
                {assignedSubjects.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.code} - {sub.name} ({sub.department} Sem {sub.semester})
                  </option>
                ))}
              </select>
            </div>

            {selectedSubject && (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginTop: '1.25rem' }}>
                <Badge variant="pill">Enrolled: {students.length}</Badge>
                <Badge variant="success">Pass: {summaryStats.pass}</Badge>
                <Badge variant="danger">Fail: {summaryStats.fail}</Badge>
                <Badge variant="warning">Pending: {summaryStats.pending}</Badge>
              </div>
            )}
          </div>

          <Button
            variant="primary"
            size="lg"
            icon={<FiSave />}
            disabled={saving || loading || hasErrors || students.length === 0}
            onClick={handleSaveAll}
          >
            {saving ? 'Saving Records...' : 'Save All Marks'}
          </Button>
        </div>
      </Card>

      {/* Success Toast */}
      {toastMessage && (
        <div
          style={{
            padding: '1rem 1.25rem',
            backgroundColor: 'var(--status-success-bg)',
            border: '1px solid #86efac',
            borderRadius: 'var(--radius-card)',
            color: 'var(--status-success)',
            fontSize: '0.9375rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            boxShadow: 'var(--shadow-sm)',
            animation: 'fadeIn 0.2s ease-in'
          }}
        >
          <FiCheckCircle size={20} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Editable Evaluation Ledger Table */}
      <Card padding="none">
        <div
          style={{
            padding: '1.25rem 1.5rem',
            borderBottom: '1px solid var(--border-color)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
              CIE Evaluation Matrix (Max /90 Scale)
            </h3>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Passing Thresholds: IA1 ≥ 8/20, IA2 ≥ 8/20, Assignment ≥ 15/30, Oral ≥ 15/25, Practical ≥ 10/15
            </span>
          </div>
          <Badge variant="pill">Formula: IA avg + Practical + Assignment + Oral</Badge>
        </div>

        <div style={{ overflowX: 'auto', width: '100%' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.875rem',
              textAlign: 'left'
            }}
          >
            <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
              <tr>
                <th style={{ padding: '0.85rem 1rem' }}>USN</th>
                <th style={{ padding: '0.85rem 1rem' }}>Student Name</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '110px' }}>IA1 (/20)</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '110px' }}>IA2 (/20)</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '90px' }}>IA Avg</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '105px' }}>Practical (/15)</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '115px' }}>Assignment (/30)</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '110px' }}>Oral (/25)</th>
                <th style={{ padding: '0.85rem 0.75rem', width: '95px' }}>Total (/90)</th>
                <th style={{ padding: '0.85rem 1rem', textAlign: 'center', width: '110px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="10" style={{ textAlign: 'center', padding: '3.5rem' }}>
                    Loading students and evaluation rubrics...
                  </td>
                </tr>
              ) : students.length === 0 ? (
                <tr>
                  <td colSpan="10" style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
                    No students found in this course cohort.
                  </td>
                </tr>
              ) : (
                students.map((student) => {
                  const sMarks = marksState[student.id] || {};
                  const sErrors = errorsState[student.id] || {};
                  const cie = calculateCie(sMarks);

                  return (
                    <tr
                      key={student.id}
                      style={{ borderBottom: '1px solid var(--border-color)' }}
                    >
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 800, color: '#2563eb' }}>
                        {student.usn}
                      </td>
                      <td style={{ padding: '0.85rem 1rem', fontWeight: 600 }}>
                        {student.fullName}
                      </td>

                      {/* IA1 Input */}
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max="20"
                          className={`siams-input ${sErrors.ia1 ? 'siams-input-error' : ''}`}
                          style={{ padding: '0.45rem 0.65rem', textAlign: 'center', fontSize: '0.875rem' }}
                          value={sMarks.ia1 !== undefined ? sMarks.ia1 : ''}
                          onChange={(e) => handleMarkChange(student.id, 'ia1', e.target.value)}
                          placeholder="—"
                        />
                        {sErrors.ia1 && (
                          <span style={{ fontSize: '0.7rem', color: '#ef4444', display: 'block', marginTop: '0.2rem' }}>
                            {sErrors.ia1}
                          </span>
                        )}
                      </td>

                      {/* IA2 Input */}
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max="20"
                          className={`siams-input ${sErrors.ia2 ? 'siams-input-error' : ''}`}
                          style={{ padding: '0.45rem 0.65rem', textAlign: 'center', fontSize: '0.875rem' }}
                          value={sMarks.ia2 !== undefined ? sMarks.ia2 : ''}
                          onChange={(e) => handleMarkChange(student.id, 'ia2', e.target.value)}
                          placeholder="—"
                        />
                        {sErrors.ia2 && (
                          <span style={{ fontSize: '0.7rem', color: '#ef4444', display: 'block', marginTop: '0.2rem' }}>
                            {sErrors.ia2}
                          </span>
                        )}
                      </td>

                      {/* Computed IA Average */}
                      <td style={{ padding: '0.85rem 0.75rem', fontWeight: 700, textAlign: 'center' }}>
                        {cie.iaAvg !== null ? (
                          <span style={{ color: cie.iaAvg >= 8 ? '#10b981' : '#f59e0b' }}>
                            {cie.iaAvg}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>

                      {/* Practical Marks (Feeds from Lab Evaluation Average) */}
                      <td style={{ padding: '0.85rem 0.75rem', textAlign: 'center', fontWeight: 700 }}>
                        {cie.practical !== null ? (
                          <span style={{ color: cie.practical >= 10 ? '#10b981' : '#ef4444' }}>
                            {cie.practical}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }} title="Evaluated in Lab Evaluation">
                            Lab pending
                          </span>
                        )}
                      </td>

                      {/* Assignment Input */}
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max="30"
                          className={`siams-input ${sErrors.assignment ? 'siams-input-error' : ''}`}
                          style={{ padding: '0.45rem 0.65rem', textAlign: 'center', fontSize: '0.875rem' }}
                          value={sMarks.assignment !== undefined ? sMarks.assignment : ''}
                          onChange={(e) => handleMarkChange(student.id, 'assignment', e.target.value)}
                          placeholder="—"
                        />
                        {sErrors.assignment && (
                          <span style={{ fontSize: '0.7rem', color: '#ef4444', display: 'block', marginTop: '0.2rem' }}>
                            {sErrors.assignment}
                          </span>
                        )}
                      </td>

                      {/* Oral Input */}
                      <td style={{ padding: '0.65rem 0.75rem' }}>
                        <input
                          type="number"
                          step="0.5"
                          min="0"
                          max="25"
                          className={`siams-input ${sErrors.oral ? 'siams-input-error' : ''}`}
                          style={{ padding: '0.45rem 0.65rem', textAlign: 'center', fontSize: '0.875rem' }}
                          value={sMarks.oral !== undefined ? sMarks.oral : ''}
                          onChange={(e) => handleMarkChange(student.id, 'oral', e.target.value)}
                          placeholder="—"
                        />
                        {sErrors.oral && (
                          <span style={{ fontSize: '0.7rem', color: '#ef4444', display: 'block', marginTop: '0.2rem' }}>
                            {sErrors.oral}
                          </span>
                        )}
                      </td>

                      {/* Total Out of 90 */}
                      <td style={{ padding: '0.85rem 0.75rem', fontWeight: 800, textAlign: 'center' }}>
                        {cie.total !== null ? (
                          <span style={{ color: '#2563eb', fontSize: '0.95rem' }}>
                            {cie.total}
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>—</span>
                        )}
                      </td>

                      {/* Status Badge */}
                      <td style={{ padding: '0.85rem 1rem', textAlign: 'center' }}>
                        <Badge
                          variant={
                            cie.status === 'PASS'
                              ? 'success'
                              : cie.status === 'FAIL'
                              ? 'danger'
                              : 'warning'
                          }
                          size="sm"
                        >
                          {cie.status}
                        </Badge>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </DashboardLayout>
  );
};

export default CieMarksEntry;
