import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client'

function PipelineCreate() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [pipelineName, setPipelineName] = useState('')
  const [description, setDescription] = useState('')
  const [esgStandardId, setEsgStandardId] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [esgStandards, setEsgStandards] = useState([])

  React.useEffect(() => {
    const fetchStandards = async () => {
      try {
        const res = await client.get('/api/esg-standards')
        setEsgStandards(res.data.standards || [])
      } catch (err) {
        console.error('Error fetching standards:', err)
      }
    }
    fetchStandards()
  }, [])

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Step 1: Upload file
      const formData = new FormData()
      formData.append('file', file)
      const uploadRes = await client.post('/api/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })

      // Step 2: Create pipeline
      const pipelineRes = await client.post('/api/pipelines/create-from-file', null, {
        params: {
          file_path: uploadRes.data.file_path,
          pipeline_name: pipelineName,
          description: description,
          esg_standard_id: esgStandardId || null,
        },
      })

      navigate(`/pipelines/${pipelineRes.data.pipeline_id}/execute`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create pipeline')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Create New Pipeline
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
          Upload a sample CSV to generate an AI-powered ESG audit pipeline
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="card" style={{ marginTop: '2rem' }}>
        {error && <div className="error">{error}</div>}

        <div className="form-group">
          <label>Pipeline Name *</label>
          <input
            type="text"
            value={pipelineName}
            onChange={(e) => setPipelineName(e.target.value)}
            required
            placeholder="e.g., Manufacturing Components Pipeline"
          />
        </div>

        <div className="form-group">
          <label>Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what this pipeline does..."
          />
        </div>

        <div className="form-group">
          <label>ESG Standard</label>
          <select
            value={esgStandardId}
            onChange={(e) => setEsgStandardId(e.target.value)}
          >
            <option value="">None (Use Default)</option>
            {esgStandards.map((std) => (
              <option key={std.id} value={std.id}>
                {std.name} ({std.region})
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Sample CSV File *</label>
          <input
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            required
          />
          {file && (
            <p style={{ marginTop: '0.5rem', color: '#666' }}>
              Selected: {file.name}
            </p>
          )}
        </div>

        <div style={{ display: 'flex', gap: '1rem' }}>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Pipeline'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate('/pipelines')}
          >
            Cancel
          </button>
        </div>
      </form>

      <div className="card" style={{ marginTop: '2rem' }}>
        <h3>How it works</h3>
        <ol style={{ paddingLeft: '1.5rem', lineHeight: '1.8' }}>
          <li>Upload a sample CSV file with your ESG data</li>
          <li>Our AI agents will analyze the schema and propose metrics</li>
          <li>Review and customize the generated pipeline</li>
          <li>Save the pipeline for future use on batches of data</li>
        </ol>
      </div>
    </div>
  )
}

export default PipelineCreate

