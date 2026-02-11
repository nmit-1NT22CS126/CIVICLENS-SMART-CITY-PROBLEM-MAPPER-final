import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { authAPI, authHelpers } from "../services/api";
import "../styles/AdminLogin.css";

const Login = () => {
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

  const validateForm = () => {
    if (!formData.email.trim()) {
      setError("Email is required");
      return false;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      setError("Please enter a valid email address");
      return false;
    }
    if (!formData.password) {
      setError("Password is required");
      return false;
    }
    if (formData.password.length < 6) {
      setError("Password must be at least 6 characters");
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) return;

    setLoading(true);

    try {
      const response = await authAPI.login(formData.email, formData.password);
      
      // Store token and user data
      authHelpers.setAuth(response.access_token, {
        id: response.user_id,
        email: formData.email,
        role: response.role,
      });

      // Redirect based on role
      if (response.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/user");
      }
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-header">
          <h2>CivicLens</h2>
          <p>Secure Access Portal</p>
        </div>

        {error && (
          <div className="login-error">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label>Email Address</label>
            <input
              type="email"
              name="email"
              required
              placeholder="name@company.com"
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
            {loading ? (
              <span className="loading-spinner">Signing in...</span>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="login-links">
          <p>
            Don't have an account?{" "}
            <Link to="/register">Create Account</Link>
          </p>
        </div>
        
        <div className="demo-credentials">
          <strong>Demo Credentials:</strong>
          <p>User: user@civiclens.com / password123</p>
          <p>Admin: admin@civiclens.com / password123</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
