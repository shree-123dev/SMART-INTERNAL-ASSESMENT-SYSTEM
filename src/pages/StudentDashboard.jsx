import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import Logo from '../components/Logo';
import Card from '../components/Card';
import Badge from '../components/Badge';
import Button from '../components/Button';
import Modal from '../components/Modal';
import { subjectService } from '../services/subjectService';
import { attendanceService } from '../services/attendanceService';
import { marksService } from '../services/marksService';
import { sessionService } from '../services/sessionService';
import { calculateCie } from '../utils/cie';

// Icons
import {
  FiGrid,
  FiCheckCircle,
  FiAward,
  FiSun,
  FiMoon,
  FiCamera,
  FiAlertCircle
} from 'react-icons/fi';
import { FaUserGraduate, FaFlask, FaQrcode } from 'react-icons/fa';
import { IoQrCodeOutline, IoLogOutOutline } from 'react-icons/io5';

const normalize = (str) => (str || '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');

const isClassMatch = (student, subject) => {
  if (!student || !subject) return false;
  if (Number(student.semester) !== Number(subject.semester)) return false;

  const sDept = normalize(student.department);
  const subDept = normalize(subject.department);

  if (sDept === subDept) return true;
  const isCs = (d) => d === 'cse' || d === 'computerscience' || d === 'computerscienceengineering';
  if (isCs(sDept) && isCs(subDept)) return true;

  return false;
};

