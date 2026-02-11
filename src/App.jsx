import { BrowserRouter as Router, Routes, Route, useLocation } from "react-router-dom";
import Home from "./pages/Home";
import ReportIssue from "./pages/ReportIssue";
import ViewReports from "./pages/ViewReports";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Login from "./pages/Login";
import Register from "./pages/Register";
import UserDashboard from "./pages/UserDashboard";
import TrackComplaint from "./pages/TrackComplaint";
import UserComplaints from "./pages/UserComplaints";
import NotFound from "./pages/NotFound";

// Admin Pages
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminComplaints from "./pages/admin/AdminComplaints";
import AdminComplaintDetail from "./pages/admin/AdminComplaintDetail";
import AdminMap from "./pages/admin/AdminMap";

// Layouts
import UserLayout from "./layouts/UserLayout";
import AdminLayout from "./layouts/AdminLayout";

import { AnimatePresence, motion } from "framer-motion";
import "leaflet/dist/leaflet.css";

// Smooth Page Transition Component
const PageTransition = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    transition={{ duration: 0.4, ease: "easeInOut" }}
    className="min-h-screen bg-gradient-to-b from-blue-50 to-white"
  >
    {children}
  </motion.div>
);

// Animated Routes Setup
const AnimatedRoutes = () => {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        {/* Public Routes */}
        <Route path="/login" element={<PageTransition><Login /></PageTransition>} />
        <Route path="/register" element={<PageTransition><Register /></PageTransition>} />
        <Route path="/track" element={<PageTransition><TrackComplaint /></PageTransition>} />
        <Route path="/track/:trackingId" element={<PageTransition><TrackComplaint /></PageTransition>} />
        <Route path="/" element={<Login />} /> {/* Redirect root to login */}

        {/* User Routes */}
        <Route path="/user" element={<UserLayout />}>
          <Route index element={<PageTransition><Home /></PageTransition>} />
          <Route path="report" element={<PageTransition><ReportIssue /></PageTransition>} />
          <Route path="view" element={<PageTransition><ViewReports /></PageTransition>} />
          <Route path="complaints" element={<PageTransition><UserComplaints /></PageTransition>} />
          <Route path="track" element={<PageTransition><TrackComplaint /></PageTransition>} />
          <Route path="track/:trackingId" element={<PageTransition><TrackComplaint /></PageTransition>} />
          <Route path="about" element={<PageTransition><About /></PageTransition>} />
          <Route path="contact" element={<PageTransition><Contact /></PageTransition>} />
          <Route path="dashboard" element={<PageTransition><UserDashboard /></PageTransition>} />
        </Route>

        {/* Admin Routes */}
        <Route path="/admin" element={<AdminLayout />}>
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="complaints" element={<AdminComplaints />} />
            <Route path="complaint/:id" element={<AdminComplaintDetail />} />
            <Route path="map" element={<AdminMap />} />
        </Route>
        
        {/* 404 Not Found */}
        <Route path="*" element={<PageTransition><NotFound /></PageTransition>} />
      </Routes>
    </AnimatePresence>
  );
};

const App = () => {
  return (
    <Router>
      <AnimatedRoutes />
    </Router>
  );
};

export default App;
