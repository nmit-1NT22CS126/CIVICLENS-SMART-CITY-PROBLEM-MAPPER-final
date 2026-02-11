// src/components/Footer.jsx
import React from "react";

const styles = {
  footer: {
    background: '#111827',
    color: '#d1d5db',
    padding: '1.5rem 0',
    textAlign: 'center'
  },
  copyright: {
    fontSize: '0.875rem'
  },
  brand: {
    color: '#60a5fa',
    fontWeight: '600'
  },
  linkContainer: {
    marginTop: '0.5rem',
    display: 'flex',
    gap: '1rem',
    justifyContent: 'center'
  },
  link: {
    color: '#d1d5db',
    textDecoration: 'none',
    transition: 'color 0.2s ease',
    ':hover': {
      color: '#60a5fa'
    }
  }
};

const Footer = () => {
  return (
    <footer style={styles.footer}>
      <p style={styles.copyright}>
        © {new Date().getFullYear()} <span style={styles.brand}>CivicLens</span> · All Rights Reserved
      </p>
      <div style={styles.linkContainer}>
        <a 
          href="/about" 
          style={styles.link}
          onMouseOver={e => e.target.style.color = '#60a5fa'}
          onMouseOut={e => e.target.style.color = '#d1d5db'}
        >
          About
        </a>
        <a 
          href="/contact" 
          style={styles.link}
          onMouseOver={e => e.target.style.color = '#60a5fa'}
          onMouseOut={e => e.target.style.color = '#d1d5db'}
        >
          Contact
        </a>
      </div>
    </footer>
  );
};

export default Footer;
