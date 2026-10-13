import React from 'react';

const Input = ({
  label,
  id,
  name,
  type = 'text',
  placeholder = '',
  value,
  onChange,
  error = '',
  helperText = '',
  icon = null,
  required = false,
  className = '',
  disabled = false,
  autoComplete,
  ...rest
}) => {
  const inputId = id || name;

  return (
    <div className={`siams-form-group ${className}`}>
      {label && (
        <label htmlFor={inputId} className="siams-label">
          {label} {required && <span style={{ color: 'var(--status-danger)' }}>*</span>}
        </label>
      )}
      <div className="siams-input-wrapper">
        {icon && <span className="siams-input-icon">{icon}</span>}
        <input
          id={inputId}
          name={name}
          type={type}
          placeholder={placeholder}
          value={value}
          onChange={onChange}
          disabled={disabled}
          autoComplete={autoComplete}
          className={`siams-input ${icon ? 'has-icon' : ''} ${error ? 'siams-input-error' : ''}`}
          {...rest}
        />
      </div>
      {error ? (
        <span className="siams-error-text">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </span>
      ) : helperText ? (
        <span className="siams-helper-text">{helperText}</span>
      ) : null}
    </div>
  );
};

export default Input;
