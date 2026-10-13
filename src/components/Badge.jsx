import React from 'react';

const Badge = ({
  children,
  variant = 'pill', // pill, primary, admin, faculty, student, success, warning, danger
  size = 'md',
  icon = null,
  className = '',
  ...rest
}) => {
  const classes = [
    'siams-badge',
    `siams-badge-${variant}`,
    `siams-badge-${size}`,
    className
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <span className={classes} {...rest}>
      {icon && <span className="badge-icon">{icon}</span>}
      {children}
    </span>
  );
};

export default Badge;
