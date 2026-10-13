import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { TEACHER_NAV_ITEMS } from './teacherNav';
import { useAuth } from '../../context/AuthContext';
import Card from '../../components/Card';
import Badge from '../../components/Badge';
import Button from '../../components/Button';
import DataTable from '../../components/DataTable';
import { assignmentService } from '../../services/assignmentService';
import { subjectService } from '../../services/subjectService';
import { attendanceService } from '../../services/attendanceService';
import { attendancePercent, requiredFutureSessions } from '../../utils/cie';

// Icons
import {
  FiBook,
  FiArrowLeft,
  FiUsers,
  FiCheckCircle,
  FiAlertTriangle
} from 'react-icons/fi';
import { IoQrCodeOutline } from 'react-icons/io5';

const MyClasses = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const subjectIdParam = searchParams.get('subjectId');

  const [loading, setLoading] = useState(true);
  const [assignedSubjects, setAssignedSubjects] = useState([]);
  const [subjectMeta, setSubjectMeta] = useState({});
  const [selectedSubjectId, setSelectedSubjectId] = useState(subjectIdParam || null);
  const [classData, setClassData] = useState(null);
  const [classLoading, setClassLoading] = useState(false);

  // Load teacher assigned subjects
  const loadAssignedSubjects = async () => {
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

      // Load enrolled counts and total sessions for cards
      const meta = {};
      for (const sub of mySubjects) {
        const stats = await attendanceService.getSubjectAttendanceStats(sub.id);
        const enrolled = stats.students.length;
        let avg = null;
        if (stats.totalSessions > 0 && enrolled > 0) {
          const sum = stats.students.reduce((acc, curr) => acc + (curr.percentage || 0), 0);
          avg = Number((sum / enrolled).toFixed(1));
        }
        meta[sub.id] = { enrolled, totalSessions: stats.totalSessions, avgAttendance: avg };
      }
      setSubjectMeta(meta);

      if (subjectIdParam && mySubjects.some((s) => s.id === subjectIdParam)) {
        setSelectedSubjectId(subjectIdParam);
      }
    } catch (err) {
      console.error('Failed to load classes:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignedSubjects();
  }, [user?.id]);

  // Load selected class attendance details
  useEffect(() => {
    if (!selectedSubjectId) {
      setClassData(null);
      return;
    }

    const loadClassDetails = async () => {
      try {
        setClassLoading(true);
        const stats = await attendanceService.getSubjectAttendanceStats(selectedSubjectId);
        setClassData(stats);
      } catch (err) {
        console.error('Failed to load class details:', err);
      } finally {
        setClassLoading(false);
      }
    };

    loadClassDetails();
  }, [selectedSubjectId]);

  const handleSelectSubject = (id) => {
    setSelectedSubjectId(id);
    setSearchParams({ subjectId: id });
  };

  const handleBackToList = () => {
    setSelectedSubjectId(null);
    setSearchParams({});
  };

  const selectedSubject = assignedSubjects.find((s) => s.id === selectedSubjectId);

  // DataTable columns for student class list
  const studentColumns = [
    {
      header: 'USN',
      key: 'usn',
      render: (row) => (
        <span style={{ fontWeight: 800, color: '#2563eb' }}>
          {row.student.usn}
        </span>
      )
    },
    {
      header: 'Student Name',
      key: 'fullName',
      render: (row) => (
        <div>
          <span style={{ fontWeight: 700 }}>{row.student.fullName}</span>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            {row.student.email}
          </div>
        </div>
      )
    },
    {
      header: 'Sec',
      key: 'section',
      render: (row) => (
        <Badge variant="pill" size="sm">
          {row.student.section || 'A'}
        </Badge>
      )
    },
    {
      header: 'Sessions Attended',
      key: 'attendedCount',
      render: (row) => (
        <span style={{ fontWeight: 600 }}>
          {row.attendedCount} / {row.totalSessions}
        </span>
      )
    },
    {
      header: 'Attendance %',
      key: 'percentage',
      render: (row) => {
        if (row.percentage === null) {
          return <span style={{ color: 'var(--text-muted)' }}>N/A (0 sessions)</span>;
        }
        const isSafe = row.percentage >= 75;
        return (
          <span
            style={{
              fontWeight: 800,
              color: isSafe ? '#10b981' : '#ef4444'
            }}
          >
            {row.percentage}%
          </span>
        );
      }
    },
    {
      header: '75% Eligibility',
      key: 'eligible',
      render: (row) => (
        <Badge variant={row.eligible ? 'success' : 'danger'} size="sm">
          {row.eligible ? 'Eligible' : 'Not Eligible'}
        </Badge>
      )
    },
    {
      header: 'Remediation / Makeup Status',
      key: 'requiredMore',
      render: (row) => {
        if (row.percentage === null || row.eligible) {
          return (
            <span style={{ fontSize: '0.8125rem', color: '#10b981', fontWeight: 600 }}>
              Requirement satisfied
            </span>
          );
        }
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: '#ef4444' }}>
            <FiAlertTriangle size={14} />
            <span style={{ fontSize: '0.8125rem', fontWeight: 700 }}>
              Attend {row.requiredMore} more session{row.requiredMore === 1 ? '' : 's'}
            </span>
          </div>
        );
      }
    }
  ];

  return (
    <DashboardLayout
      title="My Classes & Roster"
      emoji="📚"
      welcomeLine={`Welcome, ${user?.name || 'Faculty Member'} 👋 • Cohort student enrollments & 75% eligibility monitor`}
      navItems={TEACHER_NAV_ITEMS}
    >
      {selectedSubject ? (
        /* Detailed Class View */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
          {/* Header Bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <Button
                variant="secondary"
                icon={<FiArrowLeft />}
                onClick={handleBackToList}
              >
                Back to All Classes
              </Button>
              <div>
                <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--text-main)' }}>
                  {selectedSubject.code} - {selectedSubject.name}
                </h2>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                  {selectedSubject.department} • Semester {selectedSubject.semester} •{' '}
                  {classData?.students?.length || 0} Students Enrolled •{' '}
                  {classData?.totalSessions || 0} Sessions Conducted
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <Button
                variant="secondary"
                icon={<FiCheckCircle />}
                onClick={() => navigate(`/teacher/cie?subjectId=${selectedSubject.id}`)}
              >
                Enter CIE Marks
              </Button>
              <Button
                variant="primary"
                icon={<IoQrCodeOutline />}
                onClick={() => navigate(`/teacher/qr?subjectId=${selectedSubject.id}`)}
              >
                Start Session
              </Button>
            </div>
          </div>

          {/* Quick Metrics for this class */}
          <div className="metrics-row" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
            <Card padding="none">
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">ENROLLED COHORT</span>
                  <span className="metric-number">{classData?.students?.length || 0}</span>
                  <span className="metric-subtext">Registered student scholars</span>
                </div>
                <div className="metric-icon-box" style={{ background: '#ede9fe', color: '#7c3aed' }}>
                  <FiUsers />
                </div>
              </div>
            </Card>

            <Card padding="none">
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">TOTAL SESSIONS HELD</span>
                  <span className="metric-number">{classData?.totalSessions || 0}</span>
                  <span className="metric-subtext">Lecture / lab meetings</span>
                </div>
                <div className="metric-icon-box" style={{ background: '#e0f2fe', color: '#0284c7' }}>
                  <FiBook />
                </div>
              </div>
            </Card>

            <Card padding="none">
              <div className="metric-card">
                <div className="metric-info">
                  <span className="metric-label">75% ELIGIBILITY PASS RATE</span>
                  <span className="metric-number" style={{ color: '#10b981' }}>
                    {classData?.students?.length
                      ? `${Math.round(
                          (classData.students.filter((s) => s.eligible).length /
                            classData.students.length) *
                            100
                        )}%`
                      : '100%'}
                  </span>
                  <span className="metric-subtext">
                    {classData?.students?.filter((s) => !s.eligible).length || 0} students below 75%
                  </span>
                </div>
                <div className="metric-icon-box" style={{ background: '#dcfce7', color: '#16a34a' }}>
                  <FiCheckCircle />
                </div>
              </div>
            </Card>
          </div>

          {/* Student Table */}
          <DataTable
            columns={studentColumns}
            data={classData?.students || []}
            loading={classLoading}
            emptyMessage="No students found matching this subject's department and semester."
            rowKey={(row) => row.student.id}
          />
        </div>
      ) : (
        /* Cards View for Each Assigned Subject */
        <div>
          <div style={{ marginBottom: '1.5rem' }}>
            <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: 'var(--text-main)' }}>
              Assigned Curriculum Courses ({assignedSubjects.length})
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Select a class below to view its enrolled students, attendance percentages, and eligibility status.
            </p>
          </div>

          {loading ? (
            <div style={{ textAlign: 'center', padding: '3.5rem', color: 'var(--text-muted)' }}>
              Loading assigned classes...
            </div>
          ) : assignedSubjects.length === 0 ? (
            <Card padding="lg">
              <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-muted)' }}>
                <FiBook size={48} style={{ color: 'var(--text-dim)', marginBottom: '1rem' }} />
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  No Subjects Assigned
                </h3>
                <p style={{ fontSize: '0.9rem', maxWidth: '400px', margin: '0 auto' }}>
                  You currently have no curriculum courses mapped to your faculty profile. Contact the administrator to assign subjects.
                </p>
              </div>
            </Card>
          ) : (
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
                gap: '1.5rem'
              }}
            >
              {assignedSubjects.map((sub) => {
                const meta = subjectMeta[sub.id] || { enrolled: 0, totalSessions: 0, avgAttendance: null };
                return (
                  <Card
                    key={sub.id}
                    padding="none"
                    hoverEffect
                    onClick={() => handleSelectSubject(sub.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div style={{ padding: '1.5rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                        <Badge variant="primary" size="md">
                          {sub.code}
                        </Badge>
                        <Badge variant="pill">Semester {sub.semester}</Badge>
                      </div>

                      <h3
                        style={{
                          fontSize: '1.2rem',
                          fontWeight: 800,
                          color: 'var(--text-main)',
                          marginBottom: '0.5rem',
                          lineHeight: 1.3
                        }}
                      >
                        {sub.name}
                      </h3>

                      <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '1.25rem' }}>
                        Dept. of {sub.department} • Active Teaching Curriculum
                      </p>

                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: '1fr 1fr',
                          gap: '0.75rem',
                          padding: '0.85rem 1rem',
                          background: 'var(--bg-secondary)',
                          borderRadius: '12px',
                          border: '1px solid var(--border-color)',
                          marginBottom: '1.25rem'
                        }}
                      >
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                            Students
                          </span>
                          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)' }}>
                            {meta.enrolled}
                          </div>
                        </div>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>
                            Attendance Avg
                          </span>
                          <div
                            style={{
                              fontSize: '1.2rem',
                              fontWeight: 800,
                              color: meta.avgAttendance !== null && meta.avgAttendance >= 75 ? '#10b981' : '#f59e0b'
                            }}
                          >
                            {meta.avgAttendance !== null ? `${meta.avgAttendance}%` : 'N/A'}
                          </div>
                        </div>
                      </div>

                      <div
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          paddingTop: '0.75rem',
                          borderTop: '1px solid var(--border-color)'
                        }}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <Button
                          variant="secondary"
                          size="sm"
                          icon={<FiCheckCircle />}
                          onClick={() => navigate(`/teacher/cie?subjectId=${sub.id}`)}
                        >
                          Enter Marks
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          icon={<IoQrCodeOutline />}
                          onClick={() => navigate(`/teacher/qr?subjectId=${sub.id}`)}
                        >
                          Start Session
                        </Button>
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
};

export default MyClasses;
