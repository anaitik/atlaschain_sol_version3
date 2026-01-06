import React, { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import client from '../api/client'

function ExecutionDetails() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [execution, setExecution] = useState(null)
  const [preview, setPreview] = useState(null)
  const [report, setReport] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [execRes, previewRes] = await Promise.all([
          client.get(`/api/executions/${id}`),
          client.get(`/api/executions/${id}/preview`).catch(() => null)
        ])

        setExecution(execRes.data)
        setPreview(previewRes?.data || null)

        // Try to load report
        try {
          const reportRes = await client.get(`/api/executions/${id}/report`)
          setReport(reportRes.data.report)
        } catch (e) {
          console.log('Report not available:', e)
        }
      } catch (err) {
        setError('Failed to load execution details')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [id])

  const handleDownloadReport = async () => {
    try {
      const response = await client.get(`/api/executions/${id}/download-report`, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `esg_report_${id}.html`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
      alert('Failed to download report')
    }
  }

  const handleDownloadData = async () => {
    if (execution?.output_file_path) {
      try {
        const response = await client.get(`/api/files/${encodeURIComponent(execution.output_file_path)}`, {
          responseType: 'blob'
        })
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        const filename = execution.output_file_path.split('/').pop() || `data_${id}.csv`
        link.setAttribute('download', filename)
        document.body.appendChild(link)
        link.click()
        link.remove()
        window.URL.revokeObjectURL(url)
      } catch (error) {
        console.error('Download failed:', error)
        alert('Failed to download data')
      }
    }
  }

  if (loading) {
    return <div className="loading">Loading execution details...</div>
  }

  if (error || !execution) {
    return <div className="error">{error || 'Execution not found'}</div>
  }

  const metrics = execution.metrics_json ? JSON.parse(execution.metrics_json) : {}

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '2rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
            Execution #{execution.id}
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '1.125rem' }}>
            Pipeline: <Link to={`/pipelines/${execution.pipeline_id}/execute`} style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 500 }}>{execution.pipeline_name || 'Unknown'}</Link>
          </p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          {report && (
            <button onClick={handleDownloadReport} className="btn btn-primary">
              Download Report
            </button>
          )}
          {execution.output_file_path && (
            <button onClick={handleDownloadData} className="btn btn-secondary">
              Download Data
            </button>
          )}
          <button onClick={() => navigate('/pipelines')} className="btn btn-secondary">
            Back to Pipelines
          </button>
        </div>
      </div>

      {/* Status Badge */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <span className={`status-badge ${execution.status}`}>
          {execution.status === 'completed' && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M11.6667 3.5L5.25 9.91667L2.33334 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          )}
          {execution.status === 'running' && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="2" fill="none" strokeDasharray="37.7" strokeDashoffset="9.4">
                <animate attributeName="stroke-dashoffset" values="37.7;0" dur="1s" repeatCount="indefinite"/>
              </circle>
            </svg>
          )}
          {execution.status === 'failed' && (
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="7" cy="7" r="6" stroke="currentColor" strokeWidth="2"/>
              <path d="M4 4L10 10M10 4L4 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          )}
          {execution.status.toUpperCase()}
        </span>
        <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.95rem', flexWrap: 'wrap' }}>
          <span>
            <strong>Started:</strong> {new Date(execution.started_at).toLocaleString()}
          </span>
          {execution.completed_at && (
            <span>
              <strong>Completed:</strong> {new Date(execution.completed_at).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '2px solid #ddd', marginBottom: '1.5rem', display: 'flex', gap: '0.5rem' }}>
        <button
          onClick={() => setActiveTab('overview')}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: activeTab === 'overview' ? '2px solid #667eea' : '2px solid transparent',
            marginBottom: '-2px',
            fontWeight: activeTab === 'overview' ? '600' : '400',
            color: activeTab === 'overview' ? '#667eea' : '#666'
          }}
        >
          Overview
        </button>
        {preview && (
          <button
            onClick={() => setActiveTab('preview')}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              borderBottom: activeTab === 'preview' ? '2px solid #667eea' : '2px solid transparent',
              marginBottom: '-2px',
              fontWeight: activeTab === 'preview' ? '600' : '400'
            }}
          >
            Data Preview
          </button>
        )}
        {report && (
          <button
            onClick={() => setActiveTab('report')}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              borderBottom: activeTab === 'report' ? '2px solid #667eea' : '2px solid transparent',
              marginBottom: '-2px',
              fontWeight: activeTab === 'report' ? '600' : '400'
            }}
          >
            ESG Report
          </button>
        )}
        <Link
          to={`/executions/${id}/blockchain`}
          style={{
            padding: '0.75rem 1.5rem',
            border: 'none',
            background: 'none',
            cursor: 'pointer',
            borderBottom: '2px solid transparent',
            marginBottom: '-2px',
            fontWeight: '400',
            textDecoration: 'none',
            color: '#667eea'
          }}
        >
          Blockchain
        </Link>
        {Object.keys(metrics).length > 0 && (
          <button
            onClick={() => setActiveTab('metrics')}
            style={{
              padding: '0.75rem 1.5rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              borderBottom: activeTab === 'metrics' ? '2px solid #667eea' : '2px solid transparent',
              marginBottom: '-2px',
              fontWeight: activeTab === 'metrics' ? '600' : '400'
            }}
          >
            Metrics
          </button>
        )}
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="card">
          <h2>Execution Details</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginTop: '1rem' }}>
            <div>
              <strong>Pipeline ID:</strong> {execution.pipeline_id}
            </div>
            <div>
              <strong>Status:</strong> {execution.status}
            </div>
            <div>
              <strong>Input File:</strong> {execution.input_file_path?.split('/').pop() || 'N/A'}
            </div>
            <div>
              <strong>Output File:</strong> {execution.output_file_path?.split('/').pop() || 'N/A'}
            </div>
            {execution.anchor_tx_id && (
              <div>
                <strong>Blockchain Anchor:</strong> 
                <code style={{ marginLeft: '0.5rem', background: '#f8f9fa', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
                  {execution.anchor_tx_id}
                </code>
              </div>
            )}
            {execution.evidence_bundle_path && (
              <div>
                <strong>Evidence Bundle:</strong> {execution.evidence_bundle_path?.split('/').pop() || 'N/A'}
              </div>
            )}
          </div>
          {execution.error_message && (
            <div className="error" style={{ marginTop: '1rem' }}>
              <strong>Error:</strong> {execution.error_message}
            </div>
          )}
        </div>
      )}

      {activeTab === 'preview' && preview && (
        <div className="card">
          <h2>Transformed Data Preview</h2>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            Showing first {preview.row_count} rows of {preview.total_columns} columns
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table className="table">
              <thead>
                <tr>
                  {preview.columns.map((col) => (
                    <th key={col}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {preview.rows.map((row, idx) => (
                  <tr key={idx}>
                    {preview.columns.map((col) => (
                      <td key={col}>{row[col] ?? '-'}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'report' && report && (
        <div className="card">
          <h2>ESG Report</h2>
          <div 
            style={{ 
              marginTop: '1rem',
              border: '1px solid #ddd',
              borderRadius: '4px',
              padding: '1rem',
              background: 'white',
              maxHeight: '80vh',
              overflow: 'auto'
            }}
            dangerouslySetInnerHTML={{ __html: report }}
          />
        </div>
      )}

      {activeTab === 'metrics' && Object.keys(metrics).length > 0 && (
        <div className="card">
          <h2>ESG Metrics</h2>
          <div style={{ marginTop: '1rem' }}>
            {Object.entries(metrics).filter(([k]) => k !== 'report').map(([key, value]) => (
              <div key={key} style={{ 
                padding: '1rem', 
                marginBottom: '0.5rem', 
                background: '#f8f9fa', 
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <strong>{key}:</strong>
                <span>{typeof value === 'object' ? JSON.stringify(value) : value}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default ExecutionDetails

