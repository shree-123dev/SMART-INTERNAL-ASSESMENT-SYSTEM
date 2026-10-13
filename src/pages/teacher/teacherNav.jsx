import React from 'react';
import { FiGrid, FiBook, FiCheckCircle } from 'react-icons/fi';
import { IoQrCodeOutline } from 'react-icons/io5';
import { FaFlask } from 'react-icons/fa';

export const TEACHER_NAV_ITEMS = [
  { label: 'Faculty Hub', path: '/teacher', icon: <FiGrid /> },
  { label: 'QR Attendance', path: '/teacher/qr', icon: <IoQrCodeOutline /> },
  { label: 'My Classes', path: '/teacher/classes', icon: <FiBook /> },
  { label: 'CIE Marks Entry', path: '/teacher/cie', icon: <FiCheckCircle /> },
  { label: 'Lab Evaluation', path: '/teacher/lab', icon: <FaFlask /> }
];
