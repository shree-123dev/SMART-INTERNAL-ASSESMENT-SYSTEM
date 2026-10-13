import React from 'react';

const Card = ({
  children,
  className = '',
  hoverEffect = false,
  padding = 'md', // none, sm, md, lg
  header = null,
  footer = null,
  onClick,
  ...rest
}) => {
  const classes = [
    'siams-card',
    `siams-card-pad-${padding}`,
    hoverEffect ? 'siams-card-hover' : '',
    onClick ? 'cursor-pointer' : '',
    className
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={classes} onClick={onClick} {...rest}>
      {header && <div className="siams-card-header">{header}</div>}
      <div className="siams-card-content">{children}</div>
      {footer && <div className="siams-card-footer">{footer}</div>}
    </div>
  );
};

export default Card;
