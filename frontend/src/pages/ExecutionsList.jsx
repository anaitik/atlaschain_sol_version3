import React, { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import client from '../api/client'

function ExecutionsList() {
  const [searchParams] = useSearchParams()
  const pipelineId = searchParams.get('pipeline_id')
  const [executions, setExecutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchExecutions = async () => {
      try {
        const url = pipelineId 
          ? `/api/executions?pipeline_id=${pipelineId}`
          : '/api/executions'
        const res = await client.get(url)
        setExecutions(res.data.executions || [])
      } catch (err) {
        setError('Failed to load executions')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchExecutions()
  }, [pipelineId])

  if (loading) {
    return <div className="loading">Loading executions...</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            {pipelineId ? 'Pipeline Executions' : 'All Executions'}
          </h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
            View and manage pipeline execution history
          </p>
        </div>
        <Link to="/pipelines" className="btn btn-secondary">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          Back to Pipelines
        </Link>
      </div>

      {error && <div className="error">{error}</div>}

      {executions.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ marginBottom: '1rem', color: '#666' }}>
            No executions found.
          </p>
        </div>
      ) : (
        <div className="card" style={{ marginTop: '2rem' }}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Pipeline</th>
                <th>Status</th>
                <th>Started</th>
                <th>Completed</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {executions.map((exec) => (
                <tr key={exec.id}>
                  <td>#{exec.id}</td>
                  <td>
                    <Link to={`/pipelines/${exec.pipeline_id}/execute`}>
                      {exec.pipeline_name || 'Unknown'}
                    </Link>
                  </td>
                  <td>
                    <span className={`status-badge ${exec.status}`}>
                      {exec.status}
                    </span>
                  </td>
                  <td>{new Date(exec.started_at).toLocaleString()}</td>
                  <td>
                    {exec.completed_at 
                      ? new Date(exec.completed_at).toLocaleString()
                      : '-'
                    }
                  </td>
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
    </div>
  )
}

export default ExecutionsList

