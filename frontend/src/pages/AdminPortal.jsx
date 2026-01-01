import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'
import './AdminPortal.css'

function AdminPortal() {
  const navigate = useNavigate()
  const [registrations, setRegistrations] = useState([])
  const [users, setUsers] = useState([])
  const [activeTab, setActiveTab] = useState('registrations')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    checkAuth()
    fetchData()
  }, [])

  const checkAuth = () => {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.role !== 'admin') {
      navigate('/')
    }
  }

  const fetchData = async () => {
    try {
      const [regRes, usersRes] = await Promise.all([
        client.get('/api/admin/registrations'),
        client.get('/api/admin/users')
      ])
      setRegistrations(regRes.data.registrations || [])
      setUsers(usersRes.data.users || [])
    } catch (err) {
      setError('Failed to load data')
      if (err.response?.status === 401 || err.response?.status === 403) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        navigate('/login')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleApprove = async (registrationId) => {
    try {
      await client.post(`/api/admin/registrations/${registrationId}/approve`)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to approve registration')
    }
  }

  const handleReject = async (registrationId) => {
    if (!window.confirm('Are you sure you want to reject this registration?')) {
      return
    }
    try {
      await client.post(`/api/admin/registrations/${registrationId}/reject`)
      fetchData()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reject registration')
    }
  }

  if (loading) {
    return <div className="loading">Loading admin portal...</div>
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Admin Portal
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
          Manage user registrations and accounts
        </p>
      </div>

      {error && <div className="error">{error}</div>}

      {/* Tabs */}
      <div style={{ borderBottom: '2px solid var(--border-light)', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('registrations')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: activeTab === 'registrations' ? '2px solid var(--primary)' : '2px solid transparent',
            marginBottom: '-2px',
            fontWeight: activeTab === 'registrations' ? '600' : '400',
            color: activeTab === 'registrations' ? 'var(--primary)' : 'var(--text-secondary)'
          }}
        >
          Pending Registrations ({registrations.length})
        </button>
        <button
          onClick={() => setActiveTab('users')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: activeTab === 'users' ? '2px solid var(--primary)' : '2px solid transparent',
            marginBottom: '-2px',
            fontWeight: activeTab === 'users' ? '600' : '400',
            color: activeTab === 'users' ? 'var(--primary)' : 'var(--text-secondary)'
          }}
        >
          All Users ({users.length})
        </button>
      </div>

      {activeTab === 'registrations' && (
        <div className="card">
          <h2>Pending User Registrations</h2>
          {registrations.length === 0 ? (
            <p style={{ color: 'var(--text-secondary)', textAlign: 'center', padding: '2rem' }}>
              No pending registrations
            </p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Full Name</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {registrations.map((reg) => (
                  <tr key={reg.id}>
                    <td><strong>{reg.username}</strong></td>
                    <td>{reg.email}</td>
                    <td>{reg.full_name || '-'}</td>
                    <td>{new Date(reg.created_at).toLocaleString()}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                          onClick={() => handleApprove(reg.id)}
                          className="btn btn-success"
                          style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleReject(reg.id)}
                          className="btn btn-secondary"
                          style={{ padding: '0.5rem 1rem', fontSize: '0.875rem', background: 'var(--error)' }}
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {activeTab === 'users' && (
        <div className="card">
          <h2>All Users</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Email</th>
                <th>Full Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td><strong>{user.username}</strong></td>
                  <td>{user.email}</td>
                  <td>{user.full_name || '-'}</td>
                  <td>
                    <span className={`status-badge ${user.role === 'admin' ? 'success' : ''}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${user.is_approved && user.is_active ? 'success' : 'failed'}`}>
                      {user.is_approved && user.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>{new Date(user.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default AdminPortal
