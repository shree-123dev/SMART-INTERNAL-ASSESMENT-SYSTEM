import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { TEACHER_NAV_ITEMS } from './teacherNav';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import { assignmentService } from '../../services/assignmentService';
import { subjectService } from '../../services/subjectService';
import { sessionService } from '../../services/sessionService';
import { marksService } from '../../services/marksService';
import { attendanceService } from '../../services/attendanceService';

// Icons
import {
  FiSave,
  FiCheckCircle,
  FiAlertCircle,
  FiAward
} from 'react-icons/fi';
import { IoQrCodeOutline } from 'react-icons/io5';
import { FaFlask } from 'react-icons/fa';

const LabEvaluation = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const subjectIdParam = searchParams.get('subjectId');
  const sessionIdParam = searchParams.get('sessionId');

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [selectedSubjectId, setSelectedSubjectId] = useState(subjectIdParam || '');
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(sessionIdParam || '');
  const [practicalMarks, setPracticalMarks] = useState({}); // { [studentId]: mark }
  const [errors, setErrors] = useState({}); // { [studentId]: errorMessage }
  const [cumulativeAverages, setCumulativeAverages] = useState({}); // { [studentId]: avg }
  const [classStudents, setClassStudents] = useState([]);
  const [toastMessage, setToastMessage] = useState('');

  // 1. Load teacher assigned subjects
  useEffect(() => {
    const loadSubjects = async () => {
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

        if (!selectedSubjectId && mySubjects.length > 0) {
          const initialId = subjectIdParam || mySubjects[0].id;
          setSelectedSubjectId(initialId);
        }
      } catch (err) {
        console.error('Failed to load assigned subjects:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSubjects();
  }, [user?.id]);

  // 2. Load sessions and class students for selected subject
  useEffect(() => {
    if (!selectedSubjectId || !user?.id) {
      setSessions([]);
      setSelectedSessionId('');
      return;
    }

    const loadSessionsForSubject = async () => {
      try {
        setLoading(true);
        const [allTeacherSessions, students, averages] = await Promise.all([
          sessionService.getByTeacher(user.id),
          attendanceService.getClassStudents(selectedSubjectId),
          marksService.getAllStudentsPracticalAverages(selectedSubjectId)
        ]);

        const subjectSessions = allTeacherSessions.filter(
          (s) => s.subjectId === selectedSubjectId
        );
        setSessions(subjectSessions);
        setClassStudents(students);
        setCumulativeAverages(averages);

        if (subjectSessions.length > 0) {
          if (sessionIdParam && subjectSessions.some((s) => s.id === sessionIdParam)) {
            setSelectedSessionId(sessionIdParam);
          } else if (!selectedSessionId || !subjectSessions.some((s) => s.id === selectedSessionId)) {
            setSelectedSessionId(subjectSessions[0].id);
          }
        } else {
          setSelectedSessionId('');
        }
      } catch (err) {
        console.error('Failed to load sessions for subject:', err);
      } finally {
        setLoading(false);
      }
    };

    loadSessionsForSubject();
  }, [selectedSubjectId, user?.id]);

  // 3. Load practical marks for selected session
  useEffect(() => {
    if (!selectedSessionId) {
      setPracticalMarks({});
      setErrors({});
      return;
    }

    const loadSessionMarks = async () => {
      try {
        const existingPractical = await marksService.getPracticalMarks(selectedSessionId);
        const map = {};
        existingPractical.forEach((record) => {
          map[record.studentId] = record.marks !== null && record.marks !== undefined ? record.marks : '';
        });
        setPracticalMarks(map);
        setErrors({});
      } catch (err) {
        console.error('Failed to load session practical marks:', err);
      }
    };

    loadSessionMarks();
  }, [selectedSessionId]);

  const selectedSession = sessions.find((s) => s.id === selectedSessionId);
  const selectedSubject = assignedSubjects.find((s) => s.id === selectedSubjectId);

  // Attendees for the selected session
  const attendees = selectedSession?.attended || [];

  // Range validation handler
  const handleMarkChange = (studentId, rawVal) => {
    const val = rawVal.trim();
    let err = '';

    if (val !== '') {
      const num = Number(val);
      if (isNaN(num)) {
        err = 'Must be a number';
      } else if (num < 0 || num > 15) {
        err = '0 - 15 only';
      }
    }

    setPracticalMarks((prev) => ({
      ...prev,
      [studentId]: val
    }));

    setErrors((prev) => ({
      ...prev,
      [studentId]: err
    }));

    if (toastMessage) setToastMessage('');
  };

  const hasErrors = Object.values(errors).some((e) => !!e);

  // Save practical marks
  const handleSaveMarks = async () => {
    if (hasErrors || !selectedSessionId || !selectedSubjectId) return;

    try {
      setSaving(true);
      const marksList = attendees.map((attendee) => {
        // Resolve studentId if present in attendee, or find by USN
        const std = classStudents.find((s) => s.usn.toUpperCase() === attendee.usn.toUpperCase());
        const studentId = attendee.studentId || std?.id;
        return {
          studentId,
          marks: practicalMarks[studentId]
        };
      }).filter((m) => !!m.studentId);

      await marksService.savePracticalMarks(selectedSessionId, selectedSubjectId, marksList);

      // Refresh cumulative averages
      const updatedAverages = await marksService.getAllStudentsPracticalAverages(selectedSubjectId);
      setCumulativeAverages(updatedAverages);

      setToastMessage('Lab practical evaluations recorded and saved successfully!');
      setTimeout(() => {
        setToastMessage('');
      }, 4000);
    } catch (err) {
      console.error('Failed to save lab marks:', err);
      alert('Error saving lab evaluations: ' + (err.message || 'Unknown error'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout
      title="Lab Practical Evaluation"
      emoji="🧪"
      welcomeLine={`Welcome, ${user?.name || 'Faculty Member'} 👋 • Laboratory experiment scoring rubrics (/15 scale)`}
      navItems={TEACHER_NAV_ITEMS}
    >
      {/* Subject & Session Picker Card */}
      <Card padding="md">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr auto', gap: '1.25rem', alignItems: 'flex-end' }}>
          <div>
            <label className="siams-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
              Curriculum Course:
            </label>
            <select
              className="siams-input"
              value={selectedSubjectId}
              onChange={(e) => {
                setSelectedSubjectId(e.target.value);
                setSearchParams({ subjectId: e.target.value });
              }}
              disabled={loading || assignedSubjects.length === 0}
            >
              {assignedSubjects.map((sub) => (
                <option key={sub.id} value={sub.id}>
                  {sub.code} - {sub.name} ({sub.department} Sem {sub.semester})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="siams-label" style={{ marginBottom: '0.35rem', display: 'block' }}>
              Experiment Session to Evaluate:
            </label>
            <select
              className="siams-input"
              value={selectedSessionId}
              onChange={(e) => {
                setSelectedSessionId(e.target.value);
                setSearchParams({ subjectId: selectedSubjectId, sessionId: e.target.value });
              }}
              disabled={loading || sessions.length === 0}
            >
              {sessions.length === 0 && (
                <option value="" disabled>No sessions recorded yet</option>
              )}
              {sessions.map((sess) => (
                <option key={sess.id} value={sess.id}>
                  Exp #{sess.experimentNumber}: {sess.experimentName} ({sess.attended?.length || 0} present) - {new Date(sess.createdAt).toLocaleDateString()}
                </option>
              ))}
            </select>
          </div>

          <Button
            variant="primary"
            size="md"
            icon={<FiSave />}
            disabled={saving || !selectedSessionId || attendees.length === 0 || hasErrors}
            onClick={handleSaveMarks}
          >
            {saving ? 'Saving...' : 'Save Evaluations'}
          </Button>
        </div>
      </Card>

      {/* Success Notification */}
      {toastMessage && (
        <div
          style={{
            padding: '1rem 1.25rem',
            backgroundColor: 'var(--status-success-bg)',
            border: '1px solid #86efac',
            borderRadius: 'var(--radius-card)',
            color: 'var(--status-success)',
            fontSize: '0.9375rem',
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: '0.75rem',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <FiCheckCircle size={20} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* No Sessions Empty State */}
      {sessions.length === 0 && !loading && (
        <Card padding="lg">
          <div style={{ textAlign: 'center', padding: '2.5rem 1rem', color: 'var(--text-muted)' }}>
            <FaFlask size={44} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
            <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
              No Lab Sessions Recorded
            </h3>
            <p style={{ maxWidth: '440px', margin: '0 auto 1.5rem auto', fontSize: '0.9rem' }}>
              No classroom or laboratory sessions have been started for {selectedSubject?.code || 'this course'} yet. Start a session to record student attendance and score practical rubrics.
            </p>
            <Button
              variant="primary"
              icon={<IoQrCodeOutline />}
              onClick={() => navigate(`/teacher/qr?subjectId=${selectedSubjectId}`)}
            >
              Start Session in QR Attendance
            </Button>
          </div>
        </Card>
      )}

      {/* Active Evaluation Table */}
      {selectedSession && (
        <Card padding="none">
          <div
            style={{
              padding: '1.25rem 1.5rem',
              borderBottom: '1px solid var(--border-color)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              flexWrap: 'wrap',
              gap: '0.75rem'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <Badge variant="pill">Exp #{selectedSession.experimentNumber}</Badge>
                <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  {selectedSession.experimentName}
                </h3>
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                Conducted on {new Date(selectedSession.createdAt).toLocaleDateString()} • {attendees.length} Students Verified Present
              </p>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <Badge variant="primary">Scale: /15 Practical Rubric</Badge>
              <Badge variant="success">Min Passing: 10/15</Badge>
            </div>
          </div>

          <div style={{ overflowX: 'auto', width: '100%' }}>
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
                  <th style={{ padding: '0.85rem 1.25rem' }}>USN</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Student Name</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Scan Time</th>
                  <th style={{ padding: '0.85rem 1.25rem', width: '150px' }}>Practical Marks (/15)</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Cumulative Avg across Exps</th>
                  <th style={{ padding: '0.85rem 1.25rem', textAlign: 'center' }}>Rubric Status</th>
                </tr>
              </thead>
              <tbody>
                {attendees.length === 0 ? (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
                      No students were marked present during this session.
                    </td>
                  </tr>
                ) : (
                  attendees.map((attendee) => {
                    const std = classStudents.find((s) => s.usn.toUpperCase() === attendee.usn.toUpperCase());
                    const studentId = attendee.studentId || std?.id;
                    const markVal = practicalMarks[studentId];
                    const err = errors[studentId];
                    const numMark = markVal !== '' && markVal !== undefined ? Number(markVal) : null;
                    const studentAvg = cumulativeAverages[studentId];

                    return (
                      <tr key={attendee.usn} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '0.85rem 1.25rem', fontWeight: 800, color: '#2563eb' }}>
                          {attendee.usn}
                        </td>
                        <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>
                          {attendee.studentName || std?.fullName}
                        </td>
                        <td style={{ padding: '0.85rem 1.25rem', color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                          {attendee.timestamp || 'Verified'}
                        </td>

                        {/* Practical Mark Input /15 */}
                        <td style={{ padding: '0.65rem 1.25rem' }}>
                          <input
                            type="number"
                            step="0.5"
                            min="0"
                            max="15"
                            className={`siams-input ${err ? 'siams-input-error' : ''}`}
                            style={{ padding: '0.45rem 0.75rem', width: '110px', textAlign: 'center', fontWeight: 700 }}
                            value={markVal !== undefined ? markVal : ''}
                            onChange={(e) => handleMarkChange(studentId, e.target.value)}
                            placeholder="0 - 15"
                          />
                          {err && (
                            <span style={{ fontSize: '0.75rem', color: '#ef4444', display: 'block', marginTop: '0.2rem' }}>
                              {err}
                            </span>
                          )}
                        </td>

                        {/* Cumulative Practical Average */}
                        <td style={{ padding: '0.85rem 1.25rem' }}>
                          {studentAvg !== undefined ? (
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span style={{ fontWeight: 800, fontSize: '0.95rem', color: studentAvg >= 10 ? '#10b981' : '#f59e0b' }}>
                                {studentAvg} / 15
                              </span>
                              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                (feeds CIE)
                              </span>
                            </div>
                          ) : (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.8125rem' }}>
                              First evaluation
                            </span>
                          )}
                        </td>

                        {/* Rubric Badge */}
                        <td style={{ padding: '0.85rem 1.25rem', textAlign: 'center' }}>
                          {numMark !== null && !isNaN(numMark) ? (
                            <Badge variant={numMark >= 10 ? 'success' : 'danger'} size="sm">
                              {numMark >= 10 ? 'Cleared (≥10)' : 'Below Min (<10)'}
                            </Badge>
                          ) : (
                            <Badge variant="warning" size="sm">
                              Pending
                            </Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Cohort Practical Average Summary Table (Feeds Practical /15 in CIE) */}
      {classStudents.length > 0 && (
        <Card padding="none" style={{ marginTop: '2rem' }}>
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
                Cohort Cumulative Practical Averages ({selectedSubject?.code})
              </h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', marginTop: '0.15rem' }}>
                Calculated across all evaluated lab experiments. This value directly feeds the Practical /15 column in CIE Marks Entry.
              </p>
            </div>
            <Button
              variant="secondary"
              size="sm"
              icon={<FiAward />}
              onClick={() => navigate(`/teacher/cie?subjectId=${selectedSubjectId}`)}
            >
              Open CIE Marks Entry
            </Button>
          </div>

          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '0.875rem',
                textAlign: 'left'
              }}
            >
              <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)' }}>
                <tr>
                  <th style={{ padding: '0.85rem 1.25rem' }}>USN</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Student Name</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Section</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Practical Avg (/15)</th>
                  <th style={{ padding: '0.85rem 1.25rem' }}>Minimum 10/15 Rule</th>
                </tr>
              </thead>
              <tbody>
                {classStudents.map((std) => {
                  const avg = cumulativeAverages[std.id];
                  return (
                    <tr key={std.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 800, color: '#2563eb' }}>
                        {std.usn}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 600 }}>
                        {std.fullName}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>
                        <Badge variant="pill" size="sm">{std.section || 'A'}</Badge>
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem', fontWeight: 800 }}>
                        {avg !== undefined ? (
                          <span style={{ color: avg >= 10 ? '#10b981' : '#ef4444', fontSize: '0.95rem' }}>
                            {avg} / 15
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Not yet evaluated</span>
                        )}
                      </td>
                      <td style={{ padding: '0.85rem 1.25rem' }}>
                        {avg !== undefined ? (
                          <Badge variant={avg >= 10 ? 'success' : 'danger'} size="sm">
                            {avg >= 10 ? 'Pass Cleared' : 'Shortage Fail'}
                          </Badge>
                        ) : (
                          <Badge variant="warning" size="sm">Pending</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </DashboardLayout>
  );
};

export default LabEvaluation;
