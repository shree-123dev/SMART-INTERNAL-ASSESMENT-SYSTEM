import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { TEACHER_NAV_ITEMS } from './teacherNav';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import Modal from '../../components/Modal';
import { assignmentService } from '../../services/assignmentService';
import { subjectService } from '../../services/subjectService';
import { sessionService } from '../../services/sessionService';
import { attendanceService } from '../../services/attendanceService';
import { marksService } from '../../services/marksService';
import { QRCodeSVG } from 'qrcode.react';

// Icons
import {
  FiBook,
  FiClock,
  FiRefreshCw,
  FiActivity
} from 'react-icons/fi';
import { FaUserGraduate } from 'react-icons/fa';
import { IoQrCodeOutline } from 'react-icons/io5';

const FacultyHub = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [attendanceLogged, setAttendanceLogged] = useState(0);
  const [pendingCieCount, setPendingCieCount] = useState(0);
  const [activeClassStudents, setActiveClassStudents] = useState([]);
  const [subjectStatsMap, setSubjectStatsMap] = useState({});
  const [isQrModalOpen, setIsQrModalOpen] = useState(false);

  const loadData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      // 1. Load assignments & subjects
      const [allAssignments, allSubjects] = await Promise.all([
        assignmentService.getAll(),
        subjectService.getAll()
      ]);

      const myAssignments = allAssignments.filter((a) => a.teacherId === user.id);
      const mySubjects = allSubjects.filter((s) =>
        myAssignments.some((a) => a.subjectId === s.id)
      );
      setAssignedSubjects(mySubjects);

      // 2. Active Session
      const active = await sessionService.getActive(user.id);
      setActiveSession(active);

      if (active) {
        const students = await attendanceService.getClassStudents(active.subjectId);
        setActiveClassStudents(students);
      } else {
        setActiveClassStudents([]);
      }

      // 3. Attendance Logged
      const totalLogged = await attendanceService.getTotalAttendanceLogged(user.id);
      setAttendanceLogged(totalLogged);

      // 4. Pending CIE Count
      const pendingCount = await marksService.getPendingCieCount(user.id);
      setPendingCieCount(pendingCount);

      // 5. Per-subject stats (enrolled count, average attendance)
      const statsMap = {};
      for (const subj of mySubjects) {
        const stats = await attendanceService.getSubjectAttendanceStats(subj.id);
        const enrolled = stats.students.length;
        let avgPercent = null;
        if (stats.totalSessions > 0 && enrolled > 0) {
          const totalP = stats.students.reduce((acc, curr) => acc + (curr.percentage || 0), 0);
          avgPercent = Number((totalP / enrolled).toFixed(1));
        }
        statsMap[subj.id] = { enrolled, avgPercent, totalSessions: stats.totalSessions };
      }
      setSubjectStatsMap(statsMap);
    } catch (err) {
      console.error('Error loading faculty hub data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [user?.id]);

  // Rolling QR refresh every 30 seconds if active session exists
  useEffect(() => {
    if (!activeSession) return;
    const interval = setInterval(async () => {
      try {
        const newToken = await sessionService.refreshToken(activeSession.id);
        setActiveSession((prev) => (prev ? { ...prev, token: newToken } : null));
      } catch (err) {
        console.error('Failed to auto-refresh session token:', err);
      }
    }, 30000);
    return () => clearInterval(interval);
  }, [activeSession?.id]);

  const handleForceTokenRefresh = async () => {
    if (!activeSession) return;
    try {
      const newToken = await sessionService.refreshToken(activeSession.id);
      setActiveSession((prev) => (prev ? { ...prev, token: newToken } : null));
    } catch (err) {
      console.error('Failed to refresh token:', err);
    }
  };

  const activeSubject = assignedSubjects.find((s) => s.id === activeSession?.subjectId);

  return (
    <DashboardLayout
      title="Faculty Dashboard"
      emoji="👩‍🏫"
      welcomeLine={`Welcome, ${user?.name || 'Faculty Member'} 👋 • Dept. of ${user?.department || 'CSE'}`}
      navItems={TEACHER_NAV_ITEMS}
    >
      {/* Metrics Row */}
      <div className="metrics-row">
        <Card padding="none" hoverEffect onClick={() => navigate('/teacher/classes')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">ASSIGNED CLASSES</span>
              <span className="metric-number">
                {loading ? '...' : assignedSubjects.length}
              </span>
              <span className="metric-subtext">Active curriculum courses</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#e0f2fe', color: '#0284c7' }}>
              <FiBook />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect onClick={() => navigate('/teacher/qr')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">LIVE SESSION</span>
              <span className="metric-number">
                {loading ? '...' : activeSession ? 1 : 'None'}
              </span>
              <span className="metric-subtext">
                {activeSession
                  ? `${activeSubject?.code || 'Live'} (Exp #${activeSession.experimentNumber})`
                  : 'No active session'}
              </span>
            </div>
            <div
              className="metric-icon-box"
              style={{
                background: activeSession ? '#dcfce7' : 'var(--bg-secondary)',
                color: activeSession ? '#16a34a' : 'var(--text-muted)'
              }}
            >
              <FiActivity />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">ATTENDANCE LOGGED</span>
              <span className="metric-number">
                {loading ? '...' : attendanceLogged}
              </span>
              <span className="metric-subtext">Total student attendances</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#ede9fe', color: '#7c3aed' }}>
              <FaUserGraduate />
            </div>
          </div>
        </Card>

        <Card padding="none" hoverEffect onClick={() => navigate('/teacher/cie')}>
          <div className="metric-card">
            <div className="metric-info">
              <span className="metric-label">PENDING CIE ENTRIES</span>
              <span className="metric-number" style={{ color: pendingCieCount > 0 ? '#d97706' : 'var(--text-main)' }}>
                {loading ? '...' : pendingCieCount}
              </span>
              <span className="metric-subtext">Students missing scores</span>
            </div>
            <div className="metric-icon-box" style={{ background: '#fef3c7', color: '#d97706' }}>
              <FiClock />
            </div>
          </div>
        </Card>
      </div>

      {/* Live Dynamic QR Section or No Session Card */}
      {activeSession ? (
        <Card padding="lg">
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: '1.2fr 1fr',
              gap: '2.5rem',
              alignItems: 'center'
            }}
          >
            <div>
              <Badge variant="success" size="md" style={{ marginBottom: '1rem' }}>
                ● Live Session Broadcasting
              </Badge>
              <h2
                style={{
                  fontSize: '1.6rem',
                  fontWeight: 800,
                  color: 'var(--text-main)',
                  marginBottom: '0.35rem'
                }}
              >
                {activeSubject?.code} - {activeSubject?.name}
              </h2>
              <p
                style={{
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  color: 'var(--primary-color)',
                  marginBottom: '0.75rem'
                }}
              >
                Exp #{activeSession.experimentNumber}: {activeSession.experimentName}
              </p>
              <p
                style={{
                  color: 'var(--text-muted)',
                  fontSize: '0.9375rem',
                  lineHeight: 1.6,
                  marginBottom: '1.5rem'
                }}
              >
                Project this dynamic QR code onto the lecture hall display. Codes rotate automatically
                every 30 seconds to prevent proxy scanning and screen-sharing fraud.
              </p>

              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                <Button
                  variant="primary"
                  icon={<IoQrCodeOutline size={18} />}
                  onClick={() => setIsQrModalOpen(true)}
                >
                  Open Fullscreen QR Projector
                </Button>
                <Button
                  variant="secondary"
                  icon={<FiRefreshCw />}
                  onClick={handleForceTokenRefresh}
                >
                  Force Token Refresh
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/teacher/qr')}
                >
                  Manage Session Attendance
                </Button>
              </div>
            </div>

            {/* QR Preview Box */}
            <div
              style={{
                background: 'var(--bg-secondary)',
                border: '1px solid var(--border-color)',
                borderRadius: '16px',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                textAlign: 'center'
              }}
            >
              <div
                style={{
                  padding: '1rem',
                  background: '#ffffff',
                  borderRadius: '12px',
                  boxShadow: '0 4px 14px rgba(0,0,0,0.06)'
                }}
              >
                <QRCodeSVG
                  value={`https://siams.edu/attendance/scan?token=${activeSession.token}&session=${activeSession.id}`}
                  size={160}
                  level="H"
                  fgColor="#1e293b"
                  bgColor="#ffffff"
                />
              </div>
              <span
                style={{
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  color: 'var(--text-muted)',
                  marginTop: '0.75rem'
                }}
              >
                Session Token: <code style={{ color: '#2563eb' }}>{activeSession.token}</code>
              </span>
              <span
                style={{
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  color: '#10b981',
                  marginTop: '0.25rem'
                }}
              >
                {activeSession.attended?.length || 0} / {activeClassStudents.length} Students Scanned
              </span>
            </div>
          </div>
        </Card>
      ) : (
        <Card padding="lg">
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '1.5rem'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
              <div
                style={{
                  width: 56,
                  height: 56,
                  borderRadius: '16px',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  color: 'var(--text-muted)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.75rem'
                }}
              >
                <IoQrCodeOutline />
              </div>
              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.25rem' }}>
                  No Live Session Broadcasting
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                  Launch a dynamic QR attendance session for your students in lecture halls or practical labs.
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              icon={<IoQrCodeOutline size={18} />}
              onClick={() => navigate('/teacher/qr')}
            >
              Start Session
            </Button>
          </div>
        </Card>
      )}

      {/* Assigned Teaching Curriculum Quick Roster */}
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
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              Assigned Teaching Curriculum
            </h3>
            <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
              Only curriculum subjects mapped by academic administration appear here
            </p>
          </div>
          <Badge variant="pill">{assignedSubjects.length} Assigned Courses</Badge>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.9rem',
              textAlign: 'left'
            }}
          >
            <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
              <tr>
                <th style={{ padding: '0.85rem 1.25rem' }}>Course Code</th>
                <th style={{ padding: '0.85rem 1.25rem' }}>Course Title</th>
                <th style={{ padding: '0.85rem 1.25rem' }}>Cohort & Sem</th>
                <th style={{ padding: '0.85rem 1.25rem' }}>Enrolled Students</th>
                <th style={{ padding: '0.85rem 1.25rem' }}>Attendance Avg</th>
                <th style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2.5rem' }}>
                    Loading assigned courses...
                  </td>
                </tr>
              ) : assignedSubjects.length === 0 ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                    No subjects are currently assigned to your faculty profile.
                  </td>
                </tr>
              ) : (
                assignedSubjects.map((subj) => {
                  const stats = subjectStatsMap[subj.id] || { enrolled: 0, avgPercent: null };
                  return (
                    <tr key={subj.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>{subj.code}</td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>{subj.name}</td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>
                        {subj.department} • Sem {subj.semester}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>
                        {stats.enrolled} Students
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>
                        {stats.avgPercent !== null ? (
                          <span style={{ color: stats.avgPercent >= 75 ? '#10b981' : '#f59e0b' }}>
                            {stats.avgPercent}%
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontWeight: 400 }}>No sessions</span>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '0.5rem' }}>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => navigate(`/teacher/classes?subjectId=${subj.id}`)}
                          >
                            Class Roster
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => navigate(`/teacher/cie?subjectId=${subj.id}`)}
                          >
                            Enter CIE
                          </Button>
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => navigate(`/teacher/qr?subjectId=${subj.id}`)}
                          >
                            Start Session
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* QR Fullscreen Projection Modal */}
      {activeSession && (
        <Modal
          isOpen={isQrModalOpen}
          onClose={() => setIsQrModalOpen(false)}
          title="Classroom Projection - Dynamic QR Session"
          size="md"
        >
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              gap: '1.25rem'
            }}
          >
            <Badge variant="pill" size="md">
              Subject: {activeSubject?.code} - {activeSubject?.name}
            </Badge>
            <div
              style={{
                padding: '1.5rem',
                background: '#ffffff',
                borderRadius: '20px',
                boxShadow: '0 8px 24px rgba(0,0,0,0.1)'
              }}
            >
              <QRCodeSVG
                value={`https://siams.edu/attendance/scan?token=${activeSession.token}&session=${activeSession.id}`}
                size={260}
                level="H"
                fgColor="#0f172a"
                bgColor="#ffffff"
              />
            </div>
            <div>
              <p style={{ fontWeight: 700, fontSize: '1.1rem', color: 'var(--text-main)' }}>
                Exp #{activeSession.experimentNumber}: {activeSession.experimentName}
              </p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Dynamic Token: <strong style={{ color: '#2563eb' }}>{activeSession.token}</strong> • Rotates in 30s
              </p>
              <p style={{ fontSize: '0.9rem', fontWeight: 700, color: '#10b981', marginTop: '0.5rem' }}>
                {activeSession.attended?.length || 0} / {activeClassStudents.length} Students Scanned
              </p>
            </div>
            <Button variant="primary" onClick={() => setIsQrModalOpen(false)}>
              Close Projector
            </Button>
          </div>
        </Modal>
      )}
    </DashboardLayout>
  );
};

export default FacultyHub;
