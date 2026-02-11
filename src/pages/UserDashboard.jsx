import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Clock, CheckCircle, AlertCircle, MapPin, RefreshCw, Loader } from "lucide-react";
import { complaintsAPI, authHelpers } from "../services/api";

const UserDashboard = () => {
  const navigate = useNavigate();
  const user = authHelpers.getUser();
  
  const [myComplaints, setMyComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchComplaints = async () => {
    if (!authHelpers.isAuthenticated()) {
      navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await complaintsAPI.getUserComplaints();
      setMyComplaints(data);
    } catch (err) {
      if (err.message.includes("login")) {
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

  const getStatusColor = (status) => {
    switch (status) {
      case "Pending": return "bg-yellow-100 text-yellow-800";
      case "In-Review": return "bg-blue-100 text-blue-800";
      case "Resolved": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
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
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8 flex flex-col md:flex-row justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Hello, {user?.email?.split('@')[0] || 'User'} 👋</h1>
            <p className="text-gray-500">Welcome to your dashboard</p>
          </div>
          <div className="flex gap-3 mt-4 md:mt-0">
            <button 
              onClick={fetchComplaints}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-4 py-2 rounded-lg font-medium transition flex items-center gap-2"
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
            <Link 
              to="/user/report" 
              className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition shadow-md"
            >
              + Report New Issue
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="text-gray-500 text-sm font-medium uppercase">Total Reports</div>
            <div className="text-3xl font-bold text-gray-800 mt-2">{myComplaints.length}</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="text-gray-500 text-sm font-medium uppercase">Pending</div>
            <div className="text-3xl font-bold text-yellow-600 mt-2">
              {myComplaints.filter(c => c.status === "Pending").length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="text-gray-500 text-sm font-medium uppercase">In Review</div>
            <div className="text-3xl font-bold text-blue-600 mt-2">
              {myComplaints.filter(c => c.status === "In-Review").length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
            <div className="text-gray-500 text-sm font-medium uppercase">Resolved</div>
            <div className="text-3xl font-bold text-green-600 mt-2">
              {myComplaints.filter(c => c.status === "Resolved").length}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Link to="/user/report" className="bg-blue-50 hover:bg-blue-100 border border-blue-200 p-4 rounded-xl text-center transition">
            <span className="text-2xl">📝</span>
            <p className="font-semibold text-blue-800 mt-2">Report Issue</p>
          </Link>
          <Link to="/user/complaints" className="bg-purple-50 hover:bg-purple-100 border border-purple-200 p-4 rounded-xl text-center transition">
            <span className="text-2xl">📋</span>
            <p className="font-semibold text-purple-800 mt-2">My Complaints</p>
          </Link>
          <Link to="/user/track" className="bg-green-50 hover:bg-green-100 border border-green-200 p-4 rounded-xl text-center transition">
            <span className="text-2xl">🔍</span>
            <p className="font-semibold text-green-800 mt-2">Track Complaint</p>
          </Link>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl mb-6 flex items-center gap-3">
            <AlertCircle size={20} />
            {error}
          </div>
        )}

        {/* Recent Reports */}
        <h2 className="text-xl font-bold text-gray-800 mb-4">Recent Reports</h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          {loading ? (
            <div className="p-12 text-center text-gray-500 flex flex-col items-center">
              <Loader size={32} className="animate-spin mb-3" />
              <p>Loading your reports...</p>
            </div>
          ) : myComplaints.length > 0 ? (
            <div className="divide-y divide-gray-100">
              {myComplaints.slice(0, 5).map((complaint) => (
                <div 
                  key={complaint.id} 
                  className="p-6 hover:bg-gray-50 transition cursor-pointer"
                  onClick={() => navigate(`/user/track/${complaint.tracking_id}`)}
                >
                  <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-2">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(complaint.status)}`}>
                          {complaint.status}
                        </span>
                        <span className="text-sm text-blue-600 font-mono font-semibold">{complaint.tracking_id}</span>
                        <span className="text-sm text-gray-400">• {formatDate(complaint.created_at)}</span>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-800">{complaint.title || complaint.category}</h3>
                      <p className="text-gray-600 mt-1 line-clamp-1">{complaint.description}</p>
                      <div className="flex items-center gap-1 text-gray-500 text-sm mt-2">
                        <MapPin size={14} />
                        {complaint.latitude?.toFixed(4)}, {complaint.longitude?.toFixed(4)}
                      </div>
                    </div>
                    <Link 
                      to={`/user/track/${complaint.tracking_id}`}
                      className="text-blue-600 hover:text-blue-800 font-medium text-sm whitespace-nowrap"
                      onClick={(e) => e.stopPropagation()}
                    >
                      View Details →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center text-gray-500">
              <p className="text-4xl mb-4">📭</p>
              <p className="text-lg font-medium">You haven't submitted any reports yet.</p>
              <Link to="/user/report" className="text-blue-600 hover:underline mt-2 inline-block">
                Report your first issue →
              </Link>
            </div>
          )}
          
          {myComplaints.length > 5 && (
            <div className="p-4 bg-gray-50 border-t text-center">
              <Link to="/user/complaints" className="text-blue-600 hover:text-blue-800 font-medium">
                View all {myComplaints.length} complaints →
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;
