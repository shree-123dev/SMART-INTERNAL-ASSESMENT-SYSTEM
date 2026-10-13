import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import Logo from '../components/Logo';
import { FiSun, FiMoon, FiUsers } from 'react-icons/fi';
import { FaChalkboardTeacher } from 'react-icons/fa';
import { IoLogOutOutline } from 'react-icons/io5';

const DashboardLayout = ({
  title = 'Dashboard',
  emoji = '🛡️',
  welcomeLine = 'Welcome to Central Management Console',
  navItems = [],
  children
}) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isActive = (path) => {
    if (path === '/admin') {
      return location.pathname === '/admin' || location.pathname === '/admin/';
    }
    if (path === '/teacher') {
      return location.pathname === '/teacher' || location.pathname === '/teacher/';
    }
    return location.pathname === path || location.pathname.startsWith(`${path}/`);
  };

  return (
    <div className="siams-dashboard-layout">
      {/* Dark Navy Sidebar (#0f172a) */}
      <aside className="siams-sidebar">
        <div className="sidebar-header">
          <Logo size="md" subtitle="" light={true} />
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => {
            const active = isActive(item.path);
            return (
              <div
                key={item.label}
                className={`sidebar-item ${active ? 'active' : ''}`}
                onClick={() => navigate(item.path)}
              >
                <span style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center' }}>
                  {item.icon}
                </span>
                <span>{item.label}</span>
              </div>
            );
          })}
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

      {/* Main Content Area */}
      <main className="dashboard-main">
        {/* Top Header Card matching screenshots */}
        <header className="dashboard-topbar">
          <div className="dashboard-title-area">
            <h1 className="dashboard-heading">
              <span>{title}</span>
              {emoji && <span style={{ fontSize: '1.25rem' }}>{emoji}</span>}
            </h1>
            <p className="dashboard-subheading">{welcomeLine}</p>
          </div>

          <div className="dashboard-actions-area">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label="Toggle theme"
              title="Toggle theme"
            >
              {theme === 'dark' ? <FiSun size={19} color="#f59e0b" /> : <FiMoon size={19} />}
            </button>

            {/* User chip */}
            <div className="user-profile-badge">
              <div
                className="profile-avatar-circle"
                style={{
                  background:
                    user?.role === 'admin'
                      ? '#f59e0b'
                      : user?.role === 'teacher'
                      ? '#0284c7'
                      : '#7c3aed'
                }}
              >
                {user?.role === 'teacher' ? <FaChalkboardTeacher size={16} /> : <FiUsers size={16} />}
              </div>
              <div className="profile-info">
                <span className="profile-name">{user?.name || 'System Administrator'}</span>
                <span
                  style={{
                    fontSize: '0.6875rem',
                    fontWeight: 700,
                    color:
                      user?.role === 'admin'
                        ? '#d97706'
                        : user?.role === 'teacher'
                        ? '#0284c7'
                        : '#7c3aed',
                    letterSpacing: '0.04em'
                  }}
                >
                  {user?.roleLabel || 'ADMINISTRATOR'}
                </span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <div className="dashboard-content">{children}</div>
      </main>
    </div>
  );
};

export default DashboardLayout;
