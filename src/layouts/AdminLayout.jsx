import React, { useEffect } from "react";
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { LayoutDashboard, FileText, Map, LogOut } from "lucide-react";
import { authHelpers } from "../services/api";
import "../styles/AdminLayout.css";

const AdminLayout = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Check authentication on mount and route changes
  useEffect(() => {
    if (!authHelpers.isAuthenticated()) {
      navigate("/login", { replace: true });
      return;
    }
    
    if (!authHelpers.isAdmin()) {
      navigate("/user", { replace: true });
    }
  }, [navigate, location.pathname]);

  const handleLogout = () => {
    authHelpers.clearAuth();
    navigate("/login", { replace: true });
  };

  const navItems = [
    { path: "/admin/dashboard", icon: <LayoutDashboard size={20} />, label: "Dashboard" },
    { path: "/admin/complaints", icon: <FileText size={20} />, label: "Complaints" },
    { path: "/admin/map", icon: <Map size={20} />, label: "Map View" },
  ];

  return (
    <div className="admin-dashboard-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title">
            🛡️ Admin Portal
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={location.pathname === item.path ? "active" : ""}
            >
              {item.icon}
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button onClick={handleLogout} className="logout-btn">
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
