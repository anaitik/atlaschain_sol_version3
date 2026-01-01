import React from 'react'
import { Link } from 'react-router-dom'
import './Footer.css'

function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-content">
          <div className="footer-section">
            <h3>AtlasChain</h3>
            <p>Agentic ESG Audit Preparation Platform</p>
            <p className="footer-tagline">
              Empowering organizations with AI-driven ESG compliance and blockchain-verified audit trails.
            </p>
          </div>

          <div className="footer-section">
            <h4>Platform</h4>
            <ul>
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/pipelines">Pipelines</Link></li>
              <li><Link to="/executions">Executions</Link></li>
              <li><Link to="/esg-standards">ESG Standards</Link></li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Features</h4>
            <ul>
              <li>AI-Powered Pipeline Creation</li>
              <li>Blockchain Anchoring</li>
              <li>ESG Report Generation</li>
              <li>Compliance Tracking</li>
            </ul>
          </div>

          <div className="footer-section">
            <h4>Resources</h4>
            <ul>
              <li><a href="https://www.globalreporting.org" target="_blank" rel="noopener noreferrer">GRI Standards</a></li>
              <li><a href="https://finance.ec.europa.eu" target="_blank" rel="noopener noreferrer">EU CSRD</a></li>
              <li><a href="https://www.sec.gov" target="_blank" rel="noopener noreferrer">SEC Guidelines</a></li>
              <li><a href="https://www.algorand.com" target="_blank" rel="noopener noreferrer">Algorand Network</a></li>
            </ul>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p>&copy; {currentYear} AtlasChain. All rights reserved.</p>
            <div className="footer-links">
              <a href="#" onClick={(e) => { e.preventDefault(); alert('Privacy Policy'); }}>Privacy Policy</a>
              <span>•</span>
              <a href="#" onClick={(e) => { e.preventDefault(); alert('Terms of Service'); }}>Terms of Service</a>
              <span>•</span>
              <a href="#" onClick={(e) => { e.preventDefault(); alert('Contact Support'); }}>Support</a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer

