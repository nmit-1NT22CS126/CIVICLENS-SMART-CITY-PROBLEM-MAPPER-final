import React, { useEffect } from "react";
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { authHelpers } from "../services/api";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

const UserLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();

  // Check authentication on mount and route changes
  useEffect(() => {
    if (!authHelpers.isAuthenticated()) {
      navigate("/login", { state: { from: location }, replace: true });
    }
  }, [navigate, location]);

  // Don't render anything if not authenticated
  if (!authHelpers.isAuthenticated()) {
    return null;
  }

  return (
    <>
      <Navbar />
      <Outlet />
      <Footer />
    </>
  );
};

export default UserLayout;
