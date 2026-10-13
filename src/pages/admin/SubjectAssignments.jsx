import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { ADMIN_NAV_ITEMS } from './adminNav';
import DataTable from '../../components/DataTable';
import ConfirmDialog from '../../components/ConfirmDialog';
import Button from '../../components/Button';
import Badge from '../../components/Badge';
import { useAssignments } from '../../hooks/useAssignments';
import { useTeachers } from '../../hooks/useTeachers';
import { useSubjects } from '../../hooks/useSubjects';

// Icons
import {
  FiLink,
  FiArrowLeft,
  FiCheckCircle,
  FiInfo,
  FiTrash2,
  FiList
} from 'react-icons/fi';
import { FaChalkboardTeacher, FaBookOpen } from 'react-icons/fa';
import { HiOutlineLink } from 'react-icons/hi';

const SubjectAssignments = () => {
  const navigate = useNavigate();
  const { assignments, loading: loadingAssignments, addAssignment, deleteAssignment } = useAssignments();
  const { teachers, loading: loadingTeachers } = useTeachers();
  const { subjects, loading: loadingSubjects } = useSubjects();

  // Assignment form state
  const [selectedTeacherId, setSelectedTeacherId] = useState('');
  const [selectedSubjectId, setSelectedSubjectId] = useState('');
  const [formError, setFormError] = useState('');
  const [formSuccess, setFormSuccess] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Unassign dialog state
  const [unassignTarget, setUnassignTarget] = useState(null);
  const [isUnassigning, setIsUnassigning] = useState(false);

  const handleAssign = async (e) => {
    e.preventDefault();
    setFormError('');
    setFormSuccess('');

    if (!selectedTeacherId) {
      setFormError('Please select a faculty instructor.');
      return;
    }
    if (!selectedSubjectId) {
      setFormError('Please select a curriculum subject.');
      return;
    }

    try {
      setIsSubmitting(true);
      await addAssignment({
        teacherId: selectedTeacherId,
        subjectId: selectedSubjectId
      });

      const teacher = teachers.find((t) => t.id === selectedTeacherId);
      const subject = subjects.find((s) => s.id === selectedSubjectId);
      setFormSuccess(
        `Successfully mapped ${subject?.code} (${subject?.name}) to ${teacher?.fullName}!`
      );
      setSelectedSubjectId('');
    } catch (err) {
      setFormError(err.message || 'Failed to create assignment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUnassignConfirm = async () => {
    if (!unassignTarget) return;
    try {
      setIsUnassigning(true);
      await deleteAssignment(unassignTarget.id);
      setUnassignTarget(null);
    } finally {
      setIsUnassigning(false);
    }
  };

  // Group assignments by teacher
  const groupedByTeacher = teachers.map((teacher) => {
    const teacherAssignments = assignments.filter((a) => a.teacherId === teacher.id);
    const assignedSubjectDetails = teacherAssignments.map((a) => {
      const sub = subjects.find((s) => s.id === a.subjectId);
      return {
        assignmentId: a.id,
        subject: sub
      };
    });
    return {
      teacher,
      assignments: assignedSubjectDetails
    };
  }).filter((group) => group.assignments.length > 0);

  const flatAssignments = assignments.map((a) => {
    const teacher = teachers.find((t) => t.id === a.teacherId);
    const subject = subjects.find((s) => s.id === a.subjectId);
    return {
      id: a.id,
      teacher,
      subject
    };
  });

  const columns = [
    {
      key: 'teacher',
      header: 'FACULTY INSTRUCTOR',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: '#0284c7',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.85rem'
            }}
          >
            {row.teacher?.fullName.replace('Prof. ', '').replace('Dr. ', '').charAt(0) || 'T'}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontWeight: 700, color: 'var(--text-main)' }}>
              {row.teacher?.fullName || 'Unknown Faculty'}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
              {row.teacher?.teacherCode} • {row.teacher?.department}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'subject',
      header: 'CURRICULUM COURSE',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span
            style={{
              fontFamily: 'monospace',
              fontWeight: 700,
              fontSize: '0.8rem',
              padding: '0.25rem 0.55rem',
              background: '#fef3c7',
              color: '#d97706',
              borderRadius: '6px'
            }}
          >
            {row.subject?.code}
          </span>
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontWeight: 600 }}>{row.subject?.name}</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Semester {row.subject?.semester}
            </span>
          </div>
        </div>
      )
    },
    {
      key: 'department',
      header: 'DEPARTMENT',
      render: (row) => (
        <Badge variant="pill" size="sm">
          {row.subject?.department || row.teacher?.department}
        </Badge>
      )
    },
    {
      key: 'actions',
      header: 'ACTION',
      align: 'right',
      render: (row) => (
        <button
          type="button"
          onClick={() => setUnassignTarget(row)}
          style={{
            padding: '0.35rem 0.75rem',
            background: '#fef2f2',
            color: '#ef4444',
            border: '1px solid #fecaca',
            borderRadius: '6px',
            fontSize: '0.75rem',
            fontWeight: 700,
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.35rem',
            cursor: 'pointer',
            transition: 'all 0.15s ease'
          }}
        >
          <FiTrash2 size={13} />
          Unassign
        </button>
      )
    }
  ];

  return (
    <DashboardLayout
      title="Admin Dashboard"
      emoji="🛡️"
      welcomeLine="Welcome, System Administrator 👋 • SIAMS Central Management Console"
      navItems={ADMIN_NAV_ITEMS}
    >
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(340px, 480px) 1fr', gap: '2rem', alignItems: 'flex-start' }}>
        {/* Assign Subject Card matching Screenshot 5 */}
        <div
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-color)',
            borderRadius: '20px',
            boxShadow: 'var(--shadow-xl)',
            overflow: 'hidden'
          }}
        >
          <div style={{ height: '4px', width: '100%', background: 'var(--primary-gradient)' }} />

          <div style={{ padding: '2.25rem 2rem' }}>
            <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1.25rem' }}>
              <div
                style={{
                  width: 54,
                  height: 54,
                  borderRadius: '16px',
                  background: '#dcfce7',
                  color: '#16a34a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.6rem',
                  boxShadow: 'var(--shadow-sm)'
                }}
              >
                <HiOutlineLink />
              </div>
            </div>

            <div style={{ textAlign: 'center', marginBottom: '1.75rem' }}>
              <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                Assign Subject to Faculty
              </h2>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Map curriculum course subjects to authorized faculty teachers
              </p>
            </div>

            {formError && (
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: 'var(--status-danger-bg)',
                  border: '1px solid #fca5a5',
                  borderRadius: '10px',
                  color: 'var(--status-danger)',
                  fontSize: '0.8125rem',
                  marginBottom: '1.25rem'
                }}
              >
                {formError}
              </div>
            )}

            {formSuccess && (
              <div
                style={{
                  padding: '0.75rem 1rem',
                  backgroundColor: 'var(--status-success-bg)',
                  border: '1px solid #86efac',
                  borderRadius: '10px',
                  color: 'var(--status-success)',
                  fontSize: '0.8125rem',
                  marginBottom: '1.25rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}
              >
                <FiCheckCircle />
                <span>{formSuccess}</span>
              </div>
            )}

            <form onSubmit={handleAssign} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Select Faculty */}
              <div className="siams-form-group" style={{ margin: 0 }}>
                <label className="siams-label">Select Faculty Instructor</label>
                <div className="siams-input-wrapper">
                  <span className="siams-input-icon">
                    <FaChalkboardTeacher />
                  </span>
                  <select
                    className="siams-input has-icon"
                    value={selectedTeacherId}
                    onChange={(e) => {
                      setSelectedTeacherId(e.target.value);
                      setFormError('');
                    }}
                  >
                    <option value="">-- Choose Instructor --</option>
                    {teachers.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.fullName} ({t.teacherCode}) • {t.department}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Select Subject */}
              <div className="siams-form-group" style={{ margin: 0 }}>
                <label className="siams-label">Select Curriculum Subject</label>
                <div className="siams-input-wrapper">
                  <span className="siams-input-icon">
                    <FaBookOpen />
                  </span>
                  <select
                    className="siams-input has-icon"
                    value={selectedSubjectId}
                    onChange={(e) => {
                      setSelectedSubjectId(e.target.value);
                      setFormError('');
                    }}
                  >
                    <option value="">-- Choose Subject Course --</option>
                    {subjects.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.code} - {s.name} (Sem {s.semester})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Info Box matching Screenshot 5 */}
              <div
                style={{
                  background: 'var(--primary-light)',
                  border: '1px solid var(--primary-border)',
                  borderRadius: '12px',
                  padding: '0.85rem 1rem',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '0.65rem',
                  fontSize: '0.8125rem',
                  color: 'var(--primary-color)',
                  lineHeight: 1.45
                }}
              >
                <FiInfo size={17} style={{ flexShrink: 0, marginTop: '2px' }} />
                <span>
                  Once assigned, the subject will appear exclusively on the assigned teacher's dashboard.
                  Duplicate assignments are automatically prevented.
                </span>
              </div>

              {/* Green Assign Button matching Screenshot 5 */}
              <button
                type="submit"
                disabled={isSubmitting}
                style={{
                  background: '#059669',
                  color: '#ffffff',
                  padding: '0.85rem 1.25rem',
                  borderRadius: '12px',
                  fontWeight: 700,
                  fontSize: '0.9375rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 4px 14px rgba(5, 150, 105, 0.3)',
                  cursor: 'pointer',
                  border: 'none',
                  transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = '#047857')}
                onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = '#059669')}
              >
                <FiCheckCircle size={18} />
                <span>{isSubmitting ? 'Assigning...' : 'Assign Subject'}</span>
              </button>
            </form>

            <div
              style={{
                marginTop: '1.75rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '0.875rem'
              }}
            >
              <a
                href="#current-assignments"
                style={{
                  color: 'var(--primary-color)',
                  fontWeight: 700,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem'
                }}
              >
                <FiList size={16} />
                View All Assignments ({assignments.length})
              </a>

              <button
                type="button"
                onClick={() => navigate('/admin')}
                style={{
                  color: 'var(--text-muted)',
                  fontWeight: 600,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer'
                }}
              >
                <FiArrowLeft size={16} />
                Back to Dashboard
              </button>
            </div>
          </div>
        </div>

        {/* Grouped & Detailed Assignment Table */}
        <div id="current-assignments" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div
            style={{
              background: 'var(--bg-card)',
              border: '1px solid var(--border-color)',
              borderRadius: '16px',
              padding: '1.25rem 1.75rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
                Active Faculty-Subject Mappings
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                Current assignments across academic departments
              </p>
            </div>
            <Badge variant="pill" size="md">
              Total: {assignments.length} Mappings
            </Badge>
          </div>

          <DataTable
            columns={columns}
            data={flatAssignments}
            loading={loadingAssignments || loadingTeachers || loadingSubjects}
            emptyMessage="No course assignments found. Pick a teacher and subject to assign."
          />
        </div>
      </div>

      {/* Unassign Confirmation Dialog */}
      <ConfirmDialog
        isOpen={Boolean(unassignTarget)}
        onClose={() => setUnassignTarget(null)}
        onConfirm={handleUnassignConfirm}
        title="Unassign Curriculum Subject"
        message={`Are you sure you want to unassign "${unassignTarget?.subject?.code} - ${unassignTarget?.subject?.name}" from "${unassignTarget?.teacher?.fullName}"?`}
        confirmText="Yes, Unassign"
        isLoading={isUnassigning}
      />
    </DashboardLayout>
  );
};

export default SubjectAssignments;
