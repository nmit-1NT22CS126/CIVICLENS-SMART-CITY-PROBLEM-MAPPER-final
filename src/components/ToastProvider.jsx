import React, { createContext, useContext, useState, useCallback } from 'react';

/**
 * Toast Context and Provider for global notifications
 * Usage:
 *   const { showToast } = useToast();
 *   showToast('Success message', 'success');
 */

const ToastContext = createContext(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = 'info', duration = 4000) => {
    const id = Date.now() + Math.random();
    const toast = { id, message, type };
    
    setToasts(prev => [...prev, toast]);
    
    // Auto-remove after duration
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, duration);
    
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  const success = useCallback((message, duration) => {
    return showToast(message, 'success', duration);
  }, [showToast]);

  const error = useCallback((message, duration) => {
    return showToast(message, 'error', duration);
  }, [showToast]);

  const warning = useCallback((message, duration) => {
    return showToast(message, 'warning', duration);
  }, [showToast]);

  const info = useCallback((message, duration) => {
    return showToast(message, 'info', duration);
  }, [showToast]);

  return (
    <ToastContext.Provider value={{ showToast, success, error, warning, info, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

// Toast Container Component
const ToastContainer = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div style={styles.container}>
      {toasts.map(toast => (
        <Toast 
          key={toast.id} 
          toast={toast} 
          onRemove={() => onRemove(toast.id)} 
        />
      ))}
    </div>
  );
};

// Individual Toast Component
const Toast = ({ toast, onRemove }) => {
  const icons = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ'
  };

  return (
    <div 
      style={{
        ...styles.toast,
        ...styles[toast.type]
      }}
      role="alert"
    >
      <span style={styles.icon}>{icons[toast.type]}</span>
      <span style={styles.message}>{toast.message}</span>
      <button 
        onClick={onRemove} 
        style={styles.closeButton}
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
};

// Inline styles
const styles = {
  container: {
    position: 'fixed',
    top: '20px',
    right: '20px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
    zIndex: 9999,
    pointerEvents: 'none',
  },
  toast: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    padding: '14px 20px',
    borderRadius: '10px',
    fontWeight: '500',
    fontSize: '0.95rem',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.12)',
    animation: 'slideIn 0.3s ease',
    pointerEvents: 'auto',
    minWidth: '300px',
    maxWidth: '450px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  success: {
    background: '#f0fdf4',
    color: '#166534',
    border: '1px solid #86efac',
  },
  error: {
    background: '#fef2f2',
    color: '#991b1b',
    border: '1px solid #fca5a5',
  },
  warning: {
    background: '#fffbeb',
    color: '#92400e',
    border: '1px solid #fcd34d',
  },
  info: {
    background: '#eff6ff',
    color: '#1e40af',
    border: '1px solid #93c5fd',
  },
  icon: {
    fontSize: '1.1rem',
    fontWeight: 'bold',
    flexShrink: 0,
  },
  message: {
    flex: 1,
    lineHeight: '1.4',
  },
  closeButton: {
    background: 'none',
    border: 'none',
    fontSize: '1.25rem',
    cursor: 'pointer',
    opacity: 0.6,
    padding: '0 4px',
    lineHeight: 1,
    color: 'currentColor',
    transition: 'opacity 0.2s',
    flexShrink: 0,
  },
};

// Add keyframe animation via style tag
if (typeof document !== 'undefined') {
  const styleSheet = document.createElement('style');
  styleSheet.textContent = `
    @keyframes slideIn {
      from {
        transform: translateX(100%);
        opacity: 0;
      }
      to {
        transform: translateX(0);
        opacity: 1;
      }
    }
  `;
  document.head.appendChild(styleSheet);
}

export default ToastProvider;
