import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { ADMIN_NAV_ITEMS } from './adminNav';
import DataTable from '../../components/DataTable';
import ConfirmDialog from '../../components/ConfirmDialog';
import Modal from '../../components/Modal';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Badge from '../../components/Badge';
import { useSubjects } from '../../hooks/useSubjects';
import { useAssignments } from '../../hooks/useAssignments';
import { useTeachers } from '../../hooks/useTeachers';

// Icons
import {
  FiSearch,
  FiPlus,
  FiArrowLeft,
  FiEdit,
  FiTrash2,
  FiEye
} from 'react-icons/fi';
import { FaBookOpen } from 'react-icons/fa';

const ManageSubjects = () => {
  const navigate = useNavigate();
  const { subjects, loading, addSubject, updateSubject, deleteSubject } = useSubjects();
  const { assignments } = useAssignments();
  const { teachers } = useTeachers();

  // Search & filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('ALL');
  const [filterSemester, setFilterSemester] = useState('ALL');

  // Modals state
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [editingSubject, setEditingSubject] = useState(null);
  const [formData, setFormData] = useState({
    code: '',
    name: '',
    department: 'CSE',
    semester: 4
  });
  const [formErrors, setFormErrors] = useState({});

  // View modal
  const [viewModalSubject, setViewModalSubject] = useState(null);

  // Delete confirm dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const openAddModal = () => {
    setEditingSubject(null);
    setFormData({
      code: '',
      name: '',
      department: 'CSE',
      semester: 4
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const openEditModal = (subject) => {
    setEditingSubject(subject);
    setFormData({
      code: subject.code,
      name: subject.name,
      department: subject.department,
      semester: subject.semester
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const validateForm = () => {
    const errors = {};
    const codeVal = formData.code.trim().toUpperCase();
    const sem = Number(formData.semester);

    if (!codeVal) {
      errors.code = 'Subject Code is required';
    }

    if (!formData.name.trim()) {
      errors.name = 'Subject Name is required';
    }

    if (!sem || sem < 1 || sem > 8) {
      errors.semester = 'Semester must be between 1 and 8';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      if (editingSubject) {
        await updateSubject(editingSubject.id, formData);
      } else {
        await addSubject(formData);
      }
      setFormModalOpen(false);
    } catch (err) {
      setFormErrors((prev) => ({ ...prev, code: err.message }));
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      await deleteSubject(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // Get assigned teachers for a subject
  const getSubjectTeachers = (subjectId) => {
    const subjectAssignments = assignments.filter((a) => a.subjectId === subjectId);
    return subjectAssignments
      .map((a) => {
        const t = teachers.find((tch) => tch.id === a.teacherId);
        return t ? `${t.fullName} (${t.teacherCode})` : null;
      })
      .filter(Boolean);
  };

  const filteredSubjects = subjects.filter((s) => {
    const matchesSearch =
      s.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.department.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDept =
      filterDepartment === 'ALL' || s.department.toLowerCase() === filterDepartment.toLowerCase();

    const matchesSem =
      filterSemester === 'ALL' || String(s.semester) === String(filterSemester);

    return matchesSearch && matchesDept && matchesSem;
  });

  const columns = [
    {
      key: 'code',
      header: 'SUBJECT CODE',
      render: (row) => (
        <span
          style={{
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: '0.85rem',
            padding: '0.3rem 0.65rem',
            background: '#fef3c7',
            color: '#d97706',
            borderRadius: '6px'
          }}
        >
          {row.code}
        </span>
      )
    },
    {
      key: 'name',
      header: 'SUBJECT NAME',
      render: (row) => (
        <span style={{ fontWeight: 700, color: 'var(--text-main)' }}>{row.name}</span>
      )
    },
    {
      key: 'department',
      header: 'DEPARTMENT',
      render: (row) => <span style={{ fontWeight: 600 }}>{row.department}</span>
    },
    {
      key: 'semester',
      header: 'SEMESTER',
      render: (row) => (
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '0.25rem 0.65rem',
            background: '#fef3c7',
            color: '#d97706',
            borderRadius: '9999px'
          }}
        >
          Semester {row.semester}
        </span>
      )
    },
    {
      key: 'assignedTeachers',
      header: 'ASSIGNED TEACHERS',
      render: (row) => {
        const assignedTeachers = getSubjectTeachers(row.id);
        if (assignedTeachers.length === 0) {
          return <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', fontStyle: 'italic' }}>Unassigned</span>;
        }
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem', alignItems: 'flex-start' }}>
            {assignedTeachers.map((tName, i) => (
              <span
                key={i}
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  padding: '0.2rem 0.55rem',
                  background: '#eff6ff',
                  color: '#2563eb',
                  borderRadius: '6px'
                }}
              >
                {tName}
              </span>
            ))}
          </div>
        );
      }
    },
    {
      key: 'actions',
      header: 'ACTIONS',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}>
          <button
            type="button"
            onClick={() => setViewModalSubject(row)}
            title="View Details"
            style={{
              padding: '0.35rem 0.65rem',
              background: '#eff6ff',
              color: '#2563eb',
              border: '1px solid #bfdbfe',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              cursor: 'pointer'
            }}
          >
            <FiEye size={13} /> View
          </button>
          <button
            type="button"
            onClick={() => openEditModal(row)}
            title="Edit"
            style={{
              padding: '0.35rem 0.65rem',
              background: '#f0fdf4',
              color: '#16a34a',
              border: '1px solid #bbf7d0',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              cursor: 'pointer'
            }}
          >
            <FiEdit size={13} /> Edit
          </button>
          <button
            type="button"
            onClick={() => setDeleteTarget(row)}
            title="Delete"
            style={{
              padding: '0.35rem 0.65rem',
              background: '#fef2f2',
              color: '#ef4444',
              border: '1px solid #fecaca',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 600,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.25rem',
              cursor: 'pointer'
            }}
          >
            <FiTrash2 size={13} /> Delete
          </button>
        </div>
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
      {/* Top Banner Card matching Screenshot 4 */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          padding: '1.5rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1.25rem',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: '14px',
              background: '#fef3c7',
              color: '#d97706',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <FaBookOpen />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              Course & Subject Catalog
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Manage academic curriculum, theory subjects, and laboratory modules
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Badge variant="pill" size="md">
            📖 Total: {subjects.length} Subjects
          </Badge>
          <Button variant="primary" icon={<FiPlus />} onClick={openAddModal}>
            Add Subject
          </Button>
          <Button variant="secondary" icon={<FiArrowLeft />} onClick={() => navigate('/admin')}>
            Admin Dashboard
          </Button>
        </div>
      </div>

      {/* Search and Filters Bar */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          padding: '1rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
          boxShadow: 'var(--shadow-sm)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flex: 1, minWidth: '320px' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <FiSearch
              style={{
                position: 'absolute',
                left: '1rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-dim)',
                fontSize: '1.1rem'
              }}
            />
            <input
              type="text"
              placeholder="Search subjects by Code, Subject Name, or Department..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{
                width: '100%',
                padding: '0.75rem 1rem 0.75rem 2.75rem',
                border: '1.5px solid var(--border-color)',
                borderRadius: '12px',
                background: 'var(--bg-input)',
                color: 'var(--text-main)',
                fontSize: '0.875rem',
                outline: 'none'
              }}
            />
          </div>

          <Button variant="primary" size="md" onClick={() => {}}>
            Search
          </Button>

          <select
            value={filterDepartment}
            onChange={(e) => setFilterDepartment(e.target.value)}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '12px',
              border: '1.5px solid var(--border-color)',
              background: 'var(--bg-input)',
              color: 'var(--text-main)',
              fontSize: '0.875rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Departments</option>
            <option value="CSE">CSE</option>
            <option value="Computer Science">Computer Science</option>
            <option value="Information Science">Information Science</option>
          </select>

          <select
            value={filterSemester}
            onChange={(e) => setFilterSemester(e.target.value)}
            style={{
              padding: '0.75rem 1rem',
              borderRadius: '12px',
              border: '1.5px solid var(--border-color)',
              background: 'var(--bg-input)',
              color: 'var(--text-main)',
              fontSize: '0.875rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            <option value="ALL">All Semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
              <option key={sem} value={sem}>
                Semester {sem}
              </option>
            ))}
          </select>
        </div>

        <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          ℹ️ Showing {filteredSubjects.length} catalog subjects
        </span>
      </div>

      {/* DataTable */}
      <DataTable
        columns={columns}
        data={filteredSubjects}
        loading={loading}
        emptyMessage="No subjects found matching your search criteria."
      />

      {/* Add / Edit Subject Modal */}
      <Modal
        isOpen={formModalOpen}
        onClose={() => setFormModalOpen(false)}
        title={editingSubject ? 'Edit Subject Details' : 'Add New Curriculum Subject'}
        size="md"
      >
        <form onSubmit={handleFormSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Input
            label="Subject Code"
            name="code"
            placeholder="e.g. CS601 or CSL607"
            value={formData.code}
            onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
            error={formErrors.code}
            required
          />

          <Input
            label="Subject Title / Name"
            name="name"
            placeholder="e.g. Machine Learning Principles"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            error={formErrors.name}
            required
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="siams-form-group">
              <label className="siams-label">Department *</label>
              <select
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="siams-input"
              >
                <option value="CSE">CSE</option>
                <option value="Computer Science">Computer Science</option>
                <option value="Information Science">Information Science</option>
              </select>
            </div>

            <div className="siams-form-group">
              <label className="siams-label">Semester (1-8) *</label>
              <select
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: Number(e.target.value) })}
                className="siams-input"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => setFormModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingSubject ? 'Save Changes' : 'Create Subject'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* View Subject Modal */}
      <Modal
        isOpen={Boolean(viewModalSubject)}
        onClose={() => setViewModalSubject(null)}
        title="Subject Syllabus Details"
        size="sm"
      >
        {viewModalSubject && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '12px',
                  background: '#fef3c7',
                  color: '#d97706',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 800
                }}
              >
                <FaBookOpen />
              </div>
              <div>
                <h4 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{viewModalSubject.name}</h4>
                <p style={{ color: '#d97706', fontWeight: 700, fontFamily: 'monospace' }}>{viewModalSubject.code}</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.875rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Department</span>
                <p style={{ fontWeight: 700 }}>{viewModalSubject.department}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Semester</span>
                <p style={{ fontWeight: 700 }}>Semester {viewModalSubject.semester}</p>
              </div>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Faculty Assigned</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', marginTop: '0.35rem' }}>
                {getSubjectTeachers(viewModalSubject.id).length === 0 ? (
                  <span style={{ color: 'var(--text-muted)', fontStyle: 'italic', fontSize: '0.85rem' }}>No instructors assigned currently</span>
                ) : (
                  getSubjectTeachers(viewModalSubject.id).map((t, i) => (
                    <Badge key={i} variant="primary" size="sm">{t}</Badge>
                  ))
                )}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <Button variant="secondary" onClick={() => setViewModalSubject(null)}>Close</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Subject Record"
        message={`Are you sure you want to remove "${deleteTarget?.name}" (${deleteTarget?.code})? All teacher assignments for this subject will also be unassigned.`}
        confirmText="Yes, Delete"
        isLoading={isDeleting}
      />
    </DashboardLayout>
  );
};

export default ManageSubjects;
