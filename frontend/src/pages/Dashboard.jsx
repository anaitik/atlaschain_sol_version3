import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'

function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    pipelines: 0,
    executions: 0,
    completed: 0,
    failed: 0,
    running: 0,
    recent_executions: []
  })
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }

    const fetchStats = async () => {
      try {
        const res = await client.get('/api/dashboard/stats')
        setStats(res.data)
      } catch (error) {
        if (error.response?.status === 401) {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          navigate('/login')
        }
        console.error('Error fetching stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [navigate])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Dashboard
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
          Overview of your ESG audit pipelines and executions
        </p>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginTop: '2rem' }}>
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Pipelines</h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--primary)' }}>
              <path d="M3 5H21M3 10H21M3 15H21" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--primary)', marginBottom: '0.5rem' }}>
            {stats.pipelines}
          </p>
          <Link to="/pipelines" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 500, fontSize: '0.95rem' }}>
            View all →
          </Link>
        </div>
        
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Total Executions</h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--success)' }}>
              <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--success)', marginBottom: '0.5rem' }}>
            {stats.executions}
          </p>
          <div style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.5rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <span style={{ color: 'var(--success-dark)', fontWeight: 600 }}>✓ {stats.completed}</span>
            <span style={{ color: 'var(--error-dark)', fontWeight: 600 }}>✗ {stats.failed}</span>
            <span style={{ color: 'var(--warning-dark)', fontWeight: 600 }}>⏳ {stats.running}</span>
          </div>
        </div>
        
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%)', border: '1px solid rgba(16, 185, 129, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Completed</h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--success)' }}>
              <path d="M9 12L11 14L15 10M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--success)', marginBottom: '0.5rem' }}>
            {stats.completed}
          </p>
          <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', fontWeight: 500 }}>
            {stats.executions > 0 ? Math.round((stats.completed / stats.executions) * 100) : 0}% success rate
          </span>
        </div>
        
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%)', border: '1px solid rgba(124, 58, 237, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>ESG Standards</h3>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--primary-gradient-end)' }}>
              <path d="M12 2L3 7V17L12 22L21 17V7L12 2Z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <p style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--primary-gradient-end)', marginBottom: '0.5rem' }}>
            {stats.standards || 0}
          </p>
          <Link to="/esg-standards" style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 500, fontSize: '0.95rem' }}>
            Manage →
          </Link>
        </div>
      </div>

      {/* Recent Executions */}
      {stats.recent_executions && stats.recent_executions.length > 0 && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <h2>Recent Executions</h2>
          <table className="table" style={{ marginTop: '1rem' }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Pipeline</th>
                <th>Status</th>
                <th>Started</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {stats.recent_executions.map((exec) => (
                <tr key={exec.id}>
                  <td>#{exec.id}</td>
                  <td>{exec.pipeline_name || 'Unknown'}</td>
                  <td>
                    <span className={`status-badge ${exec.status}`}>
                      {exec.status}
                    </span>
                  </td>
                  <td>{new Date(exec.started_at).toLocaleString()}</td>
                  <td>
                    <Link 
                      to={`/executions/${exec.id}`} 
                      className="btn btn-primary"
                      style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                    >
                      View Details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="card" style={{ marginTop: '2rem' }}>
        <h2>Quick Actions</h2>
        <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
          <Link to="/pipelines/create" className="btn btn-primary">
            Create New Pipeline
          </Link>
          <Link to="/pipelines" className="btn btn-secondary">
            View All Pipelines
          </Link>
          <Link to="/esg-standards" className="btn btn-secondary">
            Configure ESG Standards
          </Link>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

