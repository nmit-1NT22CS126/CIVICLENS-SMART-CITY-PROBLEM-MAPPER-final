import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { ArrowLeft, RefreshCw, Send, MapPin, Clock, User, FileText, MessageSquare, Camera, CheckCircle, XCircle, AlertTriangle } from "lucide-react";
import { adminAPI, authHelpers } from "../../services/api";
import "../../styles/AdminComplaintDetails.css";

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const AdminComplaintDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updating, setUpdating] = useState(false);
  const [newNote, setNewNote] = useState("");
  const [sendingNote, setSendingNote] = useState(false);
  const [adminLogs, setAdminLogs] = useState([]);
  const [afterImage, setAfterImage] = useState(null);
  const [afterImagePreview, setAfterImagePreview] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  const fetchComplaint = async () => {
    if (!authHelpers.isAuthenticated() || !authHelpers.isAdmin()) {
      navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const allComplaints = await adminAPI.getAllReports();
      const found = allComplaints.find(c => c.id === parseInt(id));
      
      if (found) {
        setComplaint(found);
        // Fetch admin logs if tracking_id exists
        if (found.tracking_id) {
          try {
            const trackData = await fetch(`http://localhost:8000/track/${found.tracking_id}`);
            const trackJson = await trackData.json();
            setAdminLogs(trackJson.admin_logs || []);
          } catch (e) {
            console.log("Could not fetch admin logs");
          }
        }
      } else {
        setError("Complaint not found");
      }
    } catch (err) {
      setError(err.message || "Failed to fetch complaint");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComplaint();
  }, [id]);

  const handleStatusUpdate = async (newStatus) => {
    setUpdating(true);
    try {
      await adminAPI.updateStatus(complaint.id, newStatus);
      setComplaint(prev => ({ ...prev, status: newStatus }));
    } catch (err) {
      // Handle different error formats
      let errorMessage = "Unknown error occurred";
      if (typeof err === "string") {
        errorMessage = err;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      } else if (err?.detail) {
        errorMessage = err.detail;
      } else if (err?.message) {
        errorMessage = err.message;
      }
      alert("Failed to update status: " + errorMessage);
    } finally {
      setUpdating(false);
    }
  };

  const handleAddNote = async () => {
    if (!newNote.trim()) return;

    setSendingNote(true);
    try {
      await adminAPI.addNote(complaint.id, newNote.trim());
      // Add to local logs
      setAdminLogs(prev => [{
        message: newNote.trim(),
        timestamp: new Date().toISOString()
      }, ...prev]);
      setNewNote("");
    } catch (err) {
      // Handle different error formats
      let errorMessage = "Unknown error occurred";
      if (typeof err === "string") {
        errorMessage = err;
      } else if (err instanceof Error) {
        errorMessage = err.message;
      } else if (err?.detail) {
        errorMessage = err.detail;
      } else if (err?.message) {
        errorMessage = err.message;
      }
      alert("Failed to add note: " + errorMessage);
    } finally {
      setSendingNote(false);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      setAfterImage(file);
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setAfterImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
      // Clear previous result
      setVerificationResult(null);
    }
  };

  const handleVerifyCompletion = async () => {
    if (!afterImage) {
      alert("Please select an after image first");
      return;
    }

    setVerifying(true);
    setVerificationResult(null);

    try {
      const formData = new FormData();
      formData.append('after_image', afterImage);

      const token = authHelpers.getToken();
      const response = await fetch(
        `http://localhost:8000/complaints/${complaint.id}/verify-completion`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          },
          body: formData
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Verification failed");
      }

      setVerificationResult(result);

      // If verified successfully, update local complaint state
      if (result.verified && result.status_updated) {
        setComplaint(prev => ({
          ...prev,
          status: "Resolved",
          after_image_url: result.after_image_url,
          verification_confidence: result.confidence
        }));
      }
    } catch (err) {
      setVerificationResult({
        verified: false,
        decision: 'ERROR',
        message: err.message || "Failed to verify completion",
        confidence: 0
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleClearVerification = () => {
    setAfterImage(null);
    setAfterImagePreview(null);
    setVerificationResult(null);
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

  if (loading) {
    return (
      <div className="detail-loading">
        <RefreshCw size={40} className="spin" />
        <p>Loading complaint details...</p>
      </div>
    );
  }

  if (error || !complaint) {
    return (
      <div className="detail-error">
        <p>{error || "Complaint not found"}</p>
        <button onClick={() => navigate(-1)} className="btn-back">
          <ArrowLeft size={18} /> Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="detail-wrapper">
      <div className="detail-container">
        {/* Header */}
        <div className="detail-header">
          <button onClick={() => navigate(-1)} className="back-btn">
            <ArrowLeft size={20} />
          </button>
          <div className="detail-title">
            <h2>Complaint Details</h2>
            <div className="detail-id">{complaint.tracking_id}</div>
          </div>
          <div className={`status-badge ${
            complaint.status === "Pending" ? "status-pending" :
            complaint.status === "In-Review" ? "status-progress" :
            "status-resolved"
          }`}>
            {complaint.status}
          </div>
        </div>

        {/* Content */}
        <div className="detail-content">
          {/* Main Info */}
          <div className="detail-main">
            <div className="detail-section">
              <div className="detail-label"><FileText size={16} /> Title</div>
              <div className="detail-value">{complaint.title || "Untitled"}</div>
            </div>

            <div className="detail-section">
              <div className="detail-label">Category</div>
              <div className="category-tag">{complaint.category}</div>
            </div>

            <div className="detail-section">
              <div className="detail-label">Description</div>
              <div className="detail-value description">{complaint.description}</div>
            </div>

            <div className="detail-section">
              <div className="detail-label"><MapPin size={16} /> Location</div>
              <div className="location-coords">
                {complaint.latitude?.toFixed(6)}, {complaint.longitude?.toFixed(6)}
              </div>
              <div className="map-wrapper">
                <MapContainer 
                  center={[complaint.latitude, complaint.longitude]} 
                  zoom={15} 
                  style={{ height: "250px", width: "100%" }}
                >
                  <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; OpenStreetMap contributors'
                  />
                  <Marker position={[complaint.latitude, complaint.longitude]} />
                </MapContainer>
              </div>
            </div>

            {/* Image Comparison Section */}
            {complaint.image_url && (
              <div className="detail-section">
                <div className="detail-label">Images</div>
                <div className="image-comparison">
                  {/* Before Image (User's Complaint) */}
                  <div className="comparison-item">
                    <div className="comparison-badge before-badge">Before (Original Complaint)</div>
                    <img src={complaint.image_url} alt="Complaint Evidence" className="comparison-image" />
                  </div>

                  {/* After Image (Admin's Verification) */}
                  {(complaint.after_image_url || afterImagePreview) && (
                    <div className="comparison-item">
                      <div className="comparison-badge after-badge">
                        After (Verification)
                        {complaint.verification_confidence && (
                          <span className="badge-confidence">
                            {(complaint.verification_confidence * 100).toFixed(0)}% Match
                          </span>
                        )}
                      </div>
                      <img 
                        src={complaint.after_image_url || afterImagePreview} 
                        alt="Verification Evidence" 
                        className="comparison-image" 
                      />
                      {verificationResult && (
                        <div className={`image-result-overlay ${
                          verificationResult.verified ? 'overlay-success' : 'overlay-warning'
                        }`}>
                          {verificationResult.verified ? (
                            <><CheckCircle size={16} /> Verified</>
                          ) : (
                            <><XCircle size={16} /> Not Verified</>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="detail-sidebar">
            {/* Status Update */}
            <div className="sidebar-card">
              <h3 className="sidebar-title">Update Status</h3>
              <select 
                className="status-select-large"
                value={complaint.status}
                onChange={(e) => handleStatusUpdate(e.target.value)}
                disabled={updating}
              >
                <option value="Pending">Pending</option>
                <option value="In-Review">In Review</option>
                <option value="Resolved">Resolved</option>
              </select>
              {updating && <p className="updating-text">Updating...</p>}
            </div>

            {/* Work Verification */}
            {complaint.status !== "Resolved" && complaint.image_url && (
              <div className="sidebar-card">
                <h3 className="sidebar-title"><Camera size={16} /> Verify Completion</h3>
                <div className="verify-section">
                  <p className="verify-description">
                    Upload an after-completion photo to verify the work using AI comparison
                  </p>

                  {/* File Upload */}
                  <div className="file-upload-wrapper">
                    <input
                      type="file"
                      id="after-image"
                      accept="image/*"
                      onChange={handleFileChange}
                      className="file-input"
                      capture="environment"
                    />
                    <label htmlFor="after-image" className="file-label">
                      <Camera size={18} />
                      {afterImage ? 'Change Photo' : 'Take/Upload Photo'}
                    </label>
                  </div>

                  {/* Image Preview */}
                  {afterImagePreview && (
                    <div className="image-preview">
                      <img src={afterImagePreview} alt="After completion" />
                    </div>
                  )}

                  {/* Verify Button */}
                  {afterImage && !verificationResult && (
                    <button
                      onClick={handleVerifyCompletion}
                      disabled={verifying}
                      className="verify-btn"
                    >
                      {verifying ? (
                        <>
                          <RefreshCw size={16} className="spin" />
                          Verifying with AI...
                        </>
                      ) : (
                        <>
                          <CheckCircle size={16} />
                          Verify Completion
                        </>
                      )}
                    </button>
                  )}

                  {/* Verification Result */}
                  {verificationResult && (
                    <div className={`verification-result ${
                      verificationResult.verified ? 'result-success' :
                      verificationResult.decision === 'ERROR' ? 'result-error' :
                      'result-warning'
                    }`}>
                      <div className="result-header">
                        {verificationResult.verified ? (
                          <CheckCircle size={20} />
                        ) : verificationResult.decision === 'ERROR' ? (
                          <XCircle size={20} />
                        ) : (
                          <AlertTriangle size={20} />
                        )}
                        <strong>
                          {verificationResult.verified ? 'Work Verified!' :
                           verificationResult.decision === 'ERROR' ? 'Error' :
                           'Not Verified'}
                        </strong>
                      </div>
                      <p className="result-message">{verificationResult.message}</p>
                      <div className="result-details">
                        <div className="detail-row">
                          <span>Confidence:</span>
                          <span className="confidence-value">
                            {(verificationResult.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                        {verificationResult.details?.location_similarity && (
                          <div className="detail-row">
                            <span>Location Match:</span>
                            <span className="confidence-value">
                              {(verificationResult.details.location_similarity * 100).toFixed(1)}%
                            </span>
                          </div>
                        )}
                        {verificationResult.details?.before_classification && (
                          <div className="detail-row">
                            <span>Before:</span>
                            <span>{verificationResult.details.before_classification.original_class}</span>
                          </div>
                        )}
                        {verificationResult.details?.after_classification && (
                          <div className="detail-row">
                            <span>After:</span>
                            <span>{verificationResult.details.after_classification.original_class}</span>
                          </div>
                        )}
                      </div>
                      <button
                        onClick={handleClearVerification}
                        className="clear-btn"
                      >
                        Try Another Photo
                      </button>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Show After Image if Already Verified */}
            {complaint.after_image_url && (
              <div className="sidebar-card">
                <h3 className="sidebar-title"><CheckCircle size={16} /> Verification Photo</h3>
                <div className="verified-image">
                  <img src={complaint.after_image_url} alt="After completion" />
                  {complaint.verification_confidence && (
                    <div className="confidence-badge">
                      {(complaint.verification_confidence * 100).toFixed(0)}% Confidence
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Timeline */}
            <div className="sidebar-card">
              <h3 className="sidebar-title"><Clock size={16} /> Timeline</h3>
              <div className="timeline-info">
                <div className="timeline-row">
                  <span>Submitted</span>
                  <span>{formatDate(complaint.created_at)}</span>
                </div>
                <div className="timeline-row">
                  <span>Last Updated</span>
                  <span>{formatDate(complaint.updated_at)}</span>
                </div>
              </div>
            </div>

            {/* Add Note */}
            <div className="sidebar-card">
              <h3 className="sidebar-title"><MessageSquare size={16} /> Add Note</h3>
              <div className="note-input-wrapper">
                <textarea
                  placeholder="Write a note for this complaint..."
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  className="note-input"
                  rows={3}
                />
                <button 
                  onClick={handleAddNote} 
                  className="send-note-btn"
                  disabled={!newNote.trim() || sendingNote}
                >
                  {sendingNote ? <RefreshCw size={16} className="spin" /> : <Send size={16} />}
                  {sendingNote ? "Sending..." : "Add Note"}
                </button>
              </div>
            </div>

            {/* Admin Logs */}
            {adminLogs.length > 0 && (
              <div className="sidebar-card">
                <h3 className="sidebar-title">Admin Notes</h3>
                <div className="admin-logs">
                  {adminLogs.map((log, index) => (
                    <div key={index} className="log-item">
                      <p className="log-message">{log.message}</p>
                      <span className="log-time">{formatDate(log.timestamp)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminComplaintDetail;
