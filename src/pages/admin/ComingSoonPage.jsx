import React from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../../layouts/DashboardLayout';
import { ADMIN_NAV_ITEMS } from './adminNav';
import Button from '../../components/Button';
import Badge from '../../components/Badge';
import { FiArrowLeft, FiClock } from 'react-icons/fi';

const ComingSoonPage = ({ title, description, icon: Icon = FiClock }) => {
  const navigate = useNavigate();

  return (
    <DashboardLayout
      title="Admin Dashboard"
      emoji="🛡️"
      welcomeLine="Welcome, System Administrator 👋 • SIAMS Central Management Console"
      navItems={ADMIN_NAV_ITEMS}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '20px',
          padding: '4rem 2rem',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
          maxWidth: '680px',
          margin: '2rem auto'
        }}
      >
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: '20px',
            background: 'var(--primary-light)',
            color: 'var(--primary-color)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '2rem',
            marginBottom: '1.5rem',
            boxShadow: 'var(--shadow-sm)'
          }}
        >
          <Icon />
        </div>

        <Badge variant="pill" size="md" style={{ marginBottom: '1rem' }}>
          Module In Development
        </Badge>

        <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.02em', marginBottom: '0.75rem' }}>
          {title}
        </h2>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', lineHeight: 1.6, maxWidth: '480px', marginBottom: '2rem' }}>
          {description ||
            'This enterprise academic module is slated for deployment in the upcoming university audit release cycle.'}
        </p>

        <Button variant="primary" icon={<FiArrowLeft />} onClick={() => navigate('/admin')}>
          Return to Admin Hub
        </Button>
      </div>
    </DashboardLayout>
  );
};

export default ComingSoonPage;
