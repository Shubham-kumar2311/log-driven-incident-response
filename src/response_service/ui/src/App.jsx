import { useState, useEffect, useCallback } from 'react'

// API base URL - uses proxy in dev, direct in production
const API_BASE = '/api'

// Available actions for dropdown
const AVAILABLE_ACTIONS = [
  { name: 'restart_database', description: 'Restart database service' },
  { name: 'restart_api', description: 'Restart API servers' },
  { name: 'lock_accounts', description: 'Lock suspicious accounts' },
  { name: 'rollback_deployment', description: 'Rollback deployment' },
  { name: 'scale_service', description: 'Scale service instances' },
  { name: 'restart_cache', description: 'Restart cache service' },
  { name: 'notify_oncall', description: 'Notify on-call engineer' }
]

// Signal types for dropdown
const SIGNAL_TYPES = [
  'DB_SLOW_QUERY',
  'HTTP_ERROR_SPIKE',
  'AUTH_FAILURE_SPIKE',
  'DEPLOYMENT_FAILURE',
  'HIGH_LATENCY',
  'CACHE_ERROR',
  'MEMORY_PRESSURE',
  'CPU_SPIKE',
  'DISK_FULL'
]

function App() {
  const [playbooks, setPlaybooks] = useState([])
  const [health, setHealth] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  // Modal state
  const [showModal, setShowModal] = useState(false)
  const [editingPlaybook, setEditingPlaybook] = useState(null)

  // Test panel state
  const [testSignal, setTestSignal] = useState('')
  const [testResult, setTestResult] = useState(null)
  const [testing, setTesting] = useState(false)

  // Fetch playbooks
  const fetchPlaybooks = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/playbooks`)
      if (!res.ok) throw new Error('Failed to fetch playbooks')
      const data = await res.json()
      setPlaybooks(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [])

  // Fetch health status
  const fetchHealth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/health`)
      if (!res.ok) throw new Error('Failed to fetch health')
      const data = await res.json()
      setHealth(data)
    } catch (err) {
      setHealth({ status: 'error' })
    }
  }, [])

  // Initial load and auto-refresh
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      await Promise.all([fetchPlaybooks(), fetchHealth()])
      setLoading(false)
    }
    load()

    // Auto-refresh every 10 seconds
    const interval = setInterval(() => {
      fetchPlaybooks()
      fetchHealth()
    }, 10000)

    return () => clearInterval(interval)
  }, [fetchPlaybooks, fetchHealth])

  // Clear messages after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000)
      return () => clearTimeout(timer)
    }
  }, [success])

  // Toggle playbook enabled/disabled
  const togglePlaybook = async (id, currentEnabled) => {
    try {
      const res = await fetch(`${API_BASE}/playbooks/${id}/toggle`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: !currentEnabled })
      })
      if (!res.ok) throw new Error('Failed to toggle playbook')
      setSuccess(`Playbook ${!currentEnabled ? 'enabled' : 'disabled'}`)
      fetchPlaybooks()
    } catch (err) {
      setError(err.message)
    }
  }

  // Delete playbook
  const deletePlaybook = async (id) => {
    if (!confirm('Are you sure you want to delete this playbook?')) return
    try {
      const res = await fetch(`${API_BASE}/playbooks/${id}`, { method: 'DELETE' })
      if (!res.ok) throw new Error('Failed to delete playbook')
      setSuccess('Playbook deleted')
      fetchPlaybooks()
    } catch (err) {
      setError(err.message)
    }
  }

  // Save playbook (create or update)
  const savePlaybook = async (data) => {
    try {
      const isEdit = !!editingPlaybook
      const url = isEdit
        ? `${API_BASE}/playbooks/${editingPlaybook.id}`
        : `${API_BASE}/playbooks`

      const res = await fetch(url, {
        method: isEdit ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      })

      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.detail || 'Failed to save playbook')
      }

      setSuccess(isEdit ? 'Playbook updated' : 'Playbook created')
      setShowModal(false)
      setEditingPlaybook(null)
      fetchPlaybooks()
    } catch (err) {
      setError(err.message)
    }
  }

  // Test playbook
  const testPlaybook = async () => {
    if (!testSignal) return
    setTesting(true)
    setTestResult(null)

    try {
      const res = await fetch(`${API_BASE}/simulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signal_type: testSignal })
      })
      const data = await res.json()
      setTestResult({ success: res.ok, data })
    } catch (err) {
      setTestResult({ success: false, data: { error: err.message } })
    } finally {
      setTesting(false)
    }
  }

  // Open edit modal
  const openEdit = (playbook) => {
    setEditingPlaybook(playbook)
    setShowModal(true)
  }

  // Open create modal
  const openCreate = () => {
    setEditingPlaybook(null)
    setShowModal(true)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <>
      <header>
        <h1>Playbook Manager</h1>
        <div className="status">
          Response Service
          <span className={`status-badge ${health?.status === 'healthy' ? 'healthy' : 'error'}`}>
            {health?.status || 'unknown'}
          </span>
          {health?.mongodb_connected && (
            <span className="status-badge healthy">MongoDB</span>
          )}
          {health?.redis_enabled && (
            <span className="status-badge healthy">Redis</span>
          )}
        </div>
      </header>

      <div className="container">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="grid-2">
          <div>
            {/* Playbooks Table */}
            <div className="card">
              <h2>
                Playbooks ({playbooks.length})
                <button
                  className="action-btn primary"
                  style={{ float: 'right' }}
                  onClick={openCreate}
                >
                  + New Playbook
                </button>
              </h2>

              <table>
                <thead>
                  <tr>
                    <th>Signal Type</th>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {playbooks.map(pb => (
                    <tr key={pb.id}>
                      <td>
                        <strong>{pb.signal_type}</strong>
                        {pb.description && (
                          <div style={{ fontSize: '0.8rem', color: '#666' }}>
                            {pb.description}
                          </div>
                        )}
                      </td>
                      <td><code>{pb.action}</code></td>
                      <td>
                        <button
                          className={`toggle-btn ${pb.enabled ? 'enabled' : 'disabled'}`}
                          onClick={() => togglePlaybook(pb.id, pb.enabled)}
                        >
                          {pb.enabled ? 'Enabled' : 'Disabled'}
                        </button>
                      </td>
                      <td>
                        <button
                          className="action-btn secondary"
                          onClick={() => openEdit(pb)}
                        >
                          Edit
                        </button>
                        <button
                          className="action-btn danger"
                          onClick={() => deletePlaybook(pb.id)}
                        >
                          Delete
                        </button>
                      </td>
                    </tr>
                  ))}
                  {playbooks.length === 0 && (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', color: '#666' }}>
                        No playbooks found. Create one to get started.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            {/* Test Panel */}
            <div className="card">
              <h2>Test Playbook</h2>

              <div className="form-group">
                <label>Signal Type</label>
                <select
                  value={testSignal}
                  onChange={(e) => setTestSignal(e.target.value)}
                >
                  <option value="">Select signal type...</option>
                  {SIGNAL_TYPES.map(sig => (
                    <option key={sig} value={sig}>{sig}</option>
                  ))}
                </select>
              </div>

              <button
                className="action-btn primary"
                onClick={testPlaybook}
                disabled={!testSignal || testing}
              >
                {testing ? 'Testing...' : 'Run Test'}
              </button>

              {testResult && (
                <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
                  {JSON.stringify(testResult.data, null, 2)}
                </div>
              )}
            </div>

            {/* Quick Stats */}
            <div className="card">
              <h2>Quick Stats</h2>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '15px' }}>
                <div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3b82f6' }}>
                    {playbooks.length}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>Total Playbooks</div>
                </div>
                <div>
                  <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#22c55e' }}>
                    {playbooks.filter(p => p.enabled).length}
                  </div>
                  <div style={{ fontSize: '0.85rem', color: '#666' }}>Enabled</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showModal && (
        <PlaybookModal
          playbook={editingPlaybook}
          onSave={savePlaybook}
          onClose={() => {
            setShowModal(false)
            setEditingPlaybook(null)
          }}
        />
      )}
    </>
  )
}

// Modal Component
function PlaybookModal({ playbook, onSave, onClose }) {
  const [formData, setFormData] = useState({
    signal_type: playbook?.signal_type || '',
    action: playbook?.action || '',
    description: playbook?.description || '',
    enabled: playbook?.enabled ?? true,
    priority: playbook?.priority || 1,
    parameters: JSON.stringify(playbook?.parameters || {}, null, 2)
  })

  const handleSubmit = (e) => {
    e.preventDefault()
    let params = {}
    try {
      params = JSON.parse(formData.parameters || '{}')
    } catch (err) {
      alert('Invalid JSON in parameters')
      return
    }

    onSave({
      ...formData,
      parameters: params
    })
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <h3>{playbook ? 'Edit Playbook' : 'Create Playbook'}</h3>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Signal Type *</label>
            <select
              value={formData.signal_type}
              onChange={(e) => handleChange('signal_type', e.target.value)}
              required
              disabled={!!playbook}
            >
              <option value="">Select signal type...</option>
              {SIGNAL_TYPES.map(sig => (
                <option key={sig} value={sig}>{sig}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Action *</label>
            <select
              value={formData.action}
              onChange={(e) => handleChange('action', e.target.value)}
              required
            >
              <option value="">Select action...</option>
              {AVAILABLE_ACTIONS.map(action => (
                <option key={action.name} value={action.name}>
                  {action.name} - {action.description}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              placeholder="Describe what this playbook does..."
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Priority</label>
              <input
                type="number"
                min="1"
                max="10"
                value={formData.priority}
                onChange={(e) => handleChange('priority', parseInt(e.target.value) || 1)}
              />
            </div>

            <div className="form-group">
              <label>Status</label>
              <select
                value={formData.enabled.toString()}
                onChange={(e) => handleChange('enabled', e.target.value === 'true')}
              >
                <option value="true">Enabled</option>
                <option value="false">Disabled</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label>Parameters (JSON)</label>
            <textarea
              value={formData.parameters}
              onChange={(e) => handleChange('parameters', e.target.value)}
              placeholder='{"key": "value"}'
              style={{ fontFamily: 'monospace' }}
            />
          </div>

          <div className="modal-actions">
            <button type="button" className="action-btn secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="action-btn primary">
              {playbook ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default App
