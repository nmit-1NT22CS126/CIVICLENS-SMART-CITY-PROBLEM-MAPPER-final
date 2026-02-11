import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <h1 style={styles.code}>404</h1>
        <h2 style={styles.title}>Page Not Found</h2>
        <p style={styles.message}>
          Sorry, we couldn't find the page you're looking for. 
          The page might have been moved, deleted, or you entered an incorrect URL.
        </p>
        
        <div style={styles.actions}>
          <button 
            onClick={() => navigate(-1)} 
            style={styles.secondaryButton}
          >
            ← Go Back
          </button>
          <Link to="/" style={styles.primaryButton}>
            🏠 Go Home
          </Link>
        </div>

        <div style={styles.links}>
          <p style={styles.linksTitle}>You might be looking for:</p>
          <div style={styles.linkList}>
            <Link to="/login" style={styles.link}>Login</Link>
            <Link to="/register" style={styles.link}>Register</Link>
            <Link to="/track" style={styles.link}>Track Complaint</Link>
            <Link to="/user" style={styles.link}>Dashboard</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

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
    padding: '60px 40px',
    borderRadius: '16px',
    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
    border: '1px solid #e2e8f0',
  },
  code: {
    fontSize: '6rem',
    fontWeight: '800',
    color: '#e2e8f0',
    lineHeight: '1',
    margin: '0 0 16px 0',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
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
    marginBottom: '40px',
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
    textDecoration: 'none',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
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
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.2s',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  links: {
    borderTop: '1px solid #e2e8f0',
    paddingTop: '24px',
  },
  linksTitle: {
    fontSize: '0.9rem',
    color: '#94a3b8',
    marginBottom: '12px',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
  linkList: {
    display: 'flex',
    gap: '20px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  link: {
    color: '#3b82f6',
    textDecoration: 'none',
    fontSize: '0.95rem',
    fontWeight: '500',
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  },
};

export default NotFound;
