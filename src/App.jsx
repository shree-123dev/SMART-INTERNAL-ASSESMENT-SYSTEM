import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';

// Public Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';

// Admin Pages
import AdminHub from './pages/admin/AdminHub';
import ManageStudents from './pages/admin/ManageStudents';
import ManageTeachers from './pages/admin/ManageTeachers';
import ManageSubjects from './pages/admin/ManageSubjects';
import SubjectAssignments from './pages/admin/SubjectAssignments';
import ComingSoonPage from './pages/admin/ComingSoonPage';

// Teacher Portal Pages
import FacultyHub from './pages/teacher/FacultyHub';
import QrAttendance from './pages/teacher/QrAttendance';
import MyClasses from './pages/teacher/MyClasses';
import CieMarksEntry from './pages/teacher/CieMarksEntry';
import LabEvaluation from './pages/teacher/LabEvaluation';

// Other Role Dashboards
import StudentDashboard from './pages/StudentDashboard';

// Icons for placeholders
import { FiClipboard, FiFileText } from 'react-icons/fi';
import { FaFlask, FaAward } from 'react-icons/fa';

// Styles
import './styles/theme.css';
import './styles/components.css';
import './styles/pages.css';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />

            {/* Admin Portal Routes */}
            <Route
              path="/admin"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AdminHub />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/students"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ManageStudents />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/teachers"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ManageTeachers />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/subjects"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ManageSubjects />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/assignments"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <SubjectAssignments />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/roster"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ComingSoonPage
                    title="Attendance Roster"
                    icon={FiClipboard}
                    description="Real-time attendance logs, 75% eligibility audits, and biometric reconciliation."
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/cie-summary"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ComingSoonPage
                    title="CIE Master Summary"
                    icon={FiFileText}
                    description="Continuous Internal Evaluation consolidated ledger across university cohorts."
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/practical-sessions"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ComingSoonPage
                    title="Practical Sessions"
                    icon={FaFlask}
                    description="Laboratory experiment logs, batch evaluations, and viva scoring rubrics."
                  />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin/academic-marks"
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <ComingSoonPage
                    title="Academic Marks"
                    icon={FaAward}
                    description="Institutional examination marks, SGPA/CGPA calculations, and transcript outputs."
                  />
                </ProtectedRoute>
              }
            />

            {/* Faculty Portal Routes */}
            <Route
              path="/teacher"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <FacultyHub />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/qr"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <QrAttendance />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/classes"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <MyClasses />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/cie"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <CieMarksEntry />
                </ProtectedRoute>
              }
            />
            <Route
              path="/teacher/lab"
              element={
                <ProtectedRoute allowedRoles={['teacher']}>
                  <LabEvaluation />
                </ProtectedRoute>
              }
            />
            <Route
              path="/student"
              element={
                <ProtectedRoute allowedRoles={['student']}>
                  <StudentDashboard />
                </ProtectedRoute>
              }
            />

            {/* Catch-all redirect to Landing */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
