// ...existing code...
import React from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { MapPin, ClipboardList, Users } from "lucide-react";
import "../styles/home.css";

const Home = () => {
  return (
    <div className="home-root">
      {/* HERO */}
      <section className="hero">
        <div className="hero-inner">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="hero-text"
          >
            <h1 className="hero-title">
              Make Your City <span className="accent">Smarter</span> with CivicLens
            </h1>
            <p className="hero-sub">
              Report civic issues instantly, empower transparency, and help authorities build cleaner, more efficient communities.
            </p>

            <div className="hero-ctas">
              <Link to="/user/report" className="btn btn-primary">
                Report an Issue
              </Link>
              <Link to="/user/view" className="btn btn-outline">
                View Reports
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8 }}
            className="hero-image-wrap"
          >
            <img
              src="https://cdn-icons-png.flaticon.com/512/3209/3209238.png"
              alt="Smart City"
              className="hero-image"
            />
          </motion.div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="features-section">
        <div className="container">
          <h2 className="section-title">Designed for Impact</h2>
          <div className="features-grid">
            {[
              {
                icon: <MapPin className="feature-icon" />,
                title: "Precise Geo-Tagging",
                desc: "Mark the exact location of any issue directly on the city map."
              },
              {
                icon: <ClipboardList className="feature-icon" />,
                title: "Transparent Tracking",
                desc: "Follow your report status and track progress from submission to resolution."
              },
              {
                icon: <Users className="feature-icon" />,
                title: "Community Driven",
                desc: "Encourage collaboration among citizens and local authorities."
              }
            ].map((feature, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                className="feature-card"
              >
                <div className="feature-icon-wrap">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-desc">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="how-section">
        <div className="container">
          <h2 className="section-title">How CivicLens Works</h2>
          <div className="steps-row">
            {[
              {
                step: "1",
                title: "Submit",
                desc: "Provide issue details and attach optional photos or videos."
              },
              {
                step: "2",
                title: "Track",
                desc: "Authorities acknowledge and update issue progress transparently."
              },
              {
                step: "3",
                title: "Resolve",
                desc: "Receive notifications once the issue has been resolved."
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: i * 0.15 }}
                className="step-card"
              >
                <div className="step-bubble">{item.step}</div>
                <h3 className="step-title">{item.title}</h3>
                <p className="step-desc">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="cta-section">
        <h2>Ready to Improve Your City?</h2>
        <p className="cta-sub">Join thousands of citizens making their neighborhoods cleaner and smarter.</p>
        <Link to="/report" className="btn btn-primary cta-btn">
          Start Reporting
        </Link>
      </section>

      {/* FOOTER */}
      <footer className="site-footer">
        © {new Date().getFullYear()} CivicLens — Empowering Smart Communities 🌍
      </footer>
    </div>
  );
};

export default Home;
// ...existing code...