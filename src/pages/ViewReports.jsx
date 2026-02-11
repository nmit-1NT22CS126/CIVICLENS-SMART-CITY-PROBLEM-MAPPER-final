import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import "../styles/viewReport.css";
import { complaintsAPI } from "../services/api";

// Fix Leaflet marker icons for deployment
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const ViewReports = () => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeView, setActiveView] = useState("list"); // 'list' or 'map'
  const [selectedImage, setSelectedImage] = useState(null); // For image modal
  const [deletingId, setDeletingId] = useState(null); // Track which complaint is being deleted
  const [deleteError, setDeleteError] = useState(null);

  // Calculate map center based on reports
  const getMapCenter = () => {
    if (reports.length === 0) return [12.9716, 77.5946]; // Default to Bangalore
    
    const validReports = reports.filter(r => r.latitude && r.longitude);
    if (validReports.length === 0) return [12.9716, 77.5946];
    
    const avgLat = validReports.reduce((sum, r) => sum + r.latitude, 0) / validReports.length;
    const avgLng = validReports.reduce((sum, r) => sum + r.longitude, 0) / validReports.length;
    return [avgLat, avgLng];
  };

  // Fetch user's reports from API
  const fetchReports = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await complaintsAPI.getUserComplaints();
      
      // Transform API data to match component format
      const formattedReports = data.map(report => ({
        id: report.id,
        tracking_id: report.tracking_id,
        category: report.category || report.title || "General",
        title: report.title,
        description: report.description,
        location: [report.latitude, report.longitude],
        latitude: report.latitude,
        longitude: report.longitude,
        status: report.status,
        image_url: report.image_url,
        classification_result: report.classification_result,
        created_at: report.created_at
      }));
      
      setReports(formattedReports);
    } catch (err) {
      console.error("Failed to fetch reports:", err);
      setError(err.message || "Failed to load your reports");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Handle delete complaint
  const handleDelete = async (complaintId, status) => {
    if (status !== "Pending") {
      setDeleteError("You cannot delete complaints that are already being processed or resolved.");
      setTimeout(() => setDeleteError(null), 4000);
      return;
    }

    if (!window.confirm("Are you sure you want to delete this complaint? This action cannot be undone.")) {
      return;
    }

    setDeletingId(complaintId);
    setDeleteError(null);

    try {
      await complaintsAPI.deleteComplaint(complaintId);
      // Remove from local state
      setReports(prev => prev.filter(r => r.id !== complaintId));
    } catch (err) {
      console.error("Failed to delete complaint:", err);
      setDeleteError(err.message || "Failed to delete complaint");
      setTimeout(() => setDeleteError(null), 4000);
    } finally {
      setDeletingId(null);
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric"
    });
  };

  // Get status class for styling
  const getStatusClass = (status) => {
    const statusMap = {
      "Pending": "pending",
      "In Progress": "in-progress",
      "In-Review": "in-progress",
      "Resolved": "resolved",
      "Rejected": "rejected"
    };
    return statusMap[status] || "pending";
  };

  // Check if complaint can be deleted
  const canDelete = (status) => status === "Pending";

  // Image Modal Component
  const ImageModal = ({ imageUrl, onClose }) => {
    if (!imageUrl) return null;
    
    return (
      <div className="image-modal-overlay" onClick={onClose}>
        <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
          <button className="image-modal-close" onClick={onClose}>×</button>
          <img src={imageUrl} alt="Complaint Evidence" />
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="view-reports-root">
        <div className="view-reports-container">
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading your reports...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="view-reports-root">
        <div className="view-reports-container">
          <div className="error-state">
            <span className="error-icon">⚠️</span>
            <h2>Unable to Load Reports</h2>
            <p>{error}</p>
            <button onClick={() => window.location.reload()} className="retry-btn">
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="view-reports-root">
      <div className="view-reports-container">
        <div className="view-header">
          <h1>My Reports</h1>
          <div className="view-toggle">
            <button
              className={`toggle-btn ${activeView === "list" ? "active" : ""}`}
              onClick={() => setActiveView("list")}
            >
              📋 List View
            </button>
            <button
              className={`toggle-btn ${activeView === "map" ? "active" : ""}`}
              onClick={() => setActiveView("map")}
            >
              🗺️ Map View
            </button>
          </div>
        </div>

        {/* Delete Error Banner */}
        {deleteError && (
          <div className="delete-error-banner">
            <span>⚠️ {deleteError}</span>
            <button onClick={() => setDeleteError(null)}>×</button>
          </div>
        )}

        {reports.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">📭</span>
            <h2>No Reports Yet</h2>
            <p>You haven't submitted any civic issue reports.</p>
            <a href="/report" className="submit-btn">Report an Issue</a>
          </div>
        ) : activeView === "list" ? (
          <div className="reports-grid">
            {reports.map((report) => (
              <div key={report.id} className="report-card">
                <div className="report-header">
                  <h3>{report.category}</h3>
                  <span className={`status-badge ${getStatusClass(report.status)}`}>
                    {report.status}
                  </span>
                </div>
                {report.title && <h4 className="report-title">{report.title}</h4>}
                <p className="description">{report.description}</p>
                
                {/* Image Thumbnail */}
                {report.image_url && (
                  <div 
                    className="report-image-thumbnail"
                    onClick={() => setSelectedImage(report.image_url)}
                  >
                    <img src={report.image_url} alt="Issue" loading="lazy" />
                    <div className="image-overlay">
                      <span>🔍 Click to view</span>
                    </div>
                  </div>
                )}

                {/* Classification Result */}
                {report.classification_result && (
                  <div className="classification-badge">
                    🤖 AI: {report.classification_result}
                  </div>
                )}

                <div className="report-footer">
                  <span className="tracking-id">🎫 {report.tracking_id}</span>
                  <span className="location-text">
                    📍 {report.latitude?.toFixed(4)}, {report.longitude?.toFixed(4)}
                  </span>
                  {report.created_at && (
                    <span className="date-text">📅 {formatDate(report.created_at)}</span>
                  )}
                </div>

                {/* Delete Button */}
                <div className="report-actions">
                  {canDelete(report.status) ? (
                    <button
                      className="delete-btn"
                      onClick={() => handleDelete(report.id, report.status)}
                      disabled={deletingId === report.id}
                    >
                      {deletingId === report.id ? (
                        <>🔄 Deleting...</>
                      ) : (
                        <>🗑️ Delete</>
                      )}
                    </button>
                  ) : (
                    <span className="cannot-delete-msg">
                      ⚠️ Cannot modify - {report.status}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="map-container">
            <MapContainer
              center={getMapCenter()}
              zoom={13}
              className="reports-map"
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {reports
                .filter(report => report.latitude && report.longitude)
                .map((report) => (
                  <Marker key={report.id} position={[report.latitude, report.longitude]}>
                    <Popup>
                      <div className="map-popup">
                        <h3>{report.category}</h3>
                        {report.title && <h4>{report.title}</h4>}
                        <p>{report.description}</p>
                        {report.image_url && (
                          <img 
                            src={report.image_url} 
                            alt="Issue" 
                            className="popup-image"
                            onClick={() => setSelectedImage(report.image_url)}
                          />
                        )}
                        <span className={`status-badge ${getStatusClass(report.status)}`}>
                          {report.status}
                        </span>
                        <div className="popup-footer">
                          <small>🎫 {report.tracking_id}</small>
                        </div>
                      </div>
                    </Popup>
                  </Marker>
                ))}
            </MapContainer>
          </div>
        )}

        {/* Image Modal */}
        {selectedImage && (
          <ImageModal 
            imageUrl={selectedImage} 
            onClose={() => setSelectedImage(null)} 
          />
        )}
      </div>
    </div>
  );
};

export default ViewReports;
