import React from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { ADMIN_NAV_ITEMS } from './adminNav';
import Card from '../../components/Card';
import { useStudents } from '../../hooks/useStudents';
import { useTeachers } from '../../hooks/useTeachers';
import { useSubjects } from '../../hooks/useSubjects';
import { useAssignments } from '../../hooks/useAssignments';

// Icons
import {
  FiLink,
  FiChevronRight,
  FiClipboard,
  FiUserPlus
} from 'react-icons/fi';
import {
  FaUserGraduate,
  FaChalkboardTeacher,
  FaBookOpen
} from 'react-icons/fa';
import {
  HiOutlineUserGroup,
  HiOutlineClipboardList
} from 'react-icons/hi';
import { IoFlaskOutline } from 'react-icons/io5';

const AdminHub = () => {
  const navigate = useNavigate();
  const { students, loading: loadingStudents } = useStudents();
  const { teachers, loading: loadingTeachers } = useTeachers();
  const { subjects, loading: loadingSubjects } = useSubjects();
  const { assignments, loading: loadingAssignments } = useAssignments();

  const operations = [
    {
      title: 'Manage Students',
      desc: 'View, search, edit, and delete student records',
      icon: <HiOutlineUserGroup />,
      bg: '#ede9fe',
      color: '#7c3aed',
      path: '/admin/students'
    },
    {
      title: 'Manage Teachers',
      desc: 'View, search, edit, and delete faculty members',
      icon: <FaChalkboardTeacher />,
      bg: '#e0f2fe',
      color: '#0284c7',
      path: '/admin/teachers'
    },
    {
      title: 'Manage Subjects',
      desc: 'Explore curriculum catalog, edit & delete courses',
      icon: <FaBookOpen />,
      bg: '#fef3c7',
      color: '#d97706',
      path: '/admin/subjects'
    },
    {
      title: 'View Assignments',
      desc: 'Inspect all teacher-subject mappings and manage links',
      icon: <HiOutlineClipboardList />,
      bg: '#dcfce7',
      color: '#16a34a',
      path: '/admin/assignments'
    },
    {
      title: 'Assign Subject',
      desc: 'Map curriculum subjects to designated instructors',
      icon: <FiLink />,
      bg: '#ccfbf1',
      color: '#0d9488',
      path: '/admin/assignments'
    },
    {
      title: 'Add Student',
      desc: 'Enroll a new student into the department',
      icon: <FiUserPlus />,
      bg: '#e0e7ff',
      color: '#4338ca',
      path: '/admin/students?add=true'
    },
    {
      title: 'Practical Sessions Log',
      desc: 'Monitor laboratory sessions & evaluations across all teachers',
      icon: <IoFlaskOutline />,
      bg: '#f3e8ff',
      color: '#9333ea',
      path: '/admin/practical-sessions'
    },
    {
      title: 'Attendance & 75% Eligibility',
      desc: 'Track lab attendance, 75% eligibility, & required makeup',
      icon: <FiClipboard />,
      bg: '#e0f2fe',
      color: '#0369a1',
      path: '/admin/roster'
    }
  ];

  return (
    <DashboardLayout
      title="Admin Dashboard"
      emoji="🛡️"
      welcomeLine="Welcome, System Administrator 👋 • SIAMS Central Management Console"
      navItems={ADMIN_NAV_ITEMS}
    >
      {/* 4 Metric Cards from live data */}
      <div className="metrics-row">
        <Card padding="none" hoverEffect onClick={() => navigate('/admin/students')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">TOTAL STUDENTS</span>
              <span className="metric-number">
                {loadingStudents ? '...' : students.length}
              </span>
              <span className="metric-subtext">Enrolled roster</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#ede9fe', color: '#7c3aed' }}>
              <FaUserGraduate />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect onClick={() => navigate('/admin/teachers')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">TOTAL TEACHERS</span>
              <span className="metric-number">
                {loadingTeachers ? '...' : teachers.length}
              </span>
              <span className="metric-subtext">Academic faculty</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#e0f2fe', color: '#0284c7' }}>
              <FaChalkboardTeacher />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect onClick={() => navigate('/admin/subjects')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">TOTAL SUBJECTS</span>
              <span className="metric-number">
                {loadingSubjects ? '...' : subjects.length}
              </span>
              <span className="metric-subtext">Curriculum courses</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#fef3c7', color: '#d97706' }}>
              <FaBookOpen />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect onClick={() => navigate('/admin/assignments')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">ACTIVE ASSIGNMENTS</span>
              <span className="metric-number">
                {loadingAssignments ? '...' : assignments.length}
              </span>
              <span className="metric-subtext">Teacher ↔ Subject links</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#dcfce7', color: '#16a34a' }}>
              <FiLink />
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Management Operations Grid */}
      <section style={{ marginTop: '0.5rem' }}>
        <div className="operations-section-header">
          <span style={{ color: '#f59e0b' }}>⚡</span>
          <span>Quick Management Operations</span>
        </div>

        <div className="operations-grid">
          {operations.map((op, idx) => (
            <Card key={idx} padding="none" hoverEffect onClick={() => navigate(op.path)}>
              <div className="operation-card">
                <div className="operation-card-left">
                  <div className="operation-icon-box" style={{ background: op.bg, color: op.color }}>
                    {op.icon}
                  </div>
                  <div className="operation-details">
                    <span className="operation-title">{op.title}</span>
                    <span className="operation-desc">{op.desc}</span>
                  </div>
                </div>
                <FiChevronRight className="operation-arrow" />
              </div>
            </Card>
          ))}
        </div>
      </section>
    </DashboardLayout>
  );
};

export default AdminHub;
