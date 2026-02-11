import React from 'react';

/**
 * Loading Spinner Component
 * Reusable loading indicator with different sizes and variants
 * 
 * @param {string} size - 'sm' | 'md' | 'lg' | 'xl'
 * @param {string} text - Optional loading text
 * @param {boolean} fullPage - Whether to show full page overlay
 * @param {string} className - Additional CSS classes
 */
const LoadingSpinner = ({ 
  size = 'md', 
  text = '', 
  fullPage = false,
  className = '' 
}) => {
  const sizes = {
    sm: { spinner: 24, border: 2 },
    md: { spinner: 40, border: 3 },
    lg: { spinner: 56, border: 4 },
    xl: { spinner: 72, border: 5 },
  };

  const { spinner: spinnerSize, border: borderWidth } = sizes[size] || sizes.md;

  const spinnerStyle = {
    width: `${spinnerSize}px`,
    height: `${spinnerSize}px`,
    border: `${borderWidth}px solid #e2e8f0`,
    borderTopColor: '#3b82f6',
    borderRadius: '50%',
    animation: 'spin 0.8s linear infinite',
  };

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '16px',
  };

  const textStyle = {
    color: '#64748b',
    fontSize: size === 'sm' ? '0.85rem' : '1rem',
    fontWeight: '500',
  };

  const fullPageStyle = {
    position: 'fixed',
    inset: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    zIndex: 9998,
  };

  const content = (
    <div style={containerStyle} className={className}>
      <div style={spinnerStyle} className="loading-spinner" />
      {text && <p style={textStyle}>{text}</p>}
    </div>
  );

  if (fullPage) {
    return (
      <div style={{ ...containerStyle, ...fullPageStyle }}>
        {content}
      </div>
    );
  }

  return content;
};

/**
 * Skeleton Loader for content placeholders
 * 
 * @param {string} variant - 'text' | 'rect' | 'circle' | 'card'
 * @param {number} width - Width in pixels or percentage string
 * @param {number} height - Height in pixels
 * @param {number} count - Number of skeleton lines (for text variant)
 */
export const Skeleton = ({ 
  variant = 'text', 
  width = '100%', 
  height = 20,
  count = 1,
  className = ''
}) => {
  const baseStyle = {
    backgroundColor: '#e2e8f0',
    borderRadius: variant === 'circle' ? '50%' : '4px',
    animation: 'pulse 1.5s ease-in-out infinite',
  };

  const getStyle = () => {
    switch (variant) {
      case 'circle':
        return {
          ...baseStyle,
          width: width || 40,
          height: width || 40,
          borderRadius: '50%',
        };
      case 'rect':
        return {
          ...baseStyle,
          width: width,
          height: height,
        };
      case 'card':
        return {
          ...baseStyle,
          width: width,
          height: height || 120,
          borderRadius: '8px',
        };
      case 'text':
      default:
        return {
          ...baseStyle,
          width: width,
          height: height || 16,
          marginBottom: count > 1 ? '8px' : 0,
        };
    }
  };

  if (variant === 'text' && count > 1) {
    return (
      <div className={className}>
        {Array.from({ length: count }).map((_, i) => (
          <div 
            key={i} 
            style={{
              ...getStyle(),
              width: i === count - 1 ? '60%' : width,
            }} 
          />
        ))}
      </div>
    );
  }

  return <div style={getStyle()} className={className} />;
};

/**
 * Card Skeleton for loading cards
 */
export const CardSkeleton = ({ className = '' }) => (
  <div 
    style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '24px',
      border: '1px solid #e2e8f0',
    }}
    className={className}
  >
    <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
      <Skeleton variant="circle" width={48} />
      <div style={{ flex: 1 }}>
        <Skeleton width="60%" height={18} />
        <div style={{ marginTop: '8px' }}>
          <Skeleton width="40%" height={14} />
        </div>
      </div>
    </div>
    <Skeleton variant="text" count={3} />
  </div>
);

/**
 * Table Row Skeleton
 */
export const TableRowSkeleton = ({ columns = 5, rows = 5 }) => (
  <>
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <tr key={rowIndex}>
        {Array.from({ length: columns }).map((_, colIndex) => (
          <td key={colIndex} style={{ padding: '16px 20px' }}>
            <Skeleton 
              width={colIndex === 0 ? '80%' : colIndex === columns - 1 ? '60px' : '70%'} 
              height={16} 
            />
          </td>
        ))}
      </tr>
    ))}
  </>
);

// Add pulse animation
if (typeof document !== 'undefined') {
  const existingStyle = document.getElementById('loading-styles');
  if (!existingStyle) {
    const styleSheet = document.createElement('style');
    styleSheet.id = 'loading-styles';
    styleSheet.textContent = `
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
    `;
    document.head.appendChild(styleSheet);
  }
}

export default LoadingSpinner;
