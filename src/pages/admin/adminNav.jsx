import React from 'react';
import {
  FiGrid,
  FiLink,
  FiClipboard,
  FiFileText
} from 'react-icons/fi';
import {
  FaUserGraduate,
  FaChalkboardTeacher,
  FaBookOpen,
  FaFlask,
  FaAward
} from 'react-icons/fa';

export const ADMIN_NAV_ITEMS = [
  { label: 'Admin Hub', path: '/admin', icon: <FiGrid /> },
  { label: 'Manage Students', path: '/admin/students', icon: <FaUserGraduate /> },
  { label: 'Manage Teachers', path: '/admin/teachers', icon: <FaChalkboardTeacher /> },
  { label: 'Manage Subjects', path: '/admin/subjects', icon: <FaBookOpen /> },
  { label: 'Subject Assignments', path: '/admin/assignments', icon: <FiLink /> },
  { label: 'Attendance Roster', path: '/admin/roster', icon: <FiClipboard /> },
  { label: 'CIE Master Summary', path: '/admin/cie-summary', icon: <FiFileText /> },
  { label: 'Practical Sessions', path: '/admin/practical-sessions', icon: <FaFlask /> },
  { label: 'Academic Marks', path: '/admin/academic-marks', icon: <FaAward /> }
];
