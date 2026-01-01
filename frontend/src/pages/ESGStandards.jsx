import React, { useEffect, useState } from 'react'
import client from '../api/client'

function ESGStandards() {
  const [standards, setStandards] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showCreate, setShowCreate] = useState(false)
  const [newStandard, setNewStandard] = useState({
    name: '',
    region: '',
    framework: '',
    description: '',
    config: '{}',
  })

  useEffect(() => {
    fetchStandards()
  }, [])

  const fetchStandards = async () => {
    try {
      const res = await client.get('/api/esg-standards')
      setStandards(res.data.standards || [])
    } catch (err) {
      setError('Failed to load ESG standards')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    try {
      const config = JSON.parse(newStandard.config)
      await client.post('/api/esg-standards', {
        name: newStandard.name,
        region: newStandard.region,
        framework: newStandard.framework,
        description: newStandard.description,
        config: config,
      })
      setShowCreate(false)
      setNewStandard({ name: '', region: '', framework: '', description: '', config: '{}' })
      fetchStandards()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create standard')
    }
  }

  if (loading) {
    return <div className="loading">Loading ESG standards...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            ESG Standards Configuration
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
            Configure ESG standards for different regions and frameworks
          </p>
        </div>
        <button
          className="btn btn-primary"
          onClick={() => setShowCreate(!showCreate)}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {showCreate ? 'Cancel' : 'Create New Standard'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {showCreate && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <h2>Create New ESG Standard</h2>
          <form onSubmit={handleCreate}>
            <div className="form-group">
              <label>Name *</label>
              <input
                type="text"
                value={newStandard.name}
                onChange={(e) => setNewStandard({ ...newStandard, name: e.target.value })}
                required
                placeholder="e.g., GRI Standards"
              />
            </div>
            <div className="form-group">
              <label>Region</label>
              <input
                type="text"
                value={newStandard.region}
                onChange={(e) => setNewStandard({ ...newStandard, region: e.target.value })}
                placeholder="e.g., Global, Europe, United States"
              />
            </div>
            <div className="form-group">
              <label>Framework</label>
              <input
                type="text"
                value={newStandard.framework}
                onChange={(e) => setNewStandard({ ...newStandard, framework: e.target.value })}
                placeholder="e.g., GRI, CSRD, SEC"
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={newStandard.description}
                onChange={(e) => setNewStandard({ ...newStandard, description: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Configuration (JSON) *</label>
              <textarea
                value={newStandard.config}
                onChange={(e) => setNewStandard({ ...newStandard, config: e.target.value })}
                required
                style={{ fontFamily: 'monospace', minHeight: '200px' }}
                placeholder='{"environmental": {...}, "social": {...}, "governance": {...}}'
              />
            </div>
            <button type="submit" className="btn btn-primary">
              Create Standard
            </button>
          </form>
        </div>
      )}

      <div className="card" style={{ marginTop: '2rem' }}>
        <h2>Available Standards</h2>
        {standards.length === 0 ? (
          <p>No ESG standards configured. Create one to get started.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Region</th>
                <th>Framework</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {standards.map((std) => (
                <tr key={std.id}>
                  <td><strong>{std.name}</strong></td>
                  <td>{std.region || '-'}</td>
                  <td>{std.framework || '-'}</td>
                  <td>{std.description || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default ESGStandards