const StudentDashboard = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const [activeNav, setActiveNav] = useState('Student Hub');
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanStatus, setScanStatus] = useState('idle'); // idle, scanning, success, no_active, error
  const [scannedSessionInfo, setScannedSessionInfo] = useState(null);
  const [scanErrorMessage, setScanErrorMessage] = useState('');

  const [loading, setLoading] = useState(true);
  const [enrolledSubjects, setEnrolledSubjects] = useState([]);
  const [attendanceData, setAttendanceData] = useState([]);
  const [overallAttendancePercent, setOverallAttendancePercent] = useState(100);
  const [isOverallEligible, setIsOverallEligible] = useState(true);
  const [averageCieScore, setAverageCieScore] = useState(0);
  const [practicalLabScore, setPracticalLabScore] = useState(null);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const loadStudentData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const allSubjects = await subjectService.getAll();
      const mySubjects = allSubjects.filter((s) => isClassMatch(user, s));
      setEnrolledSubjects(mySubjects);

      let totalAttendedCount = 0;
      let totalSessionsCount = 0;
      let totalCieSum = 0;
      let validCieCount = 0;
      let practicalScores = [];

      const rows = [];
      for (const sub of mySubjects) {
        const attStats = await attendanceService.getStudentSubjectAttendance(user.id, sub.id);
        const cieMarks = await marksService.getCieMarks(sub.id);
        const myCie = cieMarks.find((m) => m.studentId === user.id) || {};
        const practicalAvg = await marksService.getStudentPracticalAverage(user.id, sub.id);

        if (practicalAvg !== null) {
          practicalScores.push(practicalAvg);
        }

        const cieEval = calculateCie({
          ia1: myCie.ia1,
          ia2: myCie.ia2,
          assignment: myCie.assignment,
          oral: myCie.oral,
          practical: practicalAvg
        });

        if (cieEval.total !== null) {
          totalCieSum += cieEval.total;
          validCieCount += 1;
        }

        totalAttendedCount += attStats.attendedCount;
        totalSessionsCount += attStats.totalSessions;

        rows.push({
          code: sub.code,
          name: sub.name,
          attended: attStats.attendedCount,
          total: attStats.totalSessions,
          percentage: attStats.percentage,
          eligible: attStats.eligible,
          requiredMore: attStats.requiredMore,
          ia1: myCie.ia1 !== null && myCie.ia1 !== undefined ? myCie.ia1 : '—',
          ia2: myCie.ia2 !== null && myCie.ia2 !== undefined ? myCie.ia2 : '—',
          totalCie: cieEval.total !== null ? cieEval.total : '—',
          status: cieEval.status
        });
      }

      setAttendanceData(rows);

      const overall = totalSessionsCount > 0 ? Number(((totalAttendedCount / totalSessionsCount) * 100).toFixed(1)) : 100;
      setOverallAttendancePercent(overall);
      setIsOverallEligible(overall >= 75);

      if (validCieCount > 0) {
        setAverageCieScore(Number((totalCieSum / validCieCount).toFixed(1)));
      } else {
        setAverageCieScore('N/A');
      }

      if (practicalScores.length > 0) {
        const sum = practicalScores.reduce((acc, curr) => acc + curr, 0);
        setPracticalLabScore(Number((sum / practicalScores.length).toFixed(1)));
      } else {
        setPracticalLabScore(null);
      }
    } catch (err) {
      console.error('Failed to load student dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStudentData();
  }, [user?.id]);

  const handleSimulateScan = async () => {
    setScanStatus('scanning');
    setScanErrorMessage('');

    try {
      const allSessions = await sessionService.getAll();
      const active = allSessions.find((s) => s.status === 'active');

      if (!active) {
        setTimeout(() => {
          setScanStatus('no_active');
        }, 600);
        return;
      }

      // Check if session subject matches student class
      const subject = enrolledSubjects.find((s) => s.id === active.subjectId);
      const res = await sessionService.markAttendance(active.id, user.usn);

      setTimeout(() => {
        setScannedSessionInfo({
          session: active,
          subjectName: subject ? `${subject.code} - ${subject.name}` : 'Laboratory Session'
        });
        setScanStatus('success');
        loadStudentData();
      }, 700);
    } catch (err) {
      setTimeout(() => {
        setScanErrorMessage(err.message || 'Scanning failed.');
        setScanStatus('error');
      }, 600);
    }
  };

  return (
    <div className="siams-dashboard-layout">
      {/* Dark Navy Sidebar */}
      <aside className="siams-sidebar">
        <div className="sidebar-header">
          <Logo size="md" subtitle="" light={true} />
        </div>

        <nav className="sidebar-nav">
          <div
            className={`sidebar-item ${activeNav === 'Student Hub' ? 'active' : ''}`}
            onClick={() => setActiveNav('Student Hub')}
          >
            <FiGrid style={{ fontSize: '1.1rem' }} />
            <span>Student Hub</span>
          </div>

          <div
            className={`sidebar-item ${activeNav === 'Scan Attendance' ? 'active' : ''}`}
            onClick={() => {
              setActiveNav('Scan Attendance');
              setScanStatus('idle');
              setIsScanModalOpen(true);
            }}
          >
            <IoQrCodeOutline style={{ fontSize: '1.1rem' }} />
            <span>Scan QR Code</span>
          </div>

          <div
            className={`sidebar-item ${activeNav === 'CIE Marks' ? 'active' : ''}`}
            onClick={() => setActiveNav('CIE Marks')}
          >
            <FiAward style={{ fontSize: '1.1rem' }} />
            <span>CIE Marks</span>
          </div>

          <div
            className={`sidebar-item ${activeNav === 'Lab Records' ? 'active' : ''}`}
            onClick={() => setActiveNav('Lab Records')}
          >
            <FaFlask style={{ fontSize: '1.1rem' }} />
            <span>Lab Records</span>
          </div>
        </nav>

        <div className="sidebar-footer">
          <button
            type="button"
            className="sidebar-logout-btn"
            onClick={handleLogout}
          >
            <IoLogOutOutline size={20} />
            <span>Logout System</span>
          </button>
        </div>
      </aside>

      {/* Main Dashboard Content */}
      <main className="dashboard-main">
        {/* Topbar */}
        <header className="dashboard-topbar">
          <div className="dashboard-title-area">
            <h1 className="dashboard-heading">
              Student Scholar Portal <span style={{ fontSize: '1.25rem' }}>🎓</span>
            </h1>
            <p className="dashboard-subheading">
              Welcome, {user?.name || 'Alex Johnson'} 👋 • USN: {user?.usn || '1MS21CS042'} • Dept. of {user?.department || 'CSE'} (Sem {user?.semester || 6})
            </p>
          </div>

          <div className="dashboard-actions-area">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <FiSun size={19} color="#f59e0b" /> : <FiMoon size={19} />}
            </button>

            <div className="user-profile-badge">
              <div className="profile-avatar-circle" style={{ background: '#7c3aed' }}>
                <FaUserGraduate size={15} />
              </div>
              <div className="profile-info">
                <span className="profile-name">{user?.name || 'Alex Johnson'}</span>
                <span style={{ fontSize: '0.6875rem', fontWeight: 700, color: '#7c3aed' }}>
                  STUDENT
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Dashboard Content */}
        <div className="dashboard-content">
          {/* Metrics Row */}
          <div className="metrics-row">
            <Card padding="none" hoverEffect>
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">OVERALL ATTENDANCE</span>
                  <span className="metric-number">
                    {loading ? '...' : `${overallAttendancePercent}%`}
                  </span>
                  <span className="metric-subtext">Across {enrolledSubjects.length} registered courses</span>
                </div>
                <div className="metric-icon-box" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  <FiCheckCircle />
                </div>
              </div>
            </Card>

            <Card padding="none" hoverEffect>
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">75% ELIGIBILITY</span>
                  <span
                    className="metric-number"
                    style={{
                      color: isOverallEligible ? '#10b981' : '#ef4444',
                      fontSize: '1.8rem'
                    }}
                  >
                    {isOverallEligible ? 'Eligible' : 'Shortage'}
                  </span>
                  <span className="metric-subtext">
                    {isOverallEligible ? 'Safe for semester exams' : 'Makeup attendance needed'}
                  </span>
                </div>
                <div className="metric-icon-box" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <FiAward />
                </div>
              </div>
            </Card>

            <Card padding="none" hoverEffect>
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">AVERAGE CIE</span>
                  <span className="metric-number">
                    {loading ? '...' : averageCieScore !== 'N/A' ? `${averageCieScore}/90` : 'Pending'}
                  </span>
                  <span className="metric-subtext">Continuous internal score</span>
                </div>
                <div className="metric-icon-box" style={{ background: '#ede9fe', color: '#7c3aed' }}>
                  <FaUserGraduate />
                </div>
              </div>
            </Card>

            <Card padding="none" hoverEffect>
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">PRACTICAL LAB</span>
                  <span className="metric-number">
                    {practicalLabScore !== null ? `${practicalLabScore}/15` : 'Pending'}
                  </span>
                  <span className="metric-subtext">Continuous rubrics score</span>
                </div>
                <div className="metric-icon-box" style={{ background: '#fef3c7', color: '#d97706' }}>
                  <FaFlask />
                </div>
              </div>
            </Card>
          </div>

          {/* Quick Scanner Action Banner */}
          <Card padding="md">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div
                  style={{
                    width: 48,
                    height: 48,
                    borderRadius: '12px',
                    background: 'var(--primary-gradient)',
                    color: '#ffffff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '1.5rem'
                  }}
                >
                  <IoQrCodeOutline />
                </div>
                <div>
                  <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
                    In-Class Attendance Check-In
                  </h3>
                  <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                    Is your professor projecting a live attendance QR code? Click below to check in instantly.
                  </p>
                </div>
              </div>

              <Button
                variant="primary"
                size="md"
                icon={<FaQrcode />}
                onClick={() => {
                  setScanStatus('idle');
                  setIsScanModalOpen(true);
                }}
              >
                Launch QR Scanner
              </Button>
            </div>
          </Card>

          {/* Subject Breakdown Table */}
          <Card padding="none">
            <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                  Course-Wise Evaluation Ledger (Semester {user?.semester || 6})
                </h3>
                <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                  Real-time synchronization with faculty attendance broadcasts and CIE scoring rubrics
                </span>
              </div>
              <Badge variant="pill">USN: {user?.usn || '1MS21CS042'}</Badge>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem', textAlign: 'left' }}>
                <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                  <tr>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Course Code</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Course Name</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Classes Attended</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>Attendance %</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>IA 1 (/20)</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>IA 2 (/20)</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>CIE Total (/90)</th>
                    <th style={{ padding: '0.85rem 1.25rem' }}>75% Status</th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem' }}>
                        Loading academic evaluation records...
                      </td>
                    </tr>
                  ) : attendanceData.length === 0 ? (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '2.5rem', color: 'var(--text-muted)' }}>
                        No curriculum subjects found for your department and semester.
                      </td>
                    </tr>
                  ) : (
                    attendanceData.map((subj) => (
                      <tr key={subj.code} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>{subj.code}</td>
                        <td style={{ padding: '0.85rem 1.25rem' }}>{subj.name}</td>
                        <td style={{ padding: '0.85rem 1.25rem' }}>{subj.attended} / {subj.total}</td>
                        <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700 }}>
                          {subj.percentage !== null ? (
                            <span style={{ color: subj.percentage >= 75 ? '#10b981' : '#ef4444' }}>
                              {subj.percentage}%
                            </span>
                          ) : (
                            <span style={{ color: 'var(--text-muted)' }}>No sessions</span>
                          )}
                        </td>
                        <td style={{ padding: '0.85rem 1.25rem' }}>{subj.ia1}</td>
                        <td style={{ padding: '0.85rem 1.25rem' }}>{subj.ia2}</td>
                        <td style={{ padding: '0.85rem 1.25rem', fontWeight: 700, color: '#2563eb' }}>
                          {subj.totalCie}
                        </td>
                        <td style={{ padding: '0.85rem 1.25rem' }}>
                          <Badge variant={subj.eligible ? 'success' : 'danger'} size="sm">
                            {subj.eligible ? '75%+ Cleared' : `Shortage (Attend ${subj.requiredMore}+)`}
                          </Badge>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </main>

      {/* Student QR Scanner Modal Simulator */}
      <Modal
        isOpen={isScanModalOpen}
        onClose={() => setIsScanModalOpen(false)}
        title="Student QR Attendance Scanner"
        size="sm"
      >
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '1.25rem' }}>
          {scanStatus === 'idle' && (
            <>
              <div
                style={{
                  width: '100%',
                  height: '200px',
                  border: '2px dashed var(--primary-color)',
                  borderRadius: '16px',
                  background: 'var(--bg-secondary)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.75rem',
                  color: 'var(--text-muted)'
                }}
              >
                <FiCamera size={36} color="var(--primary-color)" />
                <span style={{ fontSize: '0.875rem' }}>Point camera at live classroom projection</span>
              </div>
              <Button
                variant="primary"
                fullWidth
                onClick={handleSimulateScan}
              >
                Simulate Scanning Projector QR
              </Button>
            </>
          )}

          {scanStatus === 'scanning' && (
            <div style={{ padding: '2rem 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  border: '4px solid var(--border-color)',
                  borderTopColor: 'var(--primary-color)',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}
              />
              <p style={{ fontWeight: 600, color: 'var(--text-main)' }}>Validating token with SIAMS server...</p>
            </div>
          )}

          {scanStatus === 'success' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '1rem 0' }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#dcfce7',
                  color: '#16a34a',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem'
                }}
              >
                <FiCheckCircle />
              </div>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                Attendance Recorded!
              </h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Course: <strong>{scannedSessionInfo?.subjectName || 'Current Lecture'}</strong><br />
                Timestamp: <strong>{new Date().toLocaleTimeString()}</strong><br />
                Verified for USN: <strong>{user?.usn || '1MS21CS042'}</strong>
              </p>
              <Button variant="primary" onClick={() => setIsScanModalOpen(false)}>
                Done
              </Button>
            </div>
          )}

          {scanStatus === 'no_active' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '1rem 0' }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#fef3c7',
                  color: '#d97706',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem'
                }}
              >
                <FiAlertCircle />
              </div>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                No Live Session Broadcasting
              </h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Your faculty instructor has not started a live QR session yet. Please wait for the lecture hall broadcast to begin.
              </p>
              <Button variant="secondary" onClick={() => setScanStatus('idle')}>
                Try Again
              </Button>
            </div>
          )}

          {scanStatus === 'error' && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem', padding: '1rem 0' }}>
              <div
                style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: '#fee2e2',
                  color: '#ef4444',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '2rem'
                }}
              >
                <FiAlertCircle />
              </div>
              <h4 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                Scan Rejected
              </h4>
              <p style={{ fontSize: '0.875rem', color: '#ef4444' }}>
                {scanErrorMessage}
              </p>
              <Button variant="secondary" onClick={() => setScanStatus('idle')}>
                Try Again
              </Button>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default StudentDashboard;
