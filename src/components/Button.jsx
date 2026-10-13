import React from 'react';

const Button = ({
  children,
  variant = 'primary', // primary, secondary, outline, ghost, danger
  size = 'md',         // sm, md, lg
  icon = null,
  iconPosition = 'left',
  fullWidth = false,
  className = '',
  disabled = false,
  type = 'button',
  onClick,
  ...rest
}) => {
  const classes = [
    'siams-btn',
    `siams-btn-${variant}`,
    `siams-btn-${size}`,
    fullWidth ? 'siams-btn-full' : '',
    !children && icon ? 'siams-btn-icon-only' : '',
    className
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled}
      onClick={onClick}
      {...rest}
    >
      {icon && iconPosition === 'left' && <span className="btn-icon">{icon}</span>}
      {children && <span className="btn-text">{children}</span>}
      {icon && iconPosition === 'right' && <span className="btn-icon">{icon}</span>}
    </button>
  );
};

export default Button;
