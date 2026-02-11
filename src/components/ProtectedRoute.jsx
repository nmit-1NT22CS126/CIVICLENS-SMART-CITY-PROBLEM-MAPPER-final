import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { authHelpers } from '../services/api';

/**
 * ProtectedRoute Component
 * Protects routes that require authentication
 * 
 * @param {React.ReactNode} children - Child components to render if authorized
 * @param {boolean} requireAdmin - Whether the route requires admin role
 * @param {string} redirectTo - Where to redirect if not authorized
 */
const ProtectedRoute = ({ 
  children, 
  requireAdmin = false, 
  redirectTo = '/login' 
}) => {
  const location = useLocation();
  const isAuthenticated = authHelpers.isAuthenticated();
  const isAdmin = authHelpers.isAdmin();

  // Not authenticated - redirect to login
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location }} replace />;
  }

  // Requires admin but user is not admin
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/user" replace />;
  }

  // Authenticated and authorized
  return children;
};

/**
 * PublicRoute Component
 * For routes that should only be accessible when NOT logged in (login, register)
 */
export const PublicRoute = ({ children }) => {
  const isAuthenticated = authHelpers.isAuthenticated();
  const isAdmin = authHelpers.isAdmin();

  if (isAuthenticated) {
    // Redirect based on role
    if (isAdmin) {
      return <Navigate to="/admin/dashboard" replace />;
    }
    return <Navigate to="/user" replace />;
  }

  return children;
};

export default ProtectedRoute;
