import React from 'react';
import { FaGraduationCap } from 'react-icons/fa';
import { HiShieldCheck } from 'react-icons/hi';

const Logo = ({ size = 'md', showText = true, subtitle = 'SMART ASSESSMENT', light = false }) => {
  const iconSizes = {
    sm: 32,
    md: 40,
    lg: 52
  };

  const dim = iconSizes[size] || 40;

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.75rem', userSelect: 'none' }}>
      <div
        style={{
          width: dim,
          height: dim,
          background: 'linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%)',
          borderRadius: size === 'sm' ? '8px' : '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(37, 99, 235, 0.25)',
          color: '#ffffff',
          position: 'relative',
          flexShrink: 0
        }}
      >
        <HiShieldCheck size={dim * 0.7} style={{ opacity: 0.95 }} />
        <FaGraduationCap
          size={dim * 0.4}
          style={{
            position: 'absolute',
            top: '22%',
            color: '#93c5fd'
          }}
        />
      </div>

      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <span
            style={{
              fontFamily: 'var(--font-family)',
              fontWeight: 800,
              fontSize: size === 'sm' ? '1.15rem' : size === 'lg' ? '1.5rem' : '1.3rem',
              letterSpacing: '-0.02em',
              color: light ? '#ffffff' : 'var(--text-main)',
              lineHeight: 1.1
            }}
          >
            SIAMS
          </span>
          {subtitle && (
            <span
              style={{
                fontFamily: 'var(--font-family)',
                fontSize: size === 'sm' ? '0.625rem' : '0.6875rem',
                fontWeight: 700,
                letterSpacing: '0.08em',
                color: light ? '#94a3b8' : 'var(--text-muted)',
                marginTop: '1px'
              }}
            >
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  );
};

export default Logo;
