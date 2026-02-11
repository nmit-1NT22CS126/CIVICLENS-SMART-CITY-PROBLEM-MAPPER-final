/**
 * CivicLens API Service
 * Centralized API layer with error handling, retry logic, and authentication
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ============================================
// CONFIGURATION
// ============================================

const config = {
  retryAttempts: 2,
  retryDelay: 1000,
  timeout: 30000, // 30 seconds
};

// ============================================
// UTILITY FUNCTIONS
// ============================================

// Get auth token from localStorage
const getToken = () => localStorage.getItem("token");

// Create timeout promise
const createTimeout = (ms) => {
  return new Promise((_, reject) => {
    setTimeout(() => reject(new Error("Request timeout")), ms);
  });
};

// Handle API response
const handleResponse = async (response) => {
  // Handle no content response
  if (response.status === 204) {
    return null;
  }

  let data;
  try {
    data = await response.json();
  } catch {
    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }
    return null;
  }

  if (!response.ok) {
    // Special handling for AI validation errors
    if (data?.detail?.error) {
      const errorType = data.detail.error;
      const error = new Error(`${errorType}: ${data.detail.message || "Validation failed"}`);
      error.validationError = true;
      error.errorType = errorType;
      error.response = { data };
      error.imageClassification = data.detail.image_classification;
      error.suggestion = data.detail.suggestion;
      error.confidence = data.detail.confidence;
      error.detectedCategory = data.detail.detected_category;
      error.userCategory = data.detail.user_category;
      // For low-confidence confirmation flow
      error.requiresConfirmation = data.detail.requires_confirmation;
      error.confirmationPrompt = data.detail.confirmation_prompt;
      error.status = data.detail.status;
      throw error;
    }
    
    const message = data?.detail || data?.message || getDefaultErrorMessage(response.status);
    const errorMessage = typeof message === 'object' ? JSON.stringify(message) : message;
    throw new Error(errorMessage);
  }

  return data;
};

// Get user-friendly error messages
const getDefaultErrorMessage = (status) => {
  const messages = {
    400: "Invalid request. Please check your input.",
    401: "Please login to continue.",
    403: "You don't have permission to perform this action.",
    404: "The requested resource was not found.",
    409: "A conflict occurred. The resource may already exist.",
    422: "Invalid data provided. Please check your input.",
    429: "Too many requests. Please try again later.",
    500: "Server error. Please try again later.",
    502: "Server is temporarily unavailable.",
    503: "Service temporarily unavailable. Please try again.",
  };
  return messages[status] || "Something went wrong. Please try again.";
};

// Fetch with retry and timeout
const fetchWithRetry = async (url, options, retries = config.retryAttempts) => {
  try {
    console.log(`[API] Fetching: ${url}`);
    const response = await Promise.race([
      fetch(url, options),
      createTimeout(config.timeout),
    ]);
    console.log(`[API] Response status: ${response.status}`);
    return response;
  } catch (error) {
    console.error(`[API] Fetch error for ${url}:`, error.message, error);
    
    // Don't retry on timeout or if we're out of retries
    if (retries <= 0 || error.message === "Request timeout") {
      if (error.message === "Request timeout") {
        throw new Error("Request timed out. Please check your connection.");
      }
      if (error.name === "TypeError" && error.message === "Failed to fetch") {
        throw new Error(`Unable to connect to server at ${url}. Backend may not be running.`);
      }
      throw error;
    }

    console.log(`[API] Retrying... (${retries} attempts left)`);
    // Wait before retrying
    await new Promise((resolve) => setTimeout(resolve, config.retryDelay));
    return fetchWithRetry(url, options, retries - 1);
  }
};

// Create request with common headers
const createRequest = (method, body = null, requiresAuth = false, isFormData = false) => {
  const headers = {};

  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }

  if (requiresAuth) {
    const token = getToken();
    if (!token) {
      throw new Error("Authentication required. Please login.");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const options = { method, headers };

  if (body) {
    options.body = isFormData ? body : JSON.stringify(body);
  }

  return options;
};

// ============================================
// AUTH API
// ============================================

export const authAPI = {
  // Login user
  login: async (email, password) => {
    const options = createRequest("POST", { email, password });
    const response = await fetchWithRetry(`${API_BASE_URL}/auth/login`, options);
    return handleResponse(response);
  },

  // Register user
  register: async (name, email, password) => {
    const options = createRequest("POST", { name, email, password });
    const response = await fetchWithRetry(`${API_BASE_URL}/auth/register`, options);
    return handleResponse(response);
  },

  // Verify token is still valid
  verifyToken: async () => {
    try {
      const options = createRequest("GET", null, true);
      const response = await fetch(`${API_BASE_URL}/auth/verify`, options);
      return response.ok;
    } catch {
      return false;
    }
  },
};

// ============================================
// COMPLAINTS API
// ============================================

export const complaintsAPI = {
  // Submit a new complaint
  submit: async (formData) => {
    const token = getToken();
    if (!token) {
      throw new Error("Please login to submit a complaint");
    }

    const response = await fetchWithRetry(`${API_BASE_URL}/report`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData, // FormData for multipart/form-data
    });
    return handleResponse(response);
  },

  // Get user's complaints
  getUserComplaints: async () => {
    const options = createRequest("GET", null, true);
    const response = await fetchWithRetry(`${API_BASE_URL}/user/reports`, options);
    return handleResponse(response);
  },

  // Delete user's complaint (only pending)
  deleteComplaint: async (complaintId) => {
    if (!complaintId) {
      throw new Error("Complaint ID is required");
    }
    const options = createRequest("DELETE", null, true);
    const response = await fetchWithRetry(
      `${API_BASE_URL}/user/complaint/${complaintId}`,
      options
    );
    return handleResponse(response);
  },

  // Track complaint by tracking ID (public)
  track: async (trackingId) => {
    if (!trackingId?.trim()) {
      throw new Error("Tracking ID is required");
    }
    const options = createRequest("GET");
    const response = await fetchWithRetry(`${API_BASE_URL}/track/${trackingId.trim()}`, options);
    return handleResponse(response);
  },

  // Get complaint by tracking ID (authenticated)
  getByTrackingId: async (trackingId) => {
    const token = getToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : {};
    const response = await fetchWithRetry(`${API_BASE_URL}/report/${trackingId}`, {
      method: "GET",
      headers,
    });
    return handleResponse(response);
  },
};

// ============================================
// ADMIN API
// ============================================

export const adminAPI = {
  // Get all reports
  getAllReports: async () => {
    const options = createRequest("GET", null, true);
    const response = await fetchWithRetry(`${API_BASE_URL}/admin/reports`, options);
    return handleResponse(response);
  },

  // Get single report by ID
  getReportById: async (reportId) => {
    const options = createRequest("GET", null, true);
    const response = await fetchWithRetry(`${API_BASE_URL}/admin/report/${reportId}`, options);
    return handleResponse(response);
  },

  // Update complaint status
  updateStatus: async (complaintId, status) => {
    if (!complaintId || !status) {
      throw new Error("Complaint ID and status are required");
    }
    const options = createRequest("PUT", { status }, true);
    const response = await fetchWithRetry(
      `${API_BASE_URL}/admin/report/${complaintId}/status`,
      options
    );
    return handleResponse(response);
  },

  // Add admin note
  addNote: async (complaintId, message) => {
    if (!complaintId || !message?.trim()) {
      throw new Error("Complaint ID and message are required");
    }
    const options = createRequest("POST", { message: message.trim() }, true);
    const response = await fetchWithRetry(
      `${API_BASE_URL}/admin/report/${complaintId}/note`,
      options
    );
    return handleResponse(response);
  },

  // Get dashboard stats
  getStats: async () => {
    const options = createRequest("GET", null, true);
    const response = await fetchWithRetry(`${API_BASE_URL}/admin/stats`, options);
    return handleResponse(response);
  },

  // Delete report (if available)
  deleteReport: async (reportId) => {
    const options = createRequest("DELETE", null, true);
    const response = await fetchWithRetry(`${API_BASE_URL}/admin/report/${reportId}`, options);
    return handleResponse(response);
  },
};

// ============================================
// AUTH HELPERS
// ============================================

export const authHelpers = {
  // Store auth data after login
  setAuth: (token, user) => {
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(user));
  },

  // Clear auth data on logout
  clearAuth: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("lastComplaint");
  },

  // Get current token
  getToken: () => localStorage.getItem("token"),

  // Get current user
  getUser: () => {
    try {
      const user = localStorage.getItem("user");
      return user ? JSON.parse(user) : null;
    } catch {
      return null;
    }
  },

  // Check if user is authenticated
  isAuthenticated: () => {
    return !!localStorage.getItem("token");
  },

  // Check if user is admin
  isAdmin: () => {
    // Check user object first
    const user = authHelpers.getUser();
    if (user?.role === "admin") return true;
    
    // Fallback to user_role in localStorage
    const role = localStorage.getItem("user_role");
    return role === "admin";
  },

  // Get user role
  getRole: () => {
    const user = authHelpers.getUser();
    return user?.role || null;
  },

  // Update user data
  updateUser: (updates) => {
    const user = authHelpers.getUser();
    if (user) {
      localStorage.setItem("user", JSON.stringify({ ...user, ...updates }));
    }
  },
};

// ============================================
// EXPORTS
// ============================================

export default { authAPI, complaintsAPI, adminAPI, authHelpers };
