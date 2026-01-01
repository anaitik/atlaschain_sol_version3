import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import './Navbar.css'

function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    const updateUser = () => {
      const userData = localStorage.getItem('user')
      if (userData) {
        setUser(JSON.parse(userData))
      } else {
        setUser(null)
      }
    }
    
    // Check on mount and when location changes
    updateUser()
    
    // Listen for storage changes (when user logs in/out in another tab)
    window.addEventListener('storage', updateUser)
    
    // Also check periodically in case of same-tab login
    const interval = setInterval(updateUser, 1000)
    
    return () => {
      window.removeEventListener('storage', updateUser)
      clearInterval(interval)
    }
  }, [location])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
    navigate('/login')
  }
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  const isActive = (path) => location.pathname === path

  return (
    <nav className="navbar">
      <div className="navbar-container">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="32" height="32" rx="6" fill="url(#gradient)"/>
              <path d="M16 8L24 12V20L16 24L8 20V12L16 8Z" fill="white" opacity="0.9"/>
              <path d="M16 12L20 14V18L16 20L12 18V14L16 12Z" fill="white"/>
              <defs>
                <linearGradient id="gradient" x1="0" y1="0" x2="32" y2="32">
                  <stop offset="0%" stopColor="#667eea"/>
                  <stop offset="100%" stopColor="#764ba2"/>
                </linearGradient>
              </defs>
            </svg>
          </div>
          <div className="brand-text">
            <span className="brand-name">AtlasChain</span>
            <span className="brand-tagline">ESG Audit Platform</span>
          </div>
        </Link>

        <button 
          className="mobile-menu-toggle"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div className={`navbar-menu ${isMobileMenuOpen ? 'active' : ''}`}>
          <Link 
            to="/" 
            className={`navbar-link ${isActive('/') ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M3 10L10 3L17 10M5 10V16H8V13H12V16H15V10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Dashboard
          </Link>
          <Link 
            to="/pipelines" 
            className={`navbar-link ${isActive('/pipelines') ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M3 5H17M3 10H17M3 15H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Pipelines
          </Link>
          <Link 
            to="/pipelines/create" 
            className={`navbar-link ${isActive('/pipelines/create') ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 3V17M3 10H17" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Create Pipeline
          </Link>
          <Link 
            to="/executions" 
            className={`navbar-link ${isActive('/executions') ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M3 4H17V16H3V4Z" stroke="currentColor" strokeWidth="2"/>
              <path d="M7 8H13M7 12H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            Executions
          </Link>
          <Link 
            to="/esg-standards" 
            className={`navbar-link ${isActive('/esg-standards') ? 'active' : ''}`}
            onClick={() => setIsMobileMenuOpen(false)}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M10 2L3 7V17L10 22L17 17V7L10 2Z" stroke="currentColor" strokeWidth="2"/>
              <path d="M10 10V22" stroke="currentColor" strokeWidth="2"/>
            </svg>
            ESG Standards
          </Link>
          {user && user.role === 'admin' && (
            <Link 
              to="/admin" 
              className={`navbar-link ${isActive('/admin') ? 'active' : ''}`}
              onClick={() => setIsMobileMenuOpen(false)}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2L3 7V17L10 22L17 17V7L10 2Z" stroke="currentColor" strokeWidth="2"/>
                <path d="M10 10V22" stroke="currentColor" strokeWidth="2"/>
              </svg>
              Admin
            </Link>
          )}
        </div>

        <div className="navbar-user">
          {user ? (
            <div className="user-menu">
              <span className="user-name">{user.username}</span>
              <button onClick={handleLogout} className="logout-btn">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M6 14H3C2.44772 14 2 13.5523 2 13V3C2 2.44772 2.44772 2 3 2H6M10 11L14 8L10 5M14 8H6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                </svg>
                Logout
              </button>
            </div>
          ) : (
            <Link to="/login" className="navbar-link">
              Sign In
            </Link>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar

