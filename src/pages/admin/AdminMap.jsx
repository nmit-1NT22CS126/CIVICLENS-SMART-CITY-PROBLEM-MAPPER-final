import React, { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useNavigate } from "react-router-dom";
import { adminAPI, authHelpers } from "../../services/api";
import "../../styles/AdminMap.css";

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Custom colored markers for different statuses
const createColoredIcon = (color) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: 24px;
      height: 24px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      border: 2px solid white;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [24, 24],
    iconAnchor: [12, 24],
    popupAnchor: [0, -24],
  });
};

const statusIcons = {
  "Pending": createColoredIcon("#EAB308"),      // Yellow
  "In-Review": createColoredIcon("#3B82F6"),    // Blue
  "In Progress": createColoredIcon("#3B82F6"),  // Blue
  "Resolved": createColoredIcon("#22C55E"),     // Green
  "Rejected": createColoredIcon("#EF4444"),     // Red
};

const AdminMap = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]); // Default: Bangalore

  useEffect(() => {
    const fetchComplaints = async () => {
      if (!authHelpers.isAuthenticated() || !authHelpers.isAdmin()) {
        navigate("/admin/login");
        return;
      }

      try {
        setLoading(true);
        const data = await adminAPI.getAllReports();
        
        // Filter complaints that have valid coordinates
        const validComplaints = data.filter(
          c => c.latitude && c.longitude && 
          !isNaN(c.latitude) && !isNaN(c.longitude)
        );
        
        setComplaints(validComplaints);
        
        // Calculate center based on complaints
        if (validComplaints.length > 0) {
          const avgLat = validComplaints.reduce((sum, c) => sum + c.latitude, 0) / validComplaints.length;
          const avgLng = validComplaints.reduce((sum, c) => sum + c.longitude, 0) / validComplaints.length;
          setMapCenter([avgLat, avgLng]);
        }
      } catch (err) {
        console.error("Failed to fetch complaints:", err);
        setError(err.message || "Failed to load complaints");
      } finally {
        setLoading(false);
      }
    };

    fetchComplaints();
  }, [navigate]);

  const getStatusClass = (status) => {
    switch (status) {
      case "Pending": return "status-pending";
      case "In-Review":
      case "In Progress": return "status-progress";
      case "Resolved": return "status-resolved";
      case "Rejected": return "status-rejected";
      default: return "status-pending";
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return "";
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  if (loading) {
    return (
      <div className="map-page">
        <div className="map-header">
          <h1 className="text-2xl font-bold text-gray-800">Geospatial Overview</h1>
        </div>
        <div className="map-loading">
          <div className="spinner"></div>
          <p>Loading complaints map...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="map-page">
        <div className="map-header">
          <h1 className="text-2xl font-bold text-gray-800">Geospatial Overview</h1>
        </div>
        <div className="map-error">
          <p>⚠️ {error}</p>
          <button onClick={() => window.location.reload()}>Retry</button>
        </div>
      </div>
    );
  }

  return (
    <div className="map-page">
      <div className="map-header">
        <h1 className="text-2xl font-bold text-gray-800">Geospatial Overview</h1>
        <p className="text-gray-500">
          Visualizing {complaints.length} complaint{complaints.length !== 1 ? 's' : ''} across the city.
        </p>
        <div className="map-legend">
          <span className="legend-item"><span className="dot pending"></span> Pending</span>
          <span className="legend-item"><span className="dot progress"></span> In Progress</span>
          <span className="legend-item"><span className="dot resolved"></span> Resolved</span>
          <span className="legend-item"><span className="dot rejected"></span> Rejected</span>
        </div>
      </div>
      
      <div className="map-wrapper">
        {complaints.length === 0 ? (
          <div className="map-empty">
            <p>📍 No complaints with location data found.</p>
          </div>
        ) : (
          <MapContainer 
            center={mapCenter} 
            zoom={12} 
            style={{ height: "100%", width: "100%" }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {complaints.map((complaint) => (
              <Marker 
                key={complaint.id} 
                position={[complaint.latitude, complaint.longitude]}
                icon={statusIcons[complaint.status] || statusIcons["Pending"]}
                eventHandlers={{
                  click: () => {
                    navigate(`/admin/complaint/${complaint.id}`);
                  },
                }}
              >
                <Popup>
                  <div className="map-popup-content">
                    <div className="popup-header">
                      <h3>{complaint.category || complaint.title || "Complaint"}</h3>
                      <span className={`status-badge ${getStatusClass(complaint.status)}`}>
                        {complaint.status}
                      </span>
                    </div>
                    <p className="popup-description">{complaint.description}</p>
                    <div className="popup-meta">
                      <span className="tracking-id">🎫 {complaint.tracking_id}</span>
                      {complaint.created_at && (
                        <span className="date">📅 {formatDate(complaint.created_at)}</span>
                      )}
                    </div>
                    <button 
                      className="popup-btn"
                      onClick={() => navigate(`/admin/complaint/${complaint.id}`)}
                    >
                      View Details →
                    </button>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        )}
      </div>
    </div>
  );
};

export default AdminMap;
