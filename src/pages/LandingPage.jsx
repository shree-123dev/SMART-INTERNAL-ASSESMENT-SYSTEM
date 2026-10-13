import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';
import Logo from '../components/Logo';
import Button from '../components/Button';
import Card from '../components/Card';
import Badge from '../components/Badge';

// Icons
import {
  FiSun,
  FiMoon,
  FiLogIn,
  FiCompass,
  FiCheckCircle,
  FiActivity,
  FiLayers,
  FiAward
} from 'react-icons/fi';
import { FaRocket, FaGraduationCap } from 'react-icons/fa';
import {
  IoQrCodeOutline,
  IoFlaskOutline,
  IoAnalyticsOutline,
  IoDocumentTextOutline,
  IoShieldCheckmarkOutline,
  IoCalculatorOutline
} from 'react-icons/io5';
import { QRCodeSVG } from 'qrcode.react';

const LandingPage = () => {
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleScrollTo = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const featureList = [
    {
      title: 'QR Attendance',
      desc: 'Dynamic rolling QR codes with anti-proxy validation for effortless, fraud-free classroom check-ins.',
      icon: <IoQrCodeOutline />,
      color: '#2563eb',
      bg: '#eff6ff',
      badge: 'Real-Time'
    },
    {
      title: 'IA Calculation',
      desc: 'Automate Continuous Internal Evaluation (CIE) formulas following strict university accreditation rules.',
      icon: <IoCalculatorOutline />,
      color: '#7c3aed',
      bg: '#f5f3ff',
      badge: 'Automated'
    },
    {
      title: 'Practical Labs',
      desc: 'Live experiment marking, viva scoring, rubric tracking, and digital laboratory observation logs.',
      icon: <IoFlaskOutline />,
      color: '#059669',
      bg: '#ecfdf5',
      badge: 'Continuous'
    },
    {
      title: 'Live Analytics',
      desc: 'High-visibility visual dashboards, student performance cohorts, pass rate projections, and alerts.',
      icon: <IoAnalyticsOutline />,
      color: '#d97706',
      bg: '#fffbeb',
      badge: 'Insights'
    },
    {
      title: 'Instant Reports',
      desc: 'Generate consolidated CIE sheets, 75% attendance eligibility rosters, and audit-ready PDF/Excel sheets.',
      icon: <IoDocumentTextOutline />,
      color: '#0284c7',
      bg: '#f0f9ff',
      badge: 'One-Click'
    },
    {
      title: 'Role-Based Access',
      desc: 'Fine-grained permissions and dedicated portals tailored specifically for Admins, Faculty, and Students.',
      icon: <IoShieldCheckmarkOutline />,
      color: '#4f46e5',
      bg: '#eef2ff',
      badge: 'Encrypted'
    }
  ];

  const workflowSteps = [
    {
      step: '01',
      title: 'Curriculum & Roster Setup',
      desc: 'Administrators define subjects, create semester batches, and map faculty to courses in minutes.'
    },
    {
      step: '02',
      title: 'Dynamic QR Generation',
      desc: 'Faculty activates an interactive, time-sensitive QR code on the lecture screen for students to scan.'
    },
    {
      step: '03',
      title: 'Direct Marks & Lab Entry',
      desc: 'Grade CIE tests, assignments, and practical experiments with instant formula consolidation.'
    },
    {
      step: '04',
      title: 'Audit & Institutional Analytics',
      desc: 'Export compliant accreditation ledgers and identify at-risk students before final university exams.'
    }
  ];

  return (
    <div className="siams-landing">
      {/* Sticky Navbar */}
      <header className="siams-navbar">
        <div className="siams-nav-container">
          <div onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })} style={{ cursor: 'pointer' }}>
            <Logo size="md" subtitle="SMART ASSESSMENT" />
          </div>

          <nav>
            <ul className="siams-nav-links">
              <li>
                <a href="#home" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="siams-nav-link active">
                  Home
                </a>
              </li>
              <li>
                <a href="#features" onClick={(e) => { e.preventDefault(); handleScrollTo('features'); }} className="siams-nav-link">
                  Features
                </a>
              </li>
              <li>
                <a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleScrollTo('how-it-works'); }} className="siams-nav-link">
                  How It Works
                </a>
              </li>
              <li>
                <a href="#about" onClick={(e) => { e.preventDefault(); handleScrollTo('about'); }} className="siams-nav-link">
                  About
                </a>
              </li>
            </ul>
          </nav>

          <div className="siams-nav-actions">
            <button
              type="button"
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label="Toggle color theme"
              title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
            >
              {theme === 'dark' ? <FiSun size={19} color="#f59e0b" /> : <FiMoon size={19} />}
            </button>

            <Button
              variant="primary"
              size="md"
              icon={<FiLogIn size={18} />}
              onClick={() => navigate('/login')}
            >
              Login Portal
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="siams-hero-section" id="home">
        <div className="hero-left">
          <div className="hero-badge-container">
            <Badge variant="pill" size="md">
              ⚡ Next-Gen College ERP Solution
            </Badge>
          </div>

          <h1 className="hero-title">
            Smart Internal Assessment & <span className="hero-title-highlight">Practical Evaluation</span> System
          </h1>

          <p className="hero-desc">
            Automate student attendance with dynamic mobile QR scanning, streamline continuous
            internal evaluation (CIE), record practical marks in real-time, and generate
            instant institutional analytics.
          </p>

          <div className="hero-cta-group">
            <Button
              variant="primary"
              size="lg"
              icon={<FaRocket />}
              onClick={() => navigate('/login')}
            >
              Get Started
            </Button>

            <Button
              variant="secondary"
              size="lg"
              icon={<FiCompass size={19} />}
              onClick={() => handleScrollTo('features')}
            >
              Explore Features
            </Button>
          </div>
        </div>

        {/* Hero Right: Card with Visual / QR Mockup & Stats */}
        <div className="hero-right">
          <div className="hero-card">
            <div className="hero-visual-container">
              {/* Modern tech illustration mockup using react-icons & qrcode.react */}
              <div className="hero-illustration-mockup">
                <div className="mockup-top-bar">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} />
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }} />
                    <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
                    <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                      Live Faculty Console
                    </span>
                  </div>
                  <Badge variant="success" size="sm">
                    ● Active Session
                  </Badge>
                </div>

                <div className="mockup-grid">
                  <div className="mockup-box" style={{ alignItems: 'center', textAlign: 'center', justifyContent: 'center' }}>
                    <div style={{ padding: '0.5rem', background: '#ffffff', borderRadius: '10px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)' }}>
                      <QRCodeSVG
                        value="https://siams.edu/verify?session=CS302_LIVE"
                        size={84}
                        fgColor="#1e3a8a"
                        bgColor="#ffffff"
                        level="M"
                      />
                    </div>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#2563eb', marginTop: '0.25rem' }}>
                      Scan via Student App
                    </span>
                  </div>

                  <div className="mockup-box" style={{ justifyContent: 'space-between' }}>
                    <div className="mockup-box-header">
                      <FiActivity style={{ color: '#2563eb' }} />
                      <span>Live CIE Status</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Present:</span>
                        <strong style={{ color: '#10b981' }}>58 / 60 (96.7%)</strong>
                      </div>
                      <div style={{ width: '100%', height: 6, background: 'var(--bg-secondary)', borderRadius: 3, overflow: 'hidden' }}>
                        <div style={{ width: '96.7%', height: '100%', background: 'linear-gradient(90deg, #3b82f6, #10b981)' }} />
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginTop: '0.2rem' }}>
                        <span style={{ color: 'var(--text-muted)' }}>Avg CIE:</span>
                        <strong style={{ color: 'var(--text-main)' }}>44.5 / 50</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom 3-column stats row */}
            <div className="hero-stats-row">
              <div className="hero-stat-col">
                <span className="stat-value">100%</span>
                <span className="stat-label">Paperless</span>
              </div>
              <div className="hero-stat-col">
                <span className="stat-value">Instant</span>
                <span className="stat-label">QR Scanning</span>
              </div>
              <div className="hero-stat-col">
                <span className="stat-value">3 Roles</span>
                <span className="stat-label">Admin, Faculty, Student</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="siams-section" id="features">
        <div className="section-header">
          <Badge variant="pill" size="md">
            Features Overview
          </Badge>
          <h2 className="section-title">Built for Modern Academic Workflows</h2>
          <p className="section-desc">
            Replace manual ledgers, paper sign-in sheets, and error-prone marksheets with an
            all-in-one institutional grading platform.
          </p>
        </div>

        <div className="features-grid">
          {featureList.map((feature, idx) => (
            <Card key={idx} hoverEffect padding="none">
              <div className="feature-card">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div
                    className="feature-icon-wrapper"
                    style={{ background: feature.bg, color: feature.color }}
                  >
                    {feature.icon}
                  </div>
                  <Badge variant="pill" size="sm">
                    {feature.badge}
                  </Badge>
                </div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-desc">{feature.desc}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* How It Works Section */}
      <section className="siams-section" id="how-it-works" style={{ backgroundColor: 'var(--bg-secondary)', borderRadius: '24px' }}>
        <div className="section-header">
          <Badge variant="pill" size="md">
            Step-by-Step Flow
          </Badge>
          <h2 className="section-title">How SIAMS Powers Your Campus</h2>
          <p className="section-desc">
            A unified pipeline bridging curriculum management, real-time classroom participation, and accreditation audits.
          </p>
        </div>

        <div className="how-steps-grid">
          {workflowSteps.map((item, idx) => (
            <Card key={idx} padding="md" hoverEffect>
              <div className="step-card">
                <div className="step-number-badge">{item.step}</div>
                <h3 className="step-title">{item.title}</h3>
                <p className="step-desc">{item.desc}</p>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* About Section */}
      <section className="siams-section" id="about">
        <Card padding="lg">
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '3rem', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <Badge variant="pill" size="md" style={{ alignSelf: 'flex-start' }}>
                About SIAMS Platform
              </Badge>
              <h2 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                Next-Generation Continuous Internal Evaluation
              </h2>
              <p style={{ color: 'var(--text-muted)', lineHeight: 1.7, fontSize: '1rem' }}>
                SIAMS (Smart Internal Assessment & Practical Evaluation System) was created to eliminate the friction
                of institutional assessments. By integrating dynamic QR code attendance with automated formula calculations,
                faculty save hundreds of administrative hours while colleges gain transparent, audit-ready student performance records.
              </p>
              <div style={{ display: 'flex', gap: '2rem', marginTop: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  <FiCheckCircle color="#10b981" size={18} />
                  <span>University Compliant</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: 'var(--text-main)' }}>
                  <FiCheckCircle color="#10b981" size={18} />
                  <span>Role-Based Security</span>
                </div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-secondary)', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '1rem', color: 'var(--text-main)' }}>
                Institutional Highlights
              </h4>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9375rem', color: 'var(--text-muted)' }}>
                  <FiAward color="#2563eb" /> 100% Paperless Assessment Workflows
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9375rem', color: 'var(--text-muted)' }}>
                  <FiLayers color="#2563eb" /> Unified Theory CIE & Practical Labs
                </li>
                <li style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.9375rem', color: 'var(--text-muted)' }}>
                  <IoShieldCheckmarkOutline color="#2563eb" /> Automated 75% Attendance Eligibility Filter
                </li>
              </ul>
            </div>
          </div>
        </Card>
      </section>

      {/* Footer */}
      <footer className="siams-footer">
        <div className="footer-container">
          <div className="footer-brand">
            <Logo size="md" subtitle="SMART ASSESSMENT" />
            <p className="footer-desc">
              Comprehensive academic enterprise portal for continuous evaluation, laboratory assessments,
              and attendance governance.
            </p>
          </div>

          <div>
            <h4 className="footer-col-title">Portals</h4>
            <ul className="footer-links">
              <li><a href="/login" className="footer-link">Admin Console</a></li>
              <li><a href="/login" className="footer-link">Faculty Portal</a></li>
              <li><a href="/login" className="footer-link">Student Hub</a></li>
              <li><a href="/login" className="footer-link">Lab Evaluation</a></li>
            </ul>
          </div>

          <div>
            <h4 className="footer-col-title">Navigation</h4>
            <ul className="footer-links">
              <li><a href="#home" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="footer-link">Home</a></li>
              <li><a href="#features" onClick={(e) => { e.preventDefault(); handleScrollTo('features'); }} className="footer-link">Features</a></li>
              <li><a href="#how-it-works" onClick={(e) => { e.preventDefault(); handleScrollTo('how-it-works'); }} className="footer-link">How It Works</a></li>
              <li><a href="#about" onClick={(e) => { e.preventDefault(); handleScrollTo('about'); }} className="footer-link">About SIAMS</a></li>
            </ul>
          </div>

          <div>
            <h4 className="footer-col-title">Compliance</h4>
            <ul className="footer-links">
              <li><span className="footer-link">AICTE & UGC Standards</span></li>
              <li><span className="footer-link">NAAC Criteria II Ready</span></li>
              <li><span className="footer-link">NBA Outcome Based Prep</span></li>
              <li><span className="footer-link">Institutional Privacy</span></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <span>&copy; {new Date().getFullYear()} SIAMS Smart Assessment System. All rights reserved.</span>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <span>v2.4.0 ERP Release</span>
            <span>Security Audited</span>
          </div>
        </div>
      </footer>

      {/* Floating Theme Toggle (as pictured in screenshot 1 bottom right) */}
      <button
        type="button"
        className="floating-theme-toggle"
        onClick={toggleTheme}
        aria-label="Floating theme toggle"
        title="Toggle Theme"
      >
        {theme === 'dark' ? <FiSun size={20} color="#f59e0b" /> : <FiMoon size={20} />}
      </button>
    </div>
  );
};

export default LandingPage;
