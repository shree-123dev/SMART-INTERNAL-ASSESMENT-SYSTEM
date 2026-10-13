import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { ADMIN_NAV_ITEMS } from './adminNav';
import DataTable from '../../components/DataTable';
import ConfirmDialog from '../../components/ConfirmDialog';
import Modal from '../../components/Modal';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Badge from '../../components/Badge';
import { useStudents } from '../../hooks/useStudents';
import { QRCodeCanvas } from 'qrcode.react';

// Icons
import {
  FiSearch,
  FiPlus,
  FiArrowLeft,
  FiEdit,
  FiTrash2,
  FiEye,
  FiMail,
  FiDownload,
  FiPrinter
} from 'react-icons/fi';
import { FaGraduationCap } from 'react-icons/fa';
import { IoQrCodeOutline } from 'react-icons/io5';

const ManageStudents = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { students, loading, addStudent, updateStudent, deleteStudent } = useStudents();

  // Search and filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDepartment, setFilterDepartment] = useState('ALL');
  const [filterSemester, setFilterSemester] = useState('ALL');

  // Modals state
  const [formModalOpen, setFormModalOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [formData, setFormData] = useState({
    usn: '',
    fullName: '',
    email: '',
    department: 'CSE',
    semester: 4,
    section: 'A'
  });
  const [formErrors, setFormErrors] = useState({});

  // View detail modal
  const [viewModalStudent, setViewModalStudent] = useState(null);

  // QR Modal
  const [qrModalStudent, setQrModalStudent] = useState(null);

  // Delete confirm dialog
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // Open Add modal if ?add=true in URL
  useEffect(() => {
    if (searchParams.get('add') === 'true') {
      openAddModal();
    }
  }, [searchParams]);

  const openAddModal = () => {
    setEditingStudent(null);
    setFormData({
      usn: '',
      fullName: '',
      email: '',
      department: 'CSE',
      semester: 4,
      section: 'A'
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const openEditModal = (student) => {
    setEditingStudent(student);
    setFormData({
      usn: student.usn,
      fullName: student.fullName,
      email: student.email,
      department: student.department,
      semester: student.semester,
      section: student.section
    });
    setFormErrors({});
    setFormModalOpen(true);
  };

  const validateForm = () => {
    const errors = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const usnRegex = /^[A-Z0-9]+$/;

    const usnVal = formData.usn.trim().toUpperCase();
    if (!usnVal) {
      errors.usn = 'USN is required';
    } else if (!usnRegex.test(usnVal)) {
      errors.usn = 'USN must be alphanumeric without spaces';
    }

    if (!formData.fullName.trim()) {
      errors.fullName = 'Full Name is required';
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
      if (editingStudent) {
        await updateStudent(editingStudent.id, formData);
      } else {
        await addStudent(formData);
      }
      setFormModalOpen(false);
    } catch (err) {
      setFormErrors((prev) => ({ ...prev, usn: err.message }));
    }
  };

  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return;
    try {
      setIsDeleting(true);
      await deleteStudent(deleteTarget.id);
      setDeleteTarget(null);
    } finally {
      setIsDeleting(false);
    }
  };

  const downloadQrCode = () => {
    const canvas = document.getElementById('student-qr-canvas');
    if (!canvas) return;
    const pngUrl = canvas.toDataURL('image/png');
    const downloadLink = document.createElement('a');
    downloadLink.href = pngUrl;
    downloadLink.download = `QR_${qrModalStudent?.usn || 'PASS'}.png`;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
  };

  // Filtered students
  const filteredStudents = students.filter((s) => {
    const matchesSearch =
      s.usn.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.fullName.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      s.department.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesDept =
      filterDepartment === 'ALL' || s.department.toLowerCase() === filterDepartment.toLowerCase();

    const matchesSem =
      filterSemester === 'ALL' || String(s.semester) === String(filterSemester);

    return matchesSearch && matchesDept && matchesSem;
  });

  const columns = [
    {
      key: 'usn',
      header: 'USN',
      render: (row) => (
        <span
          style={{
            fontFamily: 'monospace',
            fontWeight: 700,
            fontSize: '0.85rem',
            padding: '0.3rem 0.65rem',
            background: '#e0e7ff',
            color: '#3730a3',
            borderRadius: '6px'
          }}
        >
          {row.usn}
        </span>
      )
    },
    {
      key: 'fullName',
      header: 'Full Name',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: '50%',
              background: '#2563eb',
              color: '#ffffff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 700,
              fontSize: '0.85rem',
              flexShrink: 0
            }}
          >
            {row.fullName.charAt(0).toUpperCase()}
          </div>
          <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{row.fullName}</span>
        </div>
      )
    },
    {
      key: 'email',
      header: 'Email',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', color: 'var(--text-muted)' }}>
          <FiMail size={14} />
          <span>{row.email}</span>
        </div>
      )
    },
    {
      key: 'department',
      header: 'Department',
      render: (row) => <span style={{ fontWeight: 600 }}>{row.department}</span>
    },
    {
      key: 'semSec',
      header: 'Sem / Sec',
      render: (row) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem', alignItems: 'flex-start' }}>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '0.15rem 0.5rem',
              background: '#fef3c7',
              color: '#d97706',
              borderRadius: '4px'
            }}
          >
            Sem {row.semester}
          </span>
          <span
            style={{
              fontSize: '0.7rem',
              fontWeight: 700,
              padding: '0.15rem 0.5rem',
              background: '#dcfce7',
              color: '#16a34a',
              borderRadius: '4px'
            }}
          >
            Sec {row.section}
          </span>
        </div>
      )
    },
    {
      key: 'qrPass',
      header: 'QR Pass',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <button
            type="button"
            onClick={() => setQrModalStudent(row)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.35rem 0.65rem',
              background: '#eff6ff',
              color: '#2563eb',
              border: '1px solid #bfdbfe',
              borderRadius: '6px',
              fontSize: '0.75rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            <IoQrCodeOutline size={14} />
            View QR
          </button>
          <button
            type="button"
            onClick={() => setQrModalStudent(row)}
            title="Print Pass"
            style={{
              padding: '0.35rem 0.5rem',
              background: 'var(--bg-secondary)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              cursor: 'pointer'
            }}
          >
            <FiPrinter size={13} />
          </button>
        </div>
      )
    },
    {
      key: 'actions',
      header: 'Actions',
      align: 'right',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '0.4rem' }}>
          <button
            type="button"
            onClick={() => setViewModalStudent(row)}
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
      {/* Top Banner Card matching Screenshot 2 */}
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
              background: '#eff6ff',
              color: '#2563eb',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '1.6rem',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            <FaGraduationCap />
          </div>
          <div>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
              Student Management Directory
            </h2>
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
              Search, inspect, edit, and manage all enrolled students & QR passes
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <Badge variant="pill" size="md">
            👥 Total: {students.length} Students
          </Badge>
          <Button variant="primary" icon={<FiPlus />} onClick={openAddModal}>
            Add Student
          </Button>
          <Button variant="secondary" icon={<FiArrowLeft />} onClick={() => navigate('/admin')}>
            Admin Dashboard
          </Button>
        </div>
      </div>

      {/* Search and Filters Bar matching Screenshot 2 */}
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
              placeholder="Search students by USN, Name, Email, or Department..."
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

          {/* Department Filter */}
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
            <option value="ISE">ISE</option>
            <option value="ECE">ECE</option>
          </select>

          {/* Semester Filter */}
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
          ℹ️ Showing {filteredStudents.length} records
        </span>
      </div>

      {/* DataTable */}
      <DataTable
        columns={columns}
        data={filteredStudents}
        loading={loading}
        emptyMessage="No students found matching your search criteria."
      />

      {/* Add / Edit Student Modal */}
      <Modal
        isOpen={formModalOpen}
        onClose={() => setFormModalOpen(false)}
        title={editingStudent ? 'Edit Student Record' : 'Add New Student'}
        size="md"
      >
        <form onSubmit={handleFormSubmit} noValidate style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <Input
            label="University Seat Number (USN)"
            name="usn"
            placeholder="e.g. 1MS24CS001"
            value={formData.usn}
            onChange={(e) => setFormData({ ...formData, usn: e.target.value.toUpperCase() })}
            error={formErrors.usn}
            helperText="Uppercase alphanumeric format only"
            required
          />

          <Input
            label="Full Name"
            name="fullName"
            placeholder="e.g. Alice Student"
            value={formData.fullName}
            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
            error={formErrors.fullName}
            required
          />

          <Input
            label="Institutional Email"
            name="email"
            type="email"
            placeholder="e.g. student@test.com"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            error={formErrors.email}
            required
          />

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '1rem' }}>
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
                <option value="ECE">ECE</option>
              </select>
            </div>

            <div className="siams-form-group">
              <label className="siams-label">Semester *</label>
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

            <div className="siams-form-group">
              <label className="siams-label">Section *</label>
              <select
                value={formData.section}
                onChange={(e) => setFormData({ ...formData, section: e.target.value })}
                className="siams-input"
              >
                <option value="A">Sec A</option>
                <option value="B">Sec B</option>
                <option value="C">Sec C</option>
                <option value="D">Sec D</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '1rem' }}>
            <Button variant="secondary" onClick={() => setFormModalOpen(false)}>
              Cancel
            </Button>
            <Button variant="primary" type="submit">
              {editingStudent ? 'Save Changes' : 'Enroll Student'}
            </Button>
          </div>
        </form>
      </Modal>

      {/* QR Code Pass Modal */}
      <Modal
        isOpen={Boolean(qrModalStudent)}
        onClose={() => setQrModalStudent(null)}
        title="Student Digital QR Attendance Pass"
        size="sm"
      >
        {qrModalStudent && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '1.25rem' }}>
            <div
              style={{
                padding: '1.25rem',
                background: '#ffffff',
                borderRadius: '16px',
                boxShadow: '0 4px 16px rgba(0,0,0,0.08)',
                border: '1px solid #e2e8f0'
              }}
            >
              <QRCodeCanvas
                id="student-qr-canvas"
                value={qrModalStudent.usn}
                size={200}
                level="H"
                fgColor="#0f172a"
                bgColor="#ffffff"
              />
            </div>

            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                {qrModalStudent.fullName}
              </h3>
              <p style={{ fontFamily: 'monospace', fontWeight: 700, color: '#2563eb', fontSize: '1rem', marginTop: '0.2rem' }}>
                {qrModalStudent.usn}
              </p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                {qrModalStudent.department} • Semester {qrModalStudent.semester} ({qrModalStudent.section})
              </p>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
              <Button
                variant="primary"
                fullWidth
                icon={<FiDownload />}
                onClick={downloadQrCode}
              >
                Download PNG
              </Button>
              <Button
                variant="secondary"
                fullWidth
                icon={<FiPrinter />}
                onClick={() => window.print()}
              >
                Print Pass
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* View Details Modal */}
      <Modal
        isOpen={Boolean(viewModalStudent)}
        onClose={() => setViewModalStudent(null)}
        title="Student Profile Overview"
        size="sm"
      >
        {viewModalStudent && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', paddingBottom: '1rem', borderBottom: '1px solid var(--border-color)' }}>
              <div
                style={{
                  width: 50,
                  height: 50,
                  borderRadius: '50%',
                  background: '#2563eb',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 800
                }}
              >
                {viewModalStudent.fullName.charAt(0)}
              </div>
              <div>
                <h4 style={{ fontSize: '1.15rem', fontWeight: 800 }}>{viewModalStudent.fullName}</h4>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>{viewModalStudent.email}</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem', fontSize: '0.875rem' }}>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>USN</span>
                <p style={{ fontWeight: 700, fontFamily: 'monospace' }}>{viewModalStudent.usn}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Department</span>
                <p style={{ fontWeight: 700 }}>{viewModalStudent.department}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Semester</span>
                <p style={{ fontWeight: 700 }}>Semester {viewModalStudent.semester}</p>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Section</span>
                <p style={{ fontWeight: 700 }}>Section {viewModalStudent.section}</p>
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <Button variant="secondary" onClick={() => setViewModalStudent(null)}>Close</Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm Dialog */}
      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Student Record"
        message={`Are you sure you want to remove student "${deleteTarget?.fullName}" (${deleteTarget?.usn})?`}
        confirmText="Yes, Delete"
        isLoading={isDeleting}
      />
    </DashboardLayout>
  );
};

export default ManageStudents;
