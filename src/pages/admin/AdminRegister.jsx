import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

const AdminRegister = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    secretCode: ""
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    // Mock admin registration
    if (formData.secretCode !== "ADMIN_SECRET") {
        alert("Invalid Secret Code! You cannot register as admin.");
        return;
    }
    
    alert("Admin account created. Please login.");
    navigate("/admin/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-2xl p-8 border border-gray-800">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900">New Admin</h2>
          <p className="text-gray-500 mt-2">Create Administrative Account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              name="fullName"
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-gray-800 focus:border-transparent outline-none transition"
              value={formData.fullName}
              onChange={handleChange}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Admin Email</label>
            <input
              type="email"
              name="email"
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-gray-800 focus:border-transparent outline-none transition"
              value={formData.email}
              onChange={handleChange}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              type="password"
              name="password"
              required
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-gray-800 focus:border-transparent outline-none transition"
              value={formData.password}
              onChange={handleChange}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Secret Code</label>
            <input
              type="password"
              name="secretCode"
              required
              placeholder="Required for admin access"
              className="w-full px-4 py-3 rounded-lg border border-gray-300 focus:ring-2 focus:ring-gray-800 focus:border-transparent outline-none transition"
              value={formData.secretCode}
              onChange={handleChange}
            />
          </div>

          <button
            type="submit"
            className="w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold py-3 rounded-lg transition duration-200 shadow-md"
          >
            Register Admin
          </button>
        </form>
        
        <div className="mt-6 text-center text-sm text-gray-500">
           <Link to="/admin/login" className="hover:text-gray-900">Back to Login</Link>
        </div>
      </div>
    </div>
  );
};

export default AdminRegister;
