import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { TEACHER_NAV_ITEMS } from './teacherNav';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import Modal from '../../components/Modal';
import DataTable from '../../components/DataTable';
import ConfirmDialog from '../../components/ConfirmDialog';
import { assignmentService } from '../../services/assignmentService';
import { subjectService } from '../../services/subjectService';
import { sessionService } from '../../services/sessionService';
import { attendanceService } from '../../services/attendanceService';
import { QRCodeSVG } from 'qrcode.react';

// Icons
import {
  FiPlay,
  FiRefreshCw,
  FiAlertCircle,
  FiCheckCircle,
  FiTrash2,
  FiUserPlus,
  FiList
} from 'react-icons/fi';
import { IoQrCodeOutline, IoStopCircleOutline } from 'react-icons/io5';
import { FaFlask } from 'react-icons/fa';

const QrAttendance = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const preselectedSubject = searchParams.get('subjectId');

  const [loading, setLoading] = useState(true);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [activeSession, setActiveSession] = useState(null);
  const [sessionHistory, setSessionHistory] = useState([]);
  const [classStudents, setClassStudents] = useState([]);

  // Start Session Form State
  const [formData, setFormData] = useState({
    subjectId: preselectedSubject || '',
    experimentNumber: 1,
    experimentName: ''
  });
  const [formError, setFormError] = useState('');
  const [isStarting, setIsStarting] = useState(false);

  // USN Scan Input State
  const [scanUsn, setScanUsn] = useState('');
  const [scanError, setScanError] = useState('');
  const [scanSuccess, setScanSuccess] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  // Modal & Confirm States
  const [isQrModalOpen, setIsQrModalOpen] = useState(false);
  const [isEndModalOpen, setIsEndModalOpen] = useState(false);
  const [isEnding, setIsEnding] = useState(false);

  const loadInitialData = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const [allAssignments, allSubjects] = await Promise.all([
        assignmentService.getAll(),
        subjectService.getAll()
      ]);

      const myAssignments = allAssignments.filter((a) => a.teacherId === user.id);
      const mySubjects = allSubjects.filter((s) =>
        myAssignments.some((a) => a.subjectId === s.id)
      );
      setAssignedSubjects(mySubjects);

      if (!formData.subjectId && mySubjects.length > 0) {
        setFormData((prev) => ({
          ...prev,
          subjectId: preselectedSubject || mySubjects[0].id
        }));
      }

      // Load sessions
      const sessions = await sessionService.getByTeacher(user.id);
      setSessionHistory(sessions);

      const active = sessions.find((s) => s.status === 'active') || null;
      setActiveSession(active);

      if (active) {
        const students = await attendanceService.getClassStudents(active.subjectId);
        setClassStudents(students);
      }
    } catch (err) {
      console.error('Error loading QR attendance data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, [user?.id]);

  // Rolling QR: Auto regenerates session token every 30 seconds
  useEffect(() => {
    if (!activeSession) return;
    const interval = setInterval(async () => {
      try {
        const newToken = await sessionService.refreshToken(activeSession.id);
        setActiveSession((prev) => (prev ? { ...prev, token: newToken } : null));
      } catch (err) {
        console.error('Failed to auto refresh token:', err);
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
      console.error('Error refreshing token:', err);
    }
  };

  const handleStartSession = async (e) => {
    e.preventDefault();
    setFormError('');

    if (!formData.subjectId) {
      setFormError('Please select a curriculum subject.');
      return;
    }
    if (!formData.experimentNumber && formData.experimentNumber !== 0) {
      setFormError('Please enter an experiment number.');
      return;
    }
    if (!formData.experimentName.trim()) {
      setFormError('Please enter an experiment name or topic.');
      return;
    }

    try {
      setIsStarting(true);
      const newSession = await sessionService.start({
        teacherId: user.id,
        subjectId: formData.subjectId,
        experimentNumber: Number(formData.experimentNumber),
        experimentName: formData.experimentName
      });

      setActiveSession(newSession);
      const students = await attendanceService.getClassStudents(formData.subjectId);
      setClassStudents(students);

      const updatedHistory = await sessionService.getByTeacher(user.id);
      setSessionHistory(updatedHistory);
    } catch (err) {
      setFormError(err.message || 'Failed to start attendance session.');
    } finally {
      setIsStarting(false);
    }
  };

  const handleScanUsn = async (e) => {
    e.preventDefault();
    if (!scanUsn.trim() || !activeSession) return;

    setScanError('');
    setScanSuccess('');
    setIsScanning(true);

    try {
      const res = await sessionService.markAttendance(activeSession.id, scanUsn);
      setActiveSession(res.session);
      setScanSuccess(`Marked present: ${res.student.fullName} (${res.student.usn})`);
      setScanUsn('');
    } catch (err) {
      setScanError(err.message || 'Failed to record attendance.');
    } finally {
      setIsScanning(false);
    }
  };

  const handleRemoveStudent = async (usn) => {
    if (!activeSession) return;
    try {
      const updated = await sessionService.removeAttendance(activeSession.id, usn);
      setActiveSession(updated);
    } catch (err) {
      console.error('Failed to remove attendance record:', err);
    }
  };

  const handleConfirmEndSession = async () => {
    if (!activeSession) return;
    try {
      setIsEnding(true);
      await sessionService.end(activeSession.id);
      setIsEndModalOpen(false);
      setActiveSession(null);
      setClassStudents([]);

      const updatedHistory = await sessionService.getByTeacher(user.id);
      setSessionHistory(updatedHistory);
    } catch (err) {
      console.error('Failed to end session:', err);
    } finally {
      setIsEnding(false);
    }
  };

  const activeSubject = assignedSubjects.find((s) => s.id === activeSession?.subjectId);

  // History columns for DataTable
  const historyColumns = [
    {
      header: 'Date & Time',
      key: 'createdAt',
      render: (row) => (
        <div>
          <div style={{ fontWeight: 600 }}>{new Date(row.createdAt).toLocaleDateString()}</div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {new Date(row.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      )
    },
    {
      header: 'Course Code & Name',
      key: 'subjectId',
      render: (row) => {
        const sub = assignedSubjects.find((s) => s.id === row.subjectId);
        return (
          <div>
            <span style={{ fontWeight: 700 }}>{sub?.code || row.subjectId}</span>
            <div style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>{sub?.name}</div>
          </div>
        );
      }
    },
    {
      header: 'Experiment',
      key: 'experimentNumber',
      render: (row) => (
        <div>
          <Badge variant="pill" size="sm">Exp #{row.experimentNumber}</Badge>
          <div style={{ fontSize: '0.8125rem', fontWeight: 600, marginTop: '0.2rem' }}>
            {row.experimentName}
          </div>
        </div>
      )
    },
    {
      header: 'Students Present',
      key: 'attended',
      render: (row) => (
        <span style={{ fontWeight: 700, color: '#10b981' }}>
          {row.attended?.length || 0} Students
        </span>
      )
    },
    {
      header: 'Status',
      key: 'status',
      render: (row) => (
        <Badge variant={row.status === 'active' ? 'success' : 'secondary'} size="sm">
          {row.status === 'active' ? '● Broadcasting' : 'Completed'}
        </Badge>
      )
    },
    {
      header: 'Action',
      key: 'actions',
      align: 'right',
      render: (row) => (
        <Button
          variant="secondary"
          size="sm"
          icon={<FaFlask />}
          onClick={() => navigate(`/teacher/lab?subjectId=${row.subjectId}&sessionId=${row.id}`)}
        >
          Evaluate Lab
        </Button>
      )
    }
  ];

  return (
    <DashboardLayout
      title="Dynamic QR Attendance"
      emoji="⚡"
      welcomeLine={`Welcome, ${user?.name || 'Faculty Member'} 👋 • Real-time anti-proxy student attendance broadcast`}
      navItems={TEACHER_NAV_ITEMS}
    >
      {/* Active Session Screen OR Start Session Form */}
      {activeSession ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
          {/* Active Session Banner Card */}
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
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.85rem' }}>
                  <Badge variant="success" size="md">
                    ● Live Session Broadcasting
                  </Badge>
                  <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                    Auto-rolling token active
                  </span>
                </div>

                <h2 style={{ fontSize: '1.65rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.35rem' }}>
                  {activeSubject?.code} - {activeSubject?.name}
                </h2>
                <p style={{ fontWeight: 700, color: 'var(--primary-color)', fontSize: '1rem', marginBottom: '0.75rem' }}>
                  Experiment #{activeSession.experimentNumber}: {activeSession.experimentName}
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', lineHeight: 1.6, marginBottom: '1.5rem' }}>
                  Tokens automatically cycle every 30 seconds. Point projection projector screen towards the hall.
                  Students must scan using their mobile camera to verify attendance.
                </p>

                <div style={{ display: 'flex', gap: '0.85rem', flexWrap: 'wrap' }}>
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
                    variant="danger"
                    icon={<IoStopCircleOutline size={18} />}
                    onClick={() => setIsEndModalOpen(true)}
                  >
                    End Session
                  </Button>
                </div>
              </div>

              {/* QR Code Card */}
              <div
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '20px',
                  padding: '1.75rem',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  textAlign: 'center'
                }}
              >
                <div
                  style={{
                    padding: '1.25rem',
                    background: '#ffffff',
                    borderRadius: '16px',
                    boxShadow: '0 8px 24px rgba(0,0,0,0.08)'
                  }}
                >
                  <QRCodeSVG
                    value={`https://siams.edu/attendance/scan?token=${activeSession.token}&session=${activeSession.id}`}
                    size={175}
                    level="H"
                    fgColor="#0f172a"
                    bgColor="#ffffff"
                  />
                </div>
                <div style={{ marginTop: '1rem' }}>
                  <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--text-muted)' }}>
                    Session Token:{' '}
                    <code style={{ fontSize: '0.9375rem', fontWeight: 800, color: '#2563eb' }}>
                      {activeSession.token}
                    </code>
                  </span>
                </div>
                <div
                  style={{
                    marginTop: '0.5rem',
                    padding: '0.35rem 0.85rem',
                    background: 'rgba(16, 185, 129, 0.1)',
                    borderRadius: 'var(--radius-pill)',
                    color: '#10b981',
                    fontWeight: 800,
                    fontSize: '0.9rem'
                  }}
                >
                  {activeSession.attended?.length || 0} / {classStudents.length} Students Scanned
                </div>
              </div>
            </div>
          </Card>

          {/* USN Scanner Simulator & Live Marked List */}
          <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 1.4fr', gap: '2rem' }}>
            {/* Left: USN Scanner Simulator */}
            <Card padding="md">
              <div style={{ marginBottom: '1.25rem' }}>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  Manual Scan / USN Input Simulator
                </h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                  Simulates student scanning projector QR or barcode scan. Press Enter to record.
                </p>
              </div>

              {scanError && (
                <div
                  style={{
                    padding: '0.85rem 1rem',
                    backgroundColor: 'var(--status-danger-bg)',
                    border: '1px solid #fca5a5',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--status-danger)',
                    fontSize: '0.875rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '1rem'
                  }}
                >
                  <FiAlertCircle size={18} style={{ flexShrink: 0 }} />
                  <span>{scanError}</span>
                </div>
              )}

              {scanSuccess && (
                <div
                  style={{
                    padding: '0.85rem 1rem',
                    backgroundColor: 'var(--status-success-bg)',
                    border: '1px solid #86efac',
                    borderRadius: 'var(--radius-md)',
                    color: 'var(--status-success)',
                    fontSize: '0.875rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    marginBottom: '1rem'
                  }}
                >
                  <FiCheckCircle size={18} style={{ flexShrink: 0 }} />
                  <span>{scanSuccess}</span>
                </div>
              )}

              <form onSubmit={handleScanUsn}>
                <div style={{ display: 'flex', gap: '0.75rem' }}>
                  <div style={{ flex: 1 }}>
                    <input
                      type="text"
                      className="siams-input"
                      placeholder="e.g. 1MS21CS042"
                      value={scanUsn}
                      onChange={(e) => {
                        setScanUsn(e.target.value.toUpperCase());
                        setScanError('');
                        setScanSuccess('');
                      }}
                      autoFocus
                    />
                  </div>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={isScanning || !scanUsn.trim()}
                    icon={<FiUserPlus />}
                  >
                    Mark Present
                  </Button>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.4rem', display: 'block' }}>
                  Press Enter to submit. Enforces duplicate detection and class cohort validation.
                </span>
              </form>

              {/* Class USN Quick Chips */}
              <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem' }}>
                <span style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '0.5rem' }}>
                  Enrolled Students in this Cohort ({classStudents.length}):
                </span>
                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                  {classStudents.map((std) => {
                    const isMarked = (activeSession.attended || []).some(
                      (a) => a.usn?.toUpperCase() === std.usn.toUpperCase()
                    );
                    return (
                      <button
                        key={std.id}
                        type="button"
                        onClick={() => {
                          setScanUsn(std.usn);
                          setScanError('');
                          setScanSuccess('');
                        }}
                        style={{
                          padding: '0.25rem 0.55rem',
                          borderRadius: 'var(--radius-pill)',
                          border: '1px solid',
                          borderColor: isMarked ? '#10b981' : 'var(--border-color)',
                          background: isMarked ? '#dcfce7' : 'var(--bg-card)',
                          color: isMarked ? '#15803d' : 'var(--text-main)',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        {std.usn} {isMarked && '✓'}
                      </button>
                    );
                  })}
                </div>
              </div>
            </Card>

            {/* Right: Live List of Marked Students */}
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
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
                    Live Scanned Students ({activeSession.attended?.length || 0})
                  </h3>
                  <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                    Verified real-time attendees with timestamp
                  </span>
                </div>
                <Badge variant="pill">Live Roster</Badge>
              </div>

              <div style={{ maxHeight: '380px', overflowY: 'auto' }}>
                {(!activeSession.attended || activeSession.attended.length === 0) ? (
                  <div style={{ textAlign: 'center', padding: '3rem 1rem', color: 'var(--text-muted)' }}>
                    <IoQrCodeOutline size={36} style={{ marginBottom: '0.5rem', color: 'var(--text-dim)' }} />
                    <p style={{ fontWeight: 600 }}>No students scanned yet</p>
                    <span style={{ fontSize: '0.8125rem' }}>
                      Ask students to point their phone cameras at the dynamic QR code above.
                    </span>
                  </div>
                ) : (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
                    <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                      <tr>
                        <th style={{ padding: '0.75rem 1.25rem', textAlign: 'left' }}>USN</th>
                        <th style={{ padding: '0.75rem 1.25rem', textAlign: 'left' }}>Student Name</th>
                        <th style={{ padding: '0.75rem 1.25rem', textAlign: 'left' }}>Time</th>
                        <th style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {activeSession.attended.map((attendee, idx) => (
                        <tr
                          key={attendee.usn || idx}
                          style={{ borderBottom: '1px solid var(--border-color)' }}
                        >
                          <td style={{ padding: '0.75rem 1.25rem', fontWeight: 700, color: '#2563eb' }}>
                            {attendee.usn}
                          </td>
                          <td style={{ padding: '0.75rem 1.25rem', fontWeight: 600 }}>
                            {attendee.studentName}
                          </td>
                          <td style={{ padding: '0.75rem 1.25rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                            {attendee.timestamp}
                          </td>
                          <td style={{ padding: '0.75rem 1.25rem', textAlign: 'right' }}>
                            <Button
                              variant="ghost"
                              size="sm"
                              icon={<FiTrash2 />}
                              style={{ color: '#ef4444' }}
                              onClick={() => handleRemoveStudent(attendee.usn)}
                            >
                              Remove
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </Card>
          </div>
        </div>
      ) : (
        /* Start Session Form */
        <Card padding="lg">
          <div style={{ maxWidth: '640px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
              <div
                style={{
                  width: 42,
                  height: 42,
                  borderRadius: '12px',
                  background: 'var(--primary-gradient)',
                  color: '#ffffff',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.35rem'
                }}
              >
                <FiPlay />
              </div>
              <h2 style={{ fontSize: '1.45rem', fontWeight: 800, color: 'var(--text-main)' }}>
                Start Live Attendance Broadcast
              </h2>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9375rem', marginBottom: '1.75rem' }}>
              Select an assigned curriculum subject and experiment details. Only one active session may run at a time.
            </p>

            {formError && (
              <div
                style={{
                  padding: '0.85rem 1rem',
                  backgroundColor: 'var(--status-danger-bg)',
                  border: '1px solid #fca5a5',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--status-danger)',
                  fontSize: '0.875rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  marginBottom: '1.5rem'
                }}
              >
                <FiAlertCircle size={18} style={{ flexShrink: 0 }} />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleStartSession}>
              <div className="siams-form-group">
                <label className="siams-label">Assigned Subject / Course</label>
                <select
                  className="siams-input"
                  value={formData.subjectId}
                  onChange={(e) => setFormData({ ...formData, subjectId: e.target.value })}
                  required
                >
                  <option value="" disabled>Select assigned subject</option>
                  {assignedSubjects.map((sub) => (
                    <option key={sub.id} value={sub.id}>
                      {sub.code} - {sub.name} ({sub.department} Sem {sub.semester})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '160px 1fr', gap: '1rem' }}>
                <div className="siams-form-group">
                  <label className="siams-label">Experiment #</label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    className="siams-input"
                    value={formData.experimentNumber}
                    onChange={(e) => setFormData({ ...formData, experimentNumber: e.target.value })}
                    required
                  />
                </div>

                <div className="siams-form-group">
                  <label className="siams-label">Experiment / Session Topic</label>
                  <input
                    type="text"
                    className="siams-input"
                    placeholder="e.g. Container Orchestration & Docker Compose"
                    value={formData.experimentName}
                    onChange={(e) => setFormData({ ...formData, experimentName: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div style={{ marginTop: '1rem' }}>
                <Button
                  type="submit"
                  variant="primary"
                  size="lg"
                  disabled={isStarting || assignedSubjects.length === 0}
                  icon={<IoQrCodeOutline size={18} />}
                >
                  {isStarting ? 'Starting Broadcast...' : 'Start Session'}
                </Button>
              </div>
            </form>
          </div>
        </Card>
      )}

      {/* Session History Table */}
      <section style={{ marginTop: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <FiList style={{ color: 'var(--primary-color)', fontSize: '1.25rem' }} />
            <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Faculty Session History
            </h3>
          </div>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {sessionHistory.length} Recorded Sessions
          </span>
        </div>

        <DataTable
          columns={historyColumns}
          data={sessionHistory}
          loading={loading}
          emptyMessage="No previous sessions recorded for your faculty profile."
          rowKey="id"
        />
      </section>

      {/* Fullscreen QR Projector Modal */}
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
              {activeSubject?.code} - {activeSubject?.name}
            </Badge>
            <div
              style={{
                padding: '1.5rem',
                background: '#ffffff',
                borderRadius: '24px',
                boxShadow: '0 8px 30px rgba(0,0,0,0.12)'
              }}
            >
              <QRCodeSVG
                value={`https://siams.edu/attendance/scan?token=${activeSession.token}&session=${activeSession.id}`}
                size={270}
                level="H"
                fgColor="#0f172a"
                bgColor="#ffffff"
              />
            </div>
            <div>
              <p style={{ fontWeight: 800, fontSize: '1.2rem', color: 'var(--text-main)' }}>
                Exp #{activeSession.experimentNumber}: {activeSession.experimentName}
              </p>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.35rem' }}>
                Dynamic Token: <strong style={{ color: '#2563eb' }}>{activeSession.token}</strong> • Auto-rotates in 30s
              </p>
              <div
                style={{
                  marginTop: '0.75rem',
                  display: 'inline-block',
                  padding: '0.4rem 1rem',
                  background: '#dcfce7',
                  borderRadius: 'var(--radius-pill)',
                  color: '#16a34a',
                  fontWeight: 800
                }}
              >
                {activeSession.attended?.length || 0} / {classStudents.length} Students Scanned
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Button variant="secondary" onClick={handleForceTokenRefresh} icon={<FiRefreshCw />}>
                Refresh Token
              </Button>
              <Button variant="primary" onClick={() => setIsQrModalOpen(false)}>
                Close Projector
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Confirm End Session Dialog */}
      <ConfirmDialog
        isOpen={isEndModalOpen}
        onClose={() => setIsEndModalOpen(false)}
        onConfirm={handleConfirmEndSession}
        title="End Attendance Session?"
        message="Are you sure you want to end this attendance broadcast? Students will no longer be able to scan this QR code, and final counts will be logged into attendance records."
        confirmText="End Session"
        cancelText="Keep Broadcasting"
        isDanger={true}
        isLoading={isEnding}
      />
    </DashboardLayout>
  );
};

export default QrAttendance;
