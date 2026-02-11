// src/pages/MapView.jsx
import React, { useEffect, useState } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { loadReports } from "../utils/reportStorage";
import "leaflet/dist/images/marker-icon.png";
import "../styles/map.css"

// fix icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

const MapView = () => {
  const [reports, setReports] = useState([]);

  useEffect(() => {
    setReports(loadReports());
  }, []);

  // default center (if no reports) -> Bengaluru
  const center = reports.length ? [reports[0].lat, reports[0].lng] : [12.9716, 77.5946];

  return (
    <div className="min-h-screen bg-gray-50 py-16 px-4 mapview-root">
      <div className="max-w-6xl mx-auto mapview-container">
        <h2 className="text-2xl font-semibold mb-4">Reported Issues</h2>
        <div className="rounded-lg overflow-hidden border border-gray-200 shadow-sm mapview-mapwrap">
          <MapContainer center={center} zoom={13} style={{ height: "60vh", width: "100%" }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            {reports.map((r) => (
              <Marker key={r.id} position={[r.lat, r.lng]}>
                <Popup>
                  <div className="max-w-xs mapview-popup">
                    <h3 className="font-semibold">{r.category}</h3>
                    <p className="text-sm text-gray-600 my-1">{r.description}</p>
                    <p className="text-xs text-gray-500">By: {r.name}</p>
                    <p className="text-xs text-gray-500">Status: {r.status}</p>
                    {r.image && <img src={r.image} alt="report" className="mt-2 w-full h-24 object-cover rounded" />}
                    <p className="text-xs text-gray-400 mt-2">{new Date(r.createdAt).toLocaleString()}</p>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>

        {reports.length === 0 && (
          <p className="mt-4 text-gray-600">No reports yet. Submit one from the Report page.</p>
        )}
      </div>
    </div>
  );
};

export default MapView;
