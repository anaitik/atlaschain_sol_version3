import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import client from '../api/client'

function PipelineList() {
  const navigate = useNavigate()
  const [pipelines, setPipelines] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const token = localStorage.getItem('token')
    if (!token) {
      navigate('/login')
      return
    }

    const fetchPipelines = async () => {
      try {
        const res = await client.get('/api/pipelines')
        setPipelines(res.data.pipelines || [])
      } catch (err) {
        if (err.response?.status === 401) {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          navigate('/login')
        }
        setError('Failed to load pipelines')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchPipelines()
  }, [navigate])

  if (loading) {
    return <div className="loading">Loading pipelines...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Pipelines
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
            Manage your ESG audit pipelines
          </p>
        </div>
        <Link to="/pipelines/create" className="btn btn-primary">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M8 3V13M3 8H13" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Create New Pipeline
        </Link>
      </div>

      {error && <div className="error">{error}</div>}

      {pipelines.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            No pipelines yet. Create your first pipeline to get started.
          </p>
          <Link to="/pipelines/create" className="btn btn-primary">
            Create Pipeline
          </Link>
        </div>
      ) : (
        <div className="card" style={{ marginTop: '2rem' }}>
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Description</th>
                <th>Created</th>
                <th>Version</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {pipelines.map((pipeline) => (
                <tr key={pipeline.id}>
                  <td>
                    <strong>{pipeline.name}</strong>
                  </td>
                  <td>{pipeline.description || '-'}</td>
                  <td>{new Date(pipeline.created_at).toLocaleDateString()}</td>
                  <td>{pipeline.version}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <Link
                        to={`/pipelines/${pipeline.id}/execute`}
                        className="btn btn-success"
                        style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                      >
                        Execute
                      </Link>
                      <Link
                        to={`/executions?pipeline_id=${pipeline.id}`}
                        className="btn btn-secondary"
                        style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                      >
                        History
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default PipelineList

