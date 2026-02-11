// src/pages/About.jsx
import React from "react";
import "../styles/about.css"

const About = () => {
  return (
    <div className="about-root">
      <div className="about-container">
        <h1>
          About <span>CivicLens</span>
        </h1>

        <p className="about-intro">
          <strong>CivicLens</strong> is a community-driven platform that empowers
          citizens to identify and report civic issues — from water leaks and
          potholes to waste management and broken streetlights. Our mission is
          to help local authorities act faster and make our cities cleaner,
          smarter, and more sustainable.
        </p>

        <div className="about-grid">
          <div className="mission-card">
            <h3>🌍 Our Mission</h3>
            <p>
              To bridge the communication gap between citizens and city
              authorities using technology that encourages participation,
              transparency, and quick response.
            </p>
          </div>

          <div className="vision-card">
            <h3>💡 Our Vision</h3>
            <p>
              We envision cleaner, better-connected communities where civic
              issues are addressed swiftly through data-driven insights and
              active collaboration.
            </p>
          </div>
        </div>

        <div className="team-section">
          <h3>👩‍💻 Built By</h3>
          <p>
            A passionate team of innovators dedicated to smart city development,
            sustainability, and public participation.
          </p>
        </div>
      </div>
    </div>
  );
};

export default About;
