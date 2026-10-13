import React, { createContext, useContext, useState, useEffect } from 'react';
import { getDB } from '../services/db';

const AuthContext = createContext();

const resolveUserFromDb = (baseUser) => {
  if (!baseUser) return null;
  const db = getDB();

  if (baseUser.role === 'teacher') {
    const teacher = db.teachers?.find(
      (t) =>
        t.email?.toLowerCase() === baseUser.email?.toLowerCase() ||
        t.id === baseUser.id
    );
    if (teacher) {
      return {
        ...baseUser,
        id: teacher.id,
        name: teacher.fullName,
        fullName: teacher.fullName,
        department: teacher.department,
        teacherCode: teacher.teacherCode,
        email: teacher.email,
        role: 'teacher',
        roleLabel: 'ACADEMIC FACULTY',
        avatar: '👩‍🏫'
      };
    }
  }

  if (baseUser.role === 'student') {
    const student = db.students?.find(
      (s) =>
        s.email?.toLowerCase() === baseUser.email?.toLowerCase() ||
        s.usn?.toUpperCase() === baseUser.usn?.toUpperCase() ||
        s.id === baseUser.id
    );
    if (student) {
      return {
        ...baseUser,
        id: student.id,
        name: student.fullName,
        fullName: student.fullName,
        usn: student.usn,
        department: student.department,
        semester: student.semester,
        section: student.section,
        email: student.email,
        role: 'student',
        roleLabel: 'STUDENT SCHOLAR',
        avatar: '🎓'
      };
    }
  }

  return baseUser;
};

const MOCK_CREDENTIALS = [
  {
    email: 'admin@test.com',
    password: 'admin123',
    user: {
      id: 'usr_001',
      name: 'System Administrator',
      email: 'admin@test.com',
      role: 'admin',
      roleLabel: 'ADMINISTRATOR',
      avatar: '🛡️',
      department: 'Central Administration'
    }
  },
  {
    email: 'teacher@test.com',
    password: 'teacher123',
    user: {
      id: 'tch_7',
      name: 'Dr. Rajesh Sharma',
      email: 'teacher@test.com',
      role: 'teacher',
      roleLabel: 'ACADEMIC FACULTY',
      avatar: '👩‍🏫',
      department: 'CSE'
    }
  },
  {
    email: 'student@test.com',
    password: 'student123',
    user: {
      id: 'std_6',
      name: 'Alex Johnson',
      email: 'student@test.com',
      role: 'student',
      roleLabel: 'STUDENT SCHOLAR',
      avatar: '🎓',
      usn: '1MS21CS042',
      department: 'CSE',
      semester: 6,
      section: 'A'
    }
  }
];

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('siams_auth_user');
    if (!saved) return null;
    try {
      const parsed = JSON.parse(saved);
      return resolveUserFromDb(parsed);
    } catch {
      return null;
    }
  });

  const role = user?.role || null;

  useEffect(() => {
    if (user) {
      localStorage.setItem('siams_auth_user', JSON.stringify(user));
    } else {
      localStorage.removeItem('siams_auth_user');
    }
  }, [user]);

  const login = (email, password) => {
    const trimmedEmail = email.trim().toLowerCase();
    const account = MOCK_CREDENTIALS.find(
      (acc) => acc.email.toLowerCase() === trimmedEmail && acc.password === password
    );

    if (account) {
      const resolved = resolveUserFromDb(account.user);
      setUser(resolved);
      return { success: true, user: resolved, role: resolved.role };
    } else {
      return {
        success: false,
        error: 'Invalid institutional credentials. Please verify your email and password.'
      };
    }
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, role, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
