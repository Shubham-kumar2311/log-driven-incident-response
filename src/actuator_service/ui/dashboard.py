"""
Actuator Service Monitoring Dashboard.

A minimal, dark-themed dashboard for monitoring action executions.
"""

DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Actuator Service - Monitoring Dashboard</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    :root {
      --bg: #0d1117;
      --surface: #161b22;
      --surface2: #1c2333;
      --surface3: #21293a;
      --border: #30363d;
      --border-light: #3d444d;
      --text: #e6edf3;
      --text2: #8b949e;
      --text3: #6e7681;
      --accent: #58a6ff;
      --accent-dim: rgba(88, 166, 255, 0.15);
      --green: #3fb950;
      --green-dim: rgba(63, 185, 80, 0.15);
      --yellow: #d29922;
      --yellow-dim: rgba(210, 153, 34, 0.15);
      --red: #f85149;
      --red-dim: rgba(248, 81, 73, 0.15);
      --orange: #db6d28;
      --orange-dim: rgba(219, 109, 40, 0.15);
      --purple: #bc8cff;
      --purple-dim: rgba(188, 140, 255, 0.15);
    }

    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      min-height: 100vh;
    }

    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--border-light); }

    /* Header */
    .header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .header-logo {
      width: 32px;
      height: 32px;
      background: linear-gradient(135deg, var(--green), var(--accent));
      border-radius: 6px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 14px;
      color: white;
    }

    .header h1 {
      font-size: 16px;
      font-weight: 600;
    }

    .header .status {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 13px;
      color: var(--text2);
    }

    .header .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--green);
      animation: pulse-dot 2s ease-in-out infinite;
    }

    .header .dot.disconnected {
      background: var(--red);
      animation: none;
    }

    @keyframes pulse-dot {
      0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(63, 185, 80, 0.4); }
      50% { opacity: 0.8; box-shadow: 0 0 0 6px rgba(63, 185, 80, 0); }
    }

    /* Main container */
    .container {
      max-width: 1400px;
      margin: 0 auto;
      padding: 20px;
    }

    /* Metrics bar */
    .metrics-bar {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }

    .metric-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      text-align: center;
      transition: border-color 0.2s;
    }

    .metric-card:hover {
      border-color: var(--border-light);
    }

    .metric-value {
      font-size: 28px;
      font-weight: 700;
      color: var(--accent);
      transition: all 0.3s ease;
    }

    .metric-value.success { color: var(--green); }
    .metric-value.failed { color: var(--red); }
    .metric-value.timeout { color: var(--yellow); }

    .metric-label {
      font-size: 11px;
      color: var(--text3);
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-top: 4px;
    }

    /* Actions panel */
    .actions-panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      margin-bottom: 24px;
    }

    .actions-header {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 12px;
      color: var(--text2);
    }

    .action-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .action-tag {
      background: var(--surface2);
      border: 1px solid var(--border);
      color: var(--accent);
      padding: 4px 12px;
      border-radius: 16px;
      font-size: 12px;
      font-family: monospace;
    }

    /* Execution table */
    .table-container {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }

    .table-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px 16px;
      border-bottom: 1px solid var(--border);
      background: var(--surface2);
    }

    .table-title {
      font-size: 14px;
      font-weight: 600;
    }

    .table-controls {
      display: flex;
      gap: 8px;
    }

    .btn {
      padding: 6px 12px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      font-size: 12px;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: var(--surface3);
      border-color: var(--border-light);
    }

    .btn-primary {
      background: var(--accent-dim);
      border-color: rgba(88, 166, 255, 0.4);
      color: var(--accent);
    }

    .btn-primary:hover {
      background: rgba(88, 166, 255, 0.25);
      border-color: var(--accent);
    }

    table {
      width: 100%;
      border-collapse: collapse;
    }

    th, td {
      padding: 12px 16px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }

    th {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: var(--text3);
      background: var(--surface);
    }

    td {
      font-size: 13px;
    }

    tr:hover td {
      background: var(--surface2);
    }

    tr:last-child td {
      border-bottom: none;
    }

    /* Status badges */
    .status-badge {
      display: inline-block;
      padding: 3px 10px;
      border-radius: 12px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
    }

    .status-success {
      background: var(--green-dim);
      color: var(--green);
    }

    .status-failed {
      background: var(--red-dim);
      color: var(--red);
    }

    .status-timeout {
      background: var(--yellow-dim);
      color: var(--yellow);
    }

    .status-no_handler {
      background: var(--orange-dim);
      color: var(--orange);
    }

    /* Mode badge */
    .mode-badge {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 10px;
      font-family: monospace;
      background: var(--surface2);
      color: var(--text2);
    }

    /* Incident ID */
    .incident-id {
      font-family: monospace;
      color: var(--accent);
      font-size: 12px;
    }

    /* Action name */
    .action-name {
      font-family: monospace;
      color: var(--purple);
    }

    /* Duration */
    .duration {
      color: var(--text2);
      font-size: 12px;
    }

    /* Timestamp */
    .timestamp {
      color: var(--text3);
      font-size: 12px;
    }

    /* Output cell */
    .output-cell {
      max-width: 300px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      color: var(--text2);
      font-size: 12px;
    }

    /* Empty state */
    .empty-state {
      text-align: center;
      padding: 48px 20px;
      color: var(--text3);
    }

    .empty-state-icon {
      font-size: 48px;
      margin-bottom: 12px;
      opacity: 0.5;
    }

    /* Flash animation */
    @keyframes flashNew {
      0% { background: rgba(63, 185, 80, 0.2); }
      100% { background: transparent; }
    }

    .flash-new {
      animation: flashNew 1s ease;
    }

    /* Responsive */
    @media (max-width: 768px) {
      .metrics-bar {
        grid-template-columns: repeat(2, 1fr);
      }

      .table-container {
        overflow-x: auto;
      }

      table {
        min-width: 700px;
      }
    }
  </style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-left">
    <div class="header-logo">A</div>
    <h1>Actuator Service</h1>
  </div>
  <div class="status">
    <div class="dot" id="status-dot"></div>
    <span id="status-text">Connecting...</span>
  </div>
