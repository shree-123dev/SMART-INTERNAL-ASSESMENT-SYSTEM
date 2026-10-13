import React, { useEffect } from 'react';
import { IoClose } from 'react-icons/io5';

const Modal = ({
  isOpen,
  onClose,
  title,
  children,
  footer = null,
  size = 'md', // sm, md, lg
  className = ''
}) => {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = 'unset';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const maxWidthMap = {
    sm: '420px',
    md: '540px',
    lg: '720px'
  };

  return (
    <div className="siams-modal-backdrop" onClick={onClose}>
      <div
        className={`siams-modal-container ${className}`}
        style={{ maxWidth: maxWidthMap[size] || maxWidthMap.md }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="siams-modal-header">
          <h3 className="siams-modal-title">{title}</h3>
          <button
            type="button"
            className="siams-modal-close"
            onClick={onClose}
            aria-label="Close modal"
          >
            <IoClose />
          </button>
        </div>
        <div className="siams-modal-body">{children}</div>
        {footer && <div className="siams-modal-footer">{footer}</div>}
      </div>
    </div>
  );
};

export default Modal;
