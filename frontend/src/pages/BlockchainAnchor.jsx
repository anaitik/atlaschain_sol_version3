import React, { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import client from '../api/client'
import './BlockchainAnchor.css'

function BlockchainAnchor() {
  const { id } = useParams()
  const [execution, setExecution] = useState(null)
  const [anchorStatus, setAnchorStatus] = useState(null)
  const [verification, setVerification] = useState(null)
  const [loading, setLoading] = useState(true)
  const [anchoring, setAnchoring] = useState(false)
  const [verifying, setVerifying] = useState(false)
  const [error, setError] = useState('')
  const [merkleInfo, setMerkleInfo] = useState(null)

  useEffect(() => {
    fetchExecution()
  }, [id])

  const fetchExecution = async () => {
    try {
      const res = await client.get(`/api/executions/${id}`)
      setExecution(res.data)
      
      if (res.data.anchor_tx_id) {
        await fetchAnchorStatus(res.data.anchor_tx_id)
      }
    } catch (err) {
      setError('Failed to load execution')
    } finally {
      setLoading(false)
    }
  }

  const fetchAnchorStatus = async (txId) => {
    try {
      const res = await client.get(`/api/blockchain/verify/${txId}`)
      setAnchorStatus(res.data)
      
      // Extract Merkle info from note
      if (res.data.note) {
        const parts = res.data.note.split('|')
        const merkleData = {}
        parts.forEach(part => {
          if (part.startsWith('BATCH:')) {
            merkleData.batchId = part.split(':')[1]
          } else if (part.startsWith('ROOT:')) {
            merkleData.rootHash = part.split(':')[1]
          } else if (part.startsWith('COUNT:')) {
            merkleData.recordCount = parseInt(part.split(':')[1])
          }
        })
        setMerkleInfo(merkleData)
      }
    } catch (err) {
      console.error('Error fetching anchor status:', err)
    }
  }

  const handleAnchor = async () => {
    setAnchoring(true)
    setError('')
    try {
      const res = await client.post(`/api/blockchain/anchor/${id}`)
      setExecution(prev => ({ ...prev, anchor_tx_id: res.data.tx_id }))
      await fetchAnchorStatus(res.data.tx_id)
      
      // Set Merkle info from response
      if (res.data.root_hash) {
        setMerkleInfo({
          batchId: res.data.batch_id,
          rootHash: res.data.root_hash,
          recordCount: res.data.record_count
        })
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to anchor to blockchain')
    } finally {
      setAnchoring(false)
    }
  }

  const handleVerify = async () => {
    if (!execution?.anchor_tx_id) return
    
    setVerifying(true)
    setError('')
    try {
      const res = await client.get(`/api/blockchain/verify/${execution.anchor_tx_id}`)
      setVerification(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to verify anchor')
    } finally {
      setVerifying(false)
    }
  }

  if (loading) {
    return <div className="loading">Loading blockchain anchor information...</div>
  }

  return (
    <div>
      <div style={{ marginBottom: '2rem' }}>
        <Link to={`/executions/${id}`} className="btn btn-secondary" style={{ marginBottom: '1rem' }}>
          ← Back to Execution
        </Link>
        <h1 style={{ fontSize: '2.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
          Blockchain Anchor
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '1.125rem' }}>
          Merkle root anchoring and verification
        </p>
      </div>

      {error && <div className="error">{error}</div>}

      {execution && (
        <div className="card" style={{ marginBottom: '2rem' }}>
          <h2>Execution Information</h2>
          <div className="info-grid">
            <div>
              <label>Execution ID</label>
              <div>#{execution.id}</div>
            </div>
            <div>
              <label>Pipeline</label>
              <div>{execution.pipeline_name || 'N/A'}</div>
            </div>
            <div>
              <label>Status</label>
              <div>
                <span className={`status-badge ${execution.status === 'completed' ? 'success' : ''}`}>
                  {execution.status?.toUpperCase()}
                </span>
              </div>
            </div>
            <div>
              <label>Executed By</label>
              <div>{execution.executed_by}</div>
            </div>
          </div>
        </div>
      )}

      {!execution?.anchor_tx_id ? (
        <div className="card">
          <h2>Anchor to Blockchain</h2>
          <p style={{ marginBottom: '1.5rem', color: 'var(--text-secondary)' }}>
            Anchor the Merkle root of this execution's data to Algorand blockchain.
            Only the Merkle root is stored on-chain, not the actual data.
          </p>
          <button
            onClick={handleAnchor}
            disabled={anchoring || execution?.status !== 'completed'}
            className="btn btn-primary"
          >
            {anchoring ? 'Anchoring...' : 'Anchor to Blockchain'}
          </button>
          {execution?.status !== 'completed' && (
            <p style={{ marginTop: '1rem', color: 'var(--text-tertiary)', fontSize: '0.875rem' }}>
              Execution must be completed before anchoring
            </p>
          )}
        </div>
      ) : (
        <>
          <div className="card" style={{ marginBottom: '2rem' }}>
            <h2>Anchored Information</h2>
            
            {merkleInfo && (
              <div style={{ marginBottom: '1.5rem', padding: '1rem', background: 'var(--gray-50)', borderRadius: 'var(--radius-md)' }}>
                <h3 style={{ fontSize: '1.125rem', marginBottom: '0.75rem', color: 'var(--text-primary)' }}>
                  Merkle Tree Information
                </h3>
                <div className="info-grid">
                  <div>
                    <label>Batch ID</label>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>{merkleInfo.batchId}</div>
                  </div>
                  <div>
                    <label>Merkle Root Hash</label>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all' }}>
                      {merkleInfo.rootHash}
                    </div>
                  </div>
                  <div>
                    <label>Record Count</label>
                    <div>{merkleInfo.recordCount} records</div>
                  </div>
                </div>
                <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                  <strong>Note:</strong> Only the Merkle root is stored on blockchain. Individual records remain private.
                  Use the proof API to generate verification proofs for auditors.
                </p>
              </div>
            )}

            <div className="info-grid">
              <div>
                <label>Transaction ID</label>
                <div style={{ fontFamily: 'monospace', fontSize: '0.875rem', wordBreak: 'break-all' }}>
                  {execution.anchor_tx_id}
                </div>
              </div>
              {anchorStatus && (
                <>
                  {anchorStatus.block && (
                    <div>
                      <label>Block Number</label>
                      <div>{anchorStatus.block}</div>
                    </div>
                  )}
                  {anchorStatus.timestamp && (
                    <div>
                      <label>Timestamp</label>
                      <div>{new Date(anchorStatus.timestamp * 1000).toLocaleString()}</div>
                    </div>
                  )}
                </>
              )}
            </div>

            <div style={{ marginTop: '1.5rem' }}>
              <button
                onClick={handleVerify}
                disabled={verifying}
                className="btn btn-primary"
              >
                {verifying ? 'Verifying...' : 'Verify on Blockchain'}
              </button>
            </div>
          </div>

          {verification && (
            <div className="card">
              <h2>Verification Result</h2>
              {verification.confirmed ? (
                <div style={{ padding: '1rem', background: 'var(--success-light)', borderRadius: 'var(--radius-md)', color: 'var(--success-dark)' }}>
                  <strong>✓ Verified</strong>
                  <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                    This anchor is confirmed on the Algorand blockchain.
                  </p>
                  {verification.block && (
                    <p style={{ marginTop: '0.5rem', marginBottom: 0, fontSize: '0.875rem' }}>
                      Block: {verification.block}
                    </p>
                  )}
                </div>
              ) : (
                <div style={{ padding: '1rem', background: 'var(--error-light)', borderRadius: 'var(--radius-md)', color: 'var(--error-dark)' }}>
                  <strong>✗ Verification Failed</strong>
                  <p style={{ marginTop: '0.5rem', marginBottom: 0 }}>
                    {verification.error || 'Could not verify anchor'}
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="card">
            <h2>Auditor Verification</h2>
            <p style={{ marginBottom: '1rem', color: 'var(--text-secondary)' }}>
              Auditors can verify individual records using Merkle proofs without accessing other records.
            </p>
            <div style={{ padding: '1rem', background: 'var(--gray-50)', borderRadius: 'var(--radius-md)' }}>
              <p style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}>
                <strong>API Endpoint:</strong>
              </p>
              <code style={{ fontSize: '0.875rem', wordBreak: 'break-all' }}>
                GET /api/proof/batch/{merkleInfo?.batchId || '{batch_id}'}/record/{'{record_index}'}
              </code>
              <p style={{ marginTop: '1rem', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                This returns the canonical record, its hash, Merkle proof path, and root hash for independent verification.
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

export default BlockchainAnchor
