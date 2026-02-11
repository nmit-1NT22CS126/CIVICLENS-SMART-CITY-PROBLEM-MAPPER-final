import React, { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Menu, X, LogOut } from "lucide-react";
import { authHelpers } from "../services/api";

const styles = {
  nav: {
    width: "100%",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "0.75rem 1rem",
    position: "relative",
  },
  logo: {
    fontSize: "1.5rem",
    fontWeight: "700",
    color: "#1e40af",
    textDecoration: "none",
    display: "flex",
    alignItems: "center",
    gap: "0.5rem",
    zIndex: 51,
  },
  menuButton: {
    display: "none",
    background: "none",
    border: "none",
    color: "#1e40af",
    cursor: "pointer",
    padding: "0.5rem",
    zIndex: 51,
    "@media (max-width: 768px)": {
      display: "block",
    },
  },
  navLinks: {
    display: "flex",
    gap: "2rem",
    alignItems: "center",
  },
  mobileNav: {
    display: "none",
    "@media (max-width: 768px)": {
      position: "fixed",
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: "rgba(255,255,255,0.98)",
      flexDirection: "column",
      padding: "5rem 2rem 2rem",
      gap: "1.5rem",
      transition: "transform 0.3s ease-in-out",
      transform: "translateX(100%)",
      zIndex: 50,
    },
  },
  mobileNavOpen: {
    "@media (max-width: 768px)": {
      display: "flex",
      transform: "translateX(0)",
    },
  },
  link: {
    textDecoration: "none",
    color: "#64748b",
    fontWeight: "500",
    transition: "color 0.2s ease",
    padding: "0.5rem 0.75rem",
    borderRadius: "0.375rem",
    "@media (max-width: 768px)": {
      fontSize: "1.25rem",
      padding: "0.75rem 1rem",
      width: "100%",
      textAlign: "center",
    },
  },
  activeLink: {
    color: "#1e40af",
    background: "#eff6ff",
  },
  reportButton: {
    background: "#1e40af",
    color: "white",
    padding: "0.5rem 1rem",
    borderRadius: "0.5rem",
    fontWeight: "600",
    textDecoration: "none",
    transition: "all 0.2s ease",
    "@media (max-width: 768px)": {
      width: "100%",
      textAlign: "center",
      padding: "0.75rem 1rem",
      marginTop: "1rem",
    },
  },
};

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  // Handle logout
  const handleLogout = () => {
    authHelpers.clearAuth();
    navigate("/login", { replace: true });
  };

  // Close mobile menu when route changes
  useEffect(() => {
    setIsOpen(false);
  }, [location]);

  // Prevent body scroll when mobile menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "unset";
    }
    return () => {
      document.body.style.overflow = "unset";
    };
  }, [isOpen]);

  const toggleMenu = () => setIsOpen(!isOpen);

  const navItems = [
    { to: "/user", text: "Home" },
    { to: "/user/view", text: "View Reports" },
    { to: "/user/about", text: "About" },
    { to: "/user/contact", text: "Contact" },
  ];

  return (
    <nav style={styles.nav}>
      <Link to="/user" style={styles.logo}>
        🏙️ CivicLens
      </Link>

      {/* Desktop Navigation */}
      <div style={styles.navLinks} className="desktop-only">
        {navItems.map(({ to, text }) => (
          <Link
            key={to}
            to={to}
            style={{
              ...styles.link,
              ...(location.pathname === to && styles.activeLink),
            }}
          >
            {text}
          </Link>
        ))}
        <Link to="/user/report" style={styles.reportButton}>
          Report Issue
        </Link>
        <button 
          onClick={handleLogout} 
          style={{
            ...styles.link, 
            color: '#ef4444', 
            fontWeight: '600',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: 'inherit',
            fontFamily: 'inherit',
          }}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>

      {/* Mobile Menu Button */}
      <button
        onClick={toggleMenu}
        style={{
          ...styles.menuButton,
          display: "none",
          "@media (max-width: 768px)": {
            display: "block",
          },
        }}
        aria-label="Toggle menu"
      >
        {isOpen ? <X size={24} /> : <Menu size={24} />}
      </button>

      {/* Mobile Navigation */}
      <div
        style={{
          ...styles.mobileNav,
          ...(isOpen && styles.mobileNavOpen),
        }}
      >
        {navItems.map(({ to, text }) => (
          <Link
            key={to}
            to={to}
            style={{
              ...styles.link,
              ...(location.pathname === to && styles.activeLink),
            }}
            onClick={() => setIsOpen(false)}
          >
            {text}
          </Link>
        ))}
        <Link
          to="/user/report"
          style={styles.reportButton}
          onClick={() => setIsOpen(false)}
        >
          Report Issue
        </Link>
        <button 
          onClick={() => {
            setIsOpen(false);
            handleLogout();
          }} 
          style={{
            ...styles.link, 
            color: '#ef4444', 
            fontWeight: '600',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
            width: '100%',
            fontSize: 'inherit',
            fontFamily: 'inherit',
            marginTop: '1rem',
          }}
        >
          <LogOut size={16} />
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
