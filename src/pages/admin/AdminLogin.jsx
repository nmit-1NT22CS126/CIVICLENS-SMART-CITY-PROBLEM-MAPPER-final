import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authAPI } from "../../services/api";
import "../../styles/AdminLogin.css";

const AdminLogin = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError(""); // Clear error on input change
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await authAPI.login(formData.email, formData.password);
      
      // Check if user has admin role
      if (response.role !== "admin") {
        setError("Access denied. Admin privileges required.");
        return;
      }

      // Store auth data using authHelpers for consistency
      const userData = {
        id: response.user_id,
        email: formData.email,
        role: response.role
      };
      
      localStorage.setItem("token", response.access_token);
      localStorage.setItem("admin_token", response.access_token);
      localStorage.setItem("user", JSON.stringify(userData));
      localStorage.setItem("user_role", response.role);
      localStorage.setItem("user_id", response.user_id);

      // Navigate to admin dashboard
      navigate("/admin/dashboard");
    } catch (err) {
      console.error("Admin login error:", err);
      setError(err.message || "Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h2>Admin Portal</h2>
          <p>Restricted Access</p>
        </div>

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label>Admin Email</label>
            <input
              type="email"
              name="email"
              required
              placeholder="admin@civiclens.com"
              value={formData.email}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <div className="login-form-group">
            <label>Password</label>
            <input
              type="password"
              name="password"
              required
              placeholder="••••••••"
              value={formData.password}
              onChange={handleChange}
              disabled={loading}
            />
          </div>

          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Login to Dashboard"}
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500">
           <Link to="/" className="hover:text-gray-900">← Back to Home</Link>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