</div>

<div class="container">

  <!-- Metrics -->
  <div class="metrics-bar">
    <div class="metric-card">
      <div class="metric-value" id="m-total">0</div>
      <div class="metric-label">Total Executions</div>
    </div>
    <div class="metric-card">
      <div class="metric-value success" id="m-success">0</div>
      <div class="metric-label">Success</div>
    </div>
    <div class="metric-card">
      <div class="metric-value failed" id="m-failed">0</div>
      <div class="metric-label">Failed</div>
    </div>
    <div class="metric-card">
      <div class="metric-value timeout" id="m-timeout">0</div>
      <div class="metric-label">Timeout</div>
    </div>
    <div class="metric-card">
      <div class="metric-value" id="m-rate">0%</div>
      <div class="metric-label">Success Rate</div>
    </div>
    <div class="metric-card">
      <div class="metric-value" id="m-epm">0</div>
      <div class="metric-label">Exec/min</div>
    </div>
  </div>

  <!-- Registered Actions -->
  <div class="actions-panel">
    <div class="actions-header">Registered Actions</div>
    <div class="action-tags" id="action-tags">
      <!-- Populated by JS -->
    </div>
  </div>

  <!-- Execution History Table -->
  <div class="table-container">
    <div class="table-header">
      <span class="table-title">Recent Executions</span>
      <div class="table-controls">
        <button class="btn" onclick="refreshData()">Refresh</button>
      </div>
    </div>
    <table>
      <thead>
        <tr>
          <th>Incident ID</th>
          <th>Action</th>
          <th>Status</th>
          <th>Mode</th>
          <th>Duration</th>
          <th>Output</th>
          <th>Executed At</th>
        </tr>
      </thead>
      <tbody id="executions-table">
        <tr>
          <td colspan="7" class="empty-state">
            <div class="empty-state-icon">&#9881;</div>
            <div>No executions yet</div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

</div>

<script>
  const API = '/api/dashboard-data';
  let lastExecutionCount = 0;

  function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
  }

  function formatTime(isoString) {
    if (!isoString) return '-';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });
    } catch {
      return isoString;
    }
  }

  function updateMetrics(metrics) {
    document.getElementById('m-total').textContent = metrics.total_executions || 0;
    document.getElementById('m-success').textContent = metrics.success_count || 0;
    document.getElementById('m-failed').textContent = metrics.failed_count || 0;
    document.getElementById('m-timeout').textContent = metrics.timeout_count || 0;
    document.getElementById('m-rate').textContent = (metrics.success_rate_percent || 0).toFixed(1) + '%';
    document.getElementById('m-epm').textContent = (metrics.executions_per_minute || 0).toFixed(1);
  }

  function updateActions(actions) {
    const container = document.getElementById('action-tags');
    if (!actions || actions.length === 0) {
      container.innerHTML = '<span class="action-tag">No actions registered</span>';
      return;
    }
    container.innerHTML = actions.map(a =>
      '<span class="action-tag">' + escapeHtml(a) + '</span>'
    ).join('');
  }

  function updateTable(executions) {
    const tbody = document.getElementById('executions-table');

    if (!executions || executions.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="empty-state">
            <div class="empty-state-icon">&#9881;</div>
            <div>No executions yet</div>
          </td>
        </tr>
      `;
      return;
    }

    const isNew = executions.length > lastExecutionCount;
    lastExecutionCount = executions.length;

    tbody.innerHTML = executions.map((exec, idx) => `
      <tr class="${isNew && idx === 0 ? 'flash-new' : ''}">
        <td><span class="incident-id">${escapeHtml(exec.incident_id)}</span></td>
        <td><span class="action-name">${escapeHtml(exec.action)}</span></td>
        <td><span class="status-badge status-${exec.execution_status}">${escapeHtml(exec.execution_status)}</span></td>
        <td><span class="mode-badge">${escapeHtml(exec.mode || 'subprocess')}</span></td>
        <td><span class="duration">${(exec.duration_ms || 0).toFixed(1)}ms</span></td>
        <td><span class="output-cell" title="${escapeHtml(exec.output)}">${escapeHtml(exec.output)}</span></td>
        <td><span class="timestamp">${formatTime(exec.executed_at)}</span></td>
      </tr>
    `).join('');
  }

  async function refreshData() {
    try {
      const response = await fetch(API);
      if (!response.ok) throw new Error('API error');
      const data = await response.json();

      // Update status indicator
      const dot = document.getElementById('status-dot');
      const text = document.getElementById('status-text');

      dot.classList.remove('disconnected');

      if (data.use_redis) {
        text.textContent = data.redis_connected
          ? 'Redis Connected'
          : 'Redis Disconnected';
        if (!data.redis_connected) {
          dot.classList.add('disconnected');
        }
      } else {
        text.textContent = 'API Mode (Redis Disabled)';
      }

      // Update UI
      updateMetrics(data.metrics || {});
      updateActions(data.registered_actions || []);
      updateTable(data.executions || []);

    } catch (err) {
      console.error('Failed to refresh data:', err);
      document.getElementById('status-dot').classList.add('disconnected');
      document.getElementById('status-text').textContent = 'Connection Error';
    }
  }

  // Initial load and polling
  refreshData();
  setInterval(refreshData, 2500);
</script>
</body>
</html>
"""
