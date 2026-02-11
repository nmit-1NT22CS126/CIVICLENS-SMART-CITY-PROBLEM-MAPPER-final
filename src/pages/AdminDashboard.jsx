import React, { useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { Search, Filter, Map as MapIcon, List, X, Copy, CheckCircle, Clock, AlertCircle } from "lucide-react";

// Fix Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

// Mock Data
const MOCK_COMPLAINTS = [
  {
    id: "CVC-00102",
    type: "Pothole",
    status: "Pending",
    latitude: 12.92,
    longitude: 77.58,
    description: "Road cracked near signal",
    image: "https://placehold.co/600x400?text=Pothole+Image",
    date: "2023-10-27",
    reporter: "John Doe"
  },
  {
    id: "CVC-00103",
    type: "Garbage",
    status: "In Progress",
    latitude: 12.93,
    longitude: 77.59,
    description: "Garbage pileup on main street",
    image: "https://placehold.co/600x400?text=Garbage+Image",
    date: "2023-10-26",
    reporter: "Jane Smith"
  },
  {
    id: "CVC-00104",
    type: "Street Light",
    status: "Resolved",
    latitude: 12.94,
    longitude: 77.60,
    description: "Street light not working",
    image: "https://placehold.co/600x400?text=Street+Light",
    date: "2023-10-25",
    reporter: "Mike Johnson"
  },
  {
    id: "CVC-00105",
    type: "Water Leakage",
    status: "Pending",
    latitude: 12.95,
    longitude: 77.61,
    description: "Water pipe burst",
    image: "https://placehold.co/600x400?text=Water+Leak",
    date: "2023-10-24",
    reporter: "Sarah Wilson"
  },
  {
    id: "CVC-00106",
    type: "Pothole",
    status: "Pending",
    latitude: 12.925,
    longitude: 77.585,
    description: "Deep pothole causing traffic",
    image: "https://placehold.co/600x400?text=Pothole+2",
    date: "2023-10-28",
    reporter: "Alex Brown"
  }
];

const AdminDashboard = () => {
  const [complaints, setComplaints] = useState(MOCK_COMPLAINTS);
  const [viewMode, setViewMode] = useState("list"); // 'list' or 'map'
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [filterStatus, setFilterStatus] = useState("All");
  const [searchTerm, setSearchTerm] = useState("");

  // Filter Logic
  const filteredComplaints = complaints.filter(c => {
    const matchesStatus = filterStatus === "All" || c.status === filterStatus;
    const matchesSearch = c.type.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          c.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                          c.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  const handleStatusUpdate = (id, newStatus) => {
    setComplaints(prev => prev.map(c => c.id === id ? { ...c, status: newStatus } : c));
    if (selectedComplaint && selectedComplaint.id === id) {
      setSelectedComplaint(prev => ({ ...prev, status: newStatus }));
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert(`Copied ${text} to clipboard!`);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "Pending": return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "In Progress": return "bg-blue-100 text-blue-800 border-blue-200";
      case "Resolved": return "bg-green-100 text-green-800 border-green-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-center mb-8 bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
            <p className="text-gray-500 mt-1">Manage and track civic issues</p>
          </div>
          <div className="flex gap-3 mt-4 md:mt-0">
            <button 
              onClick={() => setViewMode("list")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${viewMode === "list" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
            >
              <List size={18} /> List View
            </button>
            <button 
              onClick={() => setViewMode("map")}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${viewMode === "map" ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
            >
              <MapIcon size={18} /> Map View
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input 
              type="text" 
              placeholder="Search by ID, Type, or Description..." 
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <select 
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none bg-white appearance-none"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="All">All Statuses</option>
              <option value="Pending">Pending</option>
              <option value="In Progress">In Progress</option>
              <option value="Resolved">Resolved</option>
            </select>
          </div>

          <div className="bg-white p-3 rounded-lg border border-gray-200 flex items-center justify-between px-6">
            <span className="text-gray-600 font-medium">Total Issues:</span>
            <span className="text-2xl font-bold text-blue-600">{filteredComplaints.length}</span>
          </div>
        </div>

        {/* Content Area */}
        {viewMode === "list" ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200 text-gray-600 text-sm uppercase tracking-wider">
                    <th className="p-4 font-semibold">ID</th>
                    <th className="p-4 font-semibold">Type</th>
                    <th className="p-4 font-semibold">Description</th>
                    <th className="p-4 font-semibold">Date</th>
                    <th className="p-4 font-semibold">Status</th>
                    <th className="p-4 font-semibold">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredComplaints.map((complaint) => (
                    <tr key={complaint.id} className="hover:bg-gray-50 transition">
                      <td className="p-4 font-medium text-gray-900">
                        <div className="flex items-center gap-2">
                          {complaint.id}
                          <button onClick={() => copyToClipboard(complaint.id)} className="text-gray-400 hover:text-blue-600">
                            <Copy size={14} />
                          </button>
                        </div>
                      </td>
                      <td className="p-4 text-gray-700">{complaint.type}</td>
                      <td className="p-4 text-gray-600 truncate max-w-xs">{complaint.description}</td>
                      <td className="p-4 text-gray-500 text-sm">{complaint.date}</td>
                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getStatusColor(complaint.status)}`}>
                          {complaint.status}
                        </span>
                      </td>
                      <td className="p-4">
                        <button 
                          onClick={() => setSelectedComplaint(complaint)}
                          className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                  {filteredComplaints.length === 0 && (
                    <tr>
                      <td colSpan="6" className="p-8 text-center text-gray-500">
                        No complaints found matching your criteria.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 h-[600px]">
            <MapContainer center={[12.9716, 77.5946]} zoom={12} style={{ height: "100%", width: "100%", borderRadius: "0.75rem" }}>
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              {filteredComplaints.map((complaint) => (
                <Marker 
                  key={complaint.id} 
                  position={[complaint.latitude, complaint.longitude]}
                  eventHandlers={{
                    click: () => setSelectedComplaint(complaint),
                  }}
                >
                  <Popup>
                    <div className="p-2">
                      <h3 className="font-bold text-gray-800">{complaint.type}</h3>
                      <p className="text-sm text-gray-600 mb-2">{complaint.id}</p>
                      <span className={`px-2 py-0.5 rounded text-xs border ${getStatusColor(complaint.status)}`}>
                        {complaint.status}
                      </span>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        )}

        {/* Details Modal */}
        {selectedComplaint && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-y-auto flex flex-col md:flex-row overflow-hidden">
              
              {/* Left: Image & Map */}
              <div className="w-full md:w-1/2 bg-gray-100 p-4 flex flex-col gap-4">
                <div className="h-64 bg-gray-200 rounded-lg overflow-hidden border border-gray-300">
                  <img 
                    src={selectedComplaint.image} 
                    alt="Complaint" 
                    className="w-full h-full object-cover"
                  />
                </div>
                <div className="h-64 rounded-lg overflow-hidden border border-gray-300 relative z-0">
                   <MapContainer 
                      center={[selectedComplaint.latitude, selectedComplaint.longitude]} 
                      zoom={15} 
                      style={{ height: "100%", width: "100%" }}
                      dragging={false}
                      scrollWheelZoom={false}
                      zoomControl={false}
                   >
                    <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <Marker position={[selectedComplaint.latitude, selectedComplaint.longitude]} />
                  </MapContainer>
                </div>
              </div>

              {/* Right: Details */}
              <div className="w-full md:w-1/2 p-8 flex flex-col">
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-1">{selectedComplaint.type}</h2>
                    <div className="flex items-center gap-2 text-gray-500 text-sm">
                      <span>ID: {selectedComplaint.id}</span>
                      <button onClick={() => copyToClipboard(selectedComplaint.id)} className="text-blue-600 hover:text-blue-800">
                        <Copy size={14} />
                      </button>
                    </div>
                  </div>
                  <button 
                    onClick={() => setSelectedComplaint(null)}
                    className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100 transition"
                  >
                    <X size={24} />
                  </button>
                </div>

                <div className="space-y-6 flex-grow">
                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-2">Description</h3>
                    <p className="text-gray-700 leading-relaxed bg-gray-50 p-4 rounded-lg border border-gray-100">
                      {selectedComplaint.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Date Reported</h3>
                      <p className="text-gray-800 font-medium">{selectedComplaint.date}</p>
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-1">Reporter</h3>
                      <p className="text-gray-800 font-medium">{selectedComplaint.reporter}</p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">Update Status</h3>
                    <div className="flex gap-3">
                      {["Pending", "In Progress", "Resolved"].map((status) => (
                        <button
                          key={status}
                          onClick={() => handleStatusUpdate(selectedComplaint.id, status)}
                          className={`flex-1 py-2 px-3 rounded-lg border text-sm font-medium transition flex items-center justify-center gap-2
                            ${selectedComplaint.status === status 
                              ? "bg-blue-600 text-white border-blue-600 shadow-md" 
                              : "bg-white text-gray-600 border-gray-300 hover:bg-gray-50"
                            }`}
                        >
                          {status === "Pending" && <AlertCircle size={16} />}
                          {status === "In Progress" && <Clock size={16} />}
                          {status === "Resolved" && <CheckCircle size={16} />}
                          {status}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-8 pt-6 border-t border-gray-100 text-center">
                  <p className="text-xs text-gray-400">
                    Location: {selectedComplaint.latitude.toFixed(4)}, {selectedComplaint.longitude.toFixed(4)}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default AdminDashboard;
