import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import { useNavigate } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Copy, ArrowRight, CheckCircle } from "lucide-react";
import { complaintsAPI, authHelpers } from "../services/api";
import "../styles/report.css";
import "../styles/ReportSuccessPopup.css";

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Location picker for map
const LocationPicker = ({ setPosition }) => {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    },
  });
  return null;
};

const ReportIssue = () => {
  const navigate = useNavigate();
  const [position, setPosition] = useState(null);
  const [showSuccessPopup, setShowSuccessPopup] = useState(false);
  const [trackingId, setTrackingId] = useState("");
  const [predictedCategory, setPredictedCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Confirmation dialog state for low-confidence predictions
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [confirmationData, setConfirmationData] = useState(null);
  
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    categories: [], // Changed to array for multi-select
    image: null
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError("");
  };

  const handleCategoryToggle = (category) => {
    setFormData(prev => {
      const categories = prev.categories.includes(category)
        ? prev.categories.filter(c => c !== category)
        : [...prev.categories, category];
      return { ...prev, categories };
    });
    setError("");
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError("Please select an image file");
        return;
      }
      // Validate file size (max 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError("Image size must be less than 5MB");
        return;
      }
      setFormData(prev => ({ ...prev, image: file }));
      setError("");
    }
  };

  const validateForm = () => {
    if (!authHelpers.isAuthenticated()) {
      setError("Please login to submit a complaint");
      return false;
    }
    if (!formData.title.trim()) {
      setError("Please enter a title for the issue");
      return false;
    }
    if (!formData.description.trim()) {
      setError("Please describe the issue");
      return false;
    }
    if (formData.categories.length === 0) {
      setError("Please select at least one category");
      return false;
    }
    if (!position) {
      setError("Please select a location on the map");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e, userConfirmed = false) => {
    if (e) e.preventDefault();
    setError("");

    if (!validateForm()) return;

    setLoading(true);

    try {
      // Create FormData for multipart upload
      const submitData = new FormData();
      submitData.append("title", formData.title.trim());
      submitData.append("description", formData.description.trim());
      // Send categories as comma-separated string or JSON
      submitData.append("category", formData.categories.join(",")); // e.g., "Garbage,Pothole"
      submitData.append("latitude", position.lat.toString());
      submitData.append("longitude", position.lng.toString());
      
      if (formData.image) {
        submitData.append("image", formData.image);
      }
      
      // Add user_confirmed flag if this is a confirmation submission
      if (userConfirmed) {
        submitData.append("user_confirmed", "true");
      }

      const response = await complaintsAPI.submit(submitData);
      
      // Store last submitted complaint
      localStorage.setItem("lastComplaint", JSON.stringify({
        tracking_id: response.tracking_id,
        title: formData.title,
        category: formData.categories.join(" + "), // Display as "Garbage + Pothole"
        status: "Pending",
        created_at: new Date().toISOString()
      }));

      setTrackingId(response.tracking_id);
      setPredictedCategory(formData.categories.join(" + "));
      setShowSuccessPopup(true);

      // Reset form
      setFormData({
        title: "",
        description: "",
        categories: [],
        image: null
      });
      setPosition(null);

    } catch (err) {
      console.error("Submission error:", err);
      
      // Check for AI validation failures
      const errorType = err.errorType || "";
      const imageClass = err.imageClassification || err.detectedCategory || "unknown";
      const suggestion = err.suggestion || "Please upload a clear image of the actual civic issue.";
      const confidence = err.confidence ? `${(err.confidence * 100).toFixed(1)}%` : "";
      
      // Handle low-confidence confirmation request
      if (errorType === "NEEDS_CONFIRMATION" || err.requiresConfirmation) {
        setConfirmationData({
          detectedCategory: err.detectedCategory || imageClass,
          confidence: err.confidence,
          message: err.message || err.confirmationPrompt,
          suggestion: suggestion
        });
        setShowConfirmDialog(true);
        setLoading(false);
        return;
      }
      
      if (errorType === "INVALID_IMAGE" || (err.message && err.message.includes("INVALID_IMAGE"))) {
        setError(`🚫 Invalid Image\n\nThe uploaded image does not appear to contain a valid civic issue.\n\nDetected: ${imageClass}${confidence ? ` (${confidence})` : ""}\n\n${suggestion}`);
      } else if (errorType === "VERY_LOW_CONFIDENCE" || errorType === "LOW_CONFIDENCE" || (err.message && err.message.includes("LOW_CONFIDENCE"))) {
        setError(`📷 Image Not Clear Enough\n\nThe AI couldn't confidently identify the issue in your image.\n\nConfidence: ${confidence}\n\n${suggestion}`);
      } else if (errorType === "CATEGORY_MISMATCH" || (err.message && err.message.includes("CATEGORY_MISMATCH"))) {
        const detectedCategory = err.detectedCategory || imageClass;
        const userCategory = err.userCategory || formData.category;
        setError(`⚠️ Category Mismatch\n\nYou selected "${userCategory}" but the image shows "${detectedCategory}".\n\nConfidence: ${confidence}\n\n${suggestion}`);
      } else if (err.validationError || (err.message && err.message.includes("FAKE_COMPLAINT"))) {
        const reason = err.message.replace("FAKE_COMPLAINT: ", "");
        setError(`⚠️ Validation Failed\n\n${reason}\n\nImage detected as: ${imageClass}\n\n${suggestion}`);
      } else if (err.message && err.message.includes("login")) {
        setError("Please login to submit a complaint");
        setTimeout(() => navigate("/login"), 2000);
      } else {
        setError(err.message || "Failed to submit complaint. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };
  
  // Handle user confirmation for low-confidence predictions
  const handleConfirmSubmit = () => {
    setShowConfirmDialog(false);
    setConfirmationData(null);
    handleSubmit(null, true); // Resubmit with user_confirmed=true
  };
  
  const handleCancelConfirm = () => {
    setShowConfirmDialog(false);
    setConfirmationData(null);
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(trackingId);
    alert("Tracking ID copied to clipboard!");
  };

  return (
    <div className="min-h-screen flex justify-center items-center bg-gray-50 py-16 px-4 report-root">
      {/* Low-Confidence Confirmation Dialog */}
      {showConfirmDialog && confirmationData && (
        <div className="popup-overlay">
          <div className="popup-card" style={{ maxWidth: "450px" }}>
            <div className="popup-icon">🤔</div>
            <h3 className="popup-title">Confirm Your Submission</h3>
            
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg mb-4">
              <p className="text-gray-700 mb-2">
                The AI detected this as <strong>{confirmationData.detectedCategory}</strong> with 
                <strong> {(confirmationData.confidence * 100).toFixed(1)}%</strong> confidence.
              </p>
              <p className="text-sm text-gray-600">
                {confirmationData.message || "The confidence is lower than usual. This might be due to image quality, lighting, or partial visibility of the issue."}
              </p>
            </div>
            
            <p className="text-gray-700 mb-4">
              Does this image show a valid <strong>{formData.categories.join(' + ')}</strong> issue?
            </p>

            <div className="popup-actions" style={{ display: "flex", gap: "12px" }}>
              <button 
                onClick={handleCancelConfirm} 
                className="btn-popup"
                style={{ 
                  backgroundColor: "#f3f4f6", 
                  color: "#374151",
                  flex: 1 
                }}
              >
                Cancel & Re-upload
              </button>
              <button 
                onClick={handleConfirmSubmit} 
                className="btn-popup"
                style={{ 
                  backgroundColor: "#10b981", 
                  color: "white",
                  flex: 1 
                }}
              >
                <CheckCircle size={18} style={{ marginRight: "6px" }} />
                Yes, Submit
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* Success Popup */}
      {showSuccessPopup && (
        <div className="popup-overlay">
          <div className="popup-card">
            <div className="popup-icon">🎉</div>
            <h3 className="popup-title">Complaint Registered Successfully</h3>
            
            <div className="tracking-section">
              <span className="tracking-label">Tracking ID</span>
              <span className="tracking-id">{trackingId}</span>
            </div>

            <div className="popup-details">
              <div className="detail-row">
                <span className="detail-label">Category:</span>
                <span className="detail-value">{predictedCategory}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Status:</span>
                <span className="status-badge">Pending</span>
              </div>
            </div>

            <div className="popup-actions">
              <button onClick={copyToClipboard} className="btn-popup btn-copy">
                <Copy size={18} /> Copy ID
              </button>
              <button onClick={() => navigate("/user/view")} className="btn-popup btn-track">
                Track Status <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="w-full max-w-2xl bg-white shadow-xl rounded-2xl border border-gray-200 p-8 report-card">
        {/* Title */}
        <h2 className="text-3xl font-extrabold mb-8 text-center text-gray-800">
          🏙️ Report a Civic Issue
        </h2>

        {/* Auth Check */}
        {!authHelpers.isAuthenticated() && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg text-yellow-800 text-center">
            Please <a href="/login" className="text-blue-600 underline font-medium">login</a> to submit a complaint
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className={`error-message ${error.includes("Validation Failed") ? "validation-error" : ""}`}>
            {error}
          </div>
        )}

        {/* Form */}
        <form className="space-y-8" onSubmit={handleSubmit}>

          {/* --- 1. Issue Details Section --- */}
          <div className="space-y-4">
            <h3 className="text-gray-800 font-semibold mb-4">
               1. Issue Details
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Issue Title *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                placeholder="Brief title for the issue"
                disabled={loading}
                className="w-full border border-gray-300 rounded-lg p-3 focus:ring-2 focus:ring-blue-500 focus:outline-none disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Issue Category * 
                <span className="text-xs text-gray-500 ml-2">(Select all that apply)</span>
              </label>
              <div className="space-y-2">
                {['Pothole', 'Garbage', 'Waterlogging'].map((category) => (
                  <label 
                    key={category}
                    className={`flex items-center p-3 border-2 rounded-lg cursor-pointer transition-all ${
                      formData.categories.includes(category)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={formData.categories.includes(category)}
                      onChange={() => handleCategoryToggle(category)}
                      disabled={loading}
                      className="w-5 h-5 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="ml-3 text-gray-800 font-medium">
                      {category === 'Waterlogging' ? 'Water Logging' : category}
                    </span>
                    {formData.categories.includes(category) && (
                      <CheckCircle size={18} className="ml-auto text-blue-600" />
                    )}
                  </label>
                ))}
              </div>
              {formData.categories.length > 0 && (
                <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-800">
                  ✓ Selected: <strong>{formData.categories.join(' + ')}</strong>
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Describe the Issue *
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                placeholder="Give a detailed description of the issue..."
                disabled={loading}
                className="w-full border border-gray-300 rounded-lg p-3 h-28 focus:ring-2 focus:ring-blue-500 focus:outline-none resize-none disabled:bg-gray-100"
              ></textarea>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Attach Photo (optional)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                disabled={loading}
                className="w-full border border-gray-300 rounded-lg p-3 bg-gray-50 focus:outline-none disabled:bg-gray-100"
              />
              {formData.image && (
                <p className="mt-1 text-sm text-green-600">
                  ✓ {formData.image.name} selected
                </p>
              )}
            </div>
          </div>

          {/* --- 2. Map Section --- */}
          <div className="space-y-4 pt-4 border-t border-gray-200">
            <h3 className="text-gray-800 font-semibold mb-2 flex items-center">
               2. Select Location on Map *
            </h3>
            <p className="text-sm text-gray-500 mb-3">
              Click any point on the map to mark the issue location.
            </p>

            <div className="rounded-lg overflow-hidden shadow-inner border border-gray-300">
              <MapContainer
                center={[12.9716, 77.5946]} // Default: Bengaluru
                zoom={13}
                style={{ height: "350px", width: "100%" }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; OpenStreetMap contributors'
                />
                <LocationPicker setPosition={setPosition} />
                {position && <Marker position={position}></Marker>}
              </MapContainer>
            </div>

            {position && (
              <p className="mt-3 text-sm text-gray-700 text-center">
                Selected Location:{" "}
                <span className="font-semibold text-gray-900">
                  {position.lat.toFixed(4)}, {position.lng.toFixed(4)}
                </span>
              </p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading || !authHelpers.isAuthenticated()}
            className="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold shadow-md mt-4 disabled:bg-blue-400 disabled:cursor-not-allowed"
          >
            {loading ? "Submitting..." : "Submit Report"}
          </button>
        </form>
      </div>
    </div>
  );
};

export default ReportIssue;