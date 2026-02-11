import React from 'react';

/**
 * ErrorBoundary Component
 * Catches JavaScript errors anywhere in the child component tree,
 * logs those errors, and displays a fallback UI.
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    // Log the error to console (could also send to error reporting service)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({ errorInfo });
    
    // You could also log to an error reporting service here
    // logErrorToService(error, errorInfo);
  }

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI or default
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={styles.container}>
          <div style={styles.content}>
            <div style={styles.icon}>⚠️</div>
            <h1 style={styles.title}>Something went wrong</h1>
            <p style={styles.message}>
              We're sorry, but something unexpected happened. 
              Please try refreshing the page or go back to the home page.
            </p>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <details style={styles.errorDetails}>
                <summary style={styles.errorSummary}>Error Details (Dev Only)</summary>
                <pre style={styles.errorStack}>
                  {this.state.error.toString()}
                  {this.state.errorInfo && this.state.errorInfo.componentStack}
                </pre>
              </details>
            )}
            
            <div style={styles.actions}>
              <button 
                onClick={this.handleReload} 
                style={styles.primaryButton}
              >
                🔄 Refresh Page
              </button>
              <button 
                onClick={this.handleGoHome} 
                style={styles.secondaryButton}
              >
                🏠 Go to Home
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Inline styles for the error boundary (to ensure they always work)
const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f8fafc',
    padding: '20px',
  },
  content: {
    maxWidth: '500px',
    textAlign: 'center',
    backgroundColor: 'white',
    padding: '48px',
    borderRadius: '16px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e2e8f0',
  },
  icon: {
    fontSize: '64px',
    marginBottom: '24px',
  },
  title: {
    fontSize: '1.75rem',
    fontWeight: '700',
    color: '#0f172a',
    marginBottom: '12px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  message: {
    fontSize: '1rem',
    color: '#64748b',
    lineHeight: '1.6',
    marginBottom: '32px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  primaryButton: {
    padding: '12px 24px',
    fontSize: '1rem',
    fontWeight: '600',
    color: 'white',
    backgroundColor: '#0a1930',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  secondaryButton: {
    padding: '12px 24px',
    fontSize: '1rem',
    fontWeight: '600',
    color: '#475569',
    backgroundColor: 'white',
    border: '1px solid #cbd5e1',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  errorDetails: {
    marginBottom: '24px',
    textAlign: 'left',
    backgroundColor: '#fef2f2',
    borderRadius: '8px',
    padding: '16px',
    border: '1px solid #fecaca',
  },
  errorSummary: {
    cursor: 'pointer',
    fontWeight: '600',
    color: '#b91c1c',
    marginBottom: '12px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  errorStack: {
    fontSize: '0.75rem',
    color: '#7f1d1d',
    whiteSpace: 'pre-wrap',
    wordBreak: 'break-word',
    maxHeight: '200px',
    overflow: 'auto',
    fontFamily: 'Monaco, Consolas, monospace',
    margin: 0,
  },
};

export default ErrorBoundary;
