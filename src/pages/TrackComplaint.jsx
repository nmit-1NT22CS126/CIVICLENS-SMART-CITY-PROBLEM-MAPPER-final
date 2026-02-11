import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Search, MapPin, Clock, User, FileText, MessageSquare, Image, RefreshCw } from "lucide-react";
import { complaintsAPI } from "../services/api";
import "../styles/trackComplaint.css";

const TrackComplaint = () => {
  const navigate = useNavigate();
  const { trackingId: urlTrackingId } = useParams();
  
  const [trackingId, setTrackingId] = useState(urlTrackingId || "");
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    e?.preventDefault();
    
    if (!trackingId.trim()) {
      setError("Please enter a tracking ID");
      return;
    }

    setLoading(true);
    setError("");
    setSearched(true);

    try {
      const data = await complaintsAPI.track(trackingId.trim());
      setComplaint(data);
    } catch (err) {
      setComplaint(null);
      setError(err.message || "Complaint not found");
    } finally {
      setLoading(false);
    }
  };

  // Auto-search if URL has tracking ID
  React.useEffect(() => {
    if (urlTrackingId) {
      handleSearch();
    }
  }, [urlTrackingId]);

  const getStatusClass = (status) => {
    switch (status) {
      case "Pending": return "status-pending";
      case "In-Review": return "status-review";
      case "Resolved": return "status-resolved";
      default: return "status-pending";
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="track-page">
      <div className="track-container">
        {/* Header */}
        <div className="track-header">
          <h1>🔍 Track Your Complaint</h1>
          <p>Enter your tracking ID to check the status of your complaint</p>
        </div>

        {/* Search Form */}
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input-wrapper">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              value={trackingId}
              onChange={(e) => {
                setTrackingId(e.target.value);
                setError("");
              }}
              placeholder="Enter Tracking ID (e.g., CVC-1234-2025)"
              className="search-input"
              disabled={loading}
            />
          </div>
          <button type="submit" className="search-btn" disabled={loading}>
            {loading ? (
              <RefreshCw className="spin" size={20} />
            ) : (
              "Track"
            )}
          </button>
        </form>

        {/* Error Message */}
        {error && searched && (
          <div className="error-message">
            <span>❌ {error}</span>
          </div>
        )}

        {/* No Result */}
        {searched && !loading && !complaint && !error && (
          <div className="no-result">
            <div className="no-result-icon">🔎</div>
            <h3>No Complaint Found</h3>
            <p>Please check your tracking ID and try again</p>
          </div>
        )}

        {/* Complaint Details */}
        {complaint && (
          <div className="complaint-details">
            {/* Status Header */}
            <div className="detail-header">
              <div className="tracking-info">
                <span className="tracking-label">Tracking ID</span>
                <span className="tracking-value">{complaint.tracking_id}</span>
              </div>
              <span className={`status-badge ${getStatusClass(complaint.status)}`}>
                {complaint.status}
              </span>
            </div>

            {/* Main Info */}
            <div className="detail-section">
              <h3 className="section-title">
                <FileText size={18} /> Issue Details
              </h3>
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="label">Title</span>
                  <span className="value">{complaint.title || "N/A"}</span>
                </div>
                <div className="detail-item">
                  <span className="label">Category</span>
                  <span className="value category-tag">{complaint.category}</span>
                </div>
                <div className="detail-item full-width">
                  <span className="label">Description</span>
                  <p className="value description">{complaint.description}</p>
                </div>
              </div>
            </div>

            {/* Location */}
            <div className="detail-section">
              <h3 className="section-title">
                <MapPin size={18} /> Location
              </h3>
              <div className="location-info">
                <span>Latitude: {complaint.latitude?.toFixed(6)}</span>
                <span>Longitude: {complaint.longitude?.toFixed(6)}</span>
              </div>
            </div>

            {/* Timestamps */}
            <div className="detail-section">
              <h3 className="section-title">
                <Clock size={18} /> Timeline
              </h3>
              <div className="timeline">
                <div className="timeline-item">
                  <span className="timeline-label">Submitted</span>
                  <span className="timeline-value">{formatDate(complaint.created_at)}</span>
                </div>
                <div className="timeline-item">
                  <span className="timeline-label">Last Updated</span>
                  <span className="timeline-value">{formatDate(complaint.updated_at)}</span>
                </div>
              </div>
            </div>

            {/* Image */}
            {complaint.image_url && (
              <div className="detail-section">
                <h3 className="section-title">
                  <Image size={18} /> Attached Image
                </h3>
                <div className="image-container">
                  <img src={complaint.image_url} alt="Complaint" className="complaint-image" />
                </div>
              </div>
            )}

            {/* Admin Notes */}
            {complaint.admin_logs && complaint.admin_logs.length > 0 && (
              <div className="detail-section">
                <h3 className="section-title">
                  <MessageSquare size={18} /> Admin Notes
                </h3>
                <div className="admin-notes">
                  {complaint.admin_logs.map((log, index) => (
                    <div key={index} className="note-item">
                      <div className="note-header">
                        <User size={14} />
                        <span className="note-admin">Admin</span>
                        <span className="note-time">{formatDate(log.timestamp)}</span>
                      </div>
                      <p className="note-message">{log.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="detail-actions">
              <button onClick={handleSearch} className="btn-refresh">
                <RefreshCw size={16} /> Refresh Status
              </button>
              <button onClick={() => navigate("/user/report")} className="btn-new">
                Report New Issue
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TrackComplaint;
