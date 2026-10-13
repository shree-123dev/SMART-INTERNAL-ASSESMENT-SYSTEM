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
import { useTeachers } from '../../hooks/useTeachers';
import { useAssignments } from '../../hooks/useAssignments';
import { useSubjects } from '../../hooks/useSubjects';

// Icons
import {
  FiSearch,
  FiPlus,
  FiArrowLeft,
  FiEdit,
  FiTrash2,
  FiEye,
  FiMail
} from 'react-icons/fi';
import { FaChalkboardTeacher } from 'react-icons/fa';

const ManageTeachers = () => {
  const navigate = useNavigate();
  const { teachers, loading, addTeacher, updateTeacher, deleteTeacher } = useTeachers();
  const { assignments } = useAssignments();
  const { subjects } = useSubjects();

  // Search & filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('ALL');

  // Modals state
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [editingTeacher, setEditingTeacher] = useState(null);
  const [formData, setFormData] = useState({
    teacherCode: '',
    fullName: '',
    email: '',
    department: 'CSE'
  });
  const [formErrors, setFormErrors] = useState({});

  // View modal
  const [viewModalTeacher, setViewModalTeacher] = useState(null);

  // Delete confirm dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const openAddModal = () => {
    setEditingTeacher(null);
    setFormData({
      teacherCode: '',
      fullName: '',
      email: '',
      department: 'CSE'
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const openEditModal = (teacher) => {
    setEditingTeacher(teacher);
    setFormData({
      teacherCode: teacher.teacherCode,
      fullName: teacher.fullName,
      email: teacher.email,
      department: teacher.department
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    if (!formData.teacherCode.trim()) {
      errors.teacherCode = 'Teacher ID/Code is required';
    }

    if (!formData.fullName.trim()) {
      errors.fullName = 'Faculty Name is required';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email address is required';
    } else if (!emailRegex.test(formData.email.trim())) {
      errors.email = 'Enter a valid institutional email';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleFormSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      if (editingTeacher) {
        await updateTeacher(editingTeacher.id, formData);
      } else {
        await addTeacher(formData);
      }
      setFormModalOpen(false);
    } catch (err) {
      setFormErrors((prev) => ({ ...prev, teacherCode: err.message }));
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      await deleteTeacher(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  // Get assigned subject codes for a teacher
  const getTeacherSubjects = (teacherId) => {
    const teacherAssignments = assignments.filter((a) => a.teacherId === teacherId);
    return teacherAssignments
      .map((a) => {
        const sub = subjects.find((s) => s.id === a.subjectId);
        return sub ? sub.code : null;
      })
      .filter(Boolean);
  };

  const filteredTeachers = teachers.filter((t) => {
    const matchesSearch =
      t.teacherCode.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.department.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDept =
      filterDepartment === 'ALL' || t.department.toLowerCase() === filterDepartment.toLowerCase();

    return matchesSearch && matchesDept;
  });

  const columns = [
    {
      key: 'teacherCode',
      header: 'TEACHER ID',
      render: (row) => (
        <span
          style={{
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: '0.85rem',
            padding: '0.3rem 0.65rem',
            background: '#e0f2fe',
            color: '#0284c7',
            borderRadius: '6px'
          }}
        >
          {row.teacherCode}
        </span>
      )
    },
    {
      key: 'fullName',
      header: 'FACULTY NAME',
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
              fontSize: '0.85rem',
              flexShrink: 0
            }}
          >
            {row.fullName.replace('Prof. ', '').replace('Dr. ', '').charAt(0).toUpperCase()}
          </div>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{row.fullName}</span>
        </div>
      )
    },
    {
      key: 'email',
      header: 'INSTITUTIONAL EMAIL',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-muted)' }}>
          <FiMail size={14} />
          <span>{row.email}</span>
        </div>
      )
    },
    {
      key: 'department',
      header: 'DEPARTMENT',
      render: (row) => (
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            padding: '0.25rem 0.65rem',
            background: '#ede9fe',
            color: '#7c3aed',
            borderRadius: '9999px'
          }}
        >
          {row.department}
        </span>
      )
    },
    {
      key: 'assignedCourses',
      header: 'ASSIGNED COURSES',
      render: (row) => {
        const assignedCodes = getTeacherSubjects(row.id);
        if (assignedCodes.length === 0) {
          return <span style={{ color: 'var(--text-dim)', fontSize: '0.8rem', fontStyle: 'italic' }}>Unassigned</span>;
        }
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
            {assignedCodes.map((c, i) => (
              <span
                key={i}
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.55rem',
                  background: '#dcfce7',
                  color: '#16a34a',
                  borderRadius: '6px'
                }}
              >
                {c}
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
            onClick={() => setViewModalTeacher(row)}
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
      {/* Top Banner Card matching Screenshot 3 */}
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
              background: '#e0f2fe',
              color: '#0284c7',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <FaChalkboardTeacher />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              Faculty & Teacher Directory
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Manage academic staff, instructors, and departmental course loads
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Badge variant="pill" size="md">
            👥 Total: {teachers.length} Faculty
          </Badge>
          <Button variant="primary" icon={<FiPlus />} onClick={openAddModal}>
            Add Faculty
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
              placeholder="Search faculty by Teacher ID, Name, Email, or Department..."
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
            <option value="ISE">ISE</option>
          </select>
        </div>

        <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', fontWeight: 600 }}>
          ℹ️ Showing {filteredTeachers.length} faculty records
        </span>
      </div>

      {/* DataTable */}
      <DataTable
        columns={columns}
        data={filteredTeachers}
        loading={loading}
        emptyMessage="No faculty records found matching your search criteria."
      />

      {/* Add / Edit Faculty Modal */}
      <Modal
        isOpen={formModalOpen}
        onClose={() => setFormModalOpen(false)}
        title={editingTeacher ? 'Edit Faculty Record' : 'Add New Faculty Member'}
        size="md"
      >
        <form onSubmit={handleFormSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Input
            label="Teacher ID / Code"
            name="teacherCode"
            placeholder="e.g. T008 or TCH_CS"
            value={formData.teacherCode}
            onChange={(e) => setFormData({ ...formData, teacherCode: e.target.value })}
            error={formErrors.teacherCode}
            required
          />

          <Input
            label="Faculty Full Name"
            name="fullName"
            placeholder="e.g. Prof. Grace Hopper"
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            error={formErrors.fullName}
            required
          />

          <Input
            label="Institutional Email"
            name="email"
            type="email"
            placeholder="e.g. grace.hopper@college.edu"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={formErrors.email}
            required
          />

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
              <option value="ISE">ISE</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => setFormModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingTeacher ? 'Save Changes' : 'Add Faculty'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* View Faculty Details Modal */}
      <Modal
        isOpen={Boolean(viewModalTeacher)}
        onClose={() => setViewModalTeacher(null)}
        title="Faculty Member Profile"
        size="sm"
      >
        {viewModalTeacher && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  background: '#0284c7',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 800
                }}
              >
                {viewModalTeacher.fullName.charAt(0)}
              </div>
              <div>
                <h4 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{viewModalTeacher.fullName}</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{viewModalTeacher.email}</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.875rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Teacher ID</span>
                <p style={{ fontWeight: 700, fontFamily: 'monospace' }}>{viewModalTeacher.teacherCode}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Department</span>
                <p style={{ fontWeight: 700 }}>{viewModalTeacher.department}</p>
              </div>
            </div>

            <div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Assigned Courses</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem', marginTop: '0.35rem' }}>
                {getTeacherSubjects(viewModalTeacher.id).map((c, i) => (
                  <Badge key={i} variant="success" size="sm">{c}</Badge>
                ))}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <Button variant="secondary" onClick={() => setViewModalTeacher(null)}>Close</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Faculty Record"
        message={`Are you sure you want to remove "${deleteTarget?.fullName}"? All course assignments linked to this faculty member will also be unassigned.`}
        confirmText="Yes, Delete"
        isLoading={isDeleting}
      />
    </DashboardLayout>
  );
};

export default ManageTeachers;
