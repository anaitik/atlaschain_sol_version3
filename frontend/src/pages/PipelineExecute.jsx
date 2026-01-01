import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

function PipelineExecute() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [pipeline, setPipeline] = useState(null)
  const [file, setFile] = useState(null)
  const [executing, setExecuting] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPipeline = async () => {
      try {
        const res = await client.get(`/api/pipelines/${id}`)
        setPipeline(res.data)
      } catch (err) {
        setError('Failed to load pipeline')
      } finally {
        setLoading(false)
      }
    }
    fetchPipeline()
  }, [id])

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleExecute = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    setError('')
    setExecuting(true)

    try {
      // Upload file
      const formData = new FormData()
      formData.append('file', file)
      const uploadRes = await client.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      // Execute pipeline
      const executeRes = await client.post('/api/pipelines/execute', {
        pipeline_id: parseInt(id),
        input_file_path: uploadRes.data.file_path,
        anchor_to_blockchain: true,
      })

      setResult(executeRes.data)
      // Auto-redirect to execution details after 2 seconds
      setTimeout(() => {
        if (executeRes.data.execution_id) {
          navigate(`/executions/${executeRes.data.execution_id}`)
        }
      }, 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Execution failed')
    } finally {
      setExecuting(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading pipeline...</div>
  }

  if (!pipeline) {
    return <div className="error">Pipeline not found</div>
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Execute Pipeline
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
          {pipeline.name}
        </p>
      </div>

      {error && (
        <div className="error">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2"/>
            <path d="M10 6V10M10 14H10.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          {error}
        </div>
      )}
      
      {result && (
        <div className="success-message" style={{ marginBottom: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'start', gap: '1rem' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: '2px' }}>
              <circle cx="12" cy="12" r="10" fill="var(--success)" opacity="0.2"/>
              <path d="M9 12L11 14L15 10" stroke="var(--success-dark)" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <div style={{ flex: 1 }}>
              <h3 style={{ marginBottom: '0.75rem' }}>Execution Completed Successfully!</h3>
              <p style={{ marginBottom: '0.5rem' }}>Output saved to: <code>{result.output_path?.split('/').pop()}</code></p>
              {result.anchor_tx_id && (
                <p style={{ marginBottom: '1rem' }}>
                  <strong>Blockchain Anchor:</strong> <code>{result.anchor_tx_id.substring(0, 20)}...</code>
                </p>
              )}
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginTop: '1rem' }}>
                <Link 
                  to={`/executions/${result.execution_id}`}
                  className="btn btn-primary"
                >
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2V8M8 8L12 4M8 8L4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  View Full Details
                </Link>
                {result.execution_id && (
                  <Link 
                    to={`/executions/${result.execution_id}/blockchain`}
                    className="btn btn-secondary"
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path d="M8 2L2 6L8 10L14 6L8 2Z" stroke="currentColor" strokeWidth="1.5"/>
                    </svg>
                    View Blockchain
                  </Link>
                )}
              </div>
              {result.metrics && Object.keys(result.metrics).filter(k => k !== 'report').length > 0 && (
                <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid rgba(16, 185, 129, 0.2)' }}>
                  <h4 style={{ marginBottom: '0.75rem', fontSize: '1rem', fontWeight: 600 }}>Quick Metrics:</h4>
                  <div style={{ background: 'rgba(255, 255, 255, 0.5)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', overflowX: 'auto' }}>
                    <pre style={{ margin: 0, fontFamily: 'inherit', whiteSpace: 'pre-wrap' }}>
                      {JSON.stringify(Object.fromEntries(Object.entries(result.metrics).filter(([k]) => k !== 'report')), null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!result && (
        <>
          <div className="card">
            <h2>Pipeline Details</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Description</p>
                <p style={{ fontWeight: 500 }}>{pipeline.description || 'No description'}</p>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Version</p>
                <p style={{ fontWeight: 500 }}>{pipeline.version}</p>
              </div>
              <div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: '0.25rem' }}>Created</p>
                <p style={{ fontWeight: 500 }}>{new Date(pipeline.created_at).toLocaleDateString()}</p>
              </div>
            </div>
          </div>

          <div className="card">
            <h2>Execute on New Data</h2>
            <div className="form-group">
              <label>Input CSV File *</label>
              <div style={{ 
                border: '2px dashed var(--border-medium)', 
                borderRadius: 'var(--radius-lg)', 
                padding: '2rem', 
                textAlign: 'center',
                background: 'var(--bg-secondary)',
                transition: 'all var(--transition-base)',
                cursor: 'pointer'
              }}>
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  disabled={executing}
                  style={{ 
                    display: 'none' 
                  }}
                  id="file-input"
                />
                <label 
                  htmlFor="file-input" 
                  style={{ 
                    cursor: 'pointer',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.75rem'
                  }}
                >
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="none" style={{ color: 'var(--primary)' }}>
                    <path d="M14 2H6C5.46957 2 4.96086 2.21071 4.58579 2.58579C4.21071 2.96086 4 3.46957 4 4V20C4 20.5304 4.21071 21.0391 4.58579 21.4142C4.96086 21.7893 5.46957 22 6 22H18C18.5304 22 19.0391 21.7893 19.4142 21.4142C19.7893 21.0391 20 20.5304 20 20V8L14 2Z" stroke="currentColor" strokeWidth="2"/>
                    <path d="M14 2V8H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                    <path d="M12 18V12M9 15H15" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                    {file ? file.name : 'Click to select CSV file'}
                  </span>
                  <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    {file ? 'Click to change file' : 'or drag and drop'}
                  </span>
                </label>
              </div>
            </div>

            <button
              onClick={handleExecute}
              className="btn btn-primary"
              disabled={executing || !file}
              style={{ width: '100%', marginTop: '1rem' }}
            >
              {executing ? (
                <>
                  <svg className="spinner" width="16" height="16" viewBox="0 0 16 16">
                    <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="2" fill="none" strokeDasharray="43.98" strokeDashoffset="10.99">
                      <animate attributeName="stroke-dashoffset" values="43.98;0" dur="1s" repeatCount="indefinite"/>
                    </circle>
                  </svg>
                  Executing Pipeline...
                </>
              ) : (
                <>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 2V8M8 8L12 4M8 8L4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  Execute Pipeline
                </>
              )}
            </button>
          </div>
        </>
      )}

      {pipeline.schema_json && (
        <div className="card" style={{ marginTop: '2rem' }}>
          <h3>Schema</h3>
          <pre style={{ background: '#f8f9fa', padding: '1rem', borderRadius: '4px', overflow: 'auto' }}>
            {JSON.stringify(pipeline.schema_json, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}

export default PipelineExecute

