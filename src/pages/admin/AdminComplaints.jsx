import React, { useState, useEffect } from "react";
import { Search, Filter, RefreshCw, CheckCircle, Clock, AlertCircle, Eye, ChevronDown, Image } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { adminAPI, authHelpers } from "../../services/api";
import "../../styles/AdminComplaints.css";

const AdminComplaints = () => {
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filterStatus, setFilterStatus] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");
  const [updatingId, setUpdatingId] = useState(null);
  const [selectedImage, setSelectedImage] = useState(null); // For image modal

  const fetchComplaints = async () => {
    if (!authHelpers.isAuthenticated() || !authHelpers.isAdmin()) {
      navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await adminAPI.getAllReports();
      setComplaints(data);
    } catch (err) {
      if (err.message.includes("Admin") || err.message.includes("403")) {
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

  // Filter Logic
  const filteredComplaints = complaints.filter(c => {
    const matchesStatus = filterStatus === "All" || c.status === filterStatus;
    const matchesSearch = 
      (c.title?.toLowerCase() || "").includes(searchTerm.toLowerCase()) || 
      c.tracking_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleStatusChange = async (complaintId, newStatus) => {
    setUpdatingId(complaintId);
    try {
      await adminAPI.updateStatus(complaintId, newStatus);
      // Update local state
      setComplaints(prev => 
        prev.map(c => c.id === complaintId ? { ...c, status: newStatus } : c)
      );
    } catch (err) {
      alert("Failed to update status: " + err.message);
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "Pending": return <AlertCircle size={14} />;
      case "In-Review": return <Clock size={14} />;
      case "Resolved": return <CheckCircle size={14} />;
      default: return null;
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString("en-IN", {
      day: "numeric",
      month: "short",
      year: "numeric"
    });
  };

  return (
    <div className="complaints-page">
      <div className="page-header">
        <div className="page-title-section">
          <h1 className="page-title">Complaints Management</h1>
          <span className="complaint-count">{complaints.length} total</span>
        </div>
        
        {/* Filters & Search */}
        <div className="filters-container">
          <div className="search-wrapper">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              placeholder="Search ID, title, category..."
              className="search-input"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="filter-wrapper">
            <Filter className="filter-icon" size={20} />
            <select
              className="filter-select"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="All">All Status</option>
              <option value="Pending">Pending</option>
              <option value="In-Review">In Review</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>

          <button onClick={fetchComplaints} className="refresh-btn" disabled={loading}>
            <RefreshCw size={18} className={loading ? "spin" : ""} />
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="error-banner">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="loading-state">
          <RefreshCw size={40} className="spin" />
          <p>Loading complaints...</p>
        </div>
      )}

      {/* Table */}
      {!loading && (
        <div className="complaints-container">
          <table className="complaints-table">
            <thead>
              <tr>
                <th>Image</th>
                <th>Tracking ID</th>
                <th>Title</th>
                <th>Category</th>
                <th>Status</th>
                <th>Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredComplaints.map((complaint) => (
                <tr key={complaint.id}>
                  <td className="image-cell">
                    {complaint.image_url ? (
                      <div 
                        className="complaint-thumbnail"
                        onClick={() => setSelectedImage(complaint.image_url)}
                      >
                        <img src={complaint.image_url} alt="Evidence" />
                        <div className="thumbnail-overlay">
                          <Image size={14} />
                        </div>
                      </div>
                    ) : (
                      <div className="no-image">
                        <Image size={16} />
                      </div>
                    )}
                  </td>
                  <td className="tracking-cell">{complaint.tracking_id}</td>
                  <td className="title-cell">{complaint.title || "Untitled"}</td>
                  <td>
                    <span className="category-badge">{complaint.category}</span>
                  </td>
                  <td>
                    <div className="status-dropdown-wrapper">
                      <select
                        className={`status-select ${complaint.status.toLowerCase().replace("-", "")}`}
                        value={complaint.status}
                        onChange={(e) => handleStatusChange(complaint.id, e.target.value)}
                        disabled={updatingId === complaint.id}
                      >
                        <option value="Pending">Pending</option>
                        <option value="In-Review">In Review</option>
                        <option value="Resolved">Resolved</option>
                      </select>
                      {updatingId === complaint.id && (
                        <RefreshCw size={14} className="updating-icon spin" />
                      )}
                    </div>
                  </td>
                  <td className="date-cell">{formatDate(complaint.created_at)}</td>
                  <td>
                    <Link 
                      to={`/admin/complaint/${complaint.id}`}
                      className="action-btn"
                    >
                      <Eye size={16} /> View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {filteredComplaints.length === 0 && !loading && (
            <div className="empty-state">
              <p>No complaints found matching your criteria.</p>
            </div>
          )}
        </div>
      )}

      {/* Image Modal */}
      {selectedImage && (
        <div className="image-modal-overlay" onClick={() => setSelectedImage(null)}>
          <div className="image-modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="image-modal-close" onClick={() => setSelectedImage(null)}>×</button>
            <img src={selectedImage} alt="Complaint Evidence" />
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminComplaints;
