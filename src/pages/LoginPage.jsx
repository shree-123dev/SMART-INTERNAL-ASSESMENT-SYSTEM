import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import Input from '../components/Input';
import Button from '../components/Button';
import Logo from '../components/Logo';

// Icons
import { HiOutlineMail, HiOutlineLockClosed } from 'react-icons/hi';
import { FiLogIn, FiArrowLeft, FiSun, FiMoon, FiAlertCircle } from 'react-icons/fi';

const LoginPage = () => {
  const { login } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    rememberMe: false
  });

  const [errors, setErrors] = useState({});
  const [authError, setAuthError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const validate = () => {
    const errs = {};
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    // Email validation
    if (!formData.email.trim()) {
      errs.email = 'Institutional email is required';
    } else if (!emailRegex.test(formData.email.trim())) {
      errs.email = 'Please enter a valid email address';
    }

    // Password validation
    if (!formData.password) {
      errs.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errs.password = 'Password must be at least 6 characters long';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
    if (authError) {
      setAuthError('');
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    setIsLoading(true);
    setAuthError('');

    setTimeout(() => {
      const result = login(formData.email, formData.password);
      setIsLoading(false);

      if (result.success) {
        // Redirect according to user role
        if (result.role === 'admin') {
          navigate('/admin');
        } else if (result.role === 'teacher') {
          navigate('/teacher');
        } else if (result.role === 'student') {
          navigate('/student');
        } else {
          navigate('/');
        }
      } else {
        setAuthError(result.error);
      }
    }, 400);
  };

  const handleFillDemo = (email, password) => {
    setFormData({
      email,
      password,
      rememberMe: true
    });
    setErrors({});
    setAuthError('');
  };

  return (
    <div className="siams-login-page">
      <div className="login-card-container">
        {/* Top gradient highlight bar */}
        <div className="login-card-top-accent" />

        <div className="login-card-inner">
          {/* Logo badge in rounded square container */}
          <div className="login-logo-box">
            <Logo size="sm" showText={false} />
          </div>

          <div className="login-header-text">
            <h1 className="login-title">Welcome to SIAMS</h1>
            <p className="login-subtitle">
              Sign in to access your role-based academic portal
            </p>
          </div>

          {authError && (
            <div
              style={{
                width: '100%',
                padding: '0.85rem 1rem',
                backgroundColor: 'var(--status-danger-bg)',
                border: '1px solid #fca5a5',
                borderRadius: 'var(--radius-md)',
                color: 'var(--status-danger)',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                marginBottom: '1.25rem'
              }}
            >
              <FiAlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{authError}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="login-form" noValidate>
            <Input
              label="Institutional Email"
              id="email"
              name="email"
              type="email"
              placeholder="e.g. name@college.edu"
              icon={<HiOutlineMail />}
              value={formData.email}
              onChange={handleChange}
              error={errors.email}
              required
              autoComplete="email"
            />

            <Input
              label="Password"
              id="password"
              name="password"
              type="password"
              placeholder="Enter your secure password"
              icon={<HiOutlineLockClosed />}
              value={formData.password}
              onChange={handleChange}
              error={errors.password}
              required
              autoComplete="current-password"
            />

            <div className="login-options-row">
              <label className="remember-label">
                <input
                  type="checkbox"
                  name="rememberMe"
                  checked={formData.rememberMe}
                  onChange={handleChange}
                  className="remember-checkbox"
                />
                Remember Me
              </label>

              <a
                href="#forgot"
                onClick={(e) => {
                  e.preventDefault();
                  alert('For password resets, contact your department campus administrator.');
                }}
                className="forgot-password-link"
              >
                Forgot Password?
              </a>
            </div>

            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              disabled={isLoading}
              icon={<FiLogIn size={18} />}
            >
              {isLoading ? 'Signing In...' : 'Sign In to Account'}
            </Button>
          </form>

          {/* Quick Demo Credentials for Testing */}
          <div className="demo-credentials-banner">
            <p>Demo Credentials (Click to Autofill):</p>
            <div className="demo-chips">
              <button
                type="button"
                className="demo-chip"
                onClick={() => handleFillDemo('admin@test.com', 'admin123')}
              >
                🛡️ Admin
              </button>
              <button
                type="button"
                className="demo-chip"
                onClick={() => handleFillDemo('teacher@test.com', 'teacher123')}
              >
                👩‍🏫 Teacher
              </button>
              <button
                type="button"
                className="demo-chip"
                onClick={() => handleFillDemo('student@test.com', 'student123')}
              >
                🎓 Student
              </button>
            </div>
          </div>

          <div className="login-footer-links">
            <div>
              Don't have an account yet?{' '}
              <a
                href="#register"
                onClick={(e) => {
                  e.preventDefault();
                  alert('Faculty and student registrations are managed by the campus administrator.');
                }}
                className="register-link"
              >
                Register Here
              </a>
            </div>

            <Link to="/" className="back-home-link">
              <FiArrowLeft size={16} />
              Back to Homepage
            </Link>
          </div>
        </div>
      </div>

      {/* Floating Theme Toggle */}
      <button
        type="button"
        className="floating-theme-toggle"
        onClick={toggleTheme}
        aria-label="Toggle theme"
        title="Toggle Theme"
      >
        {theme === 'dark' ? <FiSun size={20} color="#f59e0b" /> : <FiMoon size={20} />}
      </button>
    </div>
  );
};

export default LoginPage;
