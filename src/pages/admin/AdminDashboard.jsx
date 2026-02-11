import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { RefreshCw, AlertCircle, TrendingUp, Clock, CheckCircle, FileText } from "lucide-react";
import { adminAPI, authHelpers } from "../../services/api";
import "../../styles/AdminDashboard.css";

const AdminDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    in_review: 0,
    resolved: 0
  });
  const [recentComplaints, setRecentComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchData = async () => {
    // Check admin auth
    if (!authHelpers.isAuthenticated() || !authHelpers.isAdmin()) {
      navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      // Fetch stats and complaints in parallel
      const [statsData, complaintsData] = await Promise.all([
        adminAPI.getStats(),
        adminAPI.getAllReports()
      ]);

      setStats(statsData);
      setRecentComplaints(complaintsData.slice(0, 5)); // Latest 5
    } catch (err) {
      if (err.message.includes("Admin") || err.message.includes("403")) {
        navigate("/login");
      } else {
        setError(err.message || "Failed to fetch dashboard data");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "Pending": return "status-pending";
      case "In-Review": return "status-progress";
      case "Resolved": return "status-resolved";
      default: return "";
    }
  };

  return (
    <div>
      <div className="dashboard-header">
        <div>
          <h1 className="dashboard-title">Dashboard Overview</h1>
          <p className="dashboard-subtitle">Welcome back, Admin. Here's what's happening today.</p>
        </div>
        <button 
          onClick={fetchData} 
          className="refresh-btn"
          disabled={loading}
        >
          <RefreshCw size={18} className={loading ? "spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Stats Cards */}
      <div className="dashboard-stats">
        <div className="stat-card total">
          <div className="stat-icon"><FileText size={24} /></div>
          <div className="stat-info">
            <div className="card-value">{loading ? "..." : stats.total}</div>
            <div className="card-title">Total Complaints</div>
          </div>
        </div>
        <div className="stat-card pending">
          <div className="stat-icon"><AlertCircle size={24} /></div>
          <div className="stat-info">
            <div className="card-value">{loading ? "..." : stats.pending}</div>
            <div className="card-title">Pending</div>
          </div>
        </div>
        <div className="stat-card progress">
          <div className="stat-icon"><Clock size={24} /></div>
          <div className="stat-info">
            <div className="card-value">{loading ? "..." : stats.in_review}</div>
            <div className="card-title">In Review</div>
          </div>
        </div>
        <div className="stat-card resolved">
          <div className="stat-icon"><CheckCircle size={24} /></div>
          <div className="stat-info">
            <div className="card-value">{loading ? "..." : stats.resolved}</div>
            <div className="card-title">Resolved</div>
          </div>
        </div>
      </div>

      {/* Recent Complaints */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Recent Complaints</h2>
          <Link to="/admin/complaints" className="view-all-link">View All →</Link>
        </div>
        
        <div className="recent-list">
          {loading ? (
            <div className="loading-state">
              <RefreshCw size={32} className="spin" />
              <p>Loading...</p>
            </div>
          ) : recentComplaints.length > 0 ? (
            recentComplaints.map((complaint) => (
              <Link 
                key={complaint.id} 
                to={`/admin/complaint/${complaint.id}`}
                className="recent-item"
              >
                <div className="recent-info">
                  <span className="recent-id">{complaint.tracking_id}</span>
                  <span className="recent-title">{complaint.title || complaint.category}</span>
                </div>
                <div className="recent-meta">
                  <span className={`status-badge ${getStatusClass(complaint.status)}`}>
                    {complaint.status}
                  </span>
                  <span className="recent-date">{formatDate(complaint.created_at)}</span>
                </div>
              </Link>
            ))
          ) : (
            <div className="empty-state">
              <p>No complaints yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <div className="section-header">
          <h2 className="section-title">Quick Actions</h2>
        </div>
        <div className="quick-actions">
          <Link to="/admin/complaints" className="quick-action-btn">
            <FileText size={20} />
            Manage Complaints
          </Link>
          <Link to="/admin/map" className="quick-action-btn">
            <TrendingUp size={20} />
            View Map
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
