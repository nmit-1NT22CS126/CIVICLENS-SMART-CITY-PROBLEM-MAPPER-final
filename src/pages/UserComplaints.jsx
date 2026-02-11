import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Eye, Clock, MapPin, AlertCircle, CheckCircle, Loader } from "lucide-react";
import { complaintsAPI, authHelpers } from "../services/api";
import "../styles/userComplaints.css";

const UserComplaints = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  const fetchComplaints = async () => {
    if (!authHelpers.isAuthenticated()) {
      navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await complaintsAPI.getUserComplaints();
      setComplaints(data);
    } catch (err) {
      if (err.message.includes("login")) {
        navigate("/login");
      } else {
        setError(err.message || "Failed to fetch complaints");
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaints();
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case "Pending": return <Clock size={16} />;
      case "In-Review": return <Loader size={16} />;
      case "Resolved": return <CheckCircle size={16} />;
      default: return <AlertCircle size={16} />;
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case "Pending": return "status-pending";
      case "In-Review": return "status-review";
      case "Resolved": return "status-resolved";
      default: return "";
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  const handleViewDetails = (complaint) => {
    setSelectedComplaint(complaint);
  };

  const closeModal = () => {
    setSelectedComplaint(null);
  };

  return (
    <div className="complaints-page">
      <div className="complaints-container">
        {/* Header */}
        <div className="complaints-header">
          <div>
            <h1>📋 My Complaints</h1>
            <p>View and track all your submitted complaints</p>
          </div>
          <button onClick={fetchComplaints} className="refresh-btn" disabled={loading}>
            <RefreshCw size={18} className={loading ? "spin" : ""} />
            Refresh
          </button>
        </div>

        {/* Stats */}
        <div className="stats-row">
          <div className="stat-card">
            <span className="stat-value">{complaints.length}</span>
            <span className="stat-label">Total</span>
          </div>
          <div className="stat-card pending">
            <span className="stat-value">{complaints.filter(c => c.status === "Pending").length}</span>
            <span className="stat-label">Pending</span>
          </div>
          <div className="stat-card review">
            <span className="stat-value">{complaints.filter(c => c.status === "In-Review").length}</span>
            <span className="stat-label">In Review</span>
          </div>
          <div className="stat-card resolved">
            <span className="stat-value">{complaints.filter(c => c.status === "Resolved").length}</span>
            <span className="stat-label">Resolved</span>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="error-box">
            <AlertCircle size={20} />
            <span>{error}</span>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="loading-state">
            <RefreshCw size={40} className="spin" />
            <p>Loading your complaints...</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && complaints.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h3>No Complaints Yet</h3>
            <p>You haven't submitted any complaints yet.</p>
            <button onClick={() => navigate("/user/report")} className="report-btn">
              Report an Issue
            </button>
          </div>
        )}

        {/* Complaints List */}
        {!loading && complaints.length > 0 && (
          <div className="complaints-list">
            <table className="complaints-table">
              <thead>
                <tr>
                  <th>Tracking ID</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {complaints.map((complaint) => (
                  <tr key={complaint.id} onClick={() => handleViewDetails(complaint)}>
                    <td className="tracking-id">{complaint.tracking_id}</td>
                    <td className="title">{complaint.title || "Untitled"}</td>
                    <td>
                      <span className="category-badge">{complaint.category}</span>
                    </td>
                    <td>
                      <span className={`status-badge ${getStatusClass(complaint.status)}`}>
                        {getStatusIcon(complaint.status)}
                        {complaint.status}
                      </span>
                    </td>
                    <td className="date">{formatDate(complaint.created_at)}</td>
                    <td>
                      <button 
                        className="view-btn"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewDetails(complaint);
                        }}
                      >
                        <Eye size={16} /> View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Mobile Cards */}
            <div className="complaints-cards">
              {complaints.map((complaint) => (
                <div 
                  key={complaint.id} 
                  className="complaint-card"
                  onClick={() => handleViewDetails(complaint)}
                >
                  <div className="card-header">
                    <span className="tracking">{complaint.tracking_id}</span>
                    <span className={`status-badge ${getStatusClass(complaint.status)}`}>
                      {complaint.status}
                    </span>
                  </div>
                  <h3 className="card-title">{complaint.title || "Untitled"}</h3>
                  <div className="card-meta">
                    <span className="category">{complaint.category}</span>
                    <span className="date">{formatDate(complaint.created_at)}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detail Modal */}
        {selectedComplaint && (
          <div className="modal-overlay" onClick={closeModal}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <button className="modal-close" onClick={closeModal}>×</button>
              
              <div className="modal-header">
                <h2>{selectedComplaint.tracking_id}</h2>
                <span className={`status-badge ${getStatusClass(selectedComplaint.status)}`}>
                  {selectedComplaint.status}
                </span>
              </div>

              <div className="modal-body">
                <div className="info-row">
                  <span className="label">Title</span>
                  <span className="value">{selectedComplaint.title || "Untitled"}</span>
                </div>
                <div className="info-row">
                  <span className="label">Category</span>
                  <span className="value">{selectedComplaint.category}</span>
                </div>
                <div className="info-row">
                  <span className="label">Description</span>
                  <p className="value description">{selectedComplaint.description}</p>
                </div>
                <div className="info-row">
                  <span className="label">Location</span>
                  <span className="value">
                    <MapPin size={14} /> {selectedComplaint.latitude?.toFixed(4)}, {selectedComplaint.longitude?.toFixed(4)}
                  </span>
                </div>
                <div className="info-row">
                  <span className="label">Submitted</span>
                  <span className="value">{formatDate(selectedComplaint.created_at)}</span>
                </div>

                {selectedComplaint.image_url && (
                  <div className="info-row">
                    <span className="label">Image</span>
                    <img src={selectedComplaint.image_url} alt="Complaint" className="modal-image" />
                  </div>
                )}
              </div>

              <div className="modal-actions">
                <button onClick={() => navigate(`/track/${selectedComplaint.tracking_id}`)} className="track-btn">
                  Track Status
                </button>
                <button onClick={closeModal} className="close-btn">Close</button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserComplaints;
